#!/usr/bin/env python3
from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
RULES = ROOT / "rules"
CURRICULUM = ROOT / "curriculum" / "coverage.json"
SOURCES = ROOT / "sources" / "source_registry.json"
MANIFEST = ROOT / "manifest.json"
SCHEMA = ROOT / "schema" / "catalog-v1.schema.json"

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

RULE_FILES = [
    RULES / "solubility.json",
    RULES / "electrolytes.json",
    RULES / "oxidation_states.json",
    RULES / "metal_activity.json",
    RULES / "flame_tests.json",
    RULES / "qualitative_tests.json",
    RULES / "equation_composer.json",
]

PRIORITIES = {"core", "common", "extended"}
REVIEW = {"seed", "reviewed", "published"}
PHASES = {"s", "l", "g", "aq"}
KNOWN_ID_PREFIXES = (
    "ion:",
    "substance:",
    "reaction:",
    "phenomenon:",
    "experiment:",
    "concept:",
    "examtag:",
)


def load_json(path: Path) -> Any:
    assert path.exists(), f"missing required file: {path.relative_to(ROOT)}"
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"{path.relative_to(ROOT)}: invalid JSON: {exc}") from exc


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    assert path.exists(), f"missing required file: {path.relative_to(ROOT)}"
    rows: list[dict[str, Any]] = []
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path.relative_to(ROOT)}:{lineno}: invalid JSON: {exc}") from exc
        assert isinstance(row, dict), f"{path.relative_to(ROOT)}:{lineno}: record must be object"
        rows.append(row)
    return rows


def aggregate(parts: list[dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> tuple[dict[str, int], int]:
    atoms: dict[str, int] = {}
    charge = 0
    for part in parts:
        coeff = part.get("coefficient")
        assert isinstance(coeff, int) and coeff > 0, f"invalid coefficient: {part}"
        phase = part.get("phase")
        assert phase in PHASES, f"invalid phase: {part}"
        sid = part.get("species_id")
        assert isinstance(sid, str) and sid in by_id, f"unknown species: {sid}"
        species = by_id[sid]
        assert species["kind"] in {"ion", "substance"}, f"participant must be ion/substance: {sid}"
        for element, count in species["composition"].items():
            atoms[element] = atoms.get(element, 0) + count * coeff
        charge += species.get("charge", 0) * coeff
    return atoms, charge


def walk_stable_refs(value: Any) -> list[str]:
    refs: list[str] = []
    if isinstance(value, str):
        if value.startswith(KNOWN_ID_PREFIXES):
            refs.append(value)
    elif isinstance(value, list):
        for item in value:
            refs.extend(walk_stable_refs(item))
    elif isinstance(value, dict):
        for item in value.values():
            refs.extend(walk_stable_refs(item))
    return refs


def composition_from_ions(items: list[dict[str, Any]], by_id: dict[str, dict[str, Any]]) -> tuple[dict[str, int], int]:
    composition: dict[str, int] = {}
    total_charge = 0
    for item in items:
        iid = item.get("ion_id")
        coeff = item.get("coefficient")
        assert isinstance(iid, str) and iid in by_id and by_id[iid]["kind"] == "ion", f"unknown ion {iid}"
        assert isinstance(coeff, int) and coeff > 0, f"invalid ion coefficient: {item}"
        ion = by_id[iid]
        total_charge += ion["charge"] * coeff
        for element, count in ion["composition"].items():
            composition[element] = composition.get(element, 0) + count * coeff
    return composition, total_charge


def main() -> None:
    source_registry = load_json(SOURCES)
    source_ids = [row["id"] for row in source_registry["sources"]]
    assert len(source_ids) == len(set(source_ids)), "duplicate source id"
    source_set = set(source_ids)

    # Parse schema as part of the release contract even though validation is dependency-free.
    schema = load_json(SCHEMA)
    assert schema.get("$schema") and schema.get("oneOf"), "v1 schema is incomplete"

    rows_by_kind: dict[str, list[dict[str, Any]]] = {}
    for kind, paths in DATA_FILES.items():
        rows_by_kind[kind] = [row for path in paths for row in load_jsonl(path)]

    all_rows = [row for rows in rows_by_kind.values() for row in rows]
    ids = [row.get("id") for row in all_rows]
    assert all(isinstance(item, str) and item for item in ids), "every canonical record requires id"
    duplicates = sorted(key for key, count in Counter(ids).items() if count > 1)
    assert not duplicates, f"duplicate canonical ids: {duplicates}"
    by_id = {row["id"]: row for row in all_rows}

    for expected_kind, rows in rows_by_kind.items():
        for row in rows:
            rid = row["id"]
            assert row.get("kind") == expected_kind, f"{rid}: kind mismatch, expected {expected_kind}"
            assert row.get("teaching_priority") in PRIORITIES, f"{rid}: invalid teaching_priority"
            assert row.get("review_status") in REVIEW, f"{rid}: invalid review_status"
            sources = row.get("sources")
            assert isinstance(sources, list) and sources and len(sources) == len(set(sources)), f"{rid}: sources required/unique"
            unknown_sources = set(sources) - source_set
            assert not unknown_sources, f"{rid}: unknown source keys {sorted(unknown_sources)}"
            targets = row.get("verification_targets", [])
            assert isinstance(targets, list), f"{rid}: verification_targets must be list"
            unknown_targets = set(targets) - source_set
            assert not unknown_targets, f"{rid}: unknown verification targets {sorted(unknown_targets)}"

    elements = rows_by_kind["element_scope"]
    assert len({row["symbol"] for row in elements}) == len(elements), "duplicate element symbol"
    assert len({row["atomic_number"] for row in elements}) == len(elements), "duplicate atomic number"
    for row in elements:
        assert 1 <= row["atomic_number"] <= 118, f"{row['id']}: atomic number out of range"

    for row in rows_by_kind["ion"] + rows_by_kind["substance"]:
        composition = row.get("composition")
        assert isinstance(composition, dict) and composition, f"{row['id']}: composition required"
        for element, count in composition.items():
            assert isinstance(element, str) and element, f"{row['id']}: invalid element key"
            assert isinstance(count, int) and count > 0, f"{row['id']}: invalid composition count"

    for ion in rows_by_kind["ion"]:
        assert isinstance(ion.get("charge"), int) and ion["charge"] != 0, f"{ion['id']}: nonzero integer charge required"

    for substance in rows_by_kind["substance"]:
        projection = substance.get("ions", [])
        assert isinstance(projection, list), f"{substance['id']}: ions must be list"
        if projection:
            projected_composition, total_charge = composition_from_ions(projection, by_id)
            assert total_charge == 0, f"{substance['id']}: ionic projection is not neutral"
            assert projected_composition == substance["composition"], (
                f"{substance['id']}: ionic projection composition mismatch: "
                f"{projected_composition} != {substance['composition']}"
            )

    for reaction in rows_by_kind["reaction"]:
        rid = reaction["id"]
        reactants = reaction.get("reactants")
        products = reaction.get("products")
        assert isinstance(reactants, list) and reactants, f"{rid}: reactants required"
        assert isinstance(products, list) and products, f"{rid}: products required"
        left_atoms, left_charge = aggregate(reactants, by_id)
        right_atoms, right_charge = aggregate(products, by_id)
        assert left_atoms == right_atoms, f"{rid}: atom conservation failed: {left_atoms} != {right_atoms}"
        assert left_charge == right_charge, f"{rid}: charge conservation failed: {left_charge} != {right_charge}"
        assert isinstance(reaction.get("reaction_types"), list) and reaction["reaction_types"], f"{rid}: reaction_types required"
        assert isinstance(reaction.get("conditions"), list), f"{rid}: conditions must be list"
        assert isinstance(reaction.get("reversible"), bool), f"{rid}: reversible must be bool"
        for pid in reaction.get("phenomenon_ids", []):
            assert pid in by_id and by_id[pid]["kind"] == "phenomenon", f"{rid}: unknown phenomenon {pid}"
        net = reaction.get("net_ionic")
        if net is not None:
            assert isinstance(net, dict), f"{rid}: net_ionic must be object/null"
            n_left_atoms, n_left_charge = aggregate(net.get("reactants", []), by_id)
            n_right_atoms, n_right_charge = aggregate(net.get("products", []), by_id)
            assert n_left_atoms == n_right_atoms, f"{rid}: net ionic atom conservation failed"
            assert n_left_charge == n_right_charge, f"{rid}: net ionic charge conservation failed"

    for phenomenon in rows_by_kind["phenomenon"]:
        for rid in phenomenon.get("related_reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{phenomenon['id']}: unknown reaction {rid}"

    for experiment in rows_by_kind["experiment"]:
        assert experiment.get("delivery_mode") in {"student", "teacher_demo"}, f"{experiment['id']}: invalid delivery_mode"
        for rid in experiment.get("reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{experiment['id']}: unknown reaction {rid}"
        for pid in experiment.get("expected_phenomenon_ids", []):
            assert pid in by_id and by_id[pid]["kind"] == "phenomenon", f"{experiment['id']}: unknown phenomenon {pid}"

    for concept in rows_by_kind["concept"]:
        for rid in concept.get("related_reaction_ids", []):
            assert rid in by_id and by_id[rid]["kind"] == "reaction", f"{concept['id']}: unknown reaction {rid}"
        for sid in concept.get("related_species_ids", []):
            assert sid in by_id and by_id[sid]["kind"] in {"ion", "substance"}, f"{concept['id']}: unknown species {sid}"

    for tag in rows_by_kind["exam_tag"]:
        assert tag["id"].startswith("examtag:"), f"{tag['id']}: exam tag id prefix must be examtag:"
        for cid in tag.get("related_concept_ids", []):
            assert cid in by_id and by_id[cid]["kind"] == "concept", f"{tag['id']}: unknown concept {cid}"

    loaded_rules: list[dict[str, Any]] = []
    for path in RULE_FILES:
        rule = load_json(path)
        loaded_rules.append(rule)
        assert isinstance(rule.get("rule_set"), str) and rule["rule_set"], f"{path.name}: rule_set required"
        unknown_sources = set(rule.get("sources", [])) - source_set
        assert not unknown_sources, f"{path.name}: unknown source keys {sorted(unknown_sources)}"
        for ref in walk_stable_refs(rule):
            assert ref in by_id, f"{path.name}: unresolved canonical reference {ref}"
    assert len({rule["rule_set"] for rule in loaded_rules}) == len(loaded_rules), "duplicate rule_set name"

    coverage = load_json(CURRICULUM)
    unknown_sources = set(coverage.get("sources", [])) - source_set
    assert not unknown_sources, f"coverage: unknown source keys {sorted(unknown_sources)}"
    for ref in walk_stable_refs(coverage):
        assert ref in by_id, f"coverage: unresolved canonical reference {ref}"
    assert coverage.get("coverage_status") == "core_complete_for_v1", "coverage map not marked complete"

    manifest = load_json(MANIFEST)
    actual_counts = {
        "element_scope": len(rows_by_kind["element_scope"]),
        "ions": len(rows_by_kind["ion"]),
        "substances": len(rows_by_kind["substance"]),
        "reactions": len(rows_by_kind["reaction"]),
        "phenomena": len(rows_by_kind["phenomenon"]),
        "experiments": len(rows_by_kind["experiment"]),
        "concepts": len(rows_by_kind["concept"]),
        "exam_tags": len(rows_by_kind["exam_tag"]),
    }
    assert manifest.get("record_counts") == actual_counts, (
        f"manifest count mismatch: {manifest.get('record_counts')} != {actual_counts}"
    )
    assert manifest.get("total_records") == sum(actual_counts.values()), "manifest total_records mismatch"
    assert len(manifest.get("rule_files", [])) == 7, "manifest must list seven rule files"
    for relpath in manifest["rule_files"]:
        assert (ROOT / relpath).exists(), f"manifest references missing rule file {relpath}"
    assert (ROOT / manifest["curriculum_file"]).exists(), "manifest curriculum_file missing"
    assert (ROOT / manifest["schema_file"]).exists(), "manifest schema_file missing"
    assert (ROOT / manifest["source_review"]).exists(), "manifest source_review missing"

    print("inorganic v1 validation: OK")
    for key, value in actual_counts.items():
        print(f"  {key}: {value}")
    print(f"  total canonical records: {sum(actual_counts.values())}")
    print(f"  rule sets: {len(loaded_rules)}")
    print(f"  curriculum domains: {len(coverage.get('domains', []))}")


if __name__ == "__main__":
    main()
