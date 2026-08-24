# Parallel package coordination

本仓库允许多个聊天并行建设不同数据包。

开始写入前先检查 `coordination/claims/`。

规则：

- `status: active` 的 claim 对其 `paths` 拥有当前写入权；其他聊天可以读取和引用，但不要修改这些路径。
- 每个聊天只创建/更新自己的 claim 文件，避免共享状态文件产生冲突。
- 跨包统一、ID 对齐、schema 收敛和 provenance 合并放到后续 consolidation 阶段。
- 如果确实需要修改另一个 active claim 覆盖的路径，先由用户明确重新分配 ownership。
