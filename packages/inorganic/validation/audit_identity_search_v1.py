#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

ION_FILES = [DATA / "ions.jsonl", DATA / "v1" / "ions.ext.jsonl"]
SUBSTANCE_FILES = [
    DATA / "substances.jsonl",
    DATA / "v1" / "substances.01.ext.jsonl",
    DATA / "v1" / "substances.02.ext.jsonl",
    DATA / "v1" / "substances.03.ext.jsonl",
]


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def normalized(text: str) -> str:
    return " ".join(text.casefold().strip().split())


def main() -> None:
    ions = [row for path in ION_FILES for row in load_jsonl(path)]
    substances = [row for path in SUBSTANCE_FILES for row in load_jsonl(path)]
    errors: list[str] = []
    warnings: list[str] = []

    ion_signatures: defaultdict[tuple[str, int], list[str]] = defaultdict(list)
    for row in ions:
        ion_signatures[(row["formula"], row["charge"])].append(row["id"])
    for signature, ids in ion_signatures.items():
        if len(ids) > 1:
            errors.append(f"duplicate ion formula/charge identity {signature}: {', '.join(ids)}")

    substance_formulas: defaultdict[str, list[str]] = defaultdict(list)
    for row in substances:
        substance_formulas[row["formula"]].append(row["id"])
    duplicate_substance_formulas = {formula: ids for formula, ids in substance_formulas.items() if len(ids) > 1}
    for formula, ids in sorted(duplicate_substance_formulas.items()):
        warnings.append(f"shared substance formula {formula}: {', '.join(ids)}")

    for kind, rows in (("ion", ions), ("substance", substances)):
        primary_names: defaultdict[tuple[str, str], list[str]] = defaultdict(list)
        search_terms: defaultdict[str, set[str]] = defaultdict(set)
        for row in rows:
            for field in ("name_zh", "name_en"):
                value = row.get(field)
                if isinstance(value, str) and value.strip():
                    primary_names[(field, normalized(value))].append(row["id"])
                    search_terms[normalized(value)].add(row["id"])
            for alias in row.get("aliases", []):
                search_terms[normalized(alias)].add(row["id"])

        for (field, term), ids in primary_names.items():
            if len(ids) > 1:
                errors.append(f"duplicate {kind} primary {field}={term!r}: {', '.join(ids)}")
        collisions = [(term, sorted(ids)) for term, ids in search_terms.items() if len(ids) > 1]
        for term, ids in sorted(collisions):
            warnings.append(f"ambiguous {kind} search term {term!r}: {', '.join(ids)}")

    print("inorganic v1 identity/search collision audit")
    print(f"ions={len(ions)} substances={len(substances)}")
    print(f"duplicate_substance_formula_groups={len(duplicate_substance_formulas)}")
    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print("  " + warning)
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("identity/search hard checks: OK")


if __name__ == "__main__":
    main()
