# Consolidated status

Status: **ACTIVE / CONTRACT-READY / WAITING_FOR_INORGANIC**

Owner: `chatgpt-web-consolidation`

## Current state

- Organic v0.1 is a completed read-only input.
- Structure is a published read-only input; published `structure_id` values remain canonical.
- Inorganic is still active and is consumed only through stable public boundaries until it reports `READY_FOR_CONSOLIDATION`.
- Consolidation owns only `packages/consolidated/**` plus its coordination claim.

## Ready now

- source ownership and immutability contract;
- cross-package identity policy;
- species / Structure separation;
- provenance merge policy;
- high-school teaching taxonomy projection;
- search projection;
- Equation Lab / Reaction Builder consumer requirements;
- duplicate-resolution and release gates.

## Active consolidation work

1. Freeze consumer-facing schema contracts that can be defined without final inorganic coverage.
2. Build source-ID crosswalk and Structure-link rules against completed Organic + published Structure inputs.
3. Keep unresolved mappings explicit rather than merging by formula/name guesswork.
4. When Inorganic becomes ready, ingest its released boundary, resolve duplicates, generate the first complete consumer release, and run release validation.

## Publish gate

No consolidated release is `PUBLISHED` until all release gates in `CONTRACT.md` pass, including `READY_FOR_CONSOLIDATION` from Inorganic.
