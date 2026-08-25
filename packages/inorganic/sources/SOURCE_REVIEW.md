# Inorganic v1 source review

本记录说明无机 v1 使用外部来源的边界。`source_registry.json` 是机器可读 source key 注册表，本文件记录发布级选择理由。

## 教育部普通高中化学课程标准

用途：高中范围、教学层级与覆盖审计。

- canonical key: `src:moe-hs-chem-2020`
- 只提取“应覆盖哪些知识领域”这类范围事实，并使用本仓库自行编写的短描述。
- 不复制课程标准、教材或教辅正文。
- v1 的 `curriculum/coverage.json` 以此作为课程范围依据。

## IUPAC

用途：元素 identity、symbol 与 atomic number 校准。

- canonical key: `src:iupac-periodic-table-2022`
- 完整元素事实仍由主应用 M02 Element Data pipeline 负责；无机包只保存教学范围投影。
- 因此 v1 不复制第二套完整周期表数据。

## ChEBI

用途：开放的化学实体命名、formula、charge、ontology 与 external-ID enrichment 首选来源。

- canonical key: `src:chebi`
- 当前登记许可：CC BY 4.0。
- v1 seed 的 `verification_targets` 仅表示未来核验目标，不表示当前字段来自 ChEBI；真正导入外部值时需增加字段级 attribution / external ID。

## PubChem

用途：formula、charge、structure、synonyms、CID 等辅助核验和 enrichment。

- canonical key: `src:pubchem`
- PubChem 聚合多个 contributor，不能把“可通过 PubChem API 获取”直接等同于“所有贡献字段统一许可”。
- v1 只把 PubChem 注册为 verification target；未来发布 contributor-supplied annotation 前保留具体上游 provenance 与条款。

## NIST Chemistry WebBook

用途：后续物性、热化学、气相/离子能量等有条件数值校准。

- canonical key: `src:nist-webbook`
- 当前 v1 不批量复制 NIST 数值表；数值 enrichment 必须同时保存单位、条件、引用和检索信息。

## Periodic Table PRO

用途：中文交互覆盖和 UI/字段组织参考。

- canonical key: `src:periodic-table-pro`
- 在根数据/内容许可未明确前保持 reference-only，不将仓库正文、Wiki 文本或资源批量复制进 canonical dataset。

## Editorial seed

`src:editorial-hs-inorganic-v1` 表示本仓库为高中无机知识底座自行整理的事实选择、短中文说明、关系组织和教学优先级。

这不是外部权威来源的替代品。其状态为 `reviewed`，不自动升级为 `published`。后续真正发布具体外部事实时应增加字段级 provenance，并让 external verification 与 editorial selection 分层存在。

## v1 publication decision

无机 v1 的目标是 **consumer-ready teaching canonical seed**，而不是宣称构建全球化学事实数据库。当前发布允许：

- 稳定 identity / formula / composition / charge；
- 高中典型反应、现象和实验关联；
- 教学概念、考点标签与可解释规则；
- 明确的 source key 和后续核验目标。

当前发布暂缓：

- 来源条件不清晰的大规模网页抓取；
- 未保存温度/压力/单位的孤立数值；
- 未经字段级 provenance 审核的数据库 annotation；
- 教材/教辅的成段文字或图片；
- 由模型猜测的反应机理、原子映射或高考概率。
