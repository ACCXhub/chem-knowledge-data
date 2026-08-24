# Structure track contract

`packages/structure/` is the canonical owner of chemistry structure records in this repository.

## Write ownership

The active Structure workstream owns and may modify:

- `packages/structure/**`

Other workstreams may read and reference published structure IDs, but should not edit, duplicate, or locally patch structure records. Cross-track corrections should be recorded in the caller's own package and reconciled during consolidation.

## What this track owns

- canonical/isomeric SMILES when chemically meaningful
- Standard InChI and InChIKey when available
- structure scope and formal charge
- normalization/validation metadata
- reproducible 2D/3D structure derivation metadata
- structure descriptors that are deterministically derived from a structure
- external structure identifiers and field-level provenance
- candidate `Substance ↔ Structure` links

## What this track does not own

- inorganic/organic curriculum taxonomy
- canonical Substance names or teaching classification
- Reaction, Experiment, Phenomenon, Concept, Question, ExamTag data
- source-specific raw payloads as canonical structure fields

## Public cross-track seam

Other tracks should treat the following as the stable read surface:

- `structure_id`
- `structure_scope`
- `molecular_formula`
- `formal_charge`
- canonical/isomeric SMILES when present
- Standard InChI/InChIKey when present
- validation/review status
- source identifiers/provenance

A caller may store a `structure_id` reference. It should not copy the complete structure record into its own package.

## Identity rule

`structure_id` is dataset-owned and source-neutral. External IDs such as PubChem CID or ChEBI ID are references, never canonical IDs.

For records with a valid Standard InChI, ingestion should derive a deterministic UUIDv5 from a repository namespace plus the Standard InChI. For structures without Standard InChI, the identity key must include structure scope, normalized representation and formal charge. The exact generator is owned by this package and must remain deterministic.

## Representation rule

A chemical formula is not automatically a molecular structure. The schema distinguishes:

- `molecule`
- `ion`
- `formula_unit`
- `coordination_entity`
- `crystal`
- `other`

SMILES/InChI fields are optional because ionic solids, formula units and some extended/crystalline structures cannot be faithfully represented as a discrete molecule.

## Source and normalization policy

Preferred evidence sources include PubChem and ChEBI where their records are applicable. RDKit may normalize, validate and derive reproducible descriptors, but RDKit objects and toolkit-internal serialization are not canonical data.

Source records must retain provenance sufficient to identify the external record, retrieval context and the canonical fields supported by that evidence.

## Parallel-work rule

Inorganic and Organic workstreams may propose structure links from their own packages. Structure owns the final structure record and final link acceptance. This prevents three parallel workstreams from creating competing canonical structure representations.
