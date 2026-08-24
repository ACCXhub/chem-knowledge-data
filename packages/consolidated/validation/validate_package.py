from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import yaml
from jsonschema import Draft202012Validator, FormatChecker

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = Path(__file__).resolve().parents[3]
DATA_DIR = PACKAGE_ROOT / "data"
SCHEMA_DIR = PACKAGE_ROOT / "schema"
ORGANIC_DATA = REPO_ROOT / "packages" / "organic" / "data"
STRUCTURE_DATA = REPO_ROOT / "packages" / "structure" / "data" / "canonical"

ORGANIC_SUBSTANCE_FILES = (
    "core_substances.yaml",
    "extended_substances.yaml",
    "lipid_substances.yaml",
    "polymer_substances.yaml",
)
STRUCTURE_FILES = ("molecules.jsonl", "ions.jsonl", "formula_units.jsonl")


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected object")
    return value


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = yaml.safe_load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected mapping")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, raw in enumerate(handle, 1):
            line = raw.strip()
            if not line:
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_number}: expected object")
            result.append(value)
    return result


def schema_validator(filename: str) -> Draft202012Validator:
    schema = load_json(SCHEMA_DIR / filename)
    Draft202012Validator.check_schema(schema)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_records(
    records: list[dict[str, Any]],
    validator: Draft202012Validator,
    label: str,
    errors: list[str],
) -> None:
    for index, record in enumerate(records):
        for error in sorted(
            validator.iter_errors(record), key=lambda item: list(item.path)
        ):
            location = ".".join(str(part) for part in error.path)
            errors.append(f"{label}[{index}]:{location}: {error.message}")


def organic_source_records() -> list[dict[str, Any]]:
    result: list[dict[str, Any]] = []
    for filename in ORGANIC_SUBSTANCE_FILES:
        records = load_yaml(ORGANIC_DATA / filename).get("records", [])
        if not isinstance(records, list):
            raise ValueError(f"{filename}: records must be a list")
        result.extend(records)
    return result


def published_structures() -> dict[str, dict[str, Any]]:
    result: dict[str, dict[str, Any]] = {}
    for filename in STRUCTURE_FILES:
        for record in load_jsonl(STRUCTURE_DATA / filename):
            validation = record.get("validation", {})
            if (
                validation.get("status") == "valid"
                and validation.get("review_status") == "published"
            ):
                result[record["structure_id"]] = record
    return result


def pubchem_ids(record: dict[str, Any]) -> set[str]:
    return {
        str(item["value"])
        for item in record.get("external_ids", [])
        if item.get("namespace") == "pubchem_cid"
    }


def main() -> int:
    errors: list[str] = []

    identity_records = load_jsonl(DATA_DIR / "identity-map.jsonl")
    validate_records(
        identity_records,
        schema_validator("identity-map.schema.json"),
        "identity-map",
        errors,
    )

    identities_by_source: dict[str, dict[str, Any]] = {}
    canonical_ids: set[str] = set()
    for record in identity_records:
        if record.get("entity_kind") != "species":
            continue
        canonical_id = record.get("canonical_id")
        if canonical_id in canonical_ids:
            errors.append(f"identity-map: duplicate canonical_id {canonical_id}")
        canonical_ids.add(canonical_id)
        for source_ref in record.get("source_refs", []):
            if source_ref.get("package") != "organic":
                continue
            local_id = source_ref.get("local_id")
            if local_id in identities_by_source:
                errors.append(f"identity-map: duplicate organic source ref {local_id}")
            identities_by_source[local_id] = record

    source_records = organic_source_records()
    source_ids = {record["id"] for record in source_records}
    if len(source_records) != 50:
        errors.append(f"organic: expected 50 substances, got {len(source_records)}")
    if source_ids != set(identities_by_source):
        errors.append(
            "identity-map: organic source coverage mismatch "
            f"missing={sorted(source_ids - set(identities_by_source))} "
            f"extra={sorted(set(identities_by_source) - source_ids)}"
        )

    crossrefs = {
        record["substance_ref"]: record
        for record in load_yaml(ORGANIC_DATA / "identity_crossrefs.yaml").get(
            "crossrefs", []
        )
    }
    structures = published_structures()

    link_records = load_jsonl(DATA_DIR / "organic-structure-links.jsonl")
    validate_records(
        link_records,
        schema_validator("structure-link.schema.json"),
        "organic-structure-links",
        errors,
    )
    if len(link_records) != 7:
        errors.append(f"structure links: expected 7 direct links, got {len(link_records)}")

    seen_link_species: set[str] = set()
    for link in link_records:
        species_id = link["species_id"]
        if species_id in seen_link_species:
            errors.append(f"structure links: duplicate species link {species_id}")
        seen_link_species.add(species_id)

        local_id = link["source_ref"]["local_id"]
        identity = identities_by_source.get(local_id)
        if not identity or identity.get("canonical_id") != species_id:
            errors.append(f"structure links: identity mismatch for {local_id}")

        structure = structures.get(link["structure_id"])
        if not structure:
            errors.append(
                f"structure links: non-published structure {link['structure_id']}"
            )
            continue

        source_crossref = crossrefs.get(local_id)
        expected_pubchem = (
            str(source_crossref.get("pubchem_cid"))
            if source_crossref and source_crossref.get("pubchem_cid") is not None
            else None
        )
        structure_pubchem = pubchem_ids(structure)
        evidence_pubchem = {
            item["value"]
            for item in link["evidence"]
            if item["kind"] == "external_id_match"
            and item.get("namespace") == "pubchem_cid"
        }
        if (
            expected_pubchem is None
            or expected_pubchem not in structure_pubchem
            or expected_pubchem not in evidence_pubchem
        ):
            errors.append(
                f"structure links: PubChem evidence mismatch for {local_id}: "
                f"source={expected_pubchem}, structure={sorted(structure_pubchem)}, "
                f"evidence={sorted(evidence_pubchem)}"
            )

    generated_dir = DATA_DIR / "generated"
    species_records = load_jsonl(generated_dir / "species.jsonl")
    projection_records = load_jsonl(generated_dir / "teaching-projections.jsonl")
    validate_records(
        species_records,
        schema_validator("species.schema.json"),
        "generated species",
        errors,
    )
    validate_records(
        projection_records,
        schema_validator("teaching-projection.schema.json"),
        "generated teaching projection",
        errors,
    )

    if len(species_records) != 50:
        errors.append(f"generated species: expected 50, got {len(species_records)}")
    species_ids = {record["species_id"] for record in species_records}
    if species_ids != canonical_ids:
        errors.append("generated species IDs do not exactly match identity map IDs")
    projection_ids = {record["target"]["id"] for record in projection_records}
    if projection_ids != species_ids:
        errors.append("teaching projection IDs do not exactly match generated species")

    source_by_id = {record["id"]: record for record in source_records}
    for species in species_records:
        local_id = species["source_refs"][0]["local_id"]
        source = source_by_id[local_id]
        formula = source["formula"]
        if formula.startswith("(") and formula.endswith(")n"):
            if species["composition_basis"] != "repeat_unit":
                errors.append(f"{local_id}: polymer formula must use repeat_unit basis")
        elif species["composition_basis"] == "not_applicable":
            errors.append(f"{local_id}: ordinary formula unexpectedly not parsed")
        if species["review_status"] != "candidate":
            errors.append(f"{local_id}: preview species must remain candidate")

    summary = load_json(generated_dir / "summary.json")
    if summary.get("species") != 50 or summary.get("teaching_projections") != 50:
        errors.append(f"generated summary count mismatch: {summary}")

    preview_manifest = load_json(DATA_DIR / "preview-manifest.json")
    resolved = preview_manifest.get("resolved", {})
    if resolved.get("organic_species_identity_mappings") != 50:
        errors.append("preview manifest identity count mismatch")
    if resolved.get("organic_to_structure_links") != 7:
        errors.append("preview manifest structure-link count mismatch")
    if preview_manifest.get("consumer_release") is not False:
        errors.append("preview manifest must not claim consumer release")

    if errors:
        print("Consolidation validation FAILED")
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print("Consolidation validation PASSED")
    print(f"organic_identity_mappings={len(identities_by_source)}")
    print(f"published_structures={len(structures)}")
    print(f"direct_organic_structure_links={len(link_records)}")
    print(f"generated_species={len(species_records)}")
    print(f"teaching_projections={len(projection_records)}")
    print("consumer_release=false (inorganic pending)")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
