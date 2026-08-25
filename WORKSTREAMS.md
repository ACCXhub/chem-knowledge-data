# Active workstreams

这个文件用于多聊天并行开发时声明包级 ownership。开始修改任何 `packages/*` 前先检查这里，并结合 `coordination/claims/` 与包内 `STATUS.md` / `RELEASE.md` 判断当前写入边界。

| Package | Status | Active owner | Write boundary |
|---|---|---|---|
| `packages/inorganic/` | **AUDIT HOLD / LOCKED** | `chatgpt-web-inorganic` | v1.0.0 已合并，但发布后独立复核发现需要 v1.0.1 收敛的校正项；当前仅无机 owner 在 audit 分支修改，其他聊天只读 |
| `packages/organic/` | **COMPLETE / LOCKED** | `chatgpt-web-organic`（已完成） | v0.1 已完成；作为 consolidation 只读输入，源包本身保持不变 |
| `packages/structure_registry/` | **PUBLISHED / LOCKED** | 化学结构管理 canonical owner | 负责机器可用化学结构身份与表示；其他工作流只读 published `structure_id` |
| `packages/structural_chemistry/` | **ACTIVE / LOCKED** | `chatgpt-web-structural-chemistry` | 负责高中“物质结构与性质/结构化学”教学知识数据；只读复用其他包身份，不重建 canonical `structure_id` |
| `packages/consolidated/` | **ACTIVE / LOCKED** | `chatgpt-web-consolidation` | 负责跨包 ID/schema/provenance/教学投影与最终 consumer release；可继续契约与只读分析，但在 inorganic v1.0.1 解除 HOLD 前不要冻结基于 v1.0.0 的最终 release |

## 并行规则

- 一个包同一时间只有一个写入 owner。
- 其他聊天需要使用某包的数据时只读引用，不直接修补。
- `packages/inorganic/` 正在执行发布后独立复核；v1.0.0 可作比较输入，但最终 consolidation release 等待 v1.0.1 audit closure。
- `packages/organic/` v0.1 作为只读完成输入参与统一，不在 consolidation 中回写源文件。
- `packages/structure_registry/` 是“化学结构管理”包，保持 canonical `structure_id` / SMILES / InChI / InChIKey 等结构事实的唯一 owner。
- `packages/structural_chemistry/` 是高中“结构化学”知识包，负责原子结构、化学键、VSEPR、杂化、晶体与结构—性质教学关系；只引用 `structure_registry` 已发布的结构身份。
- `packages/consolidated/` 是统一后的 consumer-ready canonical owner；跨包 ID 对齐、去重、provenance 合并、教学分类/搜索投影和正式发布数据都在这里收敛。
- 用户个性化排序、收藏、最近使用等运行时偏好属于应用层，不进入知识数据 canonical 包。
