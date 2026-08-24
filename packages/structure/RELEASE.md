# Structure release: structure-seed-1.0.0

Status: **PUBLISHED / LOCKED**

Schema: `structure-record 1.1.0`

Published records: **33**

- molecules: 14
- ions: 9
- formula units: 10

Only source-backed records that pass deterministic ID, schema, RDKit chemistry, formula/charge, Standard InChI/InChIKey and duplicate checks are published.

Coordination-entity and crystal schemas are reserved. This release does not fabricate unsupported connectivity or crystallography.

Validation evidence:

```text
python packages/structure/validation/validate_dataset.py --strict
OK: formula_unit=10, ion=9, molecule=14; total=33; unique_ids=33

python -m unittest discover -s packages/structure/tests -v
Ran 9 tests
OK
```

`packages/structure/**` remains the locked canonical owner for structure data.
