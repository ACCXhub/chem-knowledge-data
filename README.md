# chem-knowledge-data

高中化学知识底座数据仓库。

> 多聊天并行开发前先阅读根目录 `WORKSTREAMS.md`。其中标记为 `ACTIVE / LOCKED` 的包只允许当前 owner 写入。

当前源包已经形成稳定分工，并由 `packages/consolidated/` 负责统一消费层：

- `packages/inorganic/`：无机化学知识数据，v1.0.1，`READY_FOR_CONSOLIDATION`
- `packages/organic/`：有机化学知识数据，v0.2.0，完整性复核完成
- `packages/structure_registry/`：化学结构管理与机器可用结构数据（Structure ID / SMILES / InChI / InChIKey 等），published canonical owner
- `packages/structural_chemistry/`：高中结构化学 / 物质结构与性质知识数据，v1.0.2，`READY_FOR_CONSOLIDATION`
- `packages/consolidated/`：统一 source-ID、Reaction 引用、Structure 关联、provenance、教学分类、搜索与 Equation Lab/Reaction Builder consumer projection，并生成正式 consumer release

`structure_registry` 与 `structural_chemistry` 是两个不同领域：前者管理可计算的化学结构身份与表示，后者管理高中课程中的原子结构、化学键、VSEPR、杂化、晶体、超分子与结构研究方法等教学知识。
