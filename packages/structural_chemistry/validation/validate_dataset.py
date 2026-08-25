from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

DATA_FILES = {
    "atomic_configurations": ROOT / "data" / "atomic_configurations.jsonl",
    "concepts": ROOT / "data" / "concepts.jsonl",
    "vsepr_models": ROOT / "data" / "vsepr_models.jsonl",
    "molecular_examples": ROOT / "data" / "molecular_examples.jsonl",
    "bonding_examples": ROOT / "data" / "bonding_examples.jsonl",
    "crystal_models": ROOT / "data" / "crystal_models.jsonl",
    "coordination_examples": ROOT / "data" / "coordination_examples.jsonl",
    "relations": ROOT / "data" / "relations.jsonl",
    "structure_property_rules": ROOT / "data" / "structure_property_rules.jsonl",
    "exam_tags": ROOT / "data" / "exam_tags.jsonl",
}

REQUIRED_SCHEMAS = {
    "atomic_configuration.schema.json",
    "concept.schema.json",
    "vsepr_model.schema.json",
    "molecular_structure_example.schema.json",
    "bonding_example.schema.json",
    "crystal_model.schema.json",
    "coordination_example.schema.json",
    "relation.schema.json",
    "structure_property_rule.schema.json",
    "exam_tag.schema.json",
    "curriculum_scope.schema.json",
}

REQUIRED_CURRICULUM_IDS = {
    "sc:curriculum:1.1",
    "sc:curriculum:1.2",
    "sc:curriculum:1.3",
    "sc:curriculum:2.1",
    "sc:curriculum:2.2",
    "sc:curriculum:2.3",
    "sc:curriculum:2.4",
    "sc:curriculum:2.5",
    "sc:curriculum:3.1",
    "sc:curriculum:3.2",
    "sc:curriculum:3.3",
}

REQUIRED_THEME3_CONCEPTS = {
    "sc:concept:supramolecular_structure",
    "sc:concept:multiscale_structure",
    "sc:concept:atomic_spectroscopy",
    "sc:concept:molecular_spectroscopy",
    "sc:concept:xray_diffraction",
    "sc:concept:structure_evidence",
    "sc:concept:structure_guided_design",
}

REQUIRED_THEME3_EXAM_TAGS = {
    "sc:exam-tag:multiscale_structure",
    "sc:exam-tag:structure_methods",
    "sc:exam-tag:structure_research_value",
}


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
    return rows


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "sources" / "source_registry.json").read_text(encoding="utf-8"))
    curriculum = json.loads((ROOT / "curriculum" / "scope.json").read_text(encoding="utf-8"))
    coverage = json.loads((ROOT / "curriculum" / "coverage.json").read_text(encoding="utf-8"))
    source_keys = {row["key"] for row in registry["sources"]}

    schema_files = {path.name for path in (ROOT / "schema").glob("*.schema.json")}
    missing_schemas = REQUIRED_SCHEMAS - schema_files
    assert not missing_schemas, f"missing schemas: {sorted(missing_schemas)}"

    datasets = {name: load_jsonl(path) for name, path in DATA_FILES.items()}
    datasets["curriculum_scope"] = curriculum
    all_rows = [row for rows in datasets.values() for row in rows]
    ids = [row["id"] for row in all_rows]
    assert len(ids) == len(set(ids)), "duplicate package-local IDs"

    for row in all_rows:
        assert row.get("status") == "published", f"{row['id']}: status must be published"
        refs = row.get("source_refs", [])
        assert refs, f"{row['id']}: source_refs required"
        unknown = set(refs) - source_keys
        assert not unknown, f"{row['id']}: unknown source refs {sorted(unknown)}"

    atomic = datasets["atomic_configurations"]
    assert [row["atomic_number"] for row in atomic] == list(range(1, 37)), "atomic numbers must cover 1..36 in order"
    assert len({row["symbol"] for row in atomic}) == 36, "atomic symbols must be unique"
    by_symbol = {row["symbol"]: row for row in atomic}
    assert by_symbol["Cr"]["ground_state_configuration"] == "[Ar] 3d5 4s1"
    assert by_symbol["Cu"]["ground_state_configuration"] == "[Ar] 3d10 4s1"
    assert by_symbol["Cr"]["special_case"] is True and by_symbol["Cu"]["special_case"] is True

    concepts = datasets["concepts"]
    concept_ids = {row["id"] for row in concepts}
    exam_ids = {row["id"] for row in datasets["exam_tags"]}
    assert REQUIRED_THEME3_CONCEPTS <= concept_ids, "curriculum theme 3 concept coverage regressed"
    assert REQUIRED_THEME3_EXAM_TAGS <= exam_ids, "curriculum theme 3 exam-tag coverage regressed"

    for row in datasets["relations"]:
        assert row["source_ref"] in concept_ids, f"{row['id']}: bad source_ref"
        assert row["target_ref"] in concept_ids, f"{row['id']}: bad target_ref"

    for row in datasets["exam_tags"]:
        missing = set(row["concept_refs"]) - concept_ids
        assert not missing, f"{row['id']}: missing concept refs {sorted(missing)}"

    scopes = {"intramolecular", "intermolecular", "lattice", "formation_model", "intracomplex"}
    for row in datasets["bonding_examples"]:
        for interaction in row["interactions"]:
            assert interaction["concept_ref"] in concept_ids, f"{row['id']}: unknown interaction concept"
            assert interaction["scope"] in scopes, f"{row['id']}: invalid interaction scope"

    for row in datasets["crystal_models"]:
        assert row["crystal_class"] in concept_ids, f"{row['id']}: unknown crystal class"

    for row in datasets["structure_property_rules"]:
        assert row["structure_concept_ref"] in concept_ids, f"{row['id']}: unknown structure concept"
        assert row.get("qualifier"), f"{row['id']}: generalized rule requires qualifier"

    vsepr_patterns = {row["ax_e_notation"] for row in datasets["vsepr_models"]}
    for row in datasets["vsepr_models"]:
        assert row["electron_domains"] == row["bonded_atoms"] + row["lone_pairs_on_central"], f"{row['id']}: electron-domain count mismatch"
    assert len(vsepr_patterns) == len(datasets["vsepr_models"]), "duplicate VSEPR pattern"

    allowed_hybrid = {None, "sp", "sp2", "sp3"}
    for row in datasets["molecular_examples"]:
        assert row["central_hybridization_model"] in allowed_hybrid, f"{row['id']}: unsupported hybridization truth claim"
        pattern = row["vsepr_pattern"]
        if pattern.startswith("AX"):
            assert pattern in vsepr_patterns, f"{row['id']}: unknown VSEPR pattern {pattern}"
        assert row.get("identity_resolution"), f"{row['id']}: cross-package identity must be explicit"

    curriculum_ids = {row["id"] for row in curriculum}
    assert curriculum_ids == REQUIRED_CURRICULUM_IDS, "curriculum scope must cover all three module themes"
    known_families = set(datasets) - {"curriculum_scope"}
    assert {row["scope_ref"] for row in coverage} == curriculum_ids, "coverage must include every curriculum scope exactly once"
    assert len(coverage) == len(curriculum_ids), "duplicate curriculum coverage entries"
    for row in coverage:
        assert not (set(row["record_families"]) - known_families), f"{row['scope_ref']}: unknown record family"
        assert not (set(row["concept_refs"]) - concept_ids), f"{row['scope_ref']}: unknown concept coverage ref"
        assert not (set(row["exam_tag_refs"]) - exam_ids), f"{row['scope_ref']}: unknown exam-tag coverage ref"

    expected = manifest["records"]
    actual = {name: len(rows) for name, rows in datasets.items()}
    assert expected == actual, f"manifest count mismatch: expected {expected}, actual {actual}"
    assert manifest["total_records"] == sum(actual.values()), "manifest total mismatch"

    print(f"structural_chemistry: {manifest['total_records']} records validated")
    print("1..36 configurations, schemas, typed relations, interaction scopes, and all three curriculum themes passed")


if __name__ == "__main__":
    main()
