# chem-knowledge-data

高中化学知识底座数据仓库。

> 多聊天并行开发前，先阅读根目录 `WORKSTREAMS.md`。其中标记为 `ACTIVE / LOCKED` 的包只允许当前 owner 写入。

当前源数据按独立职责包建设，随后由 `packages/consolidated/` 统一整理、去重、对齐 ID / schema / provenance 并生成正式 consumer release。

- `packages/inorganic/`：高中无机化学知识数据；
- `packages/organic/`：高中有机化学知识数据；
- `packages/structure/`：可计算化学 Structure canonical identity 与结构派生数据；
- `packages/structural_chemistry/`：高中“物质结构与性质 / 结构化学”教学事实、模型与关系；
- `packages/consolidated/`：跨包统一后的 consumer-ready 发布层。

各源包独立拥有自己的 canonical 职责。跨包 identity、教学投影、搜索投影和正式消费契约在 consolidation 阶段收敛，不在源包之间互相复制事实。
