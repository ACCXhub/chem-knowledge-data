# Structural Chemistry package

高中化学“**物质结构与性质 / 结构化学**”知识数据包。

当前发布：**`structural-chemistry-v1.0.1` / READY_FOR_CONSOLIDATION**。

> 本包与 `packages/structure_registry/` 不同：`structure_registry/` 是可计算的分子/离子/式量单位/聚合物重复单元 **Structure canonical owner**；本包只拥有高中结构化学的教学事实、模型、概念关系和课程投影。

## v1.0.1 数据规模

| 类型 | 数量 |
|---|---:|
| 1—36号元素基态电子排布 | 36 |
| 结构化学概念 | 61 |
| VSEPR 模型 | 13 |
| 分子空间结构/极性示例 | 21 |
| 成键示例 | 18 |
| 晶体模型 | 14 |
| 配位实体示例 | 8 |
| 概念关系 | 69 |
| 结构—性质规则 | 12 |
| 教学/考点标签 | 26 |
| 课程范围节点 | 11 |
| **总记录** | **289** |

## 课程覆盖

完整覆盖教育部高中化学课程标准“物质结构与性质”三个主题：

1. 原子结构与元素的性质；
2. 微粒间相互作用与物质性质；
3. 研究物质结构的方法与价值。

v1.0.1 在 v1.0.0 基础上补齐第三主题：原子—分子—超分子—聚集态多尺度结构、原子光谱、分子光谱、X射线衍射、实验事实与结构模型的关系，以及结构研究服务新物质/新材料设计的教学投影。

覆盖链路：

`原子轨道/电子排布 → 周期表分区与周期性 → 化学键 → σ/π键 → VSEPR/分子空间结构 → 分子极性/分子间作用力 → 晶体类型/晶胞 → 配位与超分子 → 多尺度结构 → 光谱/XRD结构证据 → 结构—性质关系 → 结构导向设计`

课程覆盖证据见 `curriculum/coverage.json`。

## 数据入口

- `data/atomic_configurations.jsonl`：1—36号元素基态电子排布；
- `data/concepts.jsonl`：结构化学核心概念；
- `data/vsepr_models.jsonl`：AXE 模式、电子域几何与分子构型；
- `data/molecular_examples.jsonl`：常见分子几何、极性和适用的杂化教学模型；
- `data/bonding_examples.jsonl`：区分分子内、分子间、晶格、配位实体与形成模型层级的相互作用示例；
- `data/crystal_models.jsonl`：离子/分子/共价/金属/混合型晶体代表模型；
- `data/coordination_examples.jsonl`：简单配位实体；
- `data/relations.jsonl`：typed concept graph；
- `data/structure_property_rules.jsonl`：带适用范围和例外提示的结构—性质规则；
- `data/exam_tags.jsonl`：稳定教学标签，不是 ExamHeat 概率；
- `curriculum/scope.json`：课程标准范围投影；
- `curriculum/coverage.json`：每个课程节点到数据记录族/概念/教学标签的覆盖证据；
- `sources/source_registry.json`：来源角色与使用边界；
- `validation/validate_dataset.py`：发布校验。

## Canonical boundaries

- `packages/structure_registry/` 继续拥有 `structure_id`、SMILES、InChI/InChIKey、结构归一化和可计算描述符。
- `packages/inorganic/`、`packages/organic/` 继续拥有其 Substance / Ion / Reaction 等业务事实。
- 本包中的 formula/name 仅用于教学示例定位；**不以分子式作为跨包身份**，由 consolidation 解析为 published IDs。
- 有机同分异构体、晶型、多晶型、配位水合物等不得只靠 formula 自动合并。
- VSEPR、杂化等都按“教学模型”存储，记录适用范围；不把模型当作精确量子化学真值。
- 光谱/XRD记录表达“方法提供结构证据/约束”的高中层关系，不把单一实验手段写成自动唯一确定所有结构。
- `Reaction`、Atom Mapping、Bond Diff、Mechanism 不在本包生成。

## Sources

课程边界以教育部《普通高中化学课程标准（2017年版2020年修订）》“物质结构与性质”为主；1—36号基态电子排布由 NIST 数据校准；术语边界参考 IUPAC Gold Book；OpenStax 只作为部分结构模型与结构研究方法的二级交叉核对。来源与许可策略见 `DATA_POLICY.md` 和 `sources/source_registry.json`。

## Validate

```bash
python packages/structural_chemistry/validation/validate_dataset.py
```
