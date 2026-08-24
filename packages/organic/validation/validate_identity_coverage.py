from __future__ import annotations

import json
from pathlib import Path

import yaml
from jsonschema import Draft202012Validator

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = PACKAGE_ROOT / "data"
SCHEMA_DIR = PACKAGE_ROOT / "schema"

SUBSTANCE_FILES = [
    DATA_DIR / "core_substances.yaml",
    DATA_DIR / "extended_substances.yaml",
    DATA_DIR / "polymer_substances.yaml",
    DATA_DIR / "lipid_substances.yaml",
]


def load_yaml(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return yaml.safe_load(handle)


def load_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def main() -> int:
    errors: list[str] = []

    substance_ids: set[str] = set()
    for path in SUBSTANCE_FILES:
        for record in load_yaml(path).get("records", []):
            substance_ids.add(record["id"])

    crossrefs = load_yaml(DATA_DIR / "identity_crossrefs.yaml").get("crossrefs", [])
    crossref_ids = {record["substance_ref"] for record in crossrefs}

    deferral_doc = load_yaml(DATA_DIR / "identity_deferrals.yaml")
    deferrals = deferral_doc.get("deferrals", [])
    deferral_validator = Draft202012Validator(
        load_json(SCHEMA_DIR / "identity_deferral.schema.json")
    )
    deferral_ids: set[str] = set()

    for index, record in enumerate(deferrals):
        for validation_error in sorted(
            deferral_validator.iter_errors(record), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in validation_error.path)
            errors.append(
                f"identity_deferrals:{index}:{location}: {validation_error.message}"
            )
        ref = record.get("substance_ref")
        if ref not in substance_ids:
            errors.append(f"identity_deferrals:{index}: unknown substance {ref}")
        if ref in deferral_ids:
            errors.append(f"identity_deferrals:{index}: duplicate deferral {ref}")
        if isinstance(ref, str):
            deferral_ids.add(ref)

    overlap = sorted(crossref_ids & deferral_ids)
    for ref in overlap:
        errors.append(f"identity coverage: {ref} has both crossref and deferral")

    missing = sorted(substance_ids - crossref_ids - deferral_ids)
    for ref in missing:
        errors.append(f"identity coverage: {ref} has neither crossref nor deferral")

    extras = sorted((crossref_ids | deferral_ids) - substance_ids)
    for ref in extras:
        errors.append(f"identity coverage: unknown substance referenced {ref}")

    if errors:
        print("Organic identity coverage FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Organic identity coverage PASSED")
    print(f"substances: {len(substance_ids)}")
    print(f"source_crossrefs: {len(crossref_ids)}")
    print(f"explicit_deferrals: {len(deferral_ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
