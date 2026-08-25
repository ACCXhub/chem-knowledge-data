from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]
REPO_ROOT = PACKAGE_ROOT.parents[1]


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


if __name__ == "__main__":
    unittest.main()
