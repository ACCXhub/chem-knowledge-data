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

- 41 accepted full-identity links;
- 5 additional repeat-unit abstraction links;
- 9 explicit full-identity deferrals;
- **50 / 50 Organic substances accounted**;
- **0 unaccounted**.

Current Inorganic ion seed:

- 23 accepted `ion_structure` links;
- **23 / 23 ions linked**;
- **0 unaccounted**.

The phosphate Structure remains published as useful extra coverage even though phosphate is not in the current 23-ion Inorganic seed snapshot.

## Integrity gates

The strict validator checks:

- JSON Schema;
- deterministic Structure/link/deferral IDs;
- duplicate Structure IDs, InChIKeys and external IDs;
- SMILES parse/sanitization;
- formula and formal-charge consistency;
- Standard InChI/InChIKey consistency;
- formula-unit no-fake-molecule rule;
- polymer repeat-unit attachment points and deterministic fallback identity;
- accepted-link target existence and scope;
- Organic and Inorganic coverage completeness;
- manifest counts, per-file record counts and SHA-256.

## Verification evidence

GitHub Actions **Validate structure package**, working-branch run `32809697660`, completed successfully on Python 3.13 with pinned `rdkit==2025.9.4` and `jsonschema==4.25.1`.

```text
build_release.py
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9

validate_dataset.py --strict
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50

python -m unittest discover -s packages/structure/tests -v
Ran 16 tests
OK
```

Pull-request run `32809798607` independently passed the same rebuild, strict validation, tests, and the generated-data no-diff reproducibility gate.

PR #3 was squash-merged into `main` as commit `db02499d04475b3f710e7399b4e0a3dbaeea198e`. The `main` manifest was re-read after merge and confirms `structure-foundation-1.0.0`, schema `1.2.0`, all 87 records, 23 Inorganic links, 46 Organic links and 9 Organic deferrals.

`packages/structure/**` remains the locked canonical owner. Future Structure changes are additive releases triggered by stable new cross-track entities/requests or new evidence, not speculative volume expansion.
