"""Build the consumer-ready Structure foundation release from pinned evidence.

The builder is deterministic: all timestamps are pinned, source evidence is
versioned in-repository, and every dataset-owned identifier is UUIDv5-based.
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

from rdkit.Chem import inchi

HERE = Path(__file__).resolve()
PACKAGE_ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE.parent))

from ids import deferral_id, link_id, structure_id_from_inchi  # noqa: E402
from non_discrete import normalize_formula_unit, normalize_repeat_unit  # noqa: E402
from normalize_rdkit import normalize_smiles  # noqa: E402

SCHEMA_VERSION = "1.2.0"
LINK_SCHEMA_VERSION = "1.1.0"
DEFERRAL_SCHEMA_VERSION = "1.0.0"
DATASET_VERSION = "structure-foundation-1.0.0"
GENERATED_AT = "2026-08-25T04:28:00Z"


def compact_hash(obj: dict) -> str:
    raw = json.dumps(obj, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


def load_jsonl(relative: str) -> list[dict]:
    path = PACKAGE_ROOT / relative
    rows: list[dict] = []
    for line_no, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        if not line.strip():
            continue
        try:
            rows.append(json.loads(line))
        except json.JSONDecodeError as exc:
            raise ValueError(f"{path}:{line_no}: invalid JSON") from exc
    return rows


def load_json(relative: str) -> dict:
    return json.loads((PACKAGE_ROOT / relative).read_text(encoding="utf-8"))


def write_jsonl(relative: str, rows: list[dict]) -> None:
    path = PACKAGE_ROOT / "data" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    text = "".join(json.dumps(row, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n" for row in rows)
    path.write_text(text, encoding="utf-8")


def write_json(relative: str, obj: dict) -> None:
    path = PACKAGE_ROOT / "data" / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, ensure_ascii=False, sort_keys=True, indent=2) + "\n", encoding="utf-8")


def pubchem_provenance(evidence: dict, supports: list[str]) -> dict:
    cid = evidence["cid"]
    return {
        "source_id": "pubchem",
        "record_locator": f"CID {cid}",
        "source_url": f"https://pubchem.ncbi.nlm.nih.gov/compound/{cid}",
        "retrieved_at": evidence["retrieved_at"],
        "content_sha256": compact_hash(evidence),
        "supports": supports,
    }


def rdkit_provenance(*, label: str, toolkit_version: str, supports: list[str]) -> dict:
    return {
        "source_id": "rdkit",
        "record_locator": f"RDKit {toolkit_version} normalization for {label}",
        "source_url": "https://www.rdkit.org/",
        "retrieved_at": GENERATED_AT,
        "content_sha256": None,
        "supports": supports,
    }


def build_discrete(evidence: dict) -> dict:
    normalized = normalize_smiles(evidence["source_smiles"], structure_scope=evidence["structure_scope"])
    if normalized.standard_inchi != evidence["standard_inchi"]:
        raise ValueError(f"CID {evidence['cid']} Standard InChI mismatch")
    if normalized.standard_inchikey != evidence["standard_inchikey"]:
        raise ValueError(f"CID {evidence['cid']} Standard InChIKey mismatch")
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
        "repeat_unit_smiles": None,
        "attachment_point_count": None,
        "external_ids": [{"namespace": "pubchem_cid", "value": str(evidence["cid"])}],
        "derived": normalized.derived,
        "validation": {
            "status": "valid",
            "review_status": "published",
            "normalization_method": "rdkit_smiles_sanitize_standard_inchi",
            "normalization_version": normalized.derived["toolkit_version"],
            "validated_at": GENERATED_AT,
            "issues": [],
        },
        "provenance": [
            pubchem_provenance(evidence, ["standard_inchi", "standard_inchikey", "external_ids"]),
            rdkit_provenance(
                label=evidence["label"],
                toolkit_version=normalized.derived["toolkit_version"],
                supports=["molecular_formula", "formal_charge", "canonical_smiles", "isomeric_smiles", "derived"],
            ),
        ],
        "notes": None,
    }


def build_formula_unit(evidence: dict) -> dict:
    # Formula-unit identity is sourced from the pinned Standard InChI. We do not
    # publish disconnected salt SMILES as if the solid were a discrete molecule.
    if inchi.InchiToInchiKey(evidence["standard_inchi"]) != evidence["standard_inchikey"]:
        raise ValueError(f"CID {evidence['cid']} formula-unit InChIKey mismatch")
    structure_id = structure_id_from_inchi(evidence["standard_inchi"])
    return {
        "schema_version": SCHEMA_VERSION,
        "structure_id": structure_id,
        "structure_scope": "formula_unit",
        "formula_convention": "hill_no_charge",
        "molecular_formula": evidence["molecular_formula"],
        "formal_charge": evidence["formal_charge"],
        "canonical_smiles": None,
        "isomeric_smiles": None,
        "standard_inchi": evidence["standard_inchi"],
        "standard_inchikey": evidence["standard_inchikey"],
        "repeat_unit_smiles": None,
        "attachment_point_count": None,
        "external_ids": [{"namespace": "pubchem_cid", "value": str(evidence["cid"])}],
        "derived": None,
        "validation": {
            "status": "valid",
            "review_status": "published",
            "normalization_method": "source_verified_formula_unit",
            "normalization_version": "1",
            "validated_at": GENERATED_AT,
            "issues": [],
        },
        "provenance": [
            pubchem_provenance(
                evidence,
                ["structure_scope", "molecular_formula", "formal_charge", "standard_inchi", "standard_inchikey", "external_ids"],
            )
        ],
        "notes": "Formula-unit scope; disconnected salt representations are not promoted to molecular structures.",
    }


def build_repeat_unit(target: dict) -> dict:
    normalized = normalize_repeat_unit(target["repeat_unit_smiles"])
    return {
        "schema_version": SCHEMA_VERSION,
        "structure_id": normalized.structure_id,
        "structure_scope": "polymer_repeat_unit",
        "formula_convention": "hill_no_charge",
        "molecular_formula": normalized.molecular_formula,
        "formal_charge": normalized.formal_charge,
        "canonical_smiles": None,
        "isomeric_smiles": None,
        "standard_inchi": None,
        "standard_inchikey": None,
        "repeat_unit_smiles": normalized.repeat_unit_smiles,
        "attachment_point_count": normalized.attachment_point_count,
        "external_ids": [],
        "derived": {"toolkit": "RDKit", "toolkit_version": normalized.toolkit_version},
        "validation": {
            "status": "valid",
            "review_status": "published",
            "normalization_method": "curated_repeat_unit_rdkit_normalization",
            "normalization_version": normalized.toolkit_version,
            "validated_at": GENERATED_AT,
            "issues": [],
        },
        "provenance": [
            {
                "source_id": "organic_track",
                "record_locator": target["entity_ref"],
                "source_url": None,
                "retrieved_at": GENERATED_AT,
                "content_sha256": compact_hash(target),
                "supports": ["structure_scope", "repeat_unit_smiles"],
            },
            rdkit_provenance(
                label=target["repeat_unit_key"],
                toolkit_version=normalized.toolkit_version,
                supports=["molecular_formula", "formal_charge", "attachment_point_count", "derived"],
            ),
        ],
        "notes": "Teaching-level polymer repeat-unit abstraction; this is not a full polymer molecular identity.",
    }


def make_link(track: str, target: dict, structure_id: str) -> dict:
    return {
        "schema_version": LINK_SCHEMA_VERSION,
        "link_id": link_id(
            requester_track=track,
            entity_ref=target["entity_ref"],
            structure_id=structure_id,
            relation=target["relation"],
        ),
        "requester_track": track,
        "entity_kind": target["entity_kind"],
        "entity_ref": target["entity_ref"],
        "structure_id": structure_id,
        "relation": target["relation"],
        "status": "accepted",
        "evidence": ["packages/structure/sources/cross_track_targets.json"],
        "notes": None,
    }


def make_deferral(target: dict, repeat_id_by_key: dict[str, str]) -> dict:
    available: list[str] = []
    key = target.get("available_repeat_unit_key")
    if key:
        available.append(repeat_id_by_key[key])
    return {
        "schema_version": DEFERRAL_SCHEMA_VERSION,
        "deferral_id": deferral_id(requester_track="organic", entity_ref=target["entity_ref"], reason=target["reason"]),
        "requester_track": "organic",
        "entity_kind": target["entity_kind"],
        "entity_ref": target["entity_ref"],
        "reason": target["reason"],
        "status": "open",
        "available_abstraction_structure_ids": available,
        "evidence": [
            "packages/structure/sources/cross_track_targets.json",
            "packages/organic/data/identity_deferrals.yaml",
        ],
        "notes": target.get("notes"),
    }


def main() -> int:
    molecule_evidence = load_jsonl("sources/pubchem_evidence_molecules.jsonl")
    ion_evidence = load_jsonl("sources/pubchem_evidence_ions.jsonl")
    formula_evidence = load_jsonl("sources/pubchem_evidence_formula_units.jsonl")
    targets = load_json("sources/cross_track_targets.json")

    if len(molecule_evidence) != 46:
        raise ValueError(f"expected 46 molecule evidence rows, got {len(molecule_evidence)}")
    if len(ion_evidence) != 24:
        raise ValueError(f"expected 24 ion evidence rows, got {len(ion_evidence)}")
    if len(formula_evidence) != 12:
        raise ValueError(f"expected 12 formula-unit evidence rows, got {len(formula_evidence)}")

    molecules = sorted((build_discrete(row) for row in molecule_evidence), key=lambda row: row["structure_id"])
    ions = sorted((build_discrete(row) for row in ion_evidence), key=lambda row: row["structure_id"])
    formula_units = sorted((build_formula_unit(row) for row in formula_evidence), key=lambda row: row["structure_id"])

    repeat_targets = targets["organic"]["repeat_units"]
    repeat_units = sorted((build_repeat_unit(row) for row in repeat_targets), key=lambda row: row["structure_id"])
    repeat_id_by_key = {
        target["repeat_unit_key"]: build_repeat_unit(target)["structure_id"] for target in repeat_targets
    }

    cid_to_structure: dict[int, str] = {}
    for evidence, record in zip(molecule_evidence, (build_discrete(row) for row in molecule_evidence), strict=True):
        cid_to_structure[evidence["cid"]] = record["structure_id"]
    for evidence, record in zip(ion_evidence, (build_discrete(row) for row in ion_evidence), strict=True):
        cid_to_structure[evidence["cid"]] = record["structure_id"]
    for evidence, record in zip(formula_evidence, (build_formula_unit(row) for row in formula_evidence), strict=True):
        cid_to_structure[evidence["cid"]] = record["structure_id"]

    inorganic_links = [
        make_link("inorganic", target, cid_to_structure[target["pubchem_cid"]])
        for target in targets["inorganic"]["accepted"]
    ]
    organic_links = [
        make_link("organic", target, cid_to_structure[target["pubchem_cid"]])
        for target in targets["organic"]["accepted"]
    ]
    for target in repeat_targets:
        organic_links.append(make_link("organic", target, repeat_id_by_key[target["repeat_unit_key"]]))
    inorganic_links.sort(key=lambda row: row["link_id"])
    organic_links.sort(key=lambda row: row["link_id"])

    organic_deferrals = sorted(
        (make_deferral(target, repeat_id_by_key) for target in targets["organic"]["deferrals"]),
        key=lambda row: row["deferral_id"],
    )

    write_jsonl("canonical/molecules.jsonl", molecules)
    write_jsonl("canonical/ions.jsonl", ions)
    write_jsonl("canonical/formula_units.jsonl", formula_units)
    write_jsonl("canonical/polymer_repeat_units.jsonl", repeat_units)
    write_jsonl("links/inorganic.jsonl", inorganic_links)
    write_jsonl("links/organic.jsonl", organic_links)
    write_jsonl("deferrals/organic.jsonl", organic_deferrals)

    coverage = {
        "dataset_version": DATASET_VERSION,
        "generated_at": GENERATED_AT,
        "inorganic": {
            "target_entities": len(targets["inorganic"]["accepted"]),
            "accepted_links": len(inorganic_links),
            "deferrals": 0,
            "covered_entities": len({row["entity_ref"] for row in inorganic_links}),
        },
        "organic": {
            "target_entities": len(targets["organic"]["accepted"]) + len(targets["organic"]["deferrals"]),
            "accepted_identity_links": len(targets["organic"]["accepted"]),
            "repeat_unit_links": len(repeat_targets),
            "deferrals": len(organic_deferrals),
            "covered_entities": len(
                {row["entity_ref"] for row in organic_links}
                | {row["entity_ref"] for row in organic_deferrals}
            ),
        },
    }
    write_json("coverage.json", coverage)

    generated_files = [
        "canonical/molecules.jsonl",
        "canonical/ions.jsonl",
        "canonical/formula_units.jsonl",
        "canonical/polymer_repeat_units.jsonl",
        "links/inorganic.jsonl",
        "links/organic.jsonl",
        "deferrals/organic.jsonl",
        "coverage.json",
    ]
    file_meta: dict[str, dict] = {}
    for relative in generated_files:
        path = PACKAGE_ROOT / "data" / relative
        raw = path.read_bytes()
        records = None
        if path.suffix == ".jsonl":
            records = sum(1 for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        file_meta[relative] = {"sha256": hashlib.sha256(raw).hexdigest(), "records": records}

    counts = {
        "molecule": len(molecules),
        "ion": len(ions),
        "formula_unit": len(formula_units),
        "polymer_repeat_unit": len(repeat_units),
        "coordination_entity": 0,
        "crystal": 0,
        "other": 0,
    }
    counts["total"] = sum(counts.values())
    manifest = {
        "dataset": "chem-knowledge-data/structure",
        "dataset_version": DATASET_VERSION,
        "schema_version": SCHEMA_VERSION,
        "generated_at": GENERATED_AT,
        "identity_namespace_uuid": "c9d2c469-8557-5661-ae35-950cde95e61f",
        "formula_convention": "hill_no_charge",
        "counts": counts,
        "cross_track": {
            "inorganic_accepted_links": len(inorganic_links),
            "organic_accepted_links": len(organic_links),
            "organic_deferrals": len(organic_deferrals),
        },
        "files": file_meta,
        "publication_rule": "Only validation.status=valid and validation.review_status=published is a stable Structure record.",
    }
    write_json("manifest.json", manifest)

    print(
        f"built {counts['total']} structures; "
        f"inorganic links={len(inorganic_links)}; organic links={len(organic_links)}; "
        f"organic deferrals={len(organic_deferrals)}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
