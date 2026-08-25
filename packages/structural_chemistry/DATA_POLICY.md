# Structural Chemistry Data Policy

## 1. Canonical ownership

本包的 canonical truth 是“结构化学教学知识”，不是分子结构身份本身。

- `structure_id`：只引用 `packages/structure_registry` 已发布 ID。
- `species_id`：只引用无机/有机/统一层已发布 ID。
- 教学概念使用本包稳定 `sc_*` ID。

## 2. 来源分工

- 中国高中课程标准 / 教材目录：确定课程边界、主题层级和教学优先级。
- IUPAC Gold Book：术语边界、键/配位/分子间作用等定义核对。
- NIST ASD：原子基态电子排布等原子事实核对。
- IUCr：晶胞、晶体结构、配位数等晶体学术语和结构边界核对。
- PubChem：分子 identity / 基础分子事实的交叉核对。
- `packages/structure_registry`：本仓库可计算 Structure identity 的唯一直接引用源。

## 3. 教学简化

下列内容必须视为模型/近似，而不是无条件 canonical 物理事实：

- VSEPR；
- `sp / sp2 / sp3` 杂化作为局部结构解释；
- 电负性差与键极性的经验比较；
- 键长、键级、键强度之间只在可比体系内使用的趋势；
- “相似相溶”；
- “分子量越大沸点越高”等系列内经验趋势；
- 晶体四分类对石墨、过渡结构等复杂体系的简化；
- 配合物理想几何；
- “手性碳连接四种不同取代基”作为高中常见识别模式，而非全部手性的定义。

记录必须用 `teaching_notes`、`condition` 或明确字段标注适用边界。

## 4. 数据边界

- 不复制教材正文、插图、习题或视觉资产；
- 不从 formula 唯一推断有机物结构；
- 不把手性概念扩展成 organic 包的具体立体异构 identity；
- 不给未知配位实体猜测唯一几何；
- 不把气态离散分子模型直接等同于固态结构；
- 不为了凑完整度伪造 structure link；
- 不覆盖上游 package provenance。

## 5. 发布策略

foundation 数据可以在本包内以 `reviewed` 状态积累；只有满足 schema、引用、来源、教学简化和事实复核 gate，并通过 package validator/CI 后才升级为 `published` release。
