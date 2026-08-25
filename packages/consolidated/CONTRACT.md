# Consolidation contract

本契约定义 `inorganic`、`organic`、`structure_registry`、`structural_chemistry` 如何汇聚为一套 consumer-ready 高中化学知识发布物。

## 1. Source ownership

- 四个源包继续拥有各自已发布事实与稳定 ID。
- Consolidation 只读取源包稳定边界，写入 `packages/consolidated/**`。
- 源数据错误通过 integration finding 反馈给对应源包的新 revision；consolidation 不就地修补源包。
- `structure_registry` 的 published `structure_id` 是唯一结构身份。

## 2. Consumer identity

- Consolidated ID 是稳定 import key，不取代主应用 M01 typed UUID。
- 每条 consolidated record 必须保留 source package + source ID。
- 名称、化学式、别名和外部数据库 ID 是属性/证据，不直接等同全局 identity。
- 默认一条 source species 对应一条 consolidated species；只有 reviewed identity resolution 才允许多个 source IDs 汇到同一 consumer identity。
- 一旦 consumer ID 发布，后续 revision 保持其稳定；发生 reviewed merge 时选定既有 survivor ID，并保留旧 ID 的迁移记录。

## 3. Species

Consumer species 统一：

- inorganic `ion`；
- inorganic `substance`；
- organic `substance`。

至少保留：source IDs、entity kind、中文/英文名、formula、charge、composition、aliases、分类、teaching priority、source review state、provenance、external IDs、可选 preferred Structure link。

公式保持机器可读 ASCII；上下标/电荷由 UI renderer 生成。

## 4. Structure

- Structure 是独立实体，不塞进 Substance/Ion identity。
- Consolidation 优先直接消费 `packages/structure_registry/data/links/*.jsonl` 中 `status=accepted` 的关系。
- 关系指向的 `structure_id` 必须存在于 published canonical Structure 文件。
- Formula-only 不用于分子结构身份匹配；有机同分异构体必须保持可区分。
- `structural_chemistry` 是教学知识包，不拥有 Structure identity。

## 5. Reaction

Reaction 保持一等实体。

- inorganic participant `species_id` 通过 inorganic source crosswalk 解析；
- organic `substance_ref` 通过 organic crosswalk 解析；
- organic `external_species_key=inorganic:<slug>` 必须解析到已发布 inorganic species；
- `formula_literal` 只能作为显示/核验信息，不能在 identity 不明确时隐式创建新 species；
- role、coefficient、phase、conditions、reaction class/type、phenomenon/experiment/concept refs、net ionic 等语义保留；
- 必需 participant 未解析时，该 Reaction 不得进入 ready-for-import 发布集。

## 6. 其他知识实体

Concept、Phenomenon、Experiment、FunctionalGroup、ChemicalClass、ExamTag，以及 structural chemistry 的 atomic configuration、VSEPR、bonding/crystal/coordination examples、structure-property rules、relations 等保持原有 typed semantics。

首个 consolidated release 使用统一 envelope：consumer ID + source package + source type + source ID + 原始 reviewed payload。这样实现单一发布入口，同时避免为了“统一 schema”而丢失源领域语义。

## 7. Provenance

- source provenance 原样保留并加 package namespace；
- consolidated record 增加 integration provenance；
- 多来源冲突显式记录，不静默覆盖；
- external verification target 与已验证事实区分保存。

## 8. 高中教学与搜索投影

化学事实与 UI/教学投影分离。

Primary category：

- `elemental_substance`
- `cation`
- `anion`
- `acid`
- `base`
- `salt`
- `oxide`
- `organic`
- `other`

沉淀、难溶、强/弱电解质、气体等是 tags/behavior，不与 primary category 竞争。

Search token 从中文名、别名、英文名、formula、稳定 external ID 派生；不修改 canonical labels/formula。

Equation Lab projection 生成 molecular / ionic / net-ionic suitability、默认 Palette rank 和分类检索数据。候选始终允许 `0..N`；多价态/多化合物场景不得猜唯一答案。

用户 pin、手动排序、最近使用、使用频率、隐藏项、自定义托盘全部属于应用运行时数据。

## 9. Duplicate resolution

允许自动确认的证据从强到弱：

1. 明确 source cross-reference；
2. 相同且语义兼容的 published Structure link；
3. authoritative external ID；
4. reviewed manual resolution。

Formula + charge + composition 只可作为简单无机粒子/formula-unit 的辅助证据；名称和 formula 相同默认仅生成 duplicate candidate，不自动 merge。

## 10. Consumer release artifacts

首个 release 生成：

- `species.jsonl`
- `crosswalk.jsonl`
- `structure_links.jsonl`
- `reactions.jsonl`
- `teaching_projection.jsonl`
- `knowledge_records.jsonl`
- `unresolved_findings.jsonl`
- `rules/`
- `curriculum/`
- `source_snapshot.json`
- `manifest.json`
- `validation_report.json`

## 11. Release gates

发布为 `READY_FOR_APP_IMPORT` 前必须满足：

1. 四个冻结源版本与 `SOURCE_INPUTS.json` 一致；
2. 每个 consolidated species/reaction/knowledge record 可追溯到 source ID；
3. source crosswalk 唯一且无一源多目标冲突；
4. 所有必需 Reaction participants 解析成功；
5. accepted Structure links 目标均存在且 published；
6. ambiguous molecular identities 没有被静默合并；
7. teaching/search projection 不含运行时用户状态；
8. generated file counts 与 SHA-256 和 manifest 一致；
9. validator 产生零 blocking errors。
