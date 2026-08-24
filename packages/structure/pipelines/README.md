# Structure pipelines

The pipeline boundary is deliberately source-neutral.

- `ids.py` owns deterministic dataset IDs.
- `fetch_pubchem.py` is an optional evidence fetcher; it never writes canonical data.
- `normalize_rdkit.py` parses/sanitizes a discrete structure, emits Standard InChI/InChIKey, canonical/isomeric SMILES, Hill/no-charge formula, formal charge and deterministic descriptors.
- `build_seed.py` rebuilds the checked-in seed dataset from pinned PubChem evidence.

## Rebuild

```bash
python packages/structure/pipelines/build_seed.py
python packages/structure/validation/validate_dataset.py --strict
```

A network connection is not required to rebuild the checked-in seeds because their minimal evidence is pinned in `sources/pubchem_seed_evidence.jsonl`.

Do not auto-publish freshly fetched data. New evidence enters `draft`/review first; only reviewed records become cross-track references.
