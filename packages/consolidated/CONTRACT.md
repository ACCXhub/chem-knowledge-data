# Consolidation contract

本文件定义 `packages/inorganic/`、`packages/organic/`、`packages/structure/` 汇总到 consumer-ready 数据集时的唯一跨包规则。

## 1. Source packages are immutable inputs

Consolidation 读取各源包的稳定/public 边界并生成新记录。源包 ID、schema、原始数据和已发布 Structure 记录继续由原 owner 管理；统一阶段的修正以 mapping / unresolved item 表达，不在源包内打补丁。

## 2. Canonical identity

### Species

最终 `species_id` 使用 UUID，并在 identity map 中一次分配、长期保存。它不从 formula、中文名、slug 或当前外部 ID 动态重算。

每个统一 Species 保留一个或多个 `source_refs`，指回原包本地 ID。

合并两个 source records 需要足够的同一性证据，例如：

1. 相同且已核验的外部 chemical identity（如 PubChem CID / ChEBI），并且 charge / entity semantics 兼容；或
2. 指向同一 published `structure_id`，且 structure scope、charge 与 species 语义兼容；或
3. 明确的人工 consolidation review evidence。

formula、名称或教学分类只能用于候选匹配，不能单独触发自动合并。证据不足时保留两个记录并标记 `pending`。

### Structure

`structure_id` 直接复用 `packages/structure/` 的 published canonical ID。Consolidation 不生成竞争性的 Structure ID，也不复制整条 Structure record 作为新的 canonical owner。

### Other entities

Reaction / Concept / Phenomenon / Experiment / FunctionalGroup 等跨包身份通过同一 identity-map 机制保存 source refs；各 entity family 的同一性规则独立审核，不以名称字符串自动合并。

## 3. Species consumer record

统一 Species 只承载跨模块稳定事实：

- UUID identity
- `ion | substance` entity type
- 中英文名称与 aliases
- display formula
- formal charge
- elemental composition
- accepted published Structure references
- external IDs
- source refs / field provenance
- review/publication state

用户行为、UI 排序、收藏、最近使用不属于 canonical Species。

`common_phases`、高中常用程度等教学/情境信息通过 teaching projection 输出，避免把运行时/教学偏好写成 Species 固有身份。

## 4. Reaction

Reaction 始终是一等实体。

统一后的 participant 引用 consolidated `species_id`，角色至少区分 `reactant`、`product`、`catalyst`。普通方程式使用精确整数系数；聚合/聚合物等教学 transformation 可显式使用 symbolic coefficient，并保持 `transformation_only` 状态。

Equation、conservation、Atom Mapping、Bond Diff、Mechanism 分层保持独立。Consolidation 不从 equation 或 structure 推导 mechanism truth。

跨包 participant 暂未解析时留在 unresolved report，正式 published Reaction release 不以 formula literal 代替 canonical participant identity。

## 5. Provenance

源包 provenance 永久保留，并使用 `{package, ref}` 形式避免不同包的 source ID 冲突。

统一字段选值记录 `field_provenance`。若输入只能提供 record-level provenance，则明确标记 granularity，而不是伪装成 field-level evidence。

Structure 的 provenance 继续由 Structure canonical record 提供；Species 只保存 Structure reference 与链接证据。

## 6. Teaching projection

高中教学分类是 canonical chemistry facts 之上的独立投影。

核心 family：

- `simple_substance`
- `cation`
- `anion`
- `oxide`
- `acid`
- `base`
- `salt`
- `organic_substance`
- `other`

`gas`、`precipitate`、`insoluble`、`weak_electrolyte` 等属于 tags / context，不与酸碱盐等 family 混为单一分类轴。

Projection 可以提供：

- `core | common | extended` 默认教学优先级
- 默认 Palette 分组与组内 rank
- 中文/英文/公式搜索 terms
- 高中范围标签

应用运行时可以在此基础上叠加用户固定、最近使用和使用频率；用户偏好不回写本仓库。

## 7. Search and chemical typography

数据库保存普通 formula + charge / composition。下标、上标和视觉排版由 consumer 渲染，例如 `SO4` + `-2` 渲染为 `SO₄²⁻`。

Search projection 可由 name、alias、formula、external synonym 生成；生成索引不是新的 chemical identity。

## 8. chem-wiki consumer seam

- Element 继续由 `chem-wiki` 已有 Element canonical 数据提供，本仓库不复制 118 个 Element identity。
- Equation Lab / Reaction Builder 将 Element palette 与 consolidated Species teaching projection 在应用层合并。
- M01 `SubstanceId` / `IonId` 可由 consolidated `species_id` 映射创建并保持稳定。
- Reaction participant 必须解析到统一 species identity 后再进入正式 consumer release。

## 9. Release gate

完整 consolidation release 只在 Inorganic 进入 `READY_FOR_CONSOLIDATION` 后生成。此前本包可以冻结 schema、mapping 规则并处理 Organic ↔ Structure 的可验证映射，但不得把部分数据冒充为完整高中化学发布集。

最终 release 至少输出：identity map、species、reactions、teaching projections、unresolved report 和带输入 commit/hash 的 manifest。
