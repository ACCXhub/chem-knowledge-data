from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[3]
CONSOLIDATED = ROOT / "packages" / "consolidated"
GENERATED = CONSOLIDATED / "generated"
SCHEMA = CONSOLIDATED / "schema"
STRUCTURE_REGISTRY = ROOT / "packages" / "structure_registry"
SOURCE_INPUTS = CONSOLIDATED / "SOURCE_INPUTS.json"

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


def add_schema_errors(filename: str, records: list[dict[str, Any]], errors: list[str]) -> None:
    schema_file = ARTIFACT_SCHEMAS[filename]
    validator = Draft202012Validator(load_json(SCHEMA / schema_file))
    for index, record in enumerate(records, 1):
        for issue in sorted(validator.iter_errors(record), key=lambda item: list(item.path)):
            location = ".".join(str(part) for part in issue.path)
            errors.append(f"{filename}:{index}:{location}: {issue.message}")


def published_structure_ids() -> set[str]:
    manifest = load_json(STRUCTURE_REGISTRY / "data" / "manifest.json")
    result: set[str] = set()
    for relative in manifest.get("files", {}):
        if not relative.startswith("canonical/") or not relative.endswith(".jsonl"):
            continue
        for record in load_jsonl(STRUCTURE_REGISTRY / "data" / relative):
            validation = record.get("validation", {})
            if validation.get("status") == "valid" and validation.get("review_status") == "published":
                result.add(str(record.get("structure_id")))
    return result


def validate_source_snapshot(snapshot: dict[str, Any], errors: list[str]) -> None:
    pins = load_json(SOURCE_INPUTS)["inputs"]
    actual = snapshot.get("inputs", {})
    comparisons = [
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
    for package, field, expected, observed in comparisons:
        if expected != observed:
            errors.append(f"source snapshot mismatch {package}.{field}: expected {expected!r}, got {observed!r}")


def validate_manifest(manifest: dict[str, Any], errors: list[str]) -> None:
    declared = manifest.get("files", {})
    actual_paths = {
        path.relative_to(GENERATED).as_posix()
        for path in GENERATED.rglob("*")
        if path.is_file() and path.name not in {"manifest.json", "validation_report.json"}
    }
    if set(declared) != actual_paths:
        missing = sorted(actual_paths - set(declared))
        stale = sorted(set(declared) - actual_paths)
        errors.append(f"manifest file set mismatch: undeclared={missing}, missing_files={stale}")

    for relative, meta in declared.items():
        path = GENERATED / relative
        if not path.is_file():
            continue
        observed_sha = sha256_file(path)
        if meta.get("sha256") != observed_sha:
            errors.append(f"manifest SHA-256 mismatch: {relative}")
        if path.suffix == ".jsonl" and "records" in meta:
            observed_count = len(load_jsonl(path))
            if meta.get("records") != observed_count:
                errors.append(
                    f"manifest record count mismatch: {relative}: expected {meta.get('records')}, got {observed_count}"
                )


def main() -> int:
    errors: list[str] = []
    warnings: list[str] = []

    required = [*ARTIFACT_SCHEMAS, "source_snapshot.json", "manifest.json"]
    for filename in required:
        if not (GENERATED / filename).is_file():
            errors.append(f"missing generated artifact: {filename}")
    if errors:
        report = {"status": "failed", "errors": errors, "warnings": warnings}
        GENERATED.mkdir(parents=True, exist_ok=True)
        with (GENERATED / "validation_report.json").open("w", encoding="utf-8") as handle:
            json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
            handle.write("\n")
        print(json.dumps(report, ensure_ascii=False))
        return 1

    artifacts = {filename: load_jsonl(GENERATED / filename) for filename in ARTIFACT_SCHEMAS}
    for filename, records in artifacts.items():
        add_schema_errors(filename, records, errors)

    species = artifacts["species.jsonl"]
    crosswalk = artifacts["crosswalk.jsonl"]
    teaching = artifacts["teaching_projection.jsonl"]
    reactions = artifacts["reactions.jsonl"]
    structure_links = artifacts["structure_links.jsonl"]
    knowledge = artifacts["knowledge_records.jsonl"]
    findings = artifacts["unresolved_findings.jsonl"]

    def unique_ids(records: list[dict[str, Any]], label: str) -> set[str]:
        ids: set[str] = set()
        for record in records:
            record_id = str(record.get("id", ""))
            if not record_id:
                errors.append(f"{label}: record missing id")
            elif record_id in ids:
                errors.append(f"{label}: duplicate id {record_id}")
            ids.add(record_id)
        return ids

    species_ids = unique_ids(species, "species")
    unique_ids(reactions, "reaction")
    unique_ids(knowledge, "knowledge")
    unique_ids(findings, "finding")

    crosswalk_by_source: dict[tuple[str, str], str] = {}
    for item in crosswalk:
        key = (str(item.get("source_package")), str(item.get("source_id")))
        target = item.get("consolidated_id")
        if key in crosswalk_by_source:
            errors.append(f"crosswalk duplicate source key {key[0]}:{key[1]}")
        if item.get("mapping_status") == "resolved":
            if not isinstance(target, str) or target not in species_ids:
                errors.append(f"crosswalk target missing species for {key[0]}:{key[1]} -> {target!r}")
            else:
                crosswalk_by_source[key] = target

    expected_sources_by_species: dict[str, set[tuple[str, str]]] = {}
    for item in species:
        current: set[tuple[str, str]] = set()
        for source in item.get("source_ids", []):
            key = (str(source.get("package")), str(source.get("id")))
            current.add(key)
            if crosswalk_by_source.get(key) != item.get("id"):
                errors.append(f"species {item.get('id')} source {key} does not round-trip through crosswalk")
        expected_sources_by_species[str(item.get("id"))] = current

    for key, target in crosswalk_by_source.items():
        if key not in expected_sources_by_species.get(target, set()):
            errors.append(f"crosswalk {key} -> {target} is absent from target species.source_ids")

    projected_species: set[str] = set()
    ranks: set[int] = set()
    for item in teaching:
        species_id = str(item.get("species_id"))
        if species_id not in species_ids:
            errors.append(f"teaching projection references missing species {species_id}")
        if species_id in projected_species:
            errors.append(f"duplicate teaching projection for species {species_id}")
        projected_species.add(species_id)
        rank = item.get("default_palette_rank")
        if isinstance(rank, int):
            if rank in ranks:
                errors.append(f"duplicate default palette rank {rank}")
            ranks.add(rank)
    if projected_species != species_ids:
        errors.append(
            f"teaching projection coverage mismatch: missing={sorted(species_ids - projected_species)}, extra={sorted(projected_species - species_ids)}"
        )

    published_structures = published_structure_ids()
    link_keys: set[tuple[str, str, str]] = set()
    links_by_species: dict[str, set[str]] = {}
    for item in structure_links:
        species_id = str(item.get("species_id"))
        structure_id = str(item.get("structure_id"))
        if species_id not in species_ids:
            errors.append(f"structure link references missing species {species_id}")
        if structure_id not in published_structures:
            errors.append(f"structure link references non-published Structure {structure_id}")
        key = (species_id, structure_id, str(item.get("relation")))
        if key in link_keys:
            errors.append(f"duplicate normalized structure link {key}")
        link_keys.add(key)
        links_by_species.setdefault(species_id, set()).add(structure_id)
    for item in species:
        preferred = item.get("preferred_structure_id")
        if preferred is not None:
            if preferred not in published_structures:
                errors.append(f"species {item.get('id')} preferred Structure is not published: {preferred}")
            if preferred not in links_by_species.get(str(item.get("id")), set()):
                errors.append(f"species {item.get('id')} preferred Structure lacks normalized link: {preferred}")

    for reaction in reactions:
        reaction_id = str(reaction.get("id"))
        for participant in reaction.get("participants", []):
            if participant.get("role") in {"reactant", "product"}:
                species_id = participant.get("species_id")
                if not isinstance(species_id, str) or species_id not in species_ids:
                    errors.append(f"reaction {reaction_id} has unresolved required participant {participant.get('source_species_ref')}")
        net = reaction.get("net_ionic")
        if isinstance(net, dict):
            for participant in net.get("participants", []):
                species_id = participant.get("species_id")
                if not isinstance(species_id, str) or species_id not in species_ids:
                    errors.append(f"reaction {reaction_id} has unresolved net-ionic participant {participant.get('source_species_ref')}")
        if reaction.get("integration_status") != "resolved":
            errors.append(f"reaction {reaction_id} is not integration-resolved")

    blocking_findings = [item for item in findings if item.get("severity") == "blocking"]
    if blocking_findings:
        errors.append(f"generated findings contain {len(blocking_findings)} blocking item(s)")
    review_findings = [item for item in findings if item.get("severity") == "review"]
    if review_findings:
        warnings.append(f"{len(review_findings)} reviewed integration finding(s) remain explicit; no automatic merge applied")

    snapshot = load_json(GENERATED / "source_snapshot.json")
    validate_source_snapshot(snapshot, errors)

    manifest = load_json(GENERATED / "manifest.json")
    validate_manifest(manifest, errors)
    expected_counts = {
        "species": len(species),
        "source_crosswalks": len(crosswalk),
        "structure_links": len(structure_links),
        "teaching_projections": len(teaching),
        "reactions": len(reactions),
        "knowledge_records": len(knowledge),
        "findings": len(findings),
    }
    if manifest.get("counts") != expected_counts:
        errors.append(f"manifest aggregate counts mismatch: expected {expected_counts}, got {manifest.get('counts')}")
    if manifest.get("blocking_findings") != len(blocking_findings):
        errors.append("manifest blocking_findings does not match unresolved_findings.jsonl")

    report = {
        "status": "passed" if not errors else "failed",
        "counts": expected_counts,
        "blocking_findings": len(blocking_findings),
        "review_findings": len(review_findings),
        "info_findings": sum(1 for item in findings if item.get("severity") == "info"),
        "errors": errors,
        "warnings": warnings,
    }
    with (GENERATED / "validation_report.json").open("w", encoding="utf-8", newline="\n") as handle:
        json.dump(report, handle, ensure_ascii=False, indent=2, sort_keys=True)
        handle.write("\n")

    print(json.dumps(report, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
