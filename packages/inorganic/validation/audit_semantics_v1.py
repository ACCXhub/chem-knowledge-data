#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter, defaultdict
from math import gcd
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
        DATA / "v1" / "reactions.04.ext.jsonl",
    ],
    "phenomenon": [DATA / "phenomena.jsonl", DATA / "v1" / "phenomena.ext.jsonl"],
    "experiment": [DATA / "experiments.jsonl", DATA / "v1" / "experiments.ext.jsonl"],
    "concept": [DATA / "concepts.jsonl", DATA / "v1" / "concepts.ext.jsonl"],
    "exam_tag": [DATA / "v1" / "exam_tags.jsonl"],
}


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


def coefficient_gcd(parts: list[dict[str, Any]]) -> int:
    value = 0
    for part in parts:
        value = gcd(value, int(part["coefficient"]))
    return value


def participant_key(part: dict[str, Any]) -> tuple[str, str]:
    return part["species_id"], part["phase"]


def main() -> None:
    rows_by_kind = {
        kind: [row for path in paths for row in load_jsonl(path)]
        for kind, paths in DATA_FILES.items()
    }
    all_rows = [row for rows in rows_by_kind.values() for row in rows]
    by_id = {row["id"]: row for row in all_rows}

    errors: list[str] = []
    warnings: list[str] = []

    substances = rows_by_kind["substance"]
    reactions = rows_by_kind["reaction"]
    phenomena = rows_by_kind["phenomenon"]
    experiments = rows_by_kind["experiment"]
    tags = rows_by_kind["exam_tag"]

    # Aqueous projection semantics.
    for row in substances:
        behavior = row.get("aqueous_behavior")
        ions = row.get("ions", [])
        if behavior == "strong_electrolyte" and not ions:
            errors.append(f"{row['id']}: strong_electrolyte requires explicit ionic components")
        if behavior in {"weak_electrolyte", "weak_base", "acid_equilibrium"} and ions:
            errors.append(f"{row['id']}: {behavior} must not publish a fixed ionic split")

    # Reaction taxonomy, coefficient normalization, participant duplication and net-ionic hygiene.
    equation_signatures: defaultdict[tuple[Any, ...], list[str]] = defaultdict(list)
    for reaction in reactions:
        rid = reaction["id"]
        types = reaction.get("reaction_types", [])
        if len(types) != len(set(types)):
            errors.append(f"{rid}: duplicate reaction_types")
        if reaction.get("reversible") and "equilibrium" not in types:
            errors.append(f"{rid}: reversible=true requires equilibrium type")
        if "equilibrium" in types and not reaction.get("reversible"):
            errors.append(f"{rid}: equilibrium type requires reversible=true")
        conditions = reaction.get("conditions", [])
        if len(conditions) != len(set(conditions)):
            errors.append(f"{rid}: duplicate conditions")

        all_parts = reaction.get("reactants", []) + reaction.get("products", [])
        if coefficient_gcd(all_parts) != 1:
            errors.append(f"{rid}: molecular coefficients are not in simplest integer ratio")
        for side_name in ("reactants", "products"):
            side = reaction.get(side_name, [])
            keys = [participant_key(part) for part in side]
            if len(keys) != len(set(keys)):
                errors.append(f"{rid}: duplicate species/phase on {side_name}")
            for part in side:
                species = by_id[part["species_id"]]
                if (
                    species["kind"] == "substance"
                    and part["phase"] == "aq"
                    and species.get("aqueous_behavior") == "insoluble"
                ):
                    errors.append(f"{rid}: insoluble substance used as aq participant: {species['id']}")

        net = reaction.get("net_ionic")
        if net is not None:
            net_parts = net.get("reactants", []) + net.get("products", [])
            if coefficient_gcd(net_parts) != 1:
                errors.append(f"{rid}: net-ionic coefficients are not in simplest integer ratio")
            left = Counter(participant_key(part) for part in net.get("reactants", []))
            right = Counter(participant_key(part) for part in net.get("products", []))
            spectators = sorted(set(left).intersection(right))
            if spectators:
                errors.append(f"{rid}: net_ionic still contains spectator species {spectators}")
            for side_name in ("reactants", "products"):
                side = net.get(side_name, [])
                keys = [participant_key(part) for part in side]
                if len(keys) != len(set(keys)):
                    errors.append(f"{rid}: duplicate species/phase in net_ionic {side_name}")

        signature = (
            tuple(sorted((p["species_id"], p["coefficient"], p["phase"]) for p in reaction.get("reactants", []))),
            tuple(sorted((p["species_id"], p["coefficient"], p["phase"]) for p in reaction.get("products", []))),
            tuple(sorted(conditions)),
            reaction.get("reversible"),
        )
        equation_signatures[signature].append(rid)

    duplicate_equations = [ids for ids in equation_signatures.values() if len(ids) > 1]
    for ids in duplicate_equations:
        warnings.append("duplicate molecular reaction signature: " + ", ".join(ids))

    # Reaction <-> phenomenon duplicated links must agree in both directions.
    for reaction in reactions:
        rid = reaction["id"]
        for pid in reaction.get("phenomenon_ids", []):
            phenomenon = by_id[pid]
            if rid not in phenomenon.get("related_reaction_ids", []):
                errors.append(f"{rid}: phenomenon {pid} does not backlink to reaction")
    for phenomenon in phenomena:
        pid = phenomenon["id"]
        for rid in phenomenon.get("related_reaction_ids", []):
            reaction = by_id[rid]
            if pid not in reaction.get("phenomenon_ids", []):
                errors.append(f"{pid}: reaction {rid} does not backlink to phenomenon")

    # Experiment observations must be explainable by at least one reaction in the same experiment.
    for experiment in experiments:
        reaction_ids = set(experiment.get("reaction_ids", []))
        for pid in experiment.get("expected_phenomenon_ids", []):
            linked = set(by_id[pid].get("related_reaction_ids", []))
            if reaction_ids.isdisjoint(linked):
                errors.append(f"{experiment['id']}: expected phenomenon {pid} has no linked experiment reaction")

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
    if orphan_core_substances:
        errors.append("core substances without any reaction links: " + ",".join(orphan_core_substances))

    # Core element projections need at least one canonical substance representation.
    element_species_count: Counter[str] = Counter()
    for substance in substances:
        for symbol in substance.get("composition", {}):
            element_species_count[symbol] += 1
    empty_core_elements = [
        row["id"] for row in rows_by_kind["element_scope"]
        if row.get("teaching_priority") == "core" and element_species_count[row["symbol"]] == 0
    ]
    if empty_core_elements:
        errors.append("core elements without species representation: " + ",".join(empty_core_elements))

    empty_core_tags = [
        row["id"] for row in tags
        if row.get("teaching_priority") == "core" and not row.get("related_concept_ids")
    ]
    if empty_core_tags:
        errors.append("core exam tags without concept links: " + ",".join(empty_core_tags))

    net_ionic_count = sum(1 for row in reactions if row.get("net_ionic") is not None)
    category_counts = Counter(row.get("category") for row in substances)
    phase_counts = Counter(row.get("ambient_phase") for row in substances)
    type_counts = Counter(t for row in reactions for t in row.get("reaction_types", []))

    # Provenance quality is reported separately from verification_targets; only actual sources count here.
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
    print(f"orphan_common_substances={len(orphan_common_substances)}")
    if orphan_common_substances:
        print("orphan_common_substance_ids=" + ",".join(orphan_common_substances))
    print(f"core_elements_without_species={len(empty_core_elements)}")
    print(f"core_exam_tags_without_concepts={len(empty_core_tags)}")
    print(f"duplicate_reaction_signatures={len(duplicate_equations)}")

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
