# chem-knowledge-data

高中化学知识底座数据仓库。

> 多聊天并行开发前，先阅读根目录 `WORKSTREAMS.md` 和 `coordination/claims/`。标记为 `ACTIVE / LOCKED` 的路径只允许当前 owner 写入。

源数据按三个独立包建设，跨包统一通过独立 consolidation consumer package 收敛：

- `packages/inorganic/`：无机化学知识数据
- `packages/organic/`：有机化学知识数据
- `packages/structure/`：化学结构与结构派生数据
- `packages/consolidated/`：统一 ID、去重、provenance、教学投影以及面向 `chem-wiki` 的正式消费数据

源包在采集/发布阶段保持各自 canonical ownership；consolidation 只读消费稳定边界，不反向复制或修补源包 canonical 数据。
