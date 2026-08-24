# chem-knowledge-data

高中化学知识底座数据仓库。

> 多聊天并行开发前，先阅读根目录 `WORKSTREAMS.md`。其中标记为 `ACTIVE / LOCKED` 的包只允许当前 owner 写入。

当前先按三个独立数据包并行建设，完成后再统一整理、去重、对齐 ID / schema / provenance 并生成正式发布数据集。

- `packages/inorganic/`：无机化学知识数据
- `packages/organic/`：有机化学知识数据
- `packages/structure/`：化学结构与结构派生数据

现阶段三个包各自独立推进，避免在采集期过早共享内部模型；跨包统一在后续 consolidation 阶段完成。
