# Organic package status

**Status:** ACTIVE

**Current owner:** `chatgpt-web-organic`

**Write scope:** `packages/organic/**`

## Current phase

Build the first high-school organic chemistry data package independently, then consolidate it later with the inorganic and structure packages.

Current seed coverage:

- 44 representative organic substances across core, extended and polymer seed files;
- 9 functional-group records plus 2 structural-feature records;
- 22 organic chemical-class / teaching taxonomy nodes;
- 24 reaction records forming an initial hydrocarbon → derivative → biomolecule/polymer conversion network;
- 23 concept / teaching-relation records;
- 8 experiment phenomena;
- 13 experiment catalog records;
- 12 source-crosschecked external identity links;
- package-local JSON Schemas and a reference/provenance validator, including polymer files and identity crossrefs.

## Boundaries kept during parallel work

- canonical structure patterns, SMILES/InChI, conformers and structure-derived descriptors belong to `packages/structure/**`;
- inorganic reactants/products are represented only as temporary `external_species_key` values and are not redefined here;
- reaction records do not infer atom mapping, bond diff or mechanism;
- proteins, oils/fats and nucleic acids may be represented as teaching/class nodes instead of inventing a fake single molecular formula;
- duplicate molecular formulae are allowed because formula is not chemical identity.

## Next organic work

1. continue ChEBI/PubChem identity cross-checks for representative substances;
2. expand lipids, amino acids/proteins and remaining biomolecule relations without collapsing classes into fake single compounds;
3. complete remaining curriculum reaction/phenomenon links and representative condensation-polymerization relations;
4. run the package validator after checkout and repair any schema/reference findings;
5. promote records from `seed` only after named-source cross-checks.

Other concurrent sessions should treat this package as read-only while the claim is active.
