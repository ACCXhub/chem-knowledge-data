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


def load_jsonl(path: Path) -> list[dict]:
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            row = json.loads(line)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        rows.append(row)
    return rows


def main() -> None:
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    registry = json.loads((ROOT / "sources" / "source_registry.json").read_text(encoding="utf-8"))
    curriculum = json.loads((ROOT / "curriculum" / "scope.json").read_text(encoding="utf-8"))
    source_keys = {row["key"] for row in registry["sources"]}

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

    for row in datasets["relations"]:
        assert row["source_ref"] in concept_ids, f"{row['id']}: bad source_ref"
        assert row["target_ref"] in concept_ids, f"{row['id']}: bad target_ref"

    for row in datasets["exam_tags"]:
        missing = set(row["concept_refs"]) - concept_ids
        assert not missing, f"{row['id']}: missing concept refs {sorted(missing)}"

    for row in datasets["vsepr_models"]:
        assert row["electron_domains"] == row["bonded_atoms"] + row["lone_pairs_on_central"], (
            f"{row['id']}: electron-domain count mismatch"
        )
    patterns = [row["ax_e_notation"] for row in datasets["vsepr_models"]]
    assert len(patterns) == len(set(patterns)), "duplicate VSEPR pattern"

    allowed_hybrid = {None, "sp", "sp2", "sp3"}
    for row in datasets["molecular_examples"]:
        assert row["central_hybridization_model"] in allowed_hybrid, (
            f"{row['id']}: hypervalent hybrid labels are intentionally not published as canonical truth"
        )

    expected = manifest["records"]
    actual = {name: len(rows) for name, rows in datasets.items()}
    assert expected == actual, f"manifest count mismatch: expected {expected}, actual {actual}"
    assert manifest["total_records"] == sum(actual.values()), "manifest total mismatch"

    print(f"structural_chemistry: {manifest['total_records']} records validated")
    print("atomic configurations: 1..36 complete; concept/relation/source/manifest checks passed")


if __name__ == "__main__":
    main()
