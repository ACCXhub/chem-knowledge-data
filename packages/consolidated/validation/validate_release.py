from __future__ import annotations

import hashlib
import json
from collections import defaultdict
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
CONSOLIDATED = ROOT / "packages" / "consolidated"
GENERATED = CONSOLIDATED / "generated"
SCHEMA_DIR = CONSOLIDATED / "schema"
SOURCE_INPUTS = CONSOLIDATED / "SOURCE_INPUTS.json"
STRUCTURE_REGISTRY = ROOT / "packages" / "structure_registry"

ARTIFACT_SCHEMAS = {
    "species.jsonl": "species.schema.json",
    "crosswalk.jsonl": "crosswalk.schema.json",
    "teaching_projection.jsonl": "teaching_projection.schema.json",
    "reactions.jsonl": "reaction.schema.json",
    "structure_links.jsonl": "structure_link.schema.json",
    "knowledge_records.jsonl": "knowledge_record.schema.json",
    "unresolved_findings.jsonl": "finding.schema.json",
}


def load_json(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        value = json.load(handle)
    if not isinstance(value, dict):
        raise ValueError(f"{path}: expected JSON object")
    return value


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_no, line in enumerate(handle, 1):
            if not line.strip():
                continue
            value = json.loads(line)
            if not isinstance(value, dict):
                raise ValueError(f"{path}:{line_no}: expected JSON object")
            records.append(value)
    return records


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def schema_errors(filename: str, records: list[dict[str, Any]]) -> list[str]:
    validator = Draft202012Validator(load_json(SCHEMA_DIR / ARTIFACT_SCHEMAS[filename]))
    errors: list[str] = []
    for index, record in enumerate(records, 1):
        for issue in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path)
            errors.append(f"{filename}:{index}:{location}: {issue.message}")
    return errors


def published_structure_ids() -> set[str]:
    manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    output: set[str] = set()
    for relative in manifest.get("files", {}):
        if not relative.startswith("canonical/") or not relative.endswith(".jsonl"):
            continue
        for record in load_jsonl(STRUCTURE_REGISTRY / "data" / relative):
            validation = record.get("validation", {})
            if validation.get("status") == "valid" and validation.get("review_status") == "published":
                output.add(str(record.get("structure_id")))
    return output


def unique_ids(records: list[dict[str, Any]], label: str, errors: list[str]) -> set[str]:
    values: set[str] = set()
    for record in records:
        record_id = record.get("id")
        if not isinstance(record_id, str) or not record_id:
            errors.append(f"{label}: record missing id")
            continue
        if record_id in values:
            errors.append(f"{label}: duplicate id {record_id}")
        values.add(record_id)
    return values


def validate_snapshot(snapshot: dict[str, Any], errors: list[str]) -> None:
    pins = load_json(SOURCE_INPUTS)["inputs"]
    actual = snapshot.get("inputs", {})
    checks = [
        ("inorganic", "release", pins["inorganic"]["release"], actual.get("inorganic", {}).get("release")),
        ("inorganic", "total_records", pins["inorganic"]["expected_total_records"], actual.get("inorganic", {}).get("total_records")),
        ("organic", "release", pins["organic"]["release"], actual.get("organic", {}).get("release")),
        ("organic", "substances", pins["organic"]["expected_substances"], actual.get("organic", {}).get("substances")),
        ("organic", "reactions", pins["organic"]["expected_reactions"], actual.get("organic", {}).get("reactions")),
        ("structure_registry", "release", pins["structure_registry"]["release"], actual.get("structure_registry", {}).get("release")),
        ("structure_registry", "structures", pins["structure_registry"]["expected_structures"], actual.get("structure_registry", {}).get("structures")),
        ("structure_registry", "inorganic_links", pins["structure_registry"]["expected_inorganic_links"], actual.get("structure_registry", {}).get("inorganic_links")),
        ("structure_registry", "organic_links", pins["structure_registry"]["expected_organic_links"], actual.get("structure_registry", {}).get("organic_links")),
        ("structure_registry", "organic_deferrals", pins["structure_registry"]["expected_organic_deferrals"], actual.get("structure_registry", {}).get("organic_deferrals")),
        ("structural_chemistry", "release", pins["structural_chemistry"]["release"], actual.get("structural_chemistry", {}).get("release")),
        ("structural_chemistry", "total_records", pins["structural_chemistry"]["expected_total_records"], actual.get("structural_chemistry", {}).get("total_records")),
    ]
    for package, field, expected, observed in checks:
        if expected != observed:
            errors.append(f"source snapshot mismatch {package}.{field}: expected {expected!r}, got {observed!r}")


def validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    declared = manifest.get("files", {})
    actual = {
        path.relative_to(GENERATED).as_posix()
        for path in GENERATED.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "validation_report.json"}
    }
    if set(declared) != actual:
        errors.append(
            "manifest file set mismatch: "
            f"undeclared={sorted(actual - set(declared))}, missing_files={sorted(set(declared) - actual)}"
        )
    for relative, meta in declared.items():
        path = GENERATED / relative
        if not path.is_file():
            continue
        if meta.get("sha256") != sha256_file(path):
            errors.append(f"manifest SHA-256 mismatch: {relative}")
        if path.suffix == ".jsonl" and "records" in meta:
            observed = len(load_jsonl(path))
            if meta.get("records") != observed:
                errors.append(f"manifest record count mismatch: {relative}: expected {meta.get('records')}, got {observed}")


def participant_resolved(participant: dict[str, Any], species_ids: set[str]) -> bool:
    species_id = participant.get("species_id")
    non_species_ref = participant.get("non_species_ref")
    if isinstance(species_id, str):
        return species_id in species_ids and non_species_ref is None
    if isinstance(non_species_ref, str):
        return non_species_ref.startswith("organic-material:") and species_id is None
    return False


def write_report(report: dict[str, Any]) -> None:
    GENERATED.mkdir(parents=True, exist_ok=True)
    with (GENERATED / "validation_report.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []
    required = [*ARTIFACT_SCHEMAS, "source_snapshot.json", "manifest.json"]
    for filename in required:
        if not (GENERATED / filename).is_file():
            errors.append(f"missing generated artifact: {filename}")
    if errors:
        report = {"status": "failed", "errors": errors, "warnings": warnings}
        write_report(report)
        print(json.dumps(report, ensure_ascii=False))
        return 1

    artifacts = {name: load_jsonl(GENERATED / name) for name in ARTIFACT_SCHEMAS}
    for filename, records in artifacts.items():
        errors.extend(schema_errors(filename, records))

    species = artifacts["species.jsonl"]
    crosswalk = artifacts["crosswalk.jsonl"]
    teaching = artifacts["teaching_projection.jsonl"]
    reactions = artifacts["reactions.jsonl"]
    structure_links = artifacts["structure_links.jsonl"]
    knowledge = artifacts["knowledge_records.jsonl"]
    findings = artifacts["unresolved_findings.jsonl"]

    species_ids = unique_ids(species, "species", errors)
    unique_ids(reactions, "reaction", errors)
    unique_ids(knowledge, "knowledge", errors)
    unique_ids(findings, "finding", errors)

    crosswalk_by_source: dict[tuple[str, str], str] = {}
    for item in crosswalk:
        key = (str(item.get("source_package")), str(item.get("source_id")))
        if key in crosswalk_by_source:
            errors.append(f"crosswalk duplicate source key {key[0]}:{key[1]}")
            continue
        target = item.get("consolidated_id")
        if item.get("mapping_status") == "resolved":
            if not isinstance(target, str) or target not in species_ids:
                errors.append(f"crosswalk target missing species for {key[0]}:{key[1]} -> {target!r}")
            else:
                crosswalk_by_source[key] = target

    source_membership: dict[str, set[tuple[str, str]]] = {}
    for item in species:
        current: set[tuple[str, str]] = set()
        for source in item.get("source_ids", []):
            key = (str(source.get("package")), str(source.get("id")))
            current.add(key)
            if crosswalk_by_source.get(key) != item.get("id"):
                errors.append(f"species {item.get('id')} source {key} does not round-trip through crosswalk")
        source_membership[str(item.get("id"))] = current
    for key, target in crosswalk_by_source.items():
        if key not in source_membership.get(target, set()):
            errors.append(f"crosswalk {key} -> {target} is absent from target species.source_ids")

    projected: set[str] = set()
    ranks: set[int] = set()
    for item in teaching:
        species_id = str(item.get("species_id"))
        if species_id not in species_ids:
            errors.append(f"teaching projection references missing species {species_id}")
        if species_id in projected:
            errors.append(f"duplicate teaching projection for species {species_id}")
        projected.add(species_id)
        rank = item.get("default_palette_rank")
        if isinstance(rank, int):
            if rank in ranks:
                errors.append(f"duplicate default palette rank {rank}")
            ranks.add(rank)
    if projected != species_ids:
        errors.append(f"teaching projection coverage mismatch: missing={sorted(species_ids - projected)}, extra={sorted(projected - species_ids)}")

    published_structures = published_structure_ids()
    normalized_link_keys: set[tuple[str, str, str]] = set()
    structures_by_species: dict[str, set[str]] = defaultdict(set)
    for item in structure_links:
        species_id = str(item.get("species_id"))
        structure_id = str(item.get("structure_id"))
        if species_id not in species_ids:
            errors.append(f"structure link references missing species {species_id}")
        if structure_id not in published_structures:
            errors.append(f"structure link references non-published Structure {structure_id}")
        key = (species_id, structure_id, str(item.get("relation")))
        if key in normalized_link_keys:
            errors.append(f"duplicate normalized structure link {key}")
        normalized_link_keys.add(key)
        structures_by_species[species_id].add(structure_id)
    for item in species:
        preferred = item.get("preferred_structure_id")
        if preferred is not None:
            if preferred not in published_structures:
                errors.append(f"species {item.get('id')} preferred Structure is not published: {preferred}")
            if preferred not in structures_by_species.get(str(item.get("id")), set()):
                errors.append(f"species {item.get('id')} preferred Structure lacks normalized link: {preferred}")

    for reaction in reactions:
        reaction_id = str(reaction.get("id"))
        for item in reaction.get("participants", []):
            if item.get("role") in {"reactant", "product"} and not participant_resolved(item, species_ids):
                errors.append(f"reaction {reaction_id} has unresolved required participant {item.get('source_species_ref')}")
        net = reaction.get("net_ionic")
        if isinstance(net, dict):
            for item in net.get("participants", []):
                species_id = item.get("species_id")
                if not isinstance(species_id, str) or species_id not in species_ids or item.get("non_species_ref") is not None:
                    errors.append(f"reaction {reaction_id} has unresolved/non-species net-ionic participant {item.get('source_species_ref')}")
        if reaction.get("integration_status") != "resolved":
            errors.append(f"reaction {reaction_id} is not integration-resolved")

    blocking = [item for item in findings if item.get("severity") == "blocking"]
    review = [item for item in findings if item.get("severity") == "review"]
    info = [item for item in findings if item.get("severity") == "info"]
    for item in blocking:
        errors.append(f"blocking finding {item.get('id')}: {item.get('message')} refs={item.get('source_refs')}")
    if review:
        warnings.append(f"{len(review)} explicit review finding(s) remain; no automatic identity merge applied")

    validate_snapshot(load_json(GENERATED / "source_snapshot.json"), errors)
    manifest = load_json(GENERATED / "manifest.json")
    validate_manifest(manifest, errors)
    counts = {
        "species": len(species),
        "source_crosswalks": len(crosswalk),
        "structure_links": len(structure_links),
        "teaching_projections": len(teaching),
        "reactions": len(reactions),
        "knowledge_records": len(knowledge),
        "findings": len(findings),
    }
    if manifest.get("counts") != counts:
        errors.append(f"manifest aggregate counts mismatch: expected {counts}, got {manifest.get('counts')}")
    if manifest.get("blocking_findings") != len(blocking):
        errors.append("manifest blocking_findings does not match unresolved_findings.jsonl")
    if manifest.get("review_findings") != len(review):
        errors.append("manifest review_findings does not match unresolved_findings.jsonl")
    if manifest.get("info_findings") != len(info):
        errors.append("manifest info_findings does not match unresolved_findings.jsonl")

    report = {
        "status": "passed" if not errors else "failed",
        "counts": counts,
        "blocking_findings": len(blocking),
        "review_findings": len(review),
        "info_findings": len(info),
        "errors": errors,
        "warnings": warnings,
    }
    write_report(report)
    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
