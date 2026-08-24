# Structure package

`packages/structure/` is the **canonical owner** of chemical-structure identity and normalized structure records for `chem-knowledge-data`.

Other parallel workstreams may read published structures and store `structure_id` references. They must not modify this directory or create competing canonical structure records.

## Current published seed

Release `structure-seed-1.0.0` contains 33 verified records:

- 14 molecules;
- 9 ions;
- 10 formula units.

The seed intentionally includes both inorganic and organic/common molecular structures because Structure is cross-cutting. Curriculum classification remains owned by Inorganic/Organic.

## What Structure owns

- source-neutral deterministic `structure_id`;
- structure scope (`molecule`, `ion`, `formula_unit`, `coordination_entity`, `crystal`, `other`);
- canonical/isomeric SMILES where appropriate;
- Standard InChI/InChIKey;
- Hill/no-charge machine formula and formal charge;
- deterministic descriptors and derivation metadata;
- source identifiers/provenance;
- accepted Substance ↔ Structure links.

## Read first

- `CONTRACT.md` — ownership, identity and representation rules.
- `INTEGRATION.md` — exact rules for Inorganic/Organic callers.
- `schema/structure-record.schema.json` — canonical record contract.
- `schema/structure-request.schema.json` — request shape stored in the caller's package.
- `schema/structure-link.schema.json` — accepted link contract.
- `sources/SOURCE_POLICY.md` — evidence roles and conflict handling.
- `data/manifest.json` — current release counts/hashes.
- `validation/README.md` — publication checks.

## Rebuild and verify

```bash
python packages/structure/pipelines/build_seed.py
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

`build_seed.py` rebuilds checked-in canonical JSONL from pinned minimal PubChem evidence and RDKit normalization. It does not require network access.

## Boundary

Structure does not own inorganic/organic taxonomy, names, teaching copy, Reaction, Experiment, Phenomenon, Concept, Question or ExamTag data.

A formula is not automatically a molecule. In particular, common salts are represented as `formula_unit` records instead of being mislabeled as molecular structures.
