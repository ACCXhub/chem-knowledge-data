# Import Contract

## Consumer payloads

Consolidation / 主应用消费本包时，应保留以下记录族：

- `atomic_configuration`
- `concept`
- `vsepr_model`
- `molecular_structure_example`
- `bonding_example`
- `crystal_model`
- `coordination_example`
- `concept_relation`
- `structure_property_rule`
- `exam_tag`
- `curriculum_scope`

## Cross-package resolution

1. `sc:*` ID 只作为结构化学包稳定导入键。
2. molecular / bonding / crystal / coordination example 中的 `formula` 不构成跨包身份。
3. Consolidation 应优先通过已有 inorganic/organic/structure crosswalk 解析示例：
   - 能解析到 published `structure_id` 时建立显式 link；
   - 存在同分异构体、晶型、多晶型或溶剂化歧义时保持未解析/多候选状态；
   - 不允许“同 formula = 同 identity”的隐式合并。
4. 原子电子排布记录通过 `atomic_number` 与主应用 Element UUID 对齐；本包不创建第二套 Element identity。

## Application projection

建议应用层生成：

- 原子结构学习图；
- 1—36号元素电子排布查询/轨道表示练习；
- VSEPR AXE 模型与代表分子；
- 分子极性判断训练；
- 化学键/σπ键概念图；
- 晶体分类与结构—性质对比；
- 简单配位实体概念页；
- exam-tag / curriculum 过滤投影。

`exam_tag` 仅表示稳定教学主题；动态考频、ExamHeat、用户掌握度由应用层维护。
