# Structure validation standard

A canonical structure record is publishable only when the checks applicable to its `structure_scope` pass.

## Required checks

1. Schema validation against `structure-record.schema.json`.
2. Source-neutral identity: no external source ID is used as `structure_id`.
3. Formula/charge consistency where a discrete structure representation exists.
4. SMILES parse/sanitization check when SMILES is present.
5. Standard InChI/InChIKey consistency when both are present.
6. Cross-source comparison when both PubChem and ChEBI evidence exist; material disagreement becomes `needs_review` rather than silent overwrite.
7. Derivation metadata records toolkit and version for RDKit-produced fields.
8. A formula-only inorganic solid is not promoted to a discrete molecular structure merely because a SMILES-like representation can be constructed.

## Scope-specific policy

### molecule / ion

At least one machine-usable structural representation is required: canonical SMILES or Standard InChI. Formula and formal charge must agree with the normalized structure.

### formula_unit

Formula and formal charge may be canonical even when SMILES/InChI are absent. This is the expected path for many ionic solids where a discrete molecular representation would be misleading.

### coordination_entity

Connectivity and charge require explicit evidence. Ambiguous ligand/metal connectivity remains `needs_review`.

### crystal

Crystal records require an appropriate crystallographic source/representation; molecular SMILES is not a substitute.

## Cross-track publication guarantee

Other workstreams may safely reference a `structure_id` only after `validation.review_status == "published"`.
