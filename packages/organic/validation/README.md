# Organic package validation

The organic package is validated as an independent pre-consolidation dataset.

Run from repository root:

```bash
python -m pip install -r packages/organic/validation/requirements.txt
python packages/organic/validation/validate_package.py
python packages/organic/validation/validate_identity_coverage.py
```

The validation gate checks package-local JSON Schemas, duplicate IDs, provenance references, local entity references, external identity cross-reference integrity, explicit identity deferrals, duplicate-formula warnings, and completeness of the curriculum coverage evidence map.

Every organic Substance must have either a source-crosschecked external identity entry or an explicit deferral explaining why structure/consolidation policy is required. A shared molecular formula is a warning rather than an error because formula is not chemical identity. Canonical structure validation remains owned by `packages/structure/**` and cross-package species IDs are resolved during consolidation.
