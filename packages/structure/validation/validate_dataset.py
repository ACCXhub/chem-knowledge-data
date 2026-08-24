"""Validate the canonical Structure dataset.

Usage:
    python packages/structure/validation/validate_dataset.py --strict
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import defaultdict
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
PIPELINES = PACKAGE_ROOT / "pipelines"
sys.path.insert(0, str(PIPELINES))

from ids import structure_id_from_inchi  # noqa: E402

try:
    from jsonschema import Draft202012Validator, FormatChecker
except ImportError as exc:
    raise RuntimeError("jsonschema is required; install validation/requirements.txt") from exc

try:
    from rdkit import Chem
    from rdkit.Chem import inchi
except ImportError as exc:
    raise RuntimeError("RDKit is required; install validation/requirements.txt") from exc

from normalize_rdkit import hill_formula_no_charge  # noqa: E402

EXPECTED_FILES = {
    "molecules.jsonl": "molecule",
    "ions.jsonl": "ion",
    "formula_units.jsonl": "formula_unit",
}


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


def validate_record_chemistry(record: dict) -> list[str]:
    errors: list[str] = []
    sid = record["structure_id"]
    standard_inchi = record.get("standard_inchi")
    standard_inchikey = record.get("standard_inchikey")

    if standard_inchi:
        expected_id = structure_id_from_inchi(standard_inchi)
        if sid != expected_id:
            errors.append(f"structure_id is not deterministic for Standard InChI: {sid}")
        derived_key = inchi.InchiToInchiKey(standard_inchi)
        if derived_key != standard_inchikey:
            errors.append(f"InChIKey mismatch: stored {standard_inchikey!r}, derived {derived_key!r}")

    smiles = record.get("isomeric_smiles") or record.get("canonical_smiles")
    mol = None
    if smiles:
        mol = Chem.MolFromSmiles(smiles, sanitize=True)
        if mol is None:
            errors.append("SMILES cannot be parsed/sanitized by RDKit")
        else:
            formula = hill_formula_no_charge(mol)
            charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
            if formula != record.get("molecular_formula"):
                errors.append(f"formula mismatch: stored {record.get('molecular_formula')!r}, derived {formula!r}")
            if charge != record.get("formal_charge"):
                errors.append(f"charge mismatch: stored {record.get('formal_charge')!r}, derived {charge!r}")
            if standard_inchi:
                derived_inchi = inchi.MolToInchi(mol)
                if derived_inchi != standard_inchi:
                    errors.append(f"SMILES/InChI mismatch: derived {derived_inchi!r}, stored {standard_inchi!r}")

    if mol is None and standard_inchi:
        mol = inchi.MolFromInchi(standard_inchi, sanitize=True, removeHs=False)
        if mol is not None:
            formula = hill_formula_no_charge(mol)
            charge = sum(atom.GetFormalCharge() for atom in mol.GetAtoms())
            if formula != record.get("molecular_formula"):
                errors.append(f"InChI formula mismatch: stored {record.get('molecular_formula')!r}, derived {formula!r}")
            if charge != record.get("formal_charge"):
                errors.append(f"InChI charge mismatch: stored {record.get('formal_charge')!r}, derived {charge!r}")

    if record["structure_scope"] == "formula_unit" and (record.get("canonical_smiles") is not None or record.get("isomeric_smiles") is not None):
        errors.append("formula_unit seed must not publish salt SMILES as a molecular representation")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--strict", action="store_true", help="Treat warnings as failures")
    args = parser.parse_args()

    schema_path = PACKAGE_ROOT / "schema" / "structure-record.schema.json"
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    schema_validator = Draft202012Validator(schema, format_checker=FormatChecker())

    canonical = PACKAGE_ROOT / "data" / "canonical"
    errors: list[str] = []
    warnings: list[str] = []
    ids: dict[str, str] = {}
    inchikeys: dict[str, str] = {}
    external: dict[tuple[str, str], str] = {}
    counts = defaultdict(int)

    for filename, expected_scope in EXPECTED_FILES.items():
        path = canonical / filename
        if not path.exists():
            errors.append(f"missing canonical file: {path}")
            continue
        for line_no, record in read_jsonl(path):
            loc = f"{path}:{line_no}"
            schema_errors = sorted(schema_validator.iter_errors(record), key=lambda err: list(err.path))
            for err in schema_errors:
                errors.append(f"{loc}: schema: {err.message}")
            if schema_errors:
                continue
            if record["structure_scope"] != expected_scope:
                errors.append(f"{loc}: scope {record['structure_scope']!r} does not match file {expected_scope!r}")
            counts[expected_scope] += 1

            sid = record["structure_id"]
            if sid in ids:
                errors.append(f"{loc}: duplicate structure_id; first seen at {ids[sid]}")
            else:
                ids[sid] = loc

            key = record.get("standard_inchikey")
            if key:
                if key in inchikeys and inchikeys[key] != sid:
                    errors.append(f"{loc}: InChIKey {key} maps to multiple structure IDs")
                else:
                    inchikeys[key] = sid

            for ext in record.get("external_ids", []):
                ext_key = (ext["namespace"], ext["value"])
                if ext_key in external and external[ext_key] != sid:
                    errors.append(f"{loc}: external ID {ext_key} maps to multiple structure IDs")
                else:
                    external[ext_key] = sid

            for issue in validate_record_chemistry(record):
                errors.append(f"{loc}: chemistry: {issue}")

            if record["validation"]["review_status"] == "published":
                if record["validation"]["status"] != "valid":
                    errors.append(f"{loc}: published record must have validation.status=valid")
                if not record["provenance"]:
                    errors.append(f"{loc}: published record must have provenance")

    manifest_path = PACKAGE_ROOT / "data" / "manifest.json"
    if manifest_path.exists():
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        manifest_counts = manifest.get("counts", {})
        for scope, count in counts.items():
            if manifest_counts.get(scope) != count:
                errors.append(f"manifest count mismatch for {scope}: {manifest_counts.get(scope)!r} != {count}")
    else:
        warnings.append("data/manifest.json is missing")

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

    print("OK: " + ", ".join(f"{scope}={counts[scope]}" for scope in sorted(counts)) + f"; total={sum(counts.values())}; unique_ids={len(ids)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
