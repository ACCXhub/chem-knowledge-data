# 结构数据接入说明

其他数据包只通过这里约定的稳定接口使用 Structure 数据。

## 读取入口

优先读取：

- `data/manifest.json`
- `data/canonical/*.jsonl`
- `data/links/inorganic.jsonl`
- `data/links/organic.jsonl`
- `data/deferrals/organic.jsonl`
- `data/coverage.json`

已接受的 link 是当前稳定的跨包映射。调用方不要根据 formula、SMILES 或 PubChem CID 自己重新计算 `structure_id`。

## 链接模型

`structure-link.schema.json` 使用通用字段：

- `entity_kind`：实体类型
- `entity_ref`：调用方实体引用
- `structure_id`：Structure 的规范结构 ID
- `relation`：实体与结构之间的关系

因此 Ion 不需要伪装成 Substance。

主要 `relation`：

- `primary_structure`：主要结构
- `ion_structure`：离子结构
- `formula_unit`：化学式单元
- `repeat_unit_structure`：聚合物重复单元结构

`repeat_unit_structure` 只代表聚合物的重复单元抽象，不代表具有确定链长、端基和分子量的完整聚合物分子。

## 缺失或存在歧义的结构

无法安全发布 canonical Structure 时，使用 `structure-deferral.schema.json` 记录显式延期状态。

调用方应把 deferral 当成一种真实知识状态，而不是用空字符串、占位值或临时假结构代替。

典型原因包括：

- 通用实体没有固定立体化学（stereochemistry）；
- 实体本身是异质大分子材料；
- 完整聚合物链身份没有固定；
- 晶体学 / 配位连接证据不足；
- 多个来源存在尚未解决的结构冲突。

## 新结构请求

其他工作流新增实体但缺少 Structure 时，应按照 `structure-request.schema.json` 在自己的工作区记录请求，由 Structure owner 后续统一采纳。

不要直接修改 `packages/structure/**`，也不要在调用方包内新建第二套 SMILES / InChI / Structure ID 真值。
