# Structure validation standard

A canonical structure record is publishable only when checks applicable to its `structure_scope` pass.

## Required checks

1. JSON Schema validation against `schema/structure-record.schema.json`.
2. Source-neutral deterministic `structure_id`.
3. Formula/charge consistency where a machine structure representation exists.
4. SMILES parse/sanitization when SMILES is present.
5. Standard InChI must use `InChI=1S/`; stored InChIKey must be derivable from it.
6. SMILES and Standard InChI must describe the same normalized discrete entity when both are present.
7. Cross-source disagreements become `needs_review`; they never silently overwrite.
8. RDKit-derived fields retain toolkit/version when persisted.
9. Duplicate canonical IDs, duplicate InChI identities and conflicting external IDs fail validation.
10. A formula-unit salt is not published as a molecule merely because a disconnected salt SMILES exists.
11. Manifest record counts and canonical file SHA-256 values must match the checked-in release.

## Scope rules

- **molecule / ion**: at least one machine-usable discrete representation is required.
- **formula_unit**: formula + charge are canonical; Standard InChI may identify a disconnected stoichiometric representation, but canonical molecular SMILES remains absent in the seed release.
- **coordination_entity**: connectivity/charge need explicit supporting evidence.
- **crystal**: requires crystallographic evidence; molecular SMILES is not a crystal representation.
- **other**: requires review notes.

## Command

```bash
python packages/structure/validation/validate_dataset.py --strict
```

Install `validation/requirements.txt` first if the environment does not already contain RDKit/jsonschema.

Only `published + valid` records are stable for other workstreams.
