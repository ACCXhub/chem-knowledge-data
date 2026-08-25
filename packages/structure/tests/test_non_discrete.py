from __future__ import annotations

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
sys.path.insert(0, str(PIPELINES))

from non_discrete import normalize_repeat_unit  # noqa: E402


class RepeatUnitTests(unittest.TestCase):
    def test_polyethylene_repeat_unit(self) -> None:
        record = normalize_repeat_unit("[*]CC[*]")
        self.assertEqual(record.structure_scope, "polymer_repeat_unit")
        self.assertEqual(record.molecular_formula, "C2H4")
        self.assertEqual(record.formal_charge, 0)
        self.assertEqual(record.attachment_point_count, 2)
        self.assertIsNone(record.standard_inchi)

    def test_polyvinyl_chloride_repeat_unit(self) -> None:
        record = normalize_repeat_unit("[*]CC([*])Cl")
        self.assertEqual(record.molecular_formula, "C2H3Cl")
        self.assertEqual(record.attachment_point_count, 2)

    def test_pet_repeat_unit(self) -> None:
        record = normalize_repeat_unit("[*]OCCOC(=O)c1ccc(C(=O)[*])cc1")
        self.assertEqual(record.molecular_formula, "C10H8O4")
        self.assertEqual(record.attachment_point_count, 2)

    def test_repeat_unit_requires_two_attachment_points(self) -> None:
        with self.assertRaises(ValueError):
            normalize_repeat_unit("[*]CC")


if __name__ == "__main__":
    unittest.main()
