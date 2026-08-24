# Structure package

化学结构与结构派生数据包，也是仓库内 **Structure canonical owner**。

其他并行工作流可以读取并引用本包已经 `published` 的 `structure_id`，但不直接修改、复制或在自己的包内重建 canonical structure 记录。完整边界见 [`CONTRACT.md`](./CONTRACT.md)。

## Ownership

本包独立负责：

- canonical / isomeric SMILES
- Standard InChI / InChIKey
- structure scope 与 formal charge
- 结构规范化与校验
- 2D / 3D 可再生成的派生数据与元数据
- 基础结构描述符
- 外部结构 ID 与 provenance
- `Substance ↔ Structure` 关联候选与最终结构侧接受

本包不重新定义无机/有机教学分类，也不拥有 Reaction / Experiment / Phenomenon / Concept 数据。

## Canonical files

- [`CONTRACT.md`](./CONTRACT.md)：跨工作流边界、ID 与 ownership
- [`schema/structure-record.schema.json`](./schema/structure-record.schema.json)：canonical record schema
- [`sources/registry.json`](./sources/registry.json)：结构来源与工具角色
- [`data/README.md`](./data/README.md)：数据布局和 publication 状态
- [`validation/README.md`](./validation/README.md)：结构校验标准

## Parallel rule

`WORKSTREAMS.md` 标记本包为 `ACTIVE / LOCKED` 时，只有当前 Structure workstream 写入 `packages/structure/**`。无机与有机工作流如需结构，只保存/提出 `structure_id` 引用或待整合请求，不直接修改本包。
