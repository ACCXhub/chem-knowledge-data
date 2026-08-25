# Structure data layout

Canonical structure records are validated against `../schema/structure-record.schema.json`.

## Foundation release

`structure-foundation-1.0.0` is the complete Structure foundation for the currently frozen Organic v0.1 package and the current Inorganic ion seed.

Expected canonical coverage:

- **46** discrete neutral molecules;
- **24** discrete ions;
- **12** formula units for salts / ionic compounds;
- **5** polymer repeat-unit abstractions;
- **0** coordination entities until explicit metal–ligand evidence is requested;
- **0** crystal records until crystallographic evidence is requested.

The release therefore contains **87 canonical Structure records**. Exact hashes and counts are owned by `manifest.json` after deterministic generation.

## Canonical records

JSON Lines are used for streamable, diffable canonical data:

- `canonical/molecules.jsonl`
- `canonical/ions.jsonl`
- `canonical/formula_units.jsonl`
- `canonical/polymer_repeat_units.jsonl`

A formula is not automatically a molecule. Formula-unit and polymer-repeat-unit scopes deliberately use different semantics from discrete molecules.

## Cross-track products

Structure also publishes explicit integration records:

- `links/inorganic.jsonl` — accepted Inorganic entity → Structure links;
- `links/organic.jsonl` — accepted Organic entity → Structure links, including repeat-unit abstractions;
- `deferrals/organic.jsonl` — explicit unresolved stereochemical / macromolecular / full-polymer identity cases;
- `coverage.json` — deterministic cross-track coverage summary.

Consumers should follow the links instead of copying SMILES, InChI or InChIKey into their own package as competing truth.

## Formula convention

`molecular_formula` uses `hill_no_charge` for machine comparison:

- Hill ordering;
- formal charge is stored separately;
- polymer dummy attachment atoms are excluded;
- conventional teaching/display formula formatting remains owned by the calling knowledge package.

## Publication states

- `draft`: ingested/derived but not stable;
- `reviewed`: chemistry and provenance checks passed but not yet public seam;
- `published`: stable cross-track record;
- `rejected`: retained only when useful for audit/debugging.

Only `validation.status == valid` plus `validation.review_status == published` is a stable Structure record.

## Rebuild

The canonical release is generated from pinned evidence and frozen cross-track targets:

```text
python packages/structure/pipelines/build_release.py
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

CI reruns the same sequence. The Structure working branch may auto-commit deterministic generated data; pull requests require generation to be reproducible with no diff.
