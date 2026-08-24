# Active workstreams

这个文件用于多聊天并行开发时声明包级 ownership。开始修改任何 `packages/*` 前先检查这里。

| Package | Status | Active owner | Write boundary |
|---|---|---|---|
| `packages/inorganic/` | **ACTIVE / LOCKED** | 当前“无机知识底座”聊天 | 仅此工作流修改；其他聊天只读、可引用，不修改此目录 |
| `packages/organic/` | available | 未分配 | 可由另一聊天接管 |
| `packages/structure/` | **PUBLISHED / LOCKED** | Structure canonical owner | 仅 Structure canonical owner 修改；Inorganic/Organic 只读 published `structure_id`，缺失结构按 `packages/structure/INTEGRATION.md` 在各自包内提请求 |

## 并行规则

- 一个包同一时间只有一个写入 owner。
- 其他聊天需要使用某包的数据时只读引用，不直接修补。
- 需要跨包变更时先在各自包内记录待整合项，后续 consolidation 阶段统一处理。
- `packages/inorganic/` 当前由无机工作流持续建设，直到这里把状态改为 `READY_FOR_CONSOLIDATION`。
- `packages/structure/` 已发布结构底座并保持写保护；其他工作流消费 published `structure_id`，不修改 `packages/structure/**`。
