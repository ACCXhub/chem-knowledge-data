# Inorganic data policy

## Scope

This package curates machine-readable high-school inorganic/general chemistry knowledge for application consumption. The v1 chain is:

`Element teaching projection → Ion / polyatomic group → Substance → Reaction → Phenomenon / Experiment → Concept → ExamTag`

It also publishes derived teaching rule projections for Equation Lab, ionic-equation handling, solubility, common oxidation states, metal activity, flame tests and qualitative analysis.

`Organic`, `Structure`, `FunctionalGroup`, `Mechanism`, atom mapping, bond diff and synthesis planning remain owned elsewhere.

## Canonical ownership

- `element_scope*.jsonl` stores curriculum-facing priority/coverage metadata keyed by symbol and atomic number. It is not a second periodic-table truth source.
- `ions*.jsonl` owns common monatomic/polyatomic ion identities used by the high-school inorganic layer.
- `substances*.jsonl` owns canonical inorganic species records and optional ionic-composition metadata.
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
- Substance `ions` is teaching-level ionic-composition metadata: it records canonical ion units and integer stoichiometry where that representation is useful. It does **not** itself assert an aqueous dissociation result and does not imply free solvated ions in a solid.
- Ionic-equation splitting must combine participant phase, `aqueous_behavior`, `rules/electrolytes.json`, `rules/solubility.json`, and any reaction-specific acid/base equilibrium context.
- Weak electrolytes, insoluble species and condition-dependent acid-equilibrium species are not forcibly split merely because ionic-composition metadata exists.
- Variable-valence elements must return canonical candidates instead of a guessed oxidation state.
- Numerical thermodynamic/equilibrium/electrochemical values require explicit conditions and field-level provenance before canonical publication.

## Curriculum and exam metadata

- `curriculum/coverage.json` is a scope audit, not a copied curriculum document.
- `exam_tag` is stable teaching/search metadata.
- Dynamic exam frequency, historical ExamHeat and any probability-like ranking belong to separately evidenced data and must not be fabricated from these tags.

## Release validation

v1.0.1 is release-ready only when the committed tree passes the repository validation workflow. The release gate combines:

- canonical validator and exact manifest counts;
- JSON Schema conformance for every canonical record;
- independent formula/composition, charge, conservation and reference audits;
- solubility-rule consistency;
- reaction taxonomy semantics;
- identity / alias / search collision checks;
- curriculum connectivity checks;
- diagnostic PubChem cross-checks whose ambiguous name-resolution results are reported for review rather than automatically written back.
