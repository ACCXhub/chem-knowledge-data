from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
SCHEMA_DIR = PACKAGE_ROOT / "schema"
SOURCES_FILE = PACKAGE_ROOT / "sources" / "registry.yaml"


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = yaml.safe_load(handle)
    if not isinstance(data, dict):
        raise ValueError(f"{path}: expected a mapping at document root")
    return data


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def iter_strings(value: Any):
    if isinstance(value, str):
        yield value
    elif isinstance(value, dict):
        for child in value.values():
            yield from iter_strings(child)
    elif isinstance(value, list):
        for child in value:
            yield from iter_strings(child)


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    source_doc = load_yaml(SOURCES_FILE)
    source_ids = {source["id"] for source in source_doc.get("sources", [])}

    dataset_specs = [
        ("substance", DATA_DIR / "core_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("substance", DATA_DIR / "extended_substances.yaml", "records", SCHEMA_DIR / "substance.schema.json"),
        ("functional_group", DATA_DIR / "functional_groups.yaml", "functional_groups", SCHEMA_DIR / "functional_group.schema.json"),
        ("reaction", DATA_DIR / "reactions.yaml", "reactions", SCHEMA_DIR / "reaction.schema.json"),
        ("concept", DATA_DIR / "concepts.yaml", "concepts", SCHEMA_DIR / "concept.schema.json"),
        ("phenomenon", DATA_DIR / "phenomena.yaml", "phenomena", SCHEMA_DIR / "phenomenon.schema.json"),
        ("experiment", DATA_DIR / "experiments.yaml", "experiments", SCHEMA_DIR / "experiment.schema.json"),
        ("chemical_class", DATA_DIR / "classes.yaml", "classes", SCHEMA_DIR / "chemical_class.schema.json"),
    ]

    records_by_kind: dict[str, list[dict[str, Any]]] = {}
    source_path_by_record_id: dict[str, Path] = {}

    for kind, path, root_key, schema_path in dataset_specs:
        doc = load_yaml(path)
        records = doc.get(root_key, [])
        if not isinstance(records, list):
            errors.append(f"{path}: {root_key} must be a list")
            continue

        validator = Draft202012Validator(load_json(schema_path))
        records_by_kind.setdefault(kind, []).extend(records)

        for index, record in enumerate(records):
            if not isinstance(record, dict):
                errors.append(f"{path}:{index}: record must be a mapping")
                continue

            record_id = record.get("id", f"<index:{index}>")
            for validation_error in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
                location = ".".join(str(part) for part in validation_error.path)
                errors.append(f"{path}:{record_id}:{location}: {validation_error.message}")

            if isinstance(record_id, str):
                if record_id in source_path_by_record_id:
                    errors.append(
                        f"duplicate id {record_id}: {source_path_by_record_id[record_id]} and {path}"
                    )
                else:
                    source_path_by_record_id[record_id] = path

            for provenance_ref in record.get("provenance_refs", []):
                if provenance_ref not in source_ids:
                    errors.append(f"{path}:{record_id}: unknown provenance ref {provenance_ref}")

    feature_doc = load_yaml(DATA_DIR / "functional_groups.yaml")
    feature_records = feature_doc.get("structural_features", [])
    feature_ids = {record["id"] for record in feature_records if isinstance(record, dict) and "id" in record}

    id_sets = {
        "org-substance:": {record["id"] for record in records_by_kind.get("substance", [])},
        "org-fg:": {record["id"] for record in records_by_kind.get("functional_group", [])},
        "org-reaction:": {record["id"] for record in records_by_kind.get("reaction", [])},
        "org-concept:": {record["id"] for record in records_by_kind.get("concept", [])},
        "org-phenomenon:": {record["id"] for record in records_by_kind.get("phenomenon", [])},
        "org-experiment:": {record["id"] for record in records_by_kind.get("experiment", [])},
        "org-class:": {record["id"] for record in records_by_kind.get("chemical_class", [])},
        "org-feature:": feature_ids,
    }

    for kind, records in records_by_kind.items():
        for record in records:
            record_id = record.get("id", "<unknown>")
            for value in iter_strings(record):
                for prefix, known_ids in id_sets.items():
                    if value.startswith(prefix) and value not in known_ids:
                        errors.append(f"{kind}:{record_id}: unresolved local reference {value}")
                        break

    crossref_doc = load_yaml(DATA_DIR / "identity_crossrefs.yaml")
    crossrefs = crossref_doc.get("crossrefs", [])
    crossref_validator = Draft202012Validator(load_json(SCHEMA_DIR / "identity_crossref.schema.json"))
    seen_crossref_substances: set[str] = set()
    for index, crossref in enumerate(crossrefs):
        label = crossref.get("substance_ref", f"<index:{index}>") if isinstance(crossref, dict) else f"<index:{index}>"
        if not isinstance(crossref, dict):
            errors.append(f"identity_crossrefs:{label}: record must be a mapping")
            continue
        for validation_error in sorted(crossref_validator.iter_errors(crossref), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in validation_error.path)
            errors.append(f"identity_crossrefs:{label}:{location}: {validation_error.message}")
        substance_ref = crossref.get("substance_ref")
        if substance_ref not in id_sets["org-substance:"]:
            errors.append(f"identity_crossrefs:{label}: unresolved local reference {substance_ref}")
        if substance_ref in seen_crossref_substances:
            errors.append(f"identity_crossrefs:{label}: duplicate crossref for substance")
        seen_crossref_substances.add(substance_ref)
        for provenance_ref in crossref.get("provenance_refs", []):
            if provenance_ref not in source_ids:
                errors.append(f"identity_crossrefs:{label}: unknown provenance ref {provenance_ref}")

    substance_records = records_by_kind.get("substance", [])
    formula_index: dict[str, list[str]] = {}
    for record in substance_records:
        formula_index.setdefault(record["formula"], []).append(record["id"])
    for formula, ids in sorted(formula_index.items()):
        if len(ids) > 1:
            warnings.append(
                f"shared formula {formula}: {', '.join(ids)} (allowed; verify these are distinct identities)"
            )

    if errors:
        print("Organic package validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        for warning in warnings:
            print(f"WARN: {warning}")
        return 1

    print("Organic package validation PASSED")
    for kind, records in sorted(records_by_kind.items()):
        print(f"{kind}: {len(records)}")
    print(f"identity_crossref: {len(crossrefs)}")
    print(f"structural_feature: {len(feature_ids)}")
    print(f"sources: {len(source_ids)}")
    for warning in warnings:
        print(f"WARN: {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
