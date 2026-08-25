# Structural Chemistry Contract

## Ownership

`packages/structural_chemistry/` 是高中“物质结构与性质/结构化学”教学数据 owner，负责：

- 1—36号元素基态电子排布教学事实；
- 原子轨道、电子云、构造原理、泡利不相容原理、洪特规则等概念；
- 化学键、σ/π键、分子间作用力、氢键等教学模型；
- VSEPR AXE 模式、分子空间结构、分子极性与杂化教学投影；
- 晶体类型、简单晶胞/配位数教学模型；
- 简单配位实体与配位数；
- 结构—性质关系、课程覆盖和稳定教学标签。

## Identity boundary

本包 ID 仅标识本包教学记录，例如 `sc:concept:*`、`sc:vsepr:*`。它们发布后稳定。

本包**不拥有** molecule / ion / formula unit 的 canonical `structure_id`，也不拥有 inorganic / organic Substance、Ion、Reaction、Mechanism、Atom Mapping 或 Bond Diff。

formula、中文名、英文名是教学展示和 cross-package resolution hint，不得当作跨包主键。

## Model semantics

- VSEPR 是预测常见主族分子/离子空间构型的教学模型，实际结构可偏离理想角。
- 杂化轨道字段表示高中价键模型；对超价分子不强制写 `sp3d/sp3d2` 作为真实电子结构。
- “离子/共价”不是绝对二分；教学分类保留模型边界。
- 晶体结构—性质规则均带 general-trend qualifier，不能当作无例外规则。
- 配位示例若水溶液实际物种可能更复杂，几何字段可留空而不是伪造唯一结构。
- 成键示例显式区分 intramolecular / intermolecular / lattice / formation_model / intracomplex，避免把氢键等分子间作用力误标成分子内键。

## Cross-package seam

Consolidation 可将本包示例解析到 `packages/structure_registry/` published `structure_id`，或 inorganic / organic / consolidated species IDs。解析必须通过显式 crosswalk；禁止按 formula 自动唯一化。
