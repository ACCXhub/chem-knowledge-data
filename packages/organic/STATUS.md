# Organic package status

**Status:** COMPLETE_V0_1

**Owner during build:** `chatgpt-web-organic`

**Frozen write scope:** `packages/organic/**`

**Completed:** 2026-08-24

## v0.1 scope

This is the completed independent pre-consolidation high-school organic chemistry package. It is ready to be consumed or compared with the inorganic and structure packages before the later cross-package consolidation pass.

Validated coverage:

- **50** representative organic Substance records;
- **10** functional-group records plus **2** structural-feature records;
- **25** chemical-class / teaching taxonomy nodes;
- **27** Reaction records across hydrocarbons, derivatives, carbohydrates, lipids and polymers;
- **35** Concept / teaching-relation records;
- **14** Phenomenon records;
- **14** Experiment catalog records;
- **41** source-crosschecked external identity links;
- **9** explicit identity deferrals, so all 50 Substance records have either a checked external identity or a documented reason for later structure/consolidation resolution;
- curriculum evidence for **10 topics, 16 families, 7 reaction classes and 14 experiment/activity groups**.

## Validation evidence

GitHub Actions workflow **Validate organic package**, run `32715190827`, completed successfully on Python 3.13.

The gate passed:

- package-local JSON Schema checks;
- duplicate-ID checks;
- provenance reference checks;
- local entity reference integrity;
- curriculum coverage evidence completeness;
- external identity cross-reference integrity;
- identity crossref-or-deferral completeness.

Expected duplicate-formula warnings were retained for chemically distinct identities:

- `(C6H10O5)n`: starch / cellulose;
- `C4H10`: n-butane / isobutane;
- `C6H12O6`: glucose / fructose.

These are warnings by design because molecular formula is not chemical identity.

## Deliberate boundaries for consolidation

- canonical SMILES, InChI/InChIKey, SMARTS, conformers and structure-derived descriptors remain owned by `packages/structure/**`;
- inorganic participants remain temporary cross-package species keys and are not redefined here;
- no atom mapping, bond diff or reaction mechanism is inferred from reaction equations;
- proteins, nucleic acids and heterogeneous material classes are not assigned fake single fixed molecular formulae;
- polymer identities use the teaching-level monomer/repeat-unit relationship; terminal groups, tacticity and canonical polymer structure remain deferred where appropriate;
- stereochemical identity ambiguities such as generic `alanine`/`fructose` seeds are explicitly deferred rather than silently mapped to one stereoisomer.

## Next phase

No further organic-package expansion is required for v0.1. Keep this package read-only until the planned consolidation phase aligns IDs, structure links and cross-package species references with `packages/inorganic/**` and `packages/structure/**`.
