# Active workstreams

这个文件用于多聊天并行开发时声明包级 ownership。开始修改任何 `packages/*` 前先检查这里，并结合 `coordination/claims/` 与包内 `STATUS.md` / `RELEASE.md` 判断当前写入边界。

| Package | Status | Active owner | Write boundary |
|---|---|---|---|
| `packages/inorganic/` | **COMPLETE / LOCKED** | `chatgpt-web-inorganic`（已完成） | v1.0.1 已完成发布后独立复核并标记 `READY_FOR_CONSOLIDATION`；作为 consolidation 只读输入 |
| `packages/organic/` | **COMPLETE / LOCKED** | `chatgpt-web-organic`（已完成） | v0.2.0 完整性复核已完成；作为 consolidation 只读输入 |
| `packages/structure_registry/` | **PUBLISHED / LOCKED** | `chatgpt-web-structure-registry` | `structure-registry-foundation-1.0.1` 是化学结构身份与机器可用结构表示的 canonical owner；其他工作流只消费 published `structure_id` |
| `packages/structural_chemistry/` | **COMPLETE / LOCKED** | `chatgpt-web-structural-chemistry`（已完成） | `structural-chemistry-v1.0.2` 已标记 `READY_FOR_CONSOLIDATION`；291 条 canonical records，作为 consolidation 只读输入 |
| `packages/consolidated/` | **ACTIVE / LOCKED** | `chatgpt-web-consolidation` | 负责跨包 ID/schema/provenance、Reaction 引用解析、高中教学与搜索投影、Structure 关联和最终 consumer release |

## 并行规则

- 一个包同一时间只有一个写入 owner。
- 已完成/发布的源包在 consolidation 阶段保持只读；发现源数据问题时记录 integration finding，由对应源包的新 revision 处理。
- `packages/inorganic/` v1.0.1、`packages/organic/` v0.2.0、`packages/structural_chemistry/` v1.0.2 已可作为冻结输入参与统一。
- `packages/structure_registry/` 是 `structure_id`、SMILES、InChI、InChIKey 等结构身份与表示的唯一 owner；consolidation 直接复用其 accepted links，不建立第二套 Structure 身份。
- `packages/structural_chemistry/` 管理高中“物质结构与性质”知识：原子结构、化学键、VSEPR、杂化、晶体、超分子、结构研究方法与结构—性质关系；它不拥有 Substance/Ion/Structure identity。
- `packages/consolidated/` 是统一 consumer release 的 canonical owner：跨包 source-ID crosswalk、Reaction participant 解析、Structure link、provenance 聚合、教学分类、搜索与 Equation Lab Palette projection 均在此收敛。
- 用户个性化排序、收藏、最近使用、使用频率等运行时偏好属于应用层，不进入知识数据 canonical 包。
