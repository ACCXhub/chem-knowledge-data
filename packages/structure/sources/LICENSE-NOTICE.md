# Structure data licensing and attribution notice

This package stores source-neutral factual structure records plus provenance.

- ChEBI material used as evidence is subject to **CC BY 4.0** attribution requirements.
- Crystallography Open Database data are distributed under **CC0**; original crystallographic authors should still be acknowledged in provenance.
- RDKit code/tooling is BSD-3-Clause licensed and is used only for reproducible derivation and validation.
- PubChem is used as a factual structure/identifier evidence source. Source prose, images, and depositor-specific expressive content are not copied into the canonical dataset.

Each canonical record carries field-level source provenance. When adding a source, update `sources/registry.json` and verify its current terms before importing redistributable content.
