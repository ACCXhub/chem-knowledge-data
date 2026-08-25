# Organic package status

**Status:** COMPLETE_V0_2

**Review owner:** `chatgpt-web-organic`

**Package:** `packages/organic/**`

**Reviewed:** 2026-08-25

## Scope and counts

v0.2 is the reviewed pre-consolidation high-school organic chemistry package.

- **57** representative Substance records;
- **10** FunctionalGroup records plus **2** StructuralFeature records;
- **25** chemical-class / teaching-taxonomy nodes;
- **31** Reaction records;
- **52** Concept / teaching-relation records;
- **16** Phenomenon records;
- **14** Experiment records;
- **48** source-crosschecked external identity links;
- **9** explicit identity deferrals;
- curriculum evidence for **30 topics, 16 families, 8 reaction classes and 14 experiment/activity groups**.

All 57 Substance records have either a source-crosschecked external identity or an explicit deferral for structure/consolidation policy.

## Integrity review results

The v0.2 review corrected or strengthened three layers.

### Completeness

- expanded isomerism into chain, position, functional-class and geometric-isomerism evidence;
- added representative 1-butene / cis-2-butene / trans-2-butene and methyl formate identities;
- made mass spectrometry, infrared spectroscopy, proton NMR and multi-evidence structure determination explicit;
- added organic synthesis-route reasoning;
- added ethanol / phenol / carboxylic-acid property comparison with representative equations;
- represented both acid and alkaline hydrolysis of ethyl acetate as distinct reaction records;
- made amino-acid amphoteric character, peptide/protein hydrolysis and protein-property coverage explicit;
- strengthened polymer chain architecture, thermoplastic/thermosetting and material-family concepts.

### Correctness

- corrected the aldehyde + freshly prepared Cu(OH)2 observation to brick-red **Cu2O** and renamed its phenomenon identity accordingly;
- centralized PubChem/ChEBI identity ownership in `data/identity_crossrefs.yaml`;
- retained distinct entities for shared molecular formulae;
- added element-symbol and molecular-formula syntax validation;
- atom-balanced every ordinary `balanced_seed` reaction that has non-symbolic stoichiometry;
- kept symbolic polymer equations as explicit symbolic cases rather than pretending they are ordinary fixed-coefficient equations.

### Data structure

- tightened ReactionParticipant to one chemical-species owner: local `substance_ref` or external `external_species_key`;
- added schemas for structural features, source registry, curriculum coverage, coverage evidence and package manifest;
- added external-ID uniqueness checks and `source_crosschecked -> identity_crossrefs` consistency;
- package manifest counts are checked against actual dataset contents;
- local references, provenance references and curriculum evidence references are validated as a single package graph;
- Reaction / Experiment / Phenomenon links are checked for reciprocal consistency.

## Validation

The v0.2 validation gate runs on Python 3.13 and includes:

- JSON Schema validation for records and package metadata;
- duplicate-ID and external-ID ownership checks;
- provenance and local-reference integrity;
- chemical-formula syntax and element-symbol validation;
- atom conservation for ordinary balanced equations (**22** checked; **6** symbolic polymer/macromolecule equations handled separately);
- curriculum coverage evidence completeness;
- identity crossref-or-deferral completeness;
- package-manifest count reconciliation;
- reciprocal Reaction / Experiment / Phenomenon graph validation.

Expected shared-formula warnings are retained for chemically distinct identities, including butane isomers, butene stereoisomers, acetic acid / methyl formate, glucose / fructose and starch / cellulose.

## Consolidation boundary

Canonical SMILES, InChI/InChIKey, SMARTS, conformers, canonical stereochemistry and structure-derived descriptors remain owned by `packages/structure/**`. Inorganic participants remain cross-package keys until consolidation assigns canonical IDs. Atom mapping, bond diff and mechanism data are separate future layers rather than deductions from equations.

The **9 identity deferrals are deliberate typed handoffs**, principally for polymer identity, generic stereochemical names and other cases where a one-line external compound ID would lose chemical meaning.

## Next phase

Keep the organic package read-only after merge. Consolidation may consume it to align cross-package IDs and Structure links; new organic scope should enter a later version rather than mutate v0.2 in place.
