# chem-knowledge-data

高中化学知识底座数据仓库。

> 多聊天并行开发前，先阅读根目录 `WORKSTREAMS.md`。其中标记为 `ACTIVE / LOCKED` 的包只允许当前 owner 写入。

当前各数据包独立建设，完成后再统一整理、去重、对齐 ID / schema / provenance 并生成正式发布数据集。

- `packages/inorganic/`：无机化学知识数据
- `packages/organic/`：有机化学知识数据
- `packages/structure_registry/`：化学结构管理与机器可用结构数据（SMILES / InChI / Structure ID 等）
- `packages/structural_chemistry/`：高中结构化学 / 物质结构与性质知识数据

其中 `structure_registry` 与 `structural_chemistry` 是两个明确不同的领域：前者管理可计算化学结构身份与表示，后者管理高中课程中的原子结构、化学键、VSEPR、杂化、晶体等教学知识。
