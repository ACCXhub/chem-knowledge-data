# Inorganic v1 import contract

本契约面向 `chem-wiki` 与后续 `packages/consolidated/`。它定义无机包稳定可消费边界，而不是要求应用数据库复制 JSONL 结构。

## Identity

- dataset `id` 是稳定 import key，例如 `substance:sodium-sulfate`、`reaction:hcl-naoh`。
- 主应用导入时继续使用已有 M01 typed UUID identity，并保存 dataset ID ↔ typed UUID 映射。
- v1 追加数据不得通过名称字符串建立关系；关系均使用 stable ID。

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

应用导入层把 `species_id` 解析到 M01 `SubstanceId | IonId`。不得把一个 reaction 展开为多条直接 Substance→Substance canonical reaction edge。

## Substance aqueous projection

`substance.ions` 表示高中层级下可用于水溶液拆写的 canonical 离子组成，并不声明固态物质由自由离子构成。

拆写必须结合：

- participant phase；
- `aqueous_behavior`；
- `rules/electrolytes.json`；
- `rules/solubility.json`。

弱电解质、气体、沉淀、单质和水按规则保持整体表示。

## Equation composer

Equation Lab / Reaction Builder 使用 `rules/equation_composer.json`：

- 默认只突出高中常见元素、离子/原子团和物种；
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
- `verification_targets` 仅说明推荐核验来源，不代表当前值直接复制自该来源。
- consolidation/import 需要保留 source keys，不得降成一个无法追溯的 `source: external` 字符串。
- 后续字段级外部 enrichment 应追加 external ID、retrieval/citation 与字段 provenance，而不是覆盖 editorial seed 的来源历史。

## Consumer projections

应用可以从 canonical data 派生：

- search index / alias index；
- common palette；
- element → species candidate list；
- ion-pair → neutral substance candidates；
- Substance → Reaction adjacency；
- Reaction → Phenomenon / Experiment / Concept / ExamTag；
- molecular → ionic → net-ionic display projection。

这些 projection 可以缓存，但 canonical owner 仍是本数据包/后续 consolidated release，不能反向把 UI cache 当新真相源。

## Out of scope

本契约不赋予无机包以下 ownership：

- Organic / FunctionalGroup；
- Structure identity、SMILES/molblock；
- atom mapping / bond diff；
- Mechanism / ElectronFlow；
- synthesis planning；
- 用户收藏、最近使用、个性化排序；
- 根据历史题目猜测的未来考题概率。
