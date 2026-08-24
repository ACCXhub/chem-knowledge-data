from __future__ import annotations

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
sys.path.insert(0, str(PIPELINES))

from normalize_rdkit import normalize_smiles  # noqa: E402


class NormalizeTests(unittest.TestCase):
    def test_ammonia_uses_hill_formula_not_display_formula(self) -> None:
        record = normalize_smiles("N", structure_scope="molecule")
        self.assertEqual(record.molecular_formula, "H3N")
        self.assertEqual(record.formal_charge, 0)

    def test_ammonium_separates_charge(self) -> None:
        record = normalize_smiles("[NH4+]", structure_scope="ion")
        self.assertEqual(record.molecular_formula, "H4N")
        self.assertEqual(record.formal_charge, 1)
        self.assertEqual(record.standard_inchikey, "QGZKDVFQNNGYKY-UHFFFAOYSA-O")

    def test_sulfate_normalizes_resonance_representation(self) -> None:
        record = normalize_smiles("[O-]S(=O)(=O)[O-]", structure_scope="ion")
        self.assertEqual(record.molecular_formula, "O4S")
        self.assertEqual(record.formal_charge, -2)
        self.assertTrue(record.standard_inchi.startswith("InChI=1S/"))

    def test_invalid_smiles_rejected(self) -> None:
        with self.assertRaises(ValueError):
            normalize_smiles("C[", structure_scope="molecule")


if __name__ == "__main__":
    unittest.main()
