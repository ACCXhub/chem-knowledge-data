# Structure track contract

`packages/structure/` is the canonical owner of chemistry structure records in this repository.

## Write ownership

The active Structure workstream owns and may modify:

- `packages/structure/**`

Other workstreams may read and reference published structure IDs, but must not edit, duplicate, or locally patch structure records. Cross-track corrections belong in the caller's own package as requests/notes and are reconciled by Structure.

## What this track owns

- source-neutral `structure_id`
- `structure_scope`
- canonical/isomeric SMILES when chemically meaningful
- Standard InChI and InChIKey when available
- machine comparison formula and formal charge
- normalization/validation metadata
- reproducible 2D/3D derivation metadata
- deterministic structure descriptors
- external structure identifiers and field-level provenance
- accepted `Substance ↔ Structure` links

## What this track does not own

- inorganic/organic curriculum taxonomy
- canonical Substance names
- curriculum-facing chemical-formula typography
- Reaction, Experiment, Phenomenon, Concept, Question, ExamTag data
- source-specific raw payloads as canonical fields

## Public cross-track seam

Other tracks may read:

- `structure_id`
- `structure_scope`
- `molecular_formula` (`hill_no_charge`, machine-comparison only)
- `formal_charge`
- canonical/isomeric SMILES when present
- Standard InChI/InChIKey when present
- validation/review status
- external IDs and provenance

A caller stores a `structure_id` reference. It must not copy the complete canonical structure record into its own package.

## Formula convention

Structure uses Hill ordering with charge removed. Charge is a separate integer.

Examples:

- ammonia: `H3N`, charge `0`
- ammonium: `H4N`, charge `+1`
- sulfate: `O4S`, charge `-2`

This is deliberately different from user-facing formula ownership. Inorganic/Organic may display `NH3`, `NH4+`, `SO4^2-`, `Na2SO4`, parentheses, hydration dots, and teaching notation as appropriate.

## Identity rule

Namespace UUID:

`c9d2c469-8557-5661-ae35-950cde95e61f`

For a valid Standard InChI:

`structure_id = "str_" + UUIDv5(namespace, "inchi:" + standard_inchi)`

For records without Standard InChI, Structure uses a deterministic scope-specific normalized identity key. The implementation in `pipelines/ids.py` is authoritative.

External IDs such as PubChem CID, ChEBI ID or COD number are references, never canonical IDs.

## Representation rule

A chemical formula is not automatically a molecular structure. The schema distinguishes:

- `molecule`
- `ion`
- `formula_unit`
- `coordination_entity`
- `crystal`
- `other`

SMILES/InChI fields are optional for non-discrete structures. A disconnected salt representation may support a formula-unit record, but must not be reclassified as a molecule.

## Source and normalization policy

See `sources/SOURCE_POLICY.md`.

Preferred evidence is PubChem/ChEBI for discrete chemical entities and COD for crystal structures. RDKit may normalize, validate and derive reproducible fields, but RDKit output is derived evidence rather than authority.

## Parallel-work rule

Inorganic and Organic workstreams may propose structure links **inside their own packages**. They must not create or modify files under `packages/structure/**`.

Structure owns final canonical structure records and accepted links. This prevents parallel workstreams from creating competing representations.
