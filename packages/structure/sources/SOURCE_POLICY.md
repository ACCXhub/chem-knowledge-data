# Structure source policy

## Authority roles

Structure records are source-neutral. External databases provide evidence; they do not define dataset IDs.

1. **PubChem** — broad compound structure identifiers and CID evidence.
2. **ChEBI** — curated entity structure evidence/cross-check.
3. **Crystallography Open Database (COD)** — crystal-scope evidence only.
4. **IUPAC/InChI standard** — identifier standard; Standard InChI uses `InChI=1S/`.
5. **RDKit** — normalization, validation and deterministic derivation only; not an authority source.
6. **Organic/Inorganic source packages** — read-only cross-track identity/coverage demand; never competing Structure owners.

## Conflict policy

- Material disagreement becomes `needs_review` or explicit deferral.
- No source silently overwrites another.
- Source-specific payload shapes and prose stay outside canonical records.
- Keep factual canonical fields minimal and retain source locator/retrieval context.

## Formula policy

`molecular_formula` is a machine-comparison formula:

- Hill ordering;
- formal charge omitted from formula and stored separately;
- dummy attachment atoms omitted;
- user-facing conventional formula formatting remains with Organic/Inorganic presentation data.

Cross-track formula comparison therefore uses composition, not raw string equality.

## Scope policy

- `molecule`: discrete neutral molecular entity.
- `ion`: discrete charged entity.
- `formula_unit`: stoichiometric unit for ionic/salt representation; disconnected source SMILES is not published as molecular canonical SMILES.
- `polymer_repeat_unit`: teaching/topological repeat unit with exactly two attachment points; not a complete polymer molecule.
- `coordination_entity`: explicit metal-ligand connectivity backed by evidence.
- `crystal`: crystallographic record backed by crystallographic evidence.
- `other`: exceptional reviewed scope.

## Polymer policy

A polymer repeat unit may be published when the teaching identity and repeat connectivity are clear. Full polymer identity remains deferred unless chain length, terminal groups and relevant stereochemical/tacticity state are fixed. Repeat units intentionally do not receive Standard InChI/InChIKey.
