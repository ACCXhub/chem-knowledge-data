# Organic package validation

The organic package is validated as an independent pre-consolidation dataset.

Run from repository root:

```bash
python -m pip install -r packages/organic/validation/requirements.txt
python packages/organic/validation/validate_package.py
python packages/organic/validation/validate_identity_coverage.py
python packages/organic/validation/validate_manifest.py
```

The v0.2 gate checks:

- package-local record and metadata JSON Schemas;
- duplicate IDs and local-reference integrity;
- provenance source integrity;
- molecular-formula syntax and valid element symbols;
- atom conservation for ordinary non-symbolic `balanced_seed` reactions;
- unique PubChem/ChEBI identity ownership;
- `source_crosschecked` Substance-to-crossref consistency;
- crossref-or-explicit-deferral completeness for every Substance;
- curriculum requirement-to-evidence completeness;
- package-manifest counts against actual dataset contents.

Shared molecular formulae remain warnings because formula is not chemical identity. Symbolic polymer equations remain explicit symbolic cases and are reported separately from ordinary atom-balance checks. Canonical molecular structure validation belongs to `packages/structure/**`; cross-package inorganic species IDs are resolved during consolidation.
