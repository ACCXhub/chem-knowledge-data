# Consolidated knowledge package

`packages/consolidated/` 是三个源数据包完成后面向 `chem-wiki` 的统一消费层。

当前阶段先冻结跨包身份、去重、provenance、Reaction 参与者解析和高中教学投影契约；`packages/inorganic/**`、`packages/organic/**`、`packages/structure/**` 都作为只读输入，不在这里反向修补。

## Canonical ownership

- Species/Reaction 等跨包统一身份与 consumer-ready 记录：本包拥有。
- Structure canonical identity：继续由 `packages/structure/` 拥有，本包只引用 published `structure_id`。
- 包内原始 ID：继续属于各源包，本包通过 identity map 保留来源映射。
- 用户收藏、最近使用、手动排序等个性化状态：属于应用层，不进入本包。

## Planned release surface

- `schema/identity-map.schema.json`：源包 ID → 统一 UUID 的显式映射。
- `schema/species.schema.json`：统一 Ion/Substance 消费记录。
- `schema/reaction.schema.json`：一等 Reaction 记录及 participant 引用。
- `schema/teaching-projection.schema.json`：高中分类、默认优先级、搜索和 Palette 投影。
- `data/`：仅在输入包达到 consolidation gate 后生成正式发布数据和 manifest。

## Current input state

- Organic：v0.1 complete，只读。
- Structure：published，只读消费 published + valid 记录。
- Inorganic：仍在 active 建设；完整发布等待其进入 `READY_FOR_CONSOLIDATION`。

统一规则见 `CONTRACT.md`。
