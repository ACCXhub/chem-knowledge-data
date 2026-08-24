"""Build the curated canonical seed files from pinned evidence.

Run from anywhere:
    python packages/structure/pipelines/build_seed.py
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from ids import structure_id_from_inchi  # noqa: E402
from normalize_rdkit import normalize_smiles  # noqa: E402

SCHEMA_VERSION = "1.1.0"
VALIDATED_AT = "2026-08-24T09:40:00Z"


def compact_hash(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_evidence() -> list[dict]:
    path = PACKAGE_ROOT / "sources" / "pubchem_seed_evidence.jsonl"
    rows = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
    return rows


def build_discrete(evidence: dict) -> dict:
    normalized = normalize_smiles(evidence["source_smiles"], structure_scope=evidence["structure_scope"])
    for field, actual in (("standard_inchi", normalized.standard_inchi), ("standard_inchikey", normalized.standard_inchikey)):
        expected = evidence[field]
        if actual != expected:
            raise ValueError(f"PubChem {evidence['cid']} {field} mismatch: {actual!r} != {expected!r}")
    source_hash = compact_hash(evidence)
    return {
        "schema_version": SCHEMA_VERSION,
        "structure_id": normalized.structure_id,
        "structure_scope": evidence["structure_scope"],
        "formula_convention": "hill_no_charge",
        "molecular_formula": normalized.molecular_formula,
        "formal_charge": normalized.formal_charge,
        "canonical_smiles": normalized.canonical_smiles,
        "isomeric_smiles": normalized.isomeric_smiles,
        "standard_inchi": normalized.standard_inchi,
        "standard_inchikey": normalized.standard_inchikey,
        "external_ids": [{"namespace": "pubchem_cid", "value": str(evidence["cid"])}],
        "derived": normalized.derived,
        "validation": {"status": "valid", "review_status": "published", "normalization_method": "rdkit_smiles_sanitize_standard_inchi", "normalization_version": normalized.derived["toolkit_version"], "validated_at": VALIDATED_AT, "issues": []},
        "provenance": [
            {"source_id": "pubchem", "record_locator": f"CID {evidence['cid']}", "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{evidence['cid']}", "retrieved_at": evidence["retrieved_at"], "content_sha256": source_hash, "supports": ["standard_inchi", "standard_inchikey", "external_ids"]},
            {"source_id": "rdkit", "record_locator": f"RDKit {normalized.derived['toolkit_version']} normalization of PubChem CID {evidence['cid']} structure representation", "source_url": "https://www.rdkit.org/", "retrieved_at": VALIDATED_AT, "content_sha256": None, "supports": ["molecular_formula", "formal_charge", "canonical_smiles", "isomeric_smiles", "derived"]},
        ],
        "notes": None,
    }


def build_formula_unit(evidence: dict) -> dict:
    standard_inchi = evidence["standard_inchi"]
    if not standard_inchi.startswith("InChI=1S/"):
        raise ValueError("formula-unit evidence must use Standard InChI")
    if structure_id_from_inchi(standard_inchi) != evidence["structure_id"]:
        raise ValueError(f"formula-unit structure_id mismatch for CID {evidence['cid']}")
    source_hash = compact_hash(evidence)
    return {
        "schema_version": SCHEMA_VERSION,
        "structure_id": evidence["structure_id"],
        "structure_scope": "formula_unit",
        "formula_convention": "hill_no_charge",
        "molecular_formula": evidence["molecular_formula"],
        "formal_charge": evidence["formal_charge"],
        "canonical_smiles": None,
        "isomeric_smiles": None,
        "standard_inchi": standard_inchi,
        "standard_inchikey": evidence["standard_inchikey"],
        "external_ids": [{"namespace": "pubchem_cid", "value": str(evidence["cid"])}],
        "derived": None,
        "validation": {"status": "valid", "review_status": "published", "normalization_method": "source_verified_formula_unit", "normalization_version": "1", "validated_at": VALIDATED_AT, "issues": []},
        "provenance": [{"source_id": "pubchem", "record_locator": f"CID {evidence['cid']}", "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{evidence['cid']}", "retrieved_at": evidence["retrieved_at"], "content_sha256": source_hash, "supports": ["structure_scope", "molecular_formula", "formal_charge", "standard_inchi", "standard_inchikey", "external_ids"]}],
        "notes": "Formula-unit scope: disconnected salt representation is not promoted to a molecule.",
    }


def write_jsonl(path: Path, rows: list[dict]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def main() -> int:
    discrete = []
    formula_units = []
    for evidence in load_evidence():
        if evidence["structure_scope"] in {"molecule", "ion"}:
            discrete.append(build_discrete(evidence))
        elif evidence["structure_scope"] == "formula_unit":
            formula_units.append(build_formula_unit(evidence))
        else:
            raise ValueError(f"unsupported seed scope: {evidence['structure_scope']}")

    molecules = sorted((row for row in discrete if row["structure_scope"] == "molecule"), key=lambda row: row["structure_id"])
    ions = sorted((row for row in discrete if row["structure_scope"] == "ion"), key=lambda row: row["structure_id"])
    formula_units.sort(key=lambda row: row["structure_id"])

    files = {"canonical/molecules.jsonl": molecules, "canonical/ions.jsonl": ions, "canonical/formula_units.jsonl": formula_units}
    file_meta = {}
    for relative, rows in files.items():
        path = PACKAGE_ROOT / "data" / relative
        write_jsonl(path, rows)
        payload = path.read_bytes()
        file_meta[relative] = {"records": len(rows), "sha256": hashlib.sha256(payload).hexdigest()}

    manifest = {
        "dataset": "chem-knowledge-data/structure",
        "dataset_version": "structure-seed-1.0.0",
        "schema_version": SCHEMA_VERSION,
        "generated_at": VALIDATED_AT,
        "identity_namespace_uuid": "c9d2c469-8557-5661-ae35-950cde95e61f",
        "formula_convention": "hill_no_charge",
        "counts": {"molecule": len(molecules), "ion": len(ions), "formula_unit": len(formula_units), "coordination_entity": 0, "crystal": 0, "other": 0, "total": len(molecules) + len(ions) + len(formula_units)},
        "files": file_meta,
        "publication_rule": "Only validation.status=valid and validation.review_status=published is cross-track stable.",
    }
    (PACKAGE_ROOT / "data" / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")
    print(f"wrote {len(molecules)} molecules, {len(ions)} ions, {len(formula_units)} formula units")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
