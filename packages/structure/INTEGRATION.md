# Cross-track integration for Inorganic and Organic

This file is the read-first contract for the two parallel chemistry-data workstreams.

## You may

- read `data/manifest.json`;
- read records with `validation.review_status == "published"`;
- store their `structure_id` in your own package;
- keep your own conventional formula, Chinese name, curriculum taxonomy and teaching metadata;
- create a structure request **inside your own package** when a needed structure is missing.

## You may not

- modify any file under `packages/structure/**`;
- copy a complete Structure record and treat the copy as canonical;
- create a competing `structure_id`;
- equate a display formula string with Structure's Hill/no-charge comparison formula;
- turn a salt/formula unit into a molecule just to obtain a SMILES.

## Missing structure request

Use `schema/structure-request.schema.json` as the request shape, but store the request under your own owner path, for example:

- `packages/inorganic/structure_requests/...`
- `packages/organic/structure_requests/...`

Structure later resolves it to a published `structure_id`.

## Stable identity

Use `structure_id` as the only dataset-owned structure identity. PubChem CID, ChEBI ID, COD number, SMILES and InChI are evidence/representations, not a replacement for `structure_id`.

## Current publication

See `data/manifest.json` for exact counts and file hashes. Only records marked `published + valid` are stable references.
