from __future__ import annotations

import sys
import unittest
from pathlib import Path

PIPELINES = Path(__file__).resolve().parents[1] / "pipelines"
sys.path.insert(0, str(PIPELINES))

from ids import STRUCTURE_NAMESPACE, link_id, request_id, structure_id_from_fallback, structure_id_from_inchi  # noqa: E402


class StructureIdTests(unittest.TestCase):
    def test_namespace_is_frozen(self) -> None:
        self.assertEqual(str(STRUCTURE_NAMESPACE), "c9d2c469-8557-5661-ae35-950cde95e61f")

    def test_water_id_is_stable(self) -> None:
        self.assertEqual(structure_id_from_inchi("InChI=1S/H2O/h1H2"), "str_30930b4c-d90b-5ce1-9e59-b86b1a3a367e")

    def test_nonstandard_inchi_rejected(self) -> None:
        with self.assertRaises(ValueError):
            structure_id_from_inchi("InChI=1/H2O/h1H2")

    def test_fallback_is_deterministic(self) -> None:
        kwargs = {"structure_scope": "crystal", "normalized_representation": "cod:12345", "formal_charge": 0}
        self.assertEqual(structure_id_from_fallback(**kwargs), structure_id_from_fallback(**kwargs))

    def test_link_and_request_ids_are_deterministic(self) -> None:
        args = {"requester_track": "inorganic", "substance_ref": "substance:example", "structure_id": "str_30930b4c-d90b-5ce1-9e59-b86b1a3a367e", "relation": "primary_structure"}
        self.assertEqual(link_id(**args), link_id(**args))
        self.assertEqual(request_id(requester_track="organic", local_entity_ref="ethanol"), request_id(requester_track="organic", local_entity_ref="ethanol"))


if __name__ == "__main__":
    unittest.main()
