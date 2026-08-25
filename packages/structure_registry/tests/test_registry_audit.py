from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from jsonschema import Draft202012Validator

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]
VALIDATION = PACKAGE_ROOT / "validation"
sys.path.insert(0, str(VALIDATION))

import validate_dataset as dataset_validator  # noqa: E402
from validate_dataset import validate_manifest, validate_structure_chemistry  # noqa: E402


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class StructureRegistryAuditTests(unittest.TestCase):
    def test_schema_ids_use_structure_registry_path(self) -> None:
        for path in sorted((PACKAGE_ROOT / "schema").glob("*.schema.json")):
            schema = read_json(path)
            self.assertIn(
                "/packages/structure_registry/schema/",
                schema["$id"],
                msg=f"stale schema $id in {path.name}: {schema['$id']}",
            )
            self.assertNotIn("/packages/structure/schema/", schema["$id"])

    def test_cross_track_schemas_accept_structural_chemistry(self) -> None:
        for name in (
            "structure-request.schema.json",
            "structure-link.schema.json",
            "structure-deferral.schema.json",
        ):
            schema = read_json(PACKAGE_ROOT / "schema" / name)
            self.assertIn(
                "structural_chemistry",
                schema["properties"]["requester_track"]["enum"],
                msg=f"{name} cannot represent the published structural_chemistry workstream",
            )

    def test_generated_evidence_paths_resolve(self) -> None:
        paths: set[str] = set()
        for relative in ("links/inorganic.jsonl", "links/organic.jsonl"):
            for row in read_jsonl(PACKAGE_ROOT / "data" / relative):
                paths.update(row["evidence"])
        for row in read_jsonl(PACKAGE_ROOT / "data" / "deferrals/organic.jsonl"):
            paths.update(row["evidence"])

        for evidence in sorted(paths):
            self.assertTrue(
                (REPO_ROOT / evidence).exists(),
                msg=f"generated evidence path does not exist: {evidence}",
            )

    def test_release_metadata_uses_registry_name(self) -> None:
        manifest = read_json(PACKAGE_ROOT / "data" / "manifest.json")
        coverage = read_json(PACKAGE_ROOT / "data" / "coverage.json")
        self.assertEqual(manifest["dataset"], "chem-knowledge-data/structure_registry")
        self.assertEqual(manifest["dataset_version"], "structure-registry-foundation-1.0.1")
        self.assertEqual(coverage["dataset_version"], manifest["dataset_version"])

    def test_legacy_seed_builder_cannot_overwrite_current_release(self) -> None:
        self.assertFalse(
            (PACKAGE_ROOT / "pipelines" / "build_seed.py").exists(),
            msg="legacy build_seed.py can overwrite current canonical data/manifest; remove it from active pipelines",
        )

    def test_formula_unit_formula_is_verified_from_standard_inchi(self) -> None:
        record = read_jsonl(PACKAGE_ROOT / "data" / "canonical" / "formula_units.jsonl")[0].copy()
        record["molecular_formula"] = "X"
        issues = validate_structure_chemistry(record)
        self.assertTrue(
            any("formula mismatch" in issue for issue in issues),
            msg=f"formula-unit composition is not independently checked: {issues}",
        )

    def test_molecule_and_ion_scope_are_consistent_with_net_charge(self) -> None:
        molecule = read_jsonl(PACKAGE_ROOT / "data" / "canonical" / "molecules.jsonl")[0].copy()
        molecule["structure_scope"] = "ion"
        self.assertTrue(
            any("ion scope" in issue for issue in validate_structure_chemistry(molecule)),
            msg="neutral structure can be mislabeled as ion without a chemistry error",
        )

        ion = read_jsonl(PACKAGE_ROOT / "data" / "canonical" / "ions.jsonl")[0].copy()
        ion["structure_scope"] = "molecule"
        self.assertTrue(
            any("molecule scope" in issue for issue in validate_structure_chemistry(ion)),
            msg="charged structure can be mislabeled as molecule without a chemistry error",
        )

    def test_resolved_request_requires_resolved_structure_id(self) -> None:
        schema = read_json(PACKAGE_ROOT / "schema" / "structure-request.schema.json")
        validator = Draft202012Validator(schema)
        request = {
            "schema_version": "1.2.0",
            "request_id": "sreq_00000000-0000-5000-8000-000000000000",
            "requester_track": "structural_chemistry",
            "local_entity_ref": "example:test",
            "status": "resolved",
            "resolved_structure_id": None,
        }
        self.assertFalse(validator.is_valid(request), msg="resolved request may not keep resolved_structure_id=null")

        request["status"] = "requested"
        request["resolved_structure_id"] = "str_00000000-0000-5000-8000-000000000000"
        self.assertFalse(validator.is_valid(request), msg="open request may not claim a resolved_structure_id")

    def test_manifest_must_list_every_published_data_file(self) -> None:
        manifest = read_json(PACKAGE_ROOT / "data" / "manifest.json")
        manifest = json.loads(json.dumps(manifest))
        manifest["files"].pop("links/organic.jsonl")
        errors: list[str] = []
        counts = {
            "molecule": 46,
            "ion": 24,
            "formula_unit": 12,
            "polymer_repeat_unit": 5,
        }
        validate_manifest(manifest, counts, errors)
        self.assertTrue(
            any("manifest file set mismatch" in error for error in errors),
            msg=f"validator accepts an incomplete manifest file set: {errors}",
        )

    def test_link_id_and_relation_target_scope_are_validated(self) -> None:
        validate_link_integrity = getattr(dataset_validator, "validate_link_integrity", None)
        self.assertIsNotNone(validate_link_integrity, "validator is missing link integrity checks")

        link = read_jsonl(PACKAGE_ROOT / "data" / "links" / "inorganic.jsonl")[0].copy()
        scopes = {link["structure_id"]: "molecule"}
        issues = validate_link_integrity(link, scopes)
        self.assertTrue(any("target scope" in issue for issue in issues), msg=f"scope mismatch not detected: {issues}")

        scopes[link["structure_id"]] = "ion"
        link["link_id"] = "slink_00000000-0000-5000-8000-000000000000"
        issues = validate_link_integrity(link, scopes)
        self.assertTrue(any("deterministic" in issue for issue in issues), msg=f"forged link_id not detected: {issues}")

    def test_deferral_id_is_recomputed(self) -> None:
        validate_deferral_integrity = getattr(dataset_validator, "validate_deferral_integrity", None)
        self.assertIsNotNone(validate_deferral_integrity, "validator is missing deferral integrity checks")

        row = read_jsonl(PACKAGE_ROOT / "data" / "deferrals" / "organic.jsonl")[0].copy()
        row["deferral_id"] = "sdef_00000000-0000-5000-8000-000000000000"
        issues = validate_deferral_integrity(row)
        self.assertTrue(any("deterministic" in issue for issue in issues), msg=f"forged deferral_id not detected: {issues}")


if __name__ == "__main__":
    unittest.main()
