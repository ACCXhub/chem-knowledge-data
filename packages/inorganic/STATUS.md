# Inorganic v1 status

**State:** `AUDIT_CANDIDATE`

**Release:** `1.0.1-rc1`

**Owner boundary:** `packages/inorganic/`

## Final release content

- 48 element teaching projections
- 57 ions / polyatomic groups
- 194 inorganic substances
- 152 first-class reactions
- 63 phenomena
- 31 experiments
- 64 concepts
- 32 exam tags
- **641 canonical records total**
- 7 validated consumer rule sets
- 10-domain curriculum coverage map
- source/licensing review
- v1 import contract + JSON Schema
- dependency-free v1 chemistry/reference validator

## Closure evidence

The exact v1 branch head and the merged `main` release were validated by GitHub Actions on Python 3.13. Validation covers:

- global ID uniqueness;
- source / verification-target integrity;
- ion charge and composition checks;
- Substance ionic-projection neutrality and composition equality;
- Reaction atom and total-charge conservation;
- net-ionic atom and total-charge conservation;
- cross-record references for phenomena, experiments, concepts and exam tags;
- all stable references embedded in rule sets and curriculum coverage;
- exact manifest counts: 640 records, 7 rule sets, 10 curriculum domains.

Merged release commit: `80bb64b959850d48f7f588b82ad4fa51344e98f0`.

## Handoff

`packages/consolidated/` and the application importer may consume this package as a stable read-only source. Further changes to inorganic canonical identities should be treated as a new dataset revision with migration/provenance review rather than ad-hoc consumer patches.

## Post-release audit

v1.0.0 之后执行了独立公式/组成、最简计量系数、JSON Schema、语义覆盖和 PubChem 诊断交叉检查。当前 rc1 在 audit 分支收敛命名歧义、平衡分类、一个非最简系数问题、Li2CO3 溶解性规则和核心 Ba(OH)2 反应覆盖。通过最终 CI 与人工复核后再恢复 READY_FOR_CONSOLIDATION。
