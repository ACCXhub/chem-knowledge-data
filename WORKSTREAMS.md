# Active workstreams

这个文件用于多聊天并行开发时声明包级 ownership。开始修改任何 `packages/*` 前先检查这里，并结合 `coordination/claims/` 与包内 `STATUS.md` / `RELEASE.md` 判断当前写入边界。

| Package | Status | Active owner | Write boundary |
|---|---|---|---|
| `packages/inorganic/` | **COMPLETE / LOCKED** | `chatgpt-web-inorganic`（已完成） | v1.0.1 已完成发布后独立复核并标记 `READY_FOR_CONSOLIDATION`；作为 consolidation 只读输入，后续变更按新 dataset revision 处理 |
| `packages/organic/` | **REVIEW ACTIVE / LOCKED** | `chatgpt-web-organic` | v0.1 已发布但已重新进入完整性复核；当前仅 organic owner 写入，其他聊天只读 |
| `packages/structure_registry/` | **PUBLISHED / LOCKED** | `chatgpt-web-structure-registry` | 化学结构管理 canonical owner；`structure-registry-foundation-1.0.1` 审计收敛后继续只读发布，其他工作流只消费 published `structure_id` |
| `packages/structural_chemistry/` | **COMPLETE / LOCKED** | `chatgpt-web-structural-chemistry`（已完成） | `structural-chemistry-v1.0.2` 已完成并标记 `READY_FOR_CONSOLIDATION`；291 条 canonical records，作为 consolidation 只读输入 |
| `packages/consolidated/` | **ACTIVE / LOCKED** | `chatgpt-web-consolidation` | 负责跨包 ID/schema/provenance/教学投影与最终 consumer release；inorganic v1.0.1 已解除 audit hold，最终冻结仍以各源包当前 review 状态为准 |

## 并行规则

- 一个包同一时间只有一个写入 owner。
- 其他聊天需要使用某包的数据时只读引用，不直接修补。
- `packages/inorganic/` v1.0.1 已完成发布后独立复核，现作为 `READY_FOR_CONSOLIDATION` 只读输入；后续跨包对齐在 consolidation 中完成，不回写无机源包。
- `packages/organic/` 当前正在完整性复核；已发布 v0.1 可作为冻结比较输入，但其他工作流不得回写 organic 源包。
- `packages/structure_registry/` 是“化学结构管理”包，保持 canonical `structure_id` / SMILES / InChI / InChIKey 等结构事实的唯一 owner。
- `packages/structural_chemistry/` 是高中“结构化学”知识包，负责原子结构、化学键、VSEPR、杂化、晶体、超分子、结构研究方法与结构—性质教学关系；只引用 `structure_registry` 已发布的结构身份。
- `packages/structural_chemistry/` v1.0.2 作为只读完成输入参与 consolidation，不在 consolidation 中回写源文件。
- `packages/consolidated/` 是统一后的 consumer-ready canonical owner；跨包 ID 对齐、去重、provenance 合并、教学分类/搜索投影和正式发布数据都在这里收敛。
- 用户个性化排序、收藏、最近使用等运行时偏好属于应用层，不进入知识数据 canonical 包。
