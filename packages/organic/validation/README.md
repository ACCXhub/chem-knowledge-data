# Organic package validation

The organic package is validated as an independent pre-consolidation dataset.

Run from repository root:

```bash
python -m pip install -r packages/organic/validation/requirements.txt
python packages/organic/validation/validate_package.py
```

The validator checks package-local JSON Schemas, duplicate IDs, provenance references, local entity references, external identity cross-reference integrity, duplicate-formula warnings, and completeness of the curriculum coverage evidence map.

A shared molecular formula is a warning rather than an error because formula is not chemical identity. Canonical structure validation remains owned by `packages/structure/**` and cross-package species IDs are resolved during consolidation.
