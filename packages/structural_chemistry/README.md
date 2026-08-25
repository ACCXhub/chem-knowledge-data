# Structural Chemistry 数据包

本包负责高中化学“物质结构与性质 / 结构化学”知识数据，作为 `inorganic`、`organic`、`structure_registry` 与 `consolidated` 的只读上层教学知识包。

## 所有权边界

本包拥有：

- 原子核外电子排布与轨道教学知识；
- 化学键、键参数、键极性、σ/π 键、配位键等结构概念；
- VSEPR / 杂化 / 分子空间构型 / 分子极性 / 手性教学数据；
- 分子间作用力与结构—性质关系；
- 分子晶体、共价晶体、离子晶体、金属晶体及基础晶胞/堆积模型；
- 配位化学、超分子基础与典型高中案例；
- 面向高中课程的 topic / priority / misconception / relation 投影。

本包不拥有：

- SMILES、InChI、InChIKey、结构规范化身份：由 `packages/structure_registry` 负责；
- 无机 Substance / Ion / Reaction canonical identity：由 `packages/inorganic` 负责；
- 有机 Substance / FunctionalGroup / Reaction canonical identity：由 `packages/organic` 负责；
- 跨包统一 ID 与 consumer release：由 `packages/consolidated` 负责。

## 数据布局

- `schema/record.schema.json`：统一记录契约。
- `sources/registry.yaml`：来源登记。
- `curriculum/topics.yaml`：高中课程主题树。
- `data/concepts.jsonl`、`orbital_models.jsonl`、`atomic_structure.jsonl`：原子结构与核心概念。
- `data/bond_parameters.jsonl`、`molecular_geometry.jsonl`、`chirality.jsonl`：化学键与分子结构。
- `data/crystal_models.jsonl`、`crystal_principles.jsonl`：晶体与晶胞教学模型。
- `data/coordination.jsonl`、`supramolecular.jsonl`：配位和超分子基础。
- `data/structure_property_relations.jsonl`：结构—性质教学关系。
- `validation/validate.py`：零第三方依赖的一致性校验。

## 数据原则

1. 高中课程范围优先，不把大学结构化学整本搬进来。
2. 事实、教学解释、规则、例子分层；教学简化必须显式标注。
3. 能引用已发布 `structure_id` 时引用，不重新创造分子结构身份。
4. 规则允许 `0..N` 个适用例子，不把经验规则写成绝对定律。
5. provenance 只聚合来源，不覆盖上游包自己的来源证据。
6. 课程教材只用来确定范围与教学组织，不复制教材正文或图片。

## 当前版本

`structural-chemistry-foundation-0.1.0`

当前为 foundation 阶段：覆盖高中主干概念、代表性模型与消费契约；发布前以包内 validator、来源复核和上游状态核对作为 gate。
