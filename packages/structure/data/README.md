# Structure data layout

- `canonical/structures.jsonl` — one `StructureRecord` per line; source-grounded, reviewed structure facts.
- `substance_links/links.jsonl` — Substance↔Structure links; Substance IDs are owned by sibling packages.
- `derived/descriptors.jsonl` — reproducible structure descriptors with generator/version metadata.
- `conformers/` — computed 3D conformers and metadata; keep computed geometry distinct from experimental structures.

The initial population will prioritize high-school-relevant substances already defined by inorganic/organic owners. Structure records can be created before links are published, but sibling substance records are never duplicated here.
