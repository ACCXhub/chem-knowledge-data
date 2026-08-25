# Inorganic v1 import contract

本契约面向 `chem-wiki` 与后续 `packages/consolidated/`。它定义无机包稳定可消费边界，而不是要求应用数据库复制 JSONL 结构。

## Identity

- dataset `id` 是稳定 import key，例如 `substance:sodium-sulfate`、`reaction:hcl-naoh`。
- 主应用导入时继续使用已有 M01 typed UUID identity，并保存 dataset ID ↔ typed UUID 映射。
- v1 追加数据通过 stable ID 建立关系，不依赖名称字符串作为 identity。

## Import order

1. `element_scope`
2. `ion`
3. `substance`
4. `reaction`
5. `phenomenon`
6. `experiment`
7. `concept`
8. `exam_tag`
9. rules / curriculum projections

元素教学投影按 `atomic_number` / `symbol` 对接主应用已有 Element，不创建第二个 Element canonical identity。

## Canonical record contract

`schema/catalog-v1.schema.json` 是 v1 canonical record 的机器可读契约。v1.0.1 起实际发布数据需要同时满足：

- kind-specific stable ID pattern；
- 受控 `teaching_priority` / `review_status` / phase；
- 公式 composition 的合法元素符号 key 与正整数计数；
- 受控 substance category / aqueous behavior；
- 受控 reaction taxonomy；
- participant / net-ionic 的显式结构；
- source key、relation ID、alias 等数组的类型和去重约束；
- schema 未声明的 canonical record 字段不能静默进入发布数据。

Schema conformance 只是结构门槛；公式、守恒、引用、教学语义和外部交叉核验继续由 validation/audit 层独立检查。

## Reaction

Reaction 保持一等实体：

```text
Reaction
├─ reactants[] { species_id, coefficient, phase }
├─ products[]  { species_id, coefficient, phase }
├─ conditions[]
├─ reaction_types[]
├─ phenomenon_ids[]
├─ optional net_ionic
├─ reversible
└─ provenance
```

应用导入层把 `species_id` 解析到 M01 `SubstanceId | IonId`。一个 Reaction 不应展开为多条直接 Substance→Substance canonical reaction edge。

## Substance ionic composition and aqueous projection

v1 字段 `substance.ions` 的稳定含义是 **教学级离子组成元数据**：描述该物质可由哪些 canonical 离子单元及其化学计量关系表示。

它本身 **不等于水溶液中的拆写结果**，也不声明固态物质中存在自由离子。例如 `BaSO4(s)`、`AgCl(s)` 可以保存 `ions` 作为离子组成，但在离子方程式中仍保持整体固体表示。

是否拆写必须同时结合：

- Reaction participant 的 `phase`；
- `aqueous_behavior`；
- `rules/electrolytes.json`；
- `rules/solubility.json`；
- 必要时具体反应/酸碱平衡语境。

其中：

- `strong_electrolyte`：在适用的水溶液 participant 语境中可使用明确 ionic projection；
- `weak_electrolyte` / `weak_base`：通常保持整体形式；
- `insoluble` / `sparingly_soluble`：不能仅凭 `ions` 自动拆写；
- `acid_equilibrium`：表示存在条件相关酸解离/物种平衡，v1 不发布唯一固定拆写结果。

后续 schema v2 若拆分字段，可考虑将“ionic composition”与“dissociation projection”物理分离；v1.0.x 为保持 importer 兼容继续保留 `ions` 字段名。

## Substance phase semantics

v1 字段 `ambient_phase` 同时承载两类教学数据：

- `s` / `l` / `g`：常温附近的默认教学物态；
- `aq`：该条 canonical teaching species 默认以水溶液体系表示，而不是把 `aq` 宣称为与固/液/气完全同层级的纯物质热力学相态。

Reaction participant 的 `phase` 则始终表示该反应记录中的具体参与形式。

后续 schema v2 可将 Substance 层拆为 `reference_phase` 与 `default_teaching_form`；v1.0.x 不进行破坏性字段重命名。

## Equation composer

Equation Lab / Reaction Builder 使用 `rules/equation_composer.json`：

- 默认突出高中常见元素、离子/原子团和物种；
- 其他元素显式展开或搜索；
- 离子组合按整数 charge 求最简中性比；
- 多原子团 coefficient > 1 时由 renderer 按 canonical group 边界加括号；
- 多价元素返回已有 canonical candidate，不猜价态；
- 共价分子只返回数据集中存在的 candidate；
- 无 canonical candidate 时返回 unsupported / no-candidate；
- molecular、ionic、net-ionic 各自使用明确 projection。

## Typography

数据层公式保持 ASCII / machine-readable，例如：

- `H2SO4`
- `SO4`, `charge = -2`
- `Fe2(SO4)3`

前端 renderer 负责：

- 原子个数 → 下标；
- ionic charge → 上标；
- stoichiometric coefficient 保持基线数字；
- phase 使用统一 `(s)/(l)/(g)/(aq)` 表示。

## Provenance

- 每条 canonical record 必须有 `sources`。
- `verification_targets` 说明推荐核验来源，不代表当前字段已经直接取自该来源。
- consolidation/import 保留 source keys，不降成无法追溯的泛化 external source。
- 后续字段级 external enrichment 应追加 external ID、retrieval/citation 与字段 provenance，而不是覆盖 editorial seed 的来源历史。
- 课程标准来源用于确定高中教学范围与层级，不自动成为每个具体 formula / phase / reaction 事实的字段级权威来源。

## Consumer projections

应用可以从 canonical data 派生：

- search index / alias index；
- common palette；
- element → species candidate list；
- ion-pair → neutral substance candidates；
- Substance → Reaction adjacency；
- Reaction → Phenomenon / Experiment / Concept / ExamTag；
- molecular → ionic → net-ionic display projection。

这些 projection 可以缓存，但 canonical owner 仍是本数据包/后续 consolidated release，UI cache 不反向成为新的真相源。

## Out of scope

本契约不赋予无机包以下 ownership：

- Organic / FunctionalGroup；
- Structure identity、SMILES/molblock；
- atom mapping / bond diff；
- Mechanism / ElectronFlow；
- synthesis planning；
- 用户收藏、最近使用、个性化排序；
- 根据历史题目猜测的未来考题概率。
