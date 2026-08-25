from __future__ import annotations

import json
import unittest
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parents[1]


def read_jsonl(path: Path) -> list[dict]:
    return [json.loads(line) for line in path.read_text(encoding="utf-8").splitlines() if line.strip()]


class ReleaseContractTests(unittest.TestCase):
    def test_pinned_evidence_counts(self) -> None:
        sources = PACKAGE_ROOT / "sources"
        self.assertEqual(len(read_jsonl(sources / "pubchem_evidence_molecules.jsonl")), 46)
        self.assertEqual(len(read_jsonl(sources / "pubchem_evidence_ions.jsonl")), 24)
        self.assertEqual(len(read_jsonl(sources / "pubchem_evidence_formula_units.jsonl")), 12)

    def test_cross_track_target_counts(self) -> None:
        targets = json.loads((PACKAGE_ROOT / "sources" / "cross_track_targets.json").read_text(encoding="utf-8"))
        self.assertEqual(len(targets["inorganic"]["accepted"]), 23)
        self.assertEqual(len(targets["organic"]["accepted"]), 41)
        self.assertEqual(len(targets["organic"]["deferrals"]), 9)
        self.assertEqual(len(targets["organic"]["repeat_units"]), 5)
        all_organic = {
            row["entity_ref"] for row in targets["organic"]["accepted"]
        } | {
            row["entity_ref"] for row in targets["organic"]["deferrals"]
        }
        self.assertEqual(len(all_organic), 50)

    def test_every_polymer_repeat_unit_has_matching_deferral(self) -> None:
        targets = json.loads((PACKAGE_ROOT / "sources" / "cross_track_targets.json").read_text(encoding="utf-8"))
        deferrals = {row["entity_ref"]: row for row in targets["organic"]["deferrals"]}
        for repeat in targets["organic"]["repeat_units"]:
            self.assertIn(repeat["entity_ref"], deferrals)
            self.assertEqual(
                deferrals[repeat["entity_ref"]]["available_repeat_unit_key"],
                repeat["repeat_unit_key"],
            )


if __name__ == "__main__":
    unittest.main()
