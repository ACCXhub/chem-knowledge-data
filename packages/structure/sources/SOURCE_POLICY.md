# Structure source policy

## Authority roles

Structure records are source-neutral. External databases provide evidence; they do not define the dataset ID.

1. **PubChem** — broad compound-level structure evidence and PubChem CID.
2. **ChEBI** — curated chemical-entity structure evidence and cross-checking where applicable.
3. **Crystallography Open Database (COD)** — crystal-scope evidence. Molecular SMILES is never used as a substitute for a crystal record.
4. **IUPAC/InChI standard** — identifier standard. A Standard InChI in canonical data must begin with `InChI=1S/`.
5. **RDKit** — normalization, validation and deterministic derivation only; never an authority source.

## Conflict policy

- Exact agreement is preferred where two independent evidence sources cover the same field.
- A material disagreement is retained as an issue and moves the record to `needs_review`; no source silently overwrites another.
- Source-specific response shapes and prose stay outside canonical records.
- Retrieval time, record locator and supported canonical fields are recorded per evidence item.
- Source URLs are locators, not proof that every field on a page may be redistributed. Keep canonical data factual and minimal.

## Formula policy

`molecular_formula` in Structure is a **machine comparison formula**, not the curriculum-facing display formula.

- Convention: Hill ordering with charge omitted (`hill_no_charge`).
- Formal charge is stored separately.
- Inorganic and Organic tracks own conventional/user-facing formula formatting such as `Na2SO4`, `Ca(OH)2`, or condensed organic formulas.
- Formula comparison must therefore use element counts, not string equality against another track's display formula.

## Structure-scope policy

A formula is not automatically a molecule.

- `molecule`: discrete neutral covalent molecular entity.
- `ion`: discrete charged entity.
- `formula_unit`: stoichiometric unit of an ionic/network solid or salt representation.
- `coordination_entity`: metal-ligand connectivity explicitly supported by evidence.
- `crystal`: crystallographic structure with appropriate crystal evidence.
- `other`: exceptional cases that do not fit the above; requires review notes.

Disconnected salt SMILES from a source may be retained as evidence, but formula-unit records do not become molecular records merely because a SMILES exists.
