# Inorganic data policy

## Scope

This package curates machine-readable high-school inorganic/general chemistry knowledge for application consumption. The v1 chain is:

`Element teaching projection → Ion / polyatomic group → Substance → Reaction → Phenomenon / Experiment → Concept → ExamTag`

It also publishes derived teaching rule projections for Equation Lab, ionic-equation handling, solubility, common oxidation states, metal activity, flame tests and qualitative analysis.

`Organic`, `Structure`, `FunctionalGroup`, `Mechanism`, atom mapping, bond diff and synthesis planning remain owned elsewhere.

## Canonical ownership

- `element_scope*.jsonl` stores curriculum-facing priority/coverage metadata keyed by symbol and atomic number. It is not a second periodic-table truth source.
- `ions*.jsonl` owns common monatomic/polyatomic ion identities used by the high-school inorganic layer.
- `substances*.jsonl` owns canonical inorganic species records and optional aqueous dissociation projections.
- `reactions*.jsonl` owns reaction identity, stoichiometric participants, conditions, reaction classes, optional net-ionic representation and phenomenon references.
- `phenomena*.jsonl`, `experiments*.jsonl`, `concepts*.jsonl` and `exam_tags*.jsonl` are separate stable entities referenced by ID.
- `rules/*.json` are deterministic consumer projections over canonical identities. They are not a second source of chemical species or reactions.

A reaction is never collapsed into a direct `Substance → Substance` canonical reaction edge.

## Provenance

Every canonical record contains `sources`. The v1 seed uses original editorial curation under `src:editorial-hs-inorganic-v1`; curriculum alignment uses the Ministry of Education source where appropriate.

External chemistry databases are registered as verification/enrichment targets. A source key in `verification_targets` does **not** mean the current record was copied from that database. Field-level external IDs and imported values should only be published after the exact source record and its redistribution terms are captured.

`READY_FOR_CONSOLIDATION` is a package workflow state. It does not change record-level `review_status=reviewed` into `published`.

## Copyright / licensing guardrails

- Do not copy textbook, curriculum, website or teaching-resource prose into this repository. Store factual scope tags and independently written short descriptions.
- ChEBI is preferred for reusable nomenclature/ontology enrichment because its data is registered here as CC BY 4.0.
- PubChem aggregates many contributors. PUG REST may be used for machine access, but contributor provenance and the license of an exact upstream field must be retained when redistributing contributor-supplied annotations.
- NIST Chemistry WebBook is a calibration/reference source. Numerical enrichment must retain units, conditions, citation and source-specific terms.
- Periodic Table PRO remains reference-only until its root data/content license is clearly established.
- Hazardous experiment records describe curriculum context, observation and safety classification; the dataset does not publish independent dangerous operating recipes.

See `sources/SOURCE_REVIEW.md` for the v1 release review.

## Review states

Canonical record states:

- `seed`: collected but not reviewed;
- `reviewed`: chemistry and representation reviewed for the current dataset;
- `published`: externally verified and release-approved at field/source level.

v1 canonical records are predominantly `reviewed`. Later ETL must preserve provenance history and must not silently upgrade a record to `published`.

## Data representation

- Formula strings are machine-readable ASCII chemistry notation; UI typography (subscripts/superscripts) is a renderer concern.
- Ionic charge is an integer field, not embedded as presentation markup.
- Reaction phase is participant-level because phase depends on reaction context.
- Substance `ions` represents the intended high-school aqueous dissociation projection when composition is unambiguous; it does not imply that solid material contains free solvated ions.
- Weak electrolytes and insoluble species are not forcibly split in ionic-equation projection.
- Variable-valence elements must return canonical candidates instead of a guessed oxidation state.
- Numerical thermodynamic/equilibrium/electrochemical values require explicit conditions and field-level provenance before canonical publication.

## Curriculum and exam metadata

- `curriculum/coverage.json` is a scope audit, not a copied curriculum document.
- `exam_tag` is stable teaching/search metadata.
- Dynamic exam frequency, historical ExamHeat and any probability-like ranking belong to separately evidenced data and must not be fabricated from these tags.

## Release validation

A v1 release is valid only when `validation/validate_v1.py` succeeds against the committed tree. Validation covers identity uniqueness, provenance keys, reference integrity, ionic projection neutrality/composition, molecular and net-ionic conservation, rule references, curriculum references and manifest counts.
