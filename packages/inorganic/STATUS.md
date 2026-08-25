# Inorganic v1 status

**State:** `VALIDATION_PENDING`

**Branch:** `inorganic-v1-rebuild`

## Release target

- 48 element teaching projections
- 57 ions / polyatomic groups
- 194 inorganic substances
- 151 first-class reactions
- 63 phenomena
- 31 experiments
- 64 concepts
- 32 exam tags
- 640 canonical records total
- 7 consumer rule sets
- curriculum coverage map
- source/licensing review
- v1 import contract and validation

## Closure gate

This package becomes `READY_FOR_CONSOLIDATION` only after all of the following are true:

- `validate_v1.py` succeeds on the committed branch;
- GitHub Actions validation succeeds on the exact release commit;
- manifest counts equal actual data counts;
- all reaction and net-ionic representations satisfy atom/charge conservation;
- all cross-record and rule/coverage references resolve;
- source keys resolve through `source_registry.json`;
- the v1 consumer/import contract is committed;
- the release commit changes only the inorganic ownership boundary plus its validation workflow.

The final closure commit will replace this state with `READY_FOR_CONSOLIDATION` after fresh CI evidence exists.
