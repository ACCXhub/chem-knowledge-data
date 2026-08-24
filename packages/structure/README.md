# Structure package

Owner: **Structure workstream (ACTIVE / LOCKED)**. Other workstreams may read and reference this package, but structure canonical records, schemas, provenance, derived descriptors, conformers and Substance↔Structure links are owned here.

## Scope

This package owns chemical **structure representation**, not inorganic/organic classification or reaction knowledge.

- Standard InChI / InChIKey when chemically applicable
- toolkit-qualified canonical/isomeric SMILES
- structure kind and representation scope
- validation and normalization evidence
- 2D/3D reproducible derived artifacts
- basic structure descriptors
- candidate/approved Substance ↔ Structure links
- source and generator provenance

It does not redefine `Substance`, inorganic/organic taxonomy, `Reaction`, `Experiment`, `Phenomenon`, `Concept`, or semantic functional-group knowledge.

## Identity rules

1. `structure_id` is an internal stable UUID-based identifier and does not depend on SMILES, PubChem CID, ChEBI ID or another external identifier.
2. Standard InChI/InChIKey are the preferred interoperable molecular-structure identifiers when applicable. Standard InChI is structure-based and standardized for database interoperability.
3. SMILES canonicalization is toolkit-specific. Every canonical/isomeric SMILES value must record the generator and generator version; it is never treated as a universal cross-tool primary key.
4. Ionic lattices, network solids and other non-discrete structures are represented with an explicit `structure_kind`; they are not forced into fake discrete-molecule SMILES/InChI records.
5. Experimental solid-state/crystal structure evidence and computed 3D conformers are separate evidence classes.

## Package layout

- `schema/` — package-local record contracts
- `data/canonical/` — reviewed canonical structure records
- `data/substance_links/` — cross-package Substance ↔ Structure links
- `data/derived/` — reproducible descriptors/depictions
- `data/conformers/` — generated 3D conformers with method metadata
- `sources/` — source/generator registry and acquisition metadata
- `pipelines/` — structure-only extraction/normalization logic
- `validation/` — package-local quality rules

## Cross-package contract

A/B own their Substance records. This package may reference their stable `substance_id`; it does not edit those entities. A/B may reference `structure_id`; they do not patch structure records directly. Cross-package disputes are recorded for later consolidation instead of being fixed inside a sibling package.
