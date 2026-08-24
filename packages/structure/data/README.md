# Structure data layout

Canonical structure records live in this package and are validated against `../schema/structure-record.schema.json`.

## Storage convention

Use JSON Lines for canonical records so records remain diffable, streamable and easy to validate:

- `canonical/molecules.jsonl`
- `canonical/ions.jsonl`
- `canonical/formula_units.jsonl`
- `canonical/coordination_entities.jsonl`
- `canonical/crystals.jsonl`

Large generated 2D/3D assets are not canonical source files. Store only reproducible derivation metadata or compact coordinates when a downstream consumer genuinely requires them.

## Cross-track references

Inorganic/Organic packages may reference `structure_id`. They should not duplicate canonical SMILES/InChI/InChIKey fields as their own truth.

## Publication states

- `draft`: ingested/derived but not ready for cross-track consumption
- `reviewed`: chemistry and provenance checks passed
- `published`: stable public cross-track record
- `rejected`: retained only when useful for audit/debugging

Only `published` records are considered stable references for other workstreams.
