# Structure package status

**Status:** VERIFIED_FOUNDATION_V1 — awaiting merge to main

**Owner:** Structure canonical owner

**Write scope:** `packages/structure/**`

**Release:** `structure-foundation-1.0.0`

**Verified:** 2026-08-25

## Completion definition met on working branch

The Structure foundation is complete against the stable source-package inputs available now:

- Organic v0.1: **50/50** entities explicitly accounted for by accepted full-identity links or explicit deferrals;
- current Inorganic ion seed: **23/23** ions linked;
- **87** canonical Structure records: 46 molecules, 24 ions, 12 formula units and 5 polymer repeat units;
- canonical data are reproducibly generated from pinned evidence;
- formula units, ions, molecules and polymer repeat units have distinct semantics;
- unresolved stereochemical/polymer/macromolecular identities are explicit deferrals rather than guessed structures;
- downstream workstreams have stable accepted-link and deferral seams.

## Fresh verification

GitHub Actions run `32809697660` succeeded:

```text
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50
Ran 16 tests
OK
```

The workflow-generated release data are committed on `structure-foundation-v1` as `a0c2b4d`.

## Evidence-bound future additions

These are additive future releases, not missing foundation records:

- Inorganic Substance structures that are not yet emitted as stable requests by the active Inorganic workstream;
- coordination entities without explicit metal–ligand connectivity evidence;
- crystal records without crystallographic evidence/requests;
- full polymer molecular identities where chain length/end groups/tacticity are unspecified;
- generic fructose/alanine stereochemical identities until the teaching/source identity is disambiguated.

After merge and a main-tree manifest check, this status becomes `COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED`. Other workstreams continue to treat `packages/structure/**` as read-only.
