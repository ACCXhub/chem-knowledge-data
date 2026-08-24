# Structure data layout

Canonical structure records are validated against `../schema/structure-record.schema.json`.

## Current release

`structure-seed-1.0.0` publishes **33** source-backed canonical records:

- 14 discrete neutral molecules;
- 9 discrete ions;
- 10 formula units for common salts/bases;
- 0 coordination entities;
- 0 crystal records.

Exact counts and file hashes are in `manifest.json`.

## Storage convention

Canonical records use JSON Lines:

- `canonical/molecules.jsonl`
- `canonical/ions.jsonl`
- `canonical/formula_units.jsonl`

Future scopes use the same record schema but are not represented by empty placeholder JSONL files.

Large generated 2D/3D assets are not canonical source files. Prefer reproducible derivation metadata; persist coordinates only when a downstream contract genuinely requires them.

## Cross-track references

Inorganic/Organic packages may reference a published `structure_id`. They must not duplicate canonical SMILES/InChI/InChIKey as their own truth.

Structure's `molecular_formula` uses `hill_no_charge` for machine comparison. Other tracks retain ownership of conventional display formulas and teaching notation.

## Publication states

- `draft`: ingested/derived but not stable.
- `reviewed`: chemistry and provenance checks passed but not yet public seam.
- `published`: stable cross-track record.
- `rejected`: retained only when useful for audit/debugging.

Only `published + valid` records are stable references.
