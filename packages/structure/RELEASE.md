# Structure release: structure-foundation-1.0.0

Status: **PUBLISHED / LOCKED**

Schema:

- `structure-record 1.2.0`
- `structure-link 1.1.0`
- `structure-deferral 1.0.0`

## Published canonical structures

**87** total:

- molecules: 46
- ions: 24
- formula units: 12
- polymer repeat units: 5
- coordination entities: 0
- crystals: 0

Zero coordination/crystal records are deliberate: no connectivity or crystallography is fabricated without appropriate evidence.

## Cross-track coverage

Organic `COMPLETE_V0_1`:

- 41 primary/formula-unit accepted links
- 5 additional repeat-unit abstraction links
- 9 explicit full-identity deferrals
- **50 / 50 substances accounted**
- **0 unaccounted**

Current Inorganic ion seed:

- 23 accepted `ion_structure` links
- **23 / 23 ions linked**
- **0 unaccounted**

The existing phosphate Structure remains published as useful extra coverage even though phosphate is not in the current 23-ion inorganic seed snapshot.

## Integrity gates

The strict validator checks:

- JSON Schema
- deterministic Structure/link/deferral IDs
- duplicate IDs, InChIKeys and external IDs
- SMILES parse/sanitization
- formula + formal-charge consistency
- Standard InChI/InChIKey consistency
- formula-unit no-fake-molecule rule
- polymer repeat-unit attachment points and fallback identity
- accepted-link target existence/publication/scope
- organic and inorganic coverage completeness
- manifest counts, record counts and SHA-256

Fresh local verification for this release:

```text
python packages/structure/validation/validate_dataset.py --strict
OK: molecule=46, ion=24, formula_unit=12, polymer_repeat_unit=5; canonical_total=87; organic_accounted=50/50; inorganic_ions_linked=23/23; unique_ids=87

python -m unittest discover -s packages/structure/tests -v
Ran 19 tests
OK
```

`packages/structure/**` remains the locked canonical owner.
