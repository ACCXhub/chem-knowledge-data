# 化学结构管理集成接口

其他数据包只通过本文件约定的稳定 seam 使用 Structure Registry。

## Read

优先读取：

- `data/manifest.json`
- `data/canonical/*.jsonl`
- `data/links/inorganic.jsonl`
- `data/links/organic.jsonl`
- `data/deferrals/organic.jsonl`

accepted link 是当前跨包稳定映射。调用方不要按 formula、SMILES 或 PubChem CID 自己重新计算 `structure_id`。

## Link model

`structure-link.schema.json` 使用通用字段：

- `entity_kind`
- `entity_ref`
- `structure_id`
- `relation`

因此 `Ion` 不需要伪装为 `Substance`。

主要 relation：

- `primary_structure`
- `ion_structure`
- `formula_unit`
- `repeat_unit_structure`

`repeat_unit_structure` 只表示聚合物的 repeat-unit abstraction，不表示完整 polymer molecule。

## Missing / ambiguous structure

无法安全发布 canonical Structure 时使用 `structure-deferral.schema.json`。调用方应把 deferral 当作显式知识状态，而不是空字符串或临时假结构。

典型原因：

- generic identity 未固定 stereochemistry
- heterogeneous macromolecular material
- full polymer chain identity 未固定
- crystallographic / coordination evidence 不足

## New requests

无机、有机、结构化学等其他 workstream 如新增实体且缺结构，应使用 `structure-request.schema.json` 在自己的工作区记录请求；Structure Registry owner 后续统一采纳。

调用方不直接修改 `packages/structure_registry/**`，也不建立第二份 canonical Structure 数据。
