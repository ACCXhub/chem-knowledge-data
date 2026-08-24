# Structure validation rules

These are package-local publish gates for `packages/structure/`.

## Identity and representations

1. `structure_id` is stable and internal; external database identifiers never replace it.
2. A stored Standard InChI must begin with `InChI=1S/` and include the generating software version.
3. Standard InChIKey must match the 27-character standard form.
4. Canonical/isomeric SMILES must record generator and generator version. A bare SMILES string is insufficient for a published structure record.
5. Equivalent formula alone never proves equivalent structure.

## Structure kind

- `discrete_molecule` / `molecular_ion`: molecular representations are appropriate when source evidence supports a discrete entity.
- `ionic_lattice` / `network_solid`: publish solid-state/crystal evidence separately; do not fabricate a discrete molecular structure only to obtain SMILES/InChI.
- `coordination_entity`: preserve source representation and validation notes; metal-bond conventions can differ between identifier systems.
- `unknown`: provisional only; cannot reach `published` until structure kind is resolved.

## Chemistry consistency

For applicable molecular records, validation should cover:

- parser/sanitization success;
- formal valence plausibility;
- molecular formula consistency across source and generated representation;
- total formal charge consistency;
- stereochemistry/isotope preservation when those layers are claimed.

A validation failure remains evidence; it is not silently normalized away.

## 2D / 3D derived data

- 2D depictions are reproducible derived artifacts, not chemical identity.
- Computed 3D conformers record toolkit/version, method, random seed where applicable, force field and optimization status.
- Computed conformers are never labelled as experimental geometry.
- Experimental crystal coordinates retain source ID, source locator and content hash; they are separate from computed conformers.

## Cross-package links

- `substance_ref` belongs to inorganic/organic owners.
- Structure only publishes/validates the link record and its structure side.
- A sibling package may reference a published `structure_id` but does not modify the underlying structure record.
- Ambiguous Substance↔Structure mapping stays `candidate`/`provisional` until consolidation or review.

## Provenance gate

A publishable record has at least one traceable source assertion with source locator and retrieval time. Curated/authoritative evidence is preferred over aggregated or computed evidence when resolving conflicting structure assertions.
