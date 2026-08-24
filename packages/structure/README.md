# Structure package

化学结构与结构派生数据包。

当前独立负责：

- canonical SMILES / isomeric SMILES
- InChI / InChIKey
- 结构规范化与校验
- 2D / 3D 结构表示及可再生成的派生数据
- 基础结构描述符
- Substance ↔ Structure 关联候选
- 结构来源、原始记录、清洗与验证

本包不重新定义无机或有机知识分类，也不拥有 Reaction / Experiment / Concept 数据。建议内部逐步形成：`data/`、`sources/`、`pipelines/`、`schema/`、`validation/`。跨包统一放到后续 consolidation。
