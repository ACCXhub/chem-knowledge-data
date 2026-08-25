#!/usr/bin/env python3
from __future__ import annotations

import json
import math
import re
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RULES = ROOT / "rules"
CURRICULUM = ROOT / "curriculum" / "coverage.json"

DATA_FILES: dict[str, list[Path]] = {
    "element_scope": [DATA / "element_scope.jsonl", DATA / "v1" / "element_scope.ext.jsonl"],
    "ion": [DATA / "ions.jsonl", DATA / "v1" / "ions.ext.jsonl"],
    "substance": [
        DATA / "substances.jsonl",
        DATA / "v1" / "substances.01.ext.jsonl",
        DATA / "v1" / "substances.02.ext.jsonl",
        DATA / "v1" / "substances.03.ext.jsonl",
    ],
    "reaction": [
        DATA / "reactions.jsonl",
        DATA / "v1" / "reactions.01.ext.jsonl",
        DATA / "v1" / "reactions.02.ext.jsonl",
        DATA / "v1" / "reactions.03.ext.jsonl",
    ],
    "phenomenon": [DATA / "phenomena.jsonl", DATA / "v1" / "phenomena.ext.jsonl"],
    "experiment": [DATA / "experiments.jsonl", DATA / "v1" / "experiments.ext.jsonl"],
    "concept": [DATA / "concepts.jsonl", DATA / "v1" / "concepts.ext.jsonl"],
    "exam_tag": [DATA / "v1" / "exam_tags.jsonl"],
}

EXPECTED_PREFIX = {
    "element_scope": "element-scope:",
    "ion": "ion:",
    "substance": "substance:",
    "reaction": "reaction:",
    "phenomenon": "phenomenon:",
    "experiment": "experiment:",
    "concept": "concept:",
    "exam_tag": "examtag:",
}


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def merge_counts(target: dict[str, int], source: dict[str, int], factor: int = 1) -> None:
    for key, value in source.items():
        target[key] = target.get(key, 0) + value * factor


def parse_formula_unit(text: str, start: int = 0, closing: str | None = None) -> tuple[dict[str, int], int]:
    counts: dict[str, int] = {}
    i = start
    while i < len(text):
        ch = text[i]
        if closing and ch == closing:
            return counts, i + 1
        if ch in "([":
            inner, i = parse_formula_unit(text, i + 1, ")" if ch == "(" else "]")
            m = re.match(r"\d+", text[i:])
            factor = int(m.group(0)) if m else 1
            if m:
                i += len(m.group(0))
            merge_counts(counts, inner, factor)
            continue
        if ch.isupper():
            symbol = ch
            i += 1
            if i < len(text) and text[i].islower():
                symbol += text[i]
                i += 1
            m = re.match(r"\d+", text[i:])
            factor = int(m.group(0)) if m else 1
            if m:
                i += len(m.group(0))
            counts[symbol] = counts.get(symbol, 0) + factor
            continue
        raise ValueError(f"unsupported formula token {ch!r} in {text!r}")
    if closing:
        raise ValueError(f"unclosed group {closing!r} in {text!r}")
    return counts, i


def parse_formula(formula: str) -> dict[str, int]:
    total: dict[str, int] = {}
    for part in re.split(r"[·.]", formula):
        if not part:
            continue
        m = re.match(r"^(\d+)(.*)$", part)
        factor = int(m.group(1)) if m else 1
        body = m.group(2) if m else part
        counts, end = parse_formula_unit(body)
        if end != len(body):
            raise ValueError(f"unparsed suffix in {formula!r}")
        merge_counts(total, counts, factor)
    return total


def gcd_coefficients(reaction: dict[str, Any]) -> int:
    values = [p["coefficient"] for side in ("reactants", "products") for p in reaction[side]]
    result = 0
    for value in values:
        result = math.gcd(result, value)
    return result


def main() -> None:
    rows_by_kind = {
        kind: [row for path in paths for row in load_jsonl(path)]
        for kind, paths in DATA_FILES.items()
    }
    rows = [row for group in rows_by_kind.values() for row in group]
    by_id = {row["id"]: row for row in rows}

    errors: list[str] = []
    warnings: list[str] = []

    # Identity / shape audit independent of validate_v1.py.
    for kind, group in rows_by_kind.items():
        prefix = EXPECTED_PREFIX[kind]
        for row in group:
            rid = row.get("id")
            if not isinstance(rid, str) or not rid.startswith(prefix):
                errors.append(f"{rid}: expected id prefix {prefix}")
            if not isinstance(row.get("teaching_priority"), str):
                errors.append(f"{rid}: teaching_priority missing/non-string")
            if not isinstance(row.get("review_status"), str):
                errors.append(f"{rid}: review_status missing/non-string")

    # Formula -> composition audit.
    formula_failures: list[str] = []
    for row in rows_by_kind["ion"] + rows_by_kind["substance"]:
        rid = row["id"]
        try:
            parsed = parse_formula(row["formula"])
        except Exception as exc:  # audit should report every unsupported formula
            formula_failures.append(f"{rid}: parse error: {exc}")
            continue
        if parsed != row["composition"]:
            formula_failures.append(f"{rid}: formula {row['formula']} -> {parsed}, stored {row['composition']}")
    errors.extend(formula_failures)

    # Reaction canonicality beyond conservation: simplest integer coefficients and duplicate participants.
    nonminimal: list[str] = []
    duplicate_side: list[str] = []
    for reaction in rows_by_kind["reaction"]:
        rid = reaction["id"]
        g = gcd_coefficients(reaction)
        if g != 1:
            nonminimal.append(f"{rid}: coefficient gcd={g}")
        for side in ("reactants", "products"):
            ids = [part["species_id"] for part in reaction[side]]
            dup = sorted(key for key, count in Counter(ids).items() if count > 1)
            if dup:
                duplicate_side.append(f"{rid}:{side}: duplicate species {dup}")
    errors.extend(nonminimal)
    errors.extend(duplicate_side)

    # Bidirectional reaction <-> phenomenon consistency.
    asymmetry: list[str] = []
    for reaction in rows_by_kind["reaction"]:
        for pid in reaction.get("phenomenon_ids", []):
            phenomenon = by_id.get(pid)
            if phenomenon and reaction["id"] not in phenomenon.get("related_reaction_ids", []):
                asymmetry.append(f"{reaction['id']} -> {pid} missing reverse link")
    for phenomenon in rows_by_kind["phenomenon"]:
        for rid in phenomenon.get("related_reaction_ids", []):
            reaction = by_id.get(rid)
            if reaction and phenomenon["id"] not in reaction.get("phenomenon_ids", []):
                asymmetry.append(f"{phenomenon['id']} -> {rid} missing reverse link")
    warnings.extend(asymmetry)

    # Report semantic pressure points rather than pretending they are automatically wrong.
    aq_behavior = Counter(row.get("aqueous_behavior") for row in rows_by_kind["substance"])
    aq_ambient = [row["id"] for row in rows_by_kind["substance"] if row.get("ambient_phase") == "aq"]
    insoluble_with_ions = [
        row["id"]
        for row in rows_by_kind["substance"]
        if row.get("aqueous_behavior") in {"insoluble", "sparingly_soluble"} and row.get("ions")
    ]

    review_counts = Counter(row.get("review_status") for row in rows)
    source_counts = Counter(source for row in rows for source in row.get("sources", []))
    externally_sourced = [
        row["id"]
        for row in rows
        if any(source not in {"src:editorial-hs-inorganic-v1", "src:moe-hs-chem-2020"} for source in row.get("sources", []))
    ]

    core_concept_empty = [
        row["id"]
        for row in rows_by_kind["concept"]
        if row.get("teaching_priority") == "core"
        and not row.get("related_reaction_ids")
        and not row.get("related_species_ids")
    ]

    coverage = load_json(CURRICULUM)
    coverage_rows: list[tuple[str, int, int, int]] = []
    for domain in coverage.get("domains", []):
        linked_reactions: set[str] = set()
        for cid in domain.get("concept_ids", []):
            concept = by_id.get(cid)
            if concept:
                linked_reactions.update(concept.get("related_reaction_ids", []))
        coverage_rows.append((
            domain["id"],
            len(domain.get("concept_ids", [])),
            len(domain.get("exam_tag_ids", [])),
            len(linked_reactions),
        ))

    print("inorganic v1 independent audit")
    print(f"records={len(rows)} reactions={len(rows_by_kind['reaction'])} substances={len(rows_by_kind['substance'])}")
    print(f"review_status={dict(review_counts)}")
    print(f"externally_sourced_records={len(externally_sourced)}")
    print(f"source_usage={dict(source_counts)}")
    print(f"aqueous_behavior={dict(aq_behavior)}")
    print(f"ambient_phase_aq={len(aq_ambient)}")
    if aq_ambient:
        print("ambient_phase_aq_ids=" + ",".join(aq_ambient))
    print(f"insoluble_or_sparingly_soluble_with_ions={len(insoluble_with_ions)}")
    if insoluble_with_ions:
        print("insoluble_with_ions_ids=" + ",".join(insoluble_with_ions))
    print(f"core_concepts_without_links={len(core_concept_empty)}")
    if core_concept_empty:
        print("core_concepts_without_links_ids=" + ",".join(core_concept_empty))
    print("coverage_density:")
    for domain_id, concepts, tags, linked_reactions in coverage_rows:
        print(f"  {domain_id}: concepts={concepts} tags={tags} linked_reactions={linked_reactions}")

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print("  " + warning)
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("audit hard checks: OK")


if __name__ == "__main__":
    main()
