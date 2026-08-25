# Consolidation contract

本契约定义 `inorganic`、`organic`、`structure_registry`、`structural_chemistry` 如何汇聚为一套 consumer-ready 高中化学知识发布物。

当前已审计发布：**`consolidated-1.0.0` / `READY_FOR_APP_IMPORT`**。

## 1. Source ownership

- 四个源包继续拥有各自已发布事实与稳定 ID。
- Consolidation 只读取源包稳定边界，写入 `packages/consolidated/**`。
- 源数据错误通过 integration finding 反馈给对应源包的新 revision；consolidation 不就地修补源包。
- `structure_registry` 的 published `structure_id` 是唯一结构身份。
- 每个 release 的输入必须同时固定 source release commit 与实际消费文件内容 hash；版本号和记录数仅作为辅助一致性信号。

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
- Consolidation 直接消费 `packages/structure_registry/data/links/*.jsonl` 中 `status=accepted` 的关系。
- 关系指向的 `structure_id` 必须存在于 published canonical Structure 文件。
- Formula-only 不用于分子结构身份匹配；有机同分异构体必须保持可区分。
- `structural_chemistry` 是教学知识包，不拥有 Structure identity。
- 若 accepted link 使用旧 source ID，而当前冻结源包已经对同一实体进行稳定 ID 迁移，只有在结构 target、formula/composition、formal charge/价态和来源证据一致时才允许 reviewed historical rebound；该桥接必须显式、可审计并保留原 source link ID。

## 5. Reaction

Reaction 保持一等实体。

- inorganic participant `species_id` 通过 inorganic source crosswalk 解析；
- organic `substance_ref` 通过 organic crosswalk 解析；
- organic `external_species_key=inorganic:<slug>` 必须解析到已发布 inorganic species；
- `formula_literal` 只能作为显示/核验信息，不能在 identity 不明确时隐式创建新 species；
- role、coefficient、phase、conditions、reaction class/type、phenomenon/experiment/concept refs、net ionic 等语义保留；
- 必需 participant 未解析时，该 Reaction 不得进入 ready-for-import 发布集；
- 对可数值计算的普通方程，consumer release 需独立校验元素守恒以及适用时的总电荷守恒；symbolic polymer、transformation-only 和明确的 non-discrete material 场景必须显式分类，而不是伪装成普通 fixed-coefficient equation。

## 6. 其他知识实体

Concept、Phenomenon、Experiment、FunctionalGroup、ChemicalClass、ExamTag，以及 structural chemistry 的 atomic configuration、VSEPR、bonding/crystal/coordination examples、structure-property rules、relations 等保持原有 typed semantics。

Consolidated release 使用统一 envelope：consumer ID + source package + source type + source ID + 原始 reviewed payload。这样实现单一发布入口，同时避免为了“统一 schema”而丢失源领域语义。

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

允许确认 identity 的证据从强到弱包括：

1. 明确 source cross-reference；
2. 相同且语义兼容的 published Structure link；
3. authoritative external ID；
4. reviewed manual resolution。

Formula + charge + composition 只可作为简单无机粒子/formula-unit 的辅助证据；名称和 formula 相同默认仅生成 duplicate candidate，不自动 merge。

## 10. Consumer release artifacts

稳定发布生成：

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

`generated/manifest.json` 是机器消费的 release identity/state/count/hash 入口。

## 11. Release gates

发布为 `READY_FOR_APP_IMPORT` 前必须满足：

1. 四个冻结输入的 release/version/state/count 与 `SOURCE_INPUTS.json` 一致；
2. 当前工作树中实际消费的源文件内容与各自 pinned `release_commit` 中的同一路径内容逐文件一致，并形成 source-file-set hash；
3. 每个 consolidated species/reaction/knowledge record 可追溯到 source ID；
4. source crosswalk 唯一且无一源多目标冲突；
5. 所有必需 Reaction participants 解析成功；
6. accepted Structure links 全部被解释：进入 consumer release、显式 reviewed rebound，或产生 blocking finding；不得静默丢弃；
7. accepted Structure targets 均存在且 published；
8. 可数值核验的 Reaction 与 net-ionic representation 通过独立元素/电荷守恒检查；
9. Reaction → Concept / Experiment / Phenomenon 与 rule references 均指向已发布 source records；
10. ambiguous molecular identities 没有被静默合并；
11. teaching/search projection 对全部 species 一一覆盖、Palette rank 唯一连续，且不含运行时用户状态；
12. generated file counts 与 SHA-256 和 manifest 一致；
13. independent audit 为零 error、零 blocking、零 review；
14. 同一冻结 source snapshot 连续执行两次完整 build/finalize/validate/audit 后，`generated/` 必须 byte-for-byte zero-diff。

## 12. v1.0.0 audit result

`consolidated-1.0.0` 已在 GitHub Actions run `32856769997` 通过上述门禁：309 species、309 crosswalks、69/69 accepted Structure links、183 reactions、637 knowledge records、309 teaching projections；独立审计为 0 error / 0 blocking / 0 review，完整第二次生成 zero-diff。
