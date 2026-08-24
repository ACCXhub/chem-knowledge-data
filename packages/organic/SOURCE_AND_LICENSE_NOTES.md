# Source and licensing notes

The organic package combines independently curated high-school teaching relations with source-crosschecked factual identifiers. Every record keeps `provenance_refs`; source metadata lives in `sources/registry.yaml`.

## Current source roles

- **中华人民共和国教育部**: curriculum and experiment/activity scope. These documents define what the package should cover; they are not treated as a bulk source of canonical molecular records.
- **ChEBI (EMBL-EBI)**: chemical identity, terminology and ontology reference where applicable. ChEBI data used here is attributed through the registry and its CC BY 4.0 source license must be respected.
- **PubChem (NCBI/NLM/NIH)**: objective identity/formula/name cross-checks and external CIDs. PubChem aggregates contributor data, so provenance is kept at the record/cross-reference level rather than assuming one blanket upstream license for every possible PubChem field.
- **IUPAC Gold Book**: terminology cross-check only. Long-form definitions are not copied into this package.
- **manual-seed-2026-08**: project-authored curation used to connect curriculum concepts, representative substances, reactions and experiments before full external review.

## Publication rule

The repository does not treat the presence of a source URL as permission to copy arbitrary prose or assets. Canonical factual fields and project-authored relations are stored separately from source text. Before a future public data release is assigned one blanket license, consolidation should verify that every redistributed field is compatible with that release license.
