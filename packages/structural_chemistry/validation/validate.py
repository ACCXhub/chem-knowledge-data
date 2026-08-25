#!/usr/bin/env python3
"""Minimal stdlib validator for structural_chemistry foundation data."""
from __future__ import annotations

import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
SOURCE_REGISTRY = ROOT / "sources" / "registry.yaml"
TOPICS = ROOT / "curriculum" / "topics.yaml"

FILES = [
    DATA / "concepts.jsonl",
    DATA / "orbital_models.jsonl",
    DATA / "atomic_structure.jsonl",
    DATA / "bond_parameters.jsonl",
    DATA / "molecular_geometry.jsonl",
    DATA / "chirality.jsonl",
    DATA / "crystal_models.jsonl",
    DATA / "crystal_principles.jsonl",
    DATA / "coordination.jsonl",
    DATA / "structure_property_relations.jsonl",
    DATA / "supramolecular.jsonl",
]

REQUIRED = {"id", "record_type", "topic_refs", "name_zh", "teaching_priority", "source_refs", "status"}
ALLOWED_PRIORITY = {"core", "common", "extended"}
ALLOWED_STATUS = {"draft", "reviewed", "published"}


def yaml_ids(path: Path, prefix: str) -> set[str]:
    text = path.read_text(encoding="utf-8")
    return set(re.findall(rf"^\s*- id:\s*({re.escape(prefix)}[a-z0-9_\-]+)\s*$", text, flags=re.MULTILINE))


def load_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    for line_no, raw in enumerate(path.read_text(encoding="utf-8").splitlines(), start=1):
        if not raw.strip():
            continue
        try:
            value = json.loads(raw)
        except json.JSONDecodeError as exc:
            raise AssertionError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        assert isinstance(value, dict), f"{path}:{line_no}: record must be object"
        records.append(value)
    return records


def main() -> None:
    source_ids = yaml_ids(SOURCE_REGISTRY, "sc_src_")
    topic_ids = yaml_ids(TOPICS, "sc_topic_")
    assert source_ids, "no source IDs found"
    assert topic_ids, "no topic IDs found"

    all_records: list[dict] = []
    seen: set[str] = set()
    for path in FILES:
        assert path.exists(), f"missing data file: {path}"
        for record in load_jsonl(path):
            missing = REQUIRED - record.keys()
            assert not missing, f"{record.get('id', path.name)}: missing {sorted(missing)}"
            rid = record["id"]
            assert isinstance(rid, str) and rid.startswith("sc_"), f"invalid id: {rid!r}"
            assert rid not in seen, f"duplicate id: {rid}"
            seen.add(rid)
            assert record["teaching_priority"] in ALLOWED_PRIORITY, f"{rid}: bad priority"
            assert record["status"] in ALLOWED_STATUS, f"{rid}: bad status"
            assert record["topic_refs"], f"{rid}: empty topic refs"
            assert set(record["topic_refs"]) <= topic_ids, f"{rid}: unknown topic ref"
            assert record["source_refs"], f"{rid}: empty source refs"
            assert set(record["source_refs"]) <= source_ids, f"{rid}: unknown source ref"
            structure_id = record.get("structure_id")
            if structure_id is not None:
                assert re.fullmatch(r"str_[0-9a-f\-]+", structure_id), f"{rid}: invalid structure_id"
            all_records.append(record)

    expected = {
        "concept": 43,
        "atomic_example": 28,
        "molecular_geometry": 15,
        "crystal_model": 15,
        "coordination_example": 6,
        "structure_property_relation": 21,
    }
    actual: dict[str, int] = {}
    for record in all_records:
        actual[record["record_type"]] = actual.get(record["record_type"], 0) + 1
    assert actual == expected, f"record counts changed: {actual!r} != {expected!r}"
    print(f"OK: {len(all_records)} records; counts={actual}; sources={len(source_ids)}; topics={len(topic_ids)}")


if __name__ == "__main__":
    main()
