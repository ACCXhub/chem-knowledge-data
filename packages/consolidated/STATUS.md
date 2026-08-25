# Consolidated status

**State:** `READY_FOR_APP_IMPORT`

**Release:** `consolidated-1.0.0`

**Owner:** `chatgpt-web-consolidation`

**Audited:** 2026-08-25

## Frozen inputs

- Inorganic v1.0.1 — `READY_FOR_CONSOLIDATION`, 642 canonical records.
- Organic v0.2.0 — 57 substances / 31 reactions and reviewed supporting knowledge.
- Structure Registry `structure-registry-foundation-1.0.1` — 87 published Structures and 69 accepted cross-track links.
- Structural Chemistry `structural-chemistry-v1.0.2` — 291 canonical records, `READY_FOR_CONSOLIDATION`.

`SOURCE_INPUTS.json` pins the release commits. The independent release audit also hashes every source file actually consumed from those commits, so a same-version content rewrite cannot enter the release silently.

## Release contents

- 309 consumer species;
- 309 source crosswalks;
- 69 accepted Structure links;
- 183 reactions;
- 309 teaching/search/Equation Lab projections;
- 637 non-species knowledge records;
- 13 informational findings;
- 0 review findings;
- 0 blocking findings.

## Audit closure

The first consumer release passed all release gates on GitHub Actions run `32856769997`.

Independent checks covered:

- 71 source files frozen against the declared source release commits;
- all 69 accepted Structure Registry links reconciled into the consumer release, including the reviewed historical `copper-2 / iron-2 / iron-3` source-ID rebound to current inorganic IDs;
- 174 ordinary reactions rechecked for mapped atom/charge conservation;
- 13 net-ionic equations independently rechecked for atom/charge conservation;
- 37 organic formula literals checked against mapped species composition;
- 194 rule references checked against published species/reaction/experiment/phenomenon IDs;
- complete Reaction → Concept / Experiment / Phenomenon references;
- complete 309-record teaching projection with contiguous Palette ranks and no runtime user preference data;
- manifest counts and SHA-256 hashes reconciled with generated files;
- a second full build/finalize/validate/audit cycle produced byte-for-byte zero diff.

Final validator result: **passed / 0 errors / 0 warnings / 0 blocking / 0 review**.

## Canonical consumer entry points

- `generated/manifest.json` — release identity, state, counts and file hashes;
- `generated/species.jsonl` — unified species catalog;
- `generated/crosswalk.jsonl` — source → consumer identity mapping;
- `generated/structure_links.jsonl` — accepted Structure associations;
- `generated/reactions.jsonl` — resolved reactions;
- `generated/teaching_projection.jsonl` — search/Palette/equation-mode projection;
- `generated/knowledge_records.jsonl` — non-species knowledge envelopes;
- `generated/rules/` and `generated/curriculum/` — reviewed rules and curriculum projections;
- `generated/unresolved_findings.jsonl` — explicit non-blocking integration findings;
- `generated/validation_report.json` — machine validation result.

## Next boundary

`consolidated-1.0.0` is now the stable application-import baseline. The four source packages remain read-only inputs for this release. Future source revisions enter through a new pinned source snapshot and a new consolidated release revision rather than mutating this published baseline in place.
