"""Validate the complete Structure Registry foundation release.

Usage:
    python packages/structure_registry/validation/validate_dataset.py --strict
"""

from __future__ import annotations

import argparse
import hashlib
import json
import sys
from collections import defaultdict
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
PIPELINES = PACKAGE_ROOT / "pipelines"
sys.path.insert(0, str(PIPELINES))

from ids import structure_id_from_inchi  # noqa: E402
from non_discrete import normalize_repeat_unit  # noqa: E402
from normalize_rdkit import hill_formula_no_charge  # noqa: E402

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise RuntimeError("jsonschema is required; install validation/requirements.txt") from exc

try:
    from rdkit import Chem
    from rdkit.Chem import inchi
except ImportError as exc:
    raise RuntimeError("RDKit is required; install validation/requirements.txt") from exc

STRUCTURE_FILES = {
    "canonical/molecules.jsonl": "molecule",
    "canonical/ions.jsonl": "ion",
    "canonical/formula_units.jsonl": "formula_unit",
    "canonical/polymer_repeat_units.jsonl": "polymer_repeat_unit",
}
LINK_FILES = {
    "links/inorganic.jsonl": "inorganic",
    "links/organic.jsonl": "organic",
}
DEFERRAL_FILES = {"deferrals/organic.jsonl": "organic"}
EXPECTED_COUNTS = {
    "molecule": 46,
    "ion": 24,
    "formula_unit": 12,
    "polymer_repeat_unit": 5,
}
EXPECTED_DATASET = "chem-knowledge-data/structure_registry"
EXPECTED_DATASET_VERSION = "structure-registry-foundation-1.0.1"
EXPECTED_SCHEMA_ID_PREFIX = "https://github.com/ACCXhub/chem-knowledge-data/packages/structure_registry/schema/"


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[tuple[int, dict]]:
    rows: list[tuple[int, dict]] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            value = json.loads(line)
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON: {exc}") from exc
        rows.append((line_no, value))
    return rows


def schema_validator(name: str) -> Draft202012Validator:
    schema = read_json(PACKAGE_ROOT / "schema" / name)
    return Draft202012Validator(schema, format_checker=FormatChecker())


def validate_schema_identity(name: str, errors: list[str]) -> None:
    schema = read_json(PACKAGE_ROOT / "schema" / name)
    expected = EXPECTED_SCHEMA_ID_PREFIX + name
    if schema.get("$id") != expected:
        errors.append(f"schema $id mismatch for {name}: {schema.get('$id')!r} != {expected!r}")


def validate_evidence_paths(record: dict, loc: str, errors: list[str]) -> None:
    for evidence in record.get("evidence", []):
        if evidence.startswith(("packages/", "coordination/", ".github/")):
            if not (REPO_ROOT / evidence).exists():
                errors.append(f"{loc}: evidence path does not exist: {evidence}")


def validate_structure_chemistry(record: dict) -> list[str]:
    errors: list[str] = []
    scope = record["structure_scope"]
    sid = record["structure_id"]
    standard_inchi = record.get("standard_inchi")
    standard_inchikey = record.get("standard_inchikey")

    if standard_inchi:
        if structure_id_from_inchi(standard_inchi) != sid:
            errors.append("structure_id is not deterministic for Standard InChI")
        derived_key = inchi.InchiToInchiKey(standard_inchi)
        if derived_key != standard_inchikey:
            errors.append(f"InChIKey mismatch: stored {standard_inchikey!r}, derived {derived_key!r}")

    if scope in {"molecule", "ion"}:
        smiles = record.get("isomeric_smiles") or record.get("canonical_smiles")
        if not smiles:
            errors.append("discrete structure is missing SMILES")
            return errors
        mol = Chem.MolFromSmiles(smiles, sanitize=True)
        if mol is None:
            errors.append("SMILES cannot be parsed/sanitized by RDKit")
            return errors
        formula = hill_formula_no_charge(mol)
        charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
        if formula != record.get("molecular_formula"):
            errors.append(f"formula mismatch: stored {record.get('molecular_formula')!r}, derived {formula!r}")
        if charge != record.get("formal_charge"):
            errors.append(f"charge mismatch: stored {record.get('formal_charge')!r}, derived {charge!r}")
        if scope == "molecule" and charge != 0:
            errors.append(f"molecule scope requires zero net formal charge; derived {charge}")
        if scope == "ion" and charge == 0:
            errors.append("ion scope requires nonzero net formal charge")
        if standard_inchi:
            derived_inchi = inchi.MolToInchi(mol)
            if derived_inchi != standard_inchi:
                errors.append(f"SMILES/InChI mismatch: derived {derived_inchi!r}, stored {standard_inchi!r}")
        if record.get("repeat_unit_smiles") is not None:
            errors.append("discrete structure must not publish repeat_unit_smiles")

    elif scope == "formula_unit":
        if record.get("canonical_smiles") is not None or record.get("isomeric_smiles") is not None:
            errors.append("formula_unit must not publish salt SMILES as a molecular representation")
        if not standard_inchi or not standard_inchikey:
            errors.append("formula_unit release requires pinned Standard InChI/InChIKey evidence")
        else:
            inchi_mol = inchi.MolFromInchi(standard_inchi, sanitize=True, removeHs=False)
            if inchi_mol is None:
                errors.append("formula_unit Standard InChI cannot be parsed by RDKit")
            else:
                formula = hill_formula_no_charge(inchi_mol)
                charge = sum(atom.GetFormalCharge() for atom in inchi_mol.GetAtoms())
                if formula != record.get("molecular_formula"):
                    errors.append(
                        f"formula mismatch: stored {record.get('molecular_formula')!r}, derived from Standard InChI {formula!r}"
                    )
                if charge != record.get("formal_charge"):
                    errors.append(
                        f"formula-unit charge mismatch: stored {record.get('formal_charge')!r}, derived from Standard InChI {charge!r}"
                    )
        if record.get("formal_charge") != 0:
            errors.append("published neutral formula-unit record must have formal_charge=0")

    elif scope == "polymer_repeat_unit":
        if standard_inchi is not None or standard_inchikey is not None:
            errors.append("polymer repeat unit must not publish a Standard InChI as full-polymer identity")
        repeat_smiles = record.get("repeat_unit_smiles")
        if not repeat_smiles:
            errors.append("polymer repeat unit is missing repeat_unit_smiles")
        else:
            normalized = normalize_repeat_unit(repeat_smiles)
            if normalized.structure_id != sid:
                errors.append("polymer repeat-unit structure_id is not deterministic")
            if normalized.molecular_formula != record.get("molecular_formula"):
                errors.append(
                    f"repeat-unit formula mismatch: {record.get('molecular_formula')!r} != {normalized.molecular_formula!r}"
                )
            if normalized.formal_charge != record.get("formal_charge"):
                errors.append("repeat-unit formal charge mismatch")
            if normalized.attachment_point_count != record.get("attachment_point_count"):
                errors.append("repeat-unit attachment-point count mismatch")

    return errors


def validate_manifest(manifest: dict, counts: dict[str, int], errors: list[str]) -> None:
    manifest_counts = manifest.get("counts", {})
    for scope, expected in counts.items():
        if manifest_counts.get(scope) != expected:
            errors.append(f"manifest count mismatch for {scope}: {manifest_counts.get(scope)!r} != {expected}")
    total = sum(counts.values())
    if manifest_counts.get("total") != total:
        errors.append(f"manifest total mismatch: {manifest_counts.get('total')!r} != {total}")

    for relative, metadata in manifest.get("files", {}).items():
        path = PACKAGE_ROOT / "data" / relative
        if not path.exists():
            errors.append(f"manifest file is missing: {relative}")
            continue
        digest = hashlib.sha256(path.read_bytes()).hexdigest()
        if metadata.get("sha256") != digest:
            errors.append(f"manifest sha256 mismatch for {relative}")
        if path.suffix == ".jsonl":
            actual_records = len(read_jsonl(path))
            if metadata.get("records") != actual_records:
                errors.append(
                    f"manifest record count mismatch for {relative}: {metadata.get('records')!r} != {actual_records}"
                )
        elif metadata.get("records") is not None:
            errors.append(f"manifest records must be null for non-JSONL file {relative}")


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    errors: list[str] = []
    warnings: list[str] = []
    for name in (
        "structure-record.schema.json",
        "structure-link.schema.json",
        "structure-deferral.schema.json",
        "structure-request.schema.json",
    ):
        validate_schema_identity(name, errors)

    structure_schema = schema_validator("structure-record.schema.json")
    link_schema = schema_validator("structure-link.schema.json")
    deferral_schema = schema_validator("structure-deferral.schema.json")

    registry = read_json(PACKAGE_ROOT / "sources" / "registry.json")
    known_source_ids = {row["source_id"] for row in registry["sources"]}

    structure_ids: dict[str, str] = {}
    inchikeys: dict[str, str] = {}
    external_ids: dict[tuple[str, str], str] = {}
    counts: dict[str, int] = defaultdict(int)

    for relative, expected_scope in STRUCTURE_FILES.items():
        path = PACKAGE_ROOT / "data" / relative
        if not path.exists():
            errors.append(f"missing canonical file: {relative}")
            continue
        for line_no, record in read_jsonl(path):
            loc = f"{relative}:{line_no}"
            schema_errors = sorted(structure_schema.iter_errors(record), key=lambda err: list(err.path))
            for err in schema_errors:
                errors.append(f"{loc}: schema: {err.message}")
            if schema_errors:
                continue
            if record["structure_scope"] != expected_scope:
                errors.append(f"{loc}: scope {record['structure_scope']!r} != file scope {expected_scope!r}")
            counts[expected_scope] += 1

            sid = record["structure_id"]
            if sid in structure_ids:
                errors.append(f"{loc}: duplicate structure_id; first seen at {structure_ids[sid]}")
            else:
                structure_ids[sid] = loc

            key = record.get("standard_inchikey")
            if key:
                if key in inchikeys and inchikeys[key] != sid:
                    errors.append(f"{loc}: InChIKey {key} maps to multiple structure IDs")
                else:
                    inchikeys[key] = sid

            for ext in record.get("external_ids", []):
                ext_key = (ext["namespace"], ext["value"])
                if ext_key in external_ids and external_ids[ext_key] != sid:
                    errors.append(f"{loc}: external ID {ext_key} maps to multiple structure IDs")
                else:
                    external_ids[ext_key] = sid

            for provenance in record["provenance"]:
                if provenance["source_id"] not in known_source_ids:
                    errors.append(f"{loc}: unknown provenance source_id {provenance['source_id']!r}")

            for issue in validate_structure_chemistry(record):
                errors.append(f"{loc}: chemistry: {issue}")

            if record["validation"]["review_status"] == "published":
                if record["validation"]["status"] != "valid":
                    errors.append(f"{loc}: published record must have validation.status=valid")
                if not record["provenance"]:
                    errors.append(f"{loc}: published record must have provenance")

    for scope, expected in EXPECTED_COUNTS.items():
        if counts.get(scope, 0) != expected:
            errors.append(f"release count mismatch for {scope}: {counts.get(scope, 0)} != {expected}")
    if len(structure_ids) != 87:
        errors.append(f"expected 87 unique structures, got {len(structure_ids)}")

    links_by_track: dict[str, list[dict]] = defaultdict(list)
    link_ids: set[str] = set()
    for relative, expected_track in LINK_FILES.items():
        path = PACKAGE_ROOT / "data" / relative
        if not path.exists():
            errors.append(f"missing link file: {relative}")
            continue
        for line_no, record in read_jsonl(path):
            loc = f"{relative}:{line_no}"
            schema_errors = list(link_schema.iter_errors(record))
            for err in schema_errors:
                errors.append(f"{loc}: schema: {err.message}")
            if schema_errors:
                continue
            if record["requester_track"] != expected_track:
                errors.append(f"{loc}: requester_track mismatch")
            if record["link_id"] in link_ids:
                errors.append(f"{loc}: duplicate link_id {record['link_id']}")
            link_ids.add(record["link_id"])
            if record["structure_id"] not in structure_ids:
                errors.append(f"{loc}: link points to unknown structure_id {record['structure_id']}")
            if record["status"] != "accepted":
                errors.append(f"{loc}: release link must be accepted")
            validate_evidence_paths(record, loc, errors)
            links_by_track[expected_track].append(record)

    deferrals_by_track: dict[str, list[dict]] = defaultdict(list)
    deferral_ids: set[str] = set()
    for relative, expected_track in DEFERRAL_FILES.items():
        path = PACKAGE_ROOT / "data" / relative
        if not path.exists():
            errors.append(f"missing deferral file: {relative}")
            continue
        for line_no, record in read_jsonl(path):
            loc = f"{relative}:{line_no}"
            schema_errors = list(deferral_schema.iter_errors(record))
            for err in schema_errors:
                errors.append(f"{loc}: schema: {err.message}")
            if schema_errors:
                continue
            if record["requester_track"] != expected_track:
                errors.append(f"{loc}: requester_track mismatch")
            if record["deferral_id"] in deferral_ids:
                errors.append(f"{loc}: duplicate deferral_id {record['deferral_id']}")
            deferral_ids.add(record["deferral_id"])
            for sid in record["available_abstraction_structure_ids"]:
                if sid not in structure_ids:
                    errors.append(f"{loc}: deferral references unknown abstraction structure {sid}")
            validate_evidence_paths(record, loc, errors)
            deferrals_by_track[expected_track].append(record)

    targets = read_json(PACKAGE_ROOT / "sources" / "cross_track_targets.json")
    expected_inorganic = {row["entity_ref"] for row in targets["inorganic"]["accepted"]}
    actual_inorganic = {row["entity_ref"] for row in links_by_track["inorganic"]}
    if actual_inorganic != expected_inorganic:
        errors.append(
            f"inorganic coverage mismatch: missing={sorted(expected_inorganic-actual_inorganic)}, "
            f"extra={sorted(actual_inorganic-expected_inorganic)}"
        )
    for row in links_by_track["inorganic"]:
        if row["entity_kind"] != "ion" or row["relation"] != "ion_structure":
            errors.append(f"inorganic link {row['link_id']} must be ion/ion_structure")

    accepted_org = {row["entity_ref"] for row in targets["organic"]["accepted"]}
    deferred_org = {row["entity_ref"] for row in targets["organic"]["deferrals"]}
    repeat_org = {row["entity_ref"] for row in targets["organic"]["repeat_units"]}
    identity_linked_org = {
        row["entity_ref"]
        for row in links_by_track["organic"]
        if row["relation"] in {"primary_structure", "formula_unit"}
    }
    repeat_linked_org = {
        row["entity_ref"] for row in links_by_track["organic"] if row["relation"] == "repeat_unit_structure"
    }
    actual_deferred_org = {row["entity_ref"] for row in deferrals_by_track["organic"]}
    if identity_linked_org != accepted_org:
        errors.append("organic accepted identity-link coverage does not match frozen targets")
    if repeat_linked_org != repeat_org:
        errors.append("organic repeat-unit link coverage does not match frozen targets")
    if actual_deferred_org != deferred_org:
        errors.append("organic deferral coverage does not match frozen targets")
    all_org_targets = accepted_org | deferred_org
    covered_org = identity_linked_org | actual_deferred_org
    if len(all_org_targets) != 50 or covered_org != all_org_targets:
        errors.append(f"organic entity coverage must be 50/50; got {len(covered_org)}/{len(all_org_targets)}")

    coverage_path = PACKAGE_ROOT / "data" / "coverage.json"
    if not coverage_path.exists():
        errors.append("data/coverage.json is missing")
    else:
        coverage = read_json(coverage_path)
        if coverage.get("dataset_version") != EXPECTED_DATASET_VERSION:
            errors.append(f"unexpected coverage dataset_version {coverage.get('dataset_version')!r}")
        if coverage.get("inorganic") != {
            "target_entities": 23,
            "accepted_links": 23,
            "deferrals": 0,
            "covered_entities": 23,
        }:
            errors.append(f"unexpected inorganic coverage summary: {coverage.get('inorganic')!r}")
        if coverage.get("organic") != {
            "target_entities": 50,
            "accepted_identity_links": 41,
            "repeat_unit_links": 5,
            "deferrals": 9,
            "covered_entities": 50,
        }:
            errors.append(f"unexpected organic coverage summary: {coverage.get('organic')!r}")

    evidence_counts = {
        "molecules": len(read_jsonl(PACKAGE_ROOT / "sources" / "pubchem_evidence_molecules.jsonl")),
        "ions": len(read_jsonl(PACKAGE_ROOT / "sources" / "pubchem_evidence_ions.jsonl")),
        "formula_units": len(read_jsonl(PACKAGE_ROOT / "sources" / "pubchem_evidence_formula_units.jsonl")),
    }
    if evidence_counts != {"molecules": 46, "ions": 24, "formula_units": 12}:
        errors.append(f"unexpected evidence counts: {evidence_counts!r}")

    manifest_path = PACKAGE_ROOT / "data" / "manifest.json"
    if not manifest_path.exists():
        errors.append("data/manifest.json is missing")
    else:
        manifest = read_json(manifest_path)
        validate_manifest(manifest, dict(counts), errors)
        if manifest.get("dataset") != EXPECTED_DATASET:
            errors.append(f"unexpected dataset {manifest.get('dataset')!r}")
        if manifest.get("dataset_version") != EXPECTED_DATASET_VERSION:
            errors.append(f"unexpected dataset_version {manifest.get('dataset_version')!r}")
        if manifest.get("cross_track") != {
            "inorganic_accepted_links": 23,
            "organic_accepted_links": 46,
            "organic_deferrals": 9,
        }:
            errors.append(f"unexpected manifest cross_track counts: {manifest.get('cross_track')!r}")

    for warning in warnings:
        print("WARNING:", warning)
    if errors:
        for error in errors:
            print("ERROR:", error)
        print(f"FAILED: {len(errors)} error(s), {len(warnings)} warning(s)")
        return 1
    if args.strict and warnings:
        print(f"FAILED: strict mode with {len(warnings)} warning(s)")
        return 1

    print(
        "OK: "
        + ", ".join(f"{scope}={counts[scope]}" for scope in sorted(EXPECTED_COUNTS))
        + f"; total={sum(counts.values())}; unique_ids={len(structure_ids)}; "
        + f"inorganic=23/23; organic=50/50"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
