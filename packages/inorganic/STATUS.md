# Inorganic v1 status

**State:** `READY_FOR_CONSOLIDATION`

**Release:** `1.0.1`

**Owner boundary:** `packages/inorganic/`

**Audit closure:** release metadata、数据语义、课程映射与验证证据已在发布后独立复核中收敛。

## Final release content

- 48 element teaching projections
- 58 ions / polyatomic groups
- 194 inorganic substances
- 152 first-class reactions
- 63 phenomena
- 31 experiments
- 64 concepts
- 32 exam tags
- **642 canonical records total**
- 7 validated consumer rule sets
- 10-domain curriculum coverage map
- source/licensing review
- v1 import contract + JSON Schema
- chemistry/reference audit suite

## Closure evidence

The v1.0.1 release branch is validated by GitHub Actions on Python 3.13. Validation covers:

- global ID uniqueness and cross-record reference integrity;
- JSON Schema conformance for every canonical record;
- formula ↔ composition checks and ion charge checks;
- Substance ionic-projection neutrality and composition equality;
- Reaction and net-ionic atom / total-charge conservation;
- simplest integer coefficients and reaction taxonomy semantics;
- solubility-rule compatibility with canonical substance behavior;
- identity / alias / search collision checks;
- curriculum-domain connectivity for core teaching concepts;
- phenomenon / experiment / concept / exam-tag relationship integrity;
- all stable references embedded in rule sets and curriculum coverage;
- exact manifest counts: 642 records, 7 rule sets, 10 curriculum domains;
- diagnostic PubChem cross-checks for substances and ions, with ambiguous name resolution reported rather than auto-rewriting canonical data.

## Handoff

`packages/consolidated/` and the application importer may consume this package as a stable read-only source. Further changes to inorganic canonical identities should be treated as a new dataset revision with migration/provenance review rather than ad-hoc consumer patches.

## v1.0.1 audit closure

v1.0.1 收敛了 v1.0.0 后复核发现的命名歧义、平衡分类、最简计量系数、Li2CO3 溶解性规则、Ba(OH)2 核心反应覆盖、Fe3+/SCN- 教学物种表达，以及核心课程概念映射缺口。最终 canonical 数据、规则、课程映射、Schema、manifest 与验证证据保持一致。
