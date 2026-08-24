# Inorganic data policy

## Scope

This package curates machine-readable high-school inorganic chemistry facts. The active chain is:

`Element teaching projection → Ion → Substance → Reaction → Phenomenon / Experiment → Concept`

`Structure`, `FunctionalGroup`, `Mechanism`, atom mapping, bond diff and synthesis planning remain outside this package.

## Canonical ownership

- `element_scope.jsonl` stores only curriculum-facing priority/coverage metadata keyed by symbol and atomic number. It is not a second periodic-table truth source.
- `ions.jsonl` owns common monatomic/polyatomic ion identities used by the high-school inorganic layer.
- `substances.jsonl` owns canonical inorganic species records and optional aqueous dissociation projections.
- `reactions.jsonl` owns reaction identity, stoichiometric participants, conditions, reaction classes, optional net-ionic representation and phenomenon references.
- `phenomena.jsonl`, `experiments.jsonl` and `concepts.jsonl` are separate entities referenced by stable IDs.

A reaction is never collapsed into a direct `Substance → Substance` edge.

## Provenance

Every record contains `sources`. The initial v0.1 records are original editorial curation under `src:editorial-hs-inorganic-v1`; curriculum alignment uses the Ministry of Education source where appropriate.

External chemistry databases are registered as verification/enrichment targets. A source key in `verification_targets` does **not** mean the current record was copied from that database. Field-level external IDs and imported values should only be published after the exact source record and its redistribution terms are captured.

## Copyright / licensing guardrails

- Do not copy textbook or curriculum prose into this repository. Only factual scope tags and independently written short descriptions are stored.
- ChEBI is preferred for reusable nomenclature/ontology data because it publishes data under CC BY 4.0.
- PubChem aggregates many contributors. Use PUG REST for machine access, but retain contributor provenance and check the license of the exact upstream field before redistribution when the value is contributor-supplied.
- NIST Chemistry WebBook is a calibration/reference source; retain NIST citation and source-specific terms for imported fields.
- Periodic Table PRO is reference-only until its root data/content license is clearly established.

## Review states

Current allowed states:

- `seed`: collected but not reviewed;
- `reviewed`: chemistry and representation reviewed for the current dataset;
- `published`: externally verified and release-approved.

v0.1 uses `reviewed` for the curated core. Later ETL should not silently upgrade a record to `published`.

## Data representation

- Formula strings are machine-readable ASCII chemistry notation; UI typography (subscripts/superscripts) is a renderer concern.
- Ionic charge is an integer field, not embedded as presentation markup.
- Reaction phases are participant-level because phase depends on reaction context.
- Substance `ions` represents the intended high-school aqueous dissociation projection when it is unambiguous; weak electrolytes and insoluble species are not forcibly split.
