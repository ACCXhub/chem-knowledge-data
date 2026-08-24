# Canonical structure records

Checked-in canonical records are split by structure scope:

- `molecules.jsonl`
- `ions.jsonl`
- `formula_units.jsonl`

`coordination_entity` and `crystal` scopes are schema-supported but have no published seed records yet because this release does not fabricate unsupported connectivity or crystallography.

All records in the current seed files are `published + valid`, source-neutral, deterministic-ID records. Rebuild them with `../../pipelines/build_seed.py` and verify with `../../validation/validate_dataset.py --strict`.
