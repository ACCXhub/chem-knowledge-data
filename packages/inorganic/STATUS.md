# Inorganic v1 status

**State:** `READY_FOR_CONSOLIDATION`

**Release:** `1.0.0`

**Owner boundary:** `packages/inorganic/`

## Final release content

- 48 element teaching projections
- 57 ions / polyatomic groups
- 194 inorganic substances
- 151 first-class reactions
- 63 phenomena
- 31 experiments
- 64 concepts
- 32 exam tags
- **640 canonical records total**
- 7 validated consumer rule sets
- 10-domain curriculum coverage map
- source/licensing review
- v1 import contract + JSON Schema
- dependency-free v1 chemistry/reference validator

## Closure evidence

The release candidate was validated in GitHub Actions on Python 3.13 with:

- global ID uniqueness;
- source / verification-target integrity;
- ion charge and composition checks;
- Substance ionic-projection neutrality and composition equality;
- Reaction atom and total-charge conservation;
- net-ionic atom and total-charge conservation;
- cross-record references for phenomena, experiments, concepts and exam tags;
- all stable references embedded in rule sets and curriculum coverage;
- exact manifest counts: 640 records, 7 rule sets, 10 curriculum domains.

The exact final release commit is required to pass the same workflow before merge.

## Handoff

`packages/consolidated/` and the application importer may now consume this package as a stable read-only source. Further changes to inorganic canonical identities should be treated as a new dataset revision with migration/provenance review rather than ad-hoc consumer patches.
