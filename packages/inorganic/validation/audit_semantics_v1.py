#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"

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


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def main() -> None:
    rows_by_kind = {
        kind: [row for path in paths for row in load_jsonl(path)]
        for kind, paths in DATA_FILES.items()
    }
    errors: list[str] = []
    warnings: list[str] = []

    substances = rows_by_kind["substance"]
    reactions = rows_by_kind["reaction"]
    tags = rows_by_kind["exam_tag"]

    # Electrolyte projection semantics. A strong electrolyte with no explicit ions can be
    # intentional when the high-school projection is equilibrium-sensitive (for example
    # chromic/dichromic acid). Such cases need consumer review, but are not auto-rewritten.
    for row in substances:
        behavior = row.get("aqueous_behavior")
        ions = row.get("ions", [])
        if behavior == "strong_electrolyte" and not ions:
            warnings.append(f"{row['id']}: strong_electrolyte has no explicit ionic projection")
        if behavior in {"weak_electrolyte", "weak_base"} and ions:
            errors.append(f"{row['id']}: weak electrolyte/base unexpectedly has ionic components")

    # Reversible/equilibrium semantics and duplicate taxonomy values.
    for reaction in reactions:
        rid = reaction["id"]
        types = reaction.get("reaction_types", [])
        if len(types) != len(set(types)):
            errors.append(f"{rid}: duplicate reaction_types")
        if reaction.get("reversible") and "equilibrium" not in types:
            warnings.append(f"{rid}: reversible=true without equilibrium type")
        if "equilibrium" in types and not reaction.get("reversible"):
            errors.append(f"{rid}: equilibrium type but reversible=false")
        conditions = reaction.get("conditions", [])
        if len(conditions) != len(set(conditions)):
            errors.append(f"{rid}: duplicate conditions")

    # Link-density audit for consumer readiness.
    substance_reaction_count: Counter[str] = Counter()
    for reaction in reactions:
        for part in reaction.get("reactants", []) + reaction.get("products", []):
            sid = part["species_id"]
            if sid.startswith("substance:"):
                substance_reaction_count[sid] += 1

    orphan_core_substances = [
        row["id"] for row in substances
        if row.get("teaching_priority") == "core" and substance_reaction_count[row["id"]] == 0
    ]
    orphan_common_substances = [
        row["id"] for row in substances
        if row.get("teaching_priority") == "common" and substance_reaction_count[row["id"]] == 0
    ]

    # Element teaching projections should normally have at least one species representation.
    element_species_count: Counter[str] = Counter()
    for substance in substances:
        for symbol in substance.get("composition", {}):
            element_species_count[symbol] += 1
    empty_core_elements = [
        row["id"] for row in rows_by_kind["element_scope"]
        if row.get("teaching_priority") == "core" and element_species_count[row["symbol"]] == 0
    ]

    empty_core_tags = [
        row["id"] for row in tags
        if row.get("teaching_priority") == "core" and not row.get("related_concept_ids")
    ]

    net_ionic_count = sum(1 for row in reactions if row.get("net_ionic") is not None)
    category_counts = Counter(row.get("category") for row in substances)
    phase_counts = Counter(row.get("ambient_phase") for row in substances)
    type_counts = Counter(t for row in reactions for t in row.get("reaction_types", []))

    # Provenance quality by chemistry-bearing kind.
    external_source_keys = {"src:iupac-periodic-table-2022", "src:chebi", "src:pubchem", "src:nist-webbook"}
    for kind in ("ion", "substance", "reaction", "phenomenon", "experiment", "concept"):
        group = rows_by_kind[kind]
        externally_sourced = sum(
            1 for row in group if external_source_keys.intersection(row.get("sources", []))
        )
        print(f"external_source_coverage[{kind}]={externally_sourced}/{len(group)}")

    print(f"net_ionic_records={net_ionic_count}/{len(reactions)}")
    print(f"substance_categories={dict(category_counts)}")
    print(f"substance_ambient_phases={dict(phase_counts)}")
    print(f"reaction_type_counts={dict(type_counts)}")
    print(f"orphan_core_substances={len(orphan_core_substances)}")
    if orphan_core_substances:
        print("orphan_core_substance_ids=" + ",".join(orphan_core_substances))
    print(f"orphan_common_substances={len(orphan_common_substances)}")
    if orphan_common_substances:
        print("orphan_common_substance_ids=" + ",".join(orphan_common_substances))
    print(f"core_elements_without_species={len(empty_core_elements)}")
    if empty_core_elements:
        print("core_elements_without_species_ids=" + ",".join(empty_core_elements))
    print(f"core_exam_tags_without_concepts={len(empty_core_tags)}")
    if empty_core_tags:
        print("core_exam_tags_without_concepts_ids=" + ",".join(empty_core_tags))

    if warnings:
        print("WARNINGS:")
        for warning in warnings:
            print("  " + warning)
    if errors:
        print("ERRORS:")
        for error in errors:
            print("  " + error)
        raise SystemExit(1)
    print("semantic hard checks: OK")


if __name__ == "__main__":
    main()
