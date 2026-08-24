# Consolidated chemistry knowledge package

`packages/consolidated/` is the consumer-ready integration layer for `chem-wiki`.

It does not replace or rewrite the three source packages. It reads their released/stable boundaries and converges cross-package identity, provenance, teaching projection, search projection, and release mapping here.

## Inputs

- `packages/inorganic/` — read-only until `READY_FOR_CONSOLIDATION`
- `packages/organic/` — completed v0.1 read-only input
- `packages/structure/` — published canonical structure input; published `structure_id` values remain authoritative

## Ownership

Current owner: `chatgpt-web-consolidation`.

The active write claim is `coordination/claims/consolidation.yaml`.

Source-package files remain owned by their package workstreams. Consolidation fixes cross-package inconsistencies through mappings and release projections rather than silently editing source data.

## Canonical responsibilities

This package owns:

- consolidated species identity and source-ID crosswalks;
- organic/inorganic duplicate resolution;
- links from species to published Structure records;
- provenance aggregation without erasing source provenance;
- high-school teaching categories and filter tags;
- search/index projection for Chinese name, formula, aliases, English names, and stable external IDs;
- Equation Lab / Reaction Builder consumer projections such as default palette priority and equation-mode suitability;
- consumer-ready release manifests and validation results.

Runtime user preferences such as pinned items, manual ordering, hidden items, recent usage, and usage frequency are application data and are not stored here.

## Release principle

Source records remain traceable. A consolidated record never overwrites its origin IDs; every merged entity keeps an explicit crosswalk back to package-local IDs and provenance.

The first consolidated release is produced only after the inorganic package reaches `READY_FOR_CONSOLIDATION` and the integration validation gates in `CONTRACT.md` pass.
