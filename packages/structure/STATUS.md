# Structure package status

**Status:** COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED

**Owner:** Structure canonical owner

**Write scope:** `packages/structure/**`

**Release:** `structure-foundation-1.0.0`

**Published:** 2026-08-25

## Completion definition met

The Structure foundation is complete against the stable source-package inputs available now:

- Organic v0.1: **50/50** entities explicitly accounted for by accepted full-identity links or explicit deferrals;
- current Inorganic ion seed: **23/23** ions linked;
- **87** canonical Structure records: 46 molecules, 24 ions, 12 formula units and 5 polymer repeat units;
- canonical data are reproducibly generated from pinned evidence;
- formula units, ions, molecules and polymer repeat units have distinct semantics;
- unresolved stereochemical/polymer/macromolecular identities are explicit deferrals rather than guessed structures;
- downstream workstreams have stable accepted-link and deferral seams.

## Fresh verification

Working-branch GitHub Actions run `32809697660` succeeded, and pull-request run `32809798607` independently rebuilt the release and passed the no-diff reproducibility gate before merge.

```text
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50
Ran 16 tests
OK
```

PR #3 was squash-merged to `main` as `db02499d04475b3f710e7399b4e0a3dbaeea198e`. The canonical `main` manifest was re-read after merge and confirms dataset version `structure-foundation-1.0.0`, schema `1.2.0`, total `87`, Inorganic links `23`, Organic links `46`, and Organic deferrals `9`.

## Evidence-bound future additions

These are additive future releases, not missing foundation records:

- Inorganic Substance structures that are not yet emitted as stable requests by the active Inorganic workstream;
- coordination entities without explicit metal–ligand connectivity evidence;
- crystal records without crystallographic evidence/requests;
- full polymer molecular identities where chain length/end groups/tacticity are unspecified;
- generic fructose/alanine stereochemical identities until the teaching/source identity is disambiguated.

Other workstreams must continue to treat `packages/structure/**` as read-only and consume published `structure_id` / link / deferral records through the documented integration seam.
