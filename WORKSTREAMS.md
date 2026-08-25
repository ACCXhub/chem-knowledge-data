# Active workstreams

这个文件用于多聊天并行开发时声明包级 ownership。开始修改任何 `packages/*` 前先检查这里，并结合 `coordination/claims/` 与包内 `STATUS.md` / `RELEASE.md` 判断当前写入边界。

| Package | Status | Active owner | Write boundary |
|---|---|---|---|
| `packages/inorganic/` | **COMPLETE / LOCKED** | `chatgpt-web-inorganic`（已完成） | v1.0.0 已完成并标记 `READY_FOR_CONSOLIDATION`；作为 consolidation 只读输入，源包本身保持不变 |
| `packages/organic/` | **COMPLETE / LOCKED** | `chatgpt-web-organic`（已完成） | v0.1 已完成；作为 consolidation 只读输入，源包本身保持不变 |
| `packages/structure/` | **PUBLISHED / LOCKED** | Structure canonical owner | 仅 Structure canonical owner 修改；其他工作流只读 published `structure_id` |
| `packages/consolidated/` | **ACTIVE / LOCKED** | `chatgpt-web-consolidation` | 负责跨包 ID/schema/provenance/教学投影与最终 consumer release；不反向修改三个源包 |

## 并行规则

- 一个包同一时间只有一个写入 owner。
- 其他聊天需要使用某包的数据时只读引用，不直接修补。
- `packages/inorganic/` v1.0.0 已作为 `READY_FOR_CONSOLIDATION` 只读完成输入；后续跨包对齐在 consolidation 中完成，不回写无机源包。
- `packages/organic/` v0.1 作为只读完成输入参与统一，不在 consolidation 中回写源文件。
- `packages/structure/` 保持结构 canonical owner；consolidation 复用 published `structure_id`，不复制或重建结构身份。
- `packages/consolidated/` 是统一后的 consumer-ready canonical owner；跨包 ID 对齐、去重、provenance 合并、教学分类/搜索投影和正式发布数据都在这里收敛。
- 用户个性化排序、收藏、最近使用等运行时偏好属于应用层，不进入知识数据 canonical 包。
