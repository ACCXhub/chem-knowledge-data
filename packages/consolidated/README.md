# Consolidated chemistry knowledge package

`packages/consolidated/` 是 `chem-wiki` 的统一 consumer-ready 知识数据层。

它不重写源包，而是把各源包已经发布/完成的稳定边界转换成一套可直接导入应用的统一发布物。

## 当前冻结输入

- `packages/inorganic/` — v1.0.1，`READY_FOR_CONSOLIDATION`
- `packages/organic/` — v0.2.0，完整性复核完成
- `packages/structure_registry/` — `structure-registry-foundation-1.0.1`，published Structure canonical owner
- `packages/structural_chemistry/` — `structural-chemistry-v1.0.2`，`READY_FOR_CONSOLIDATION`

精确输入版本由 `SOURCE_INPUTS.json` 固定。源包后续升级时，consolidation 通过新的 source snapshot/release revision 接入，不在旧发布物上静默漂移。

## 本包负责

- 统一 consumer species 记录与 source-ID crosswalk；
- Organic ↔ Inorganic 重复候选检测与显式 resolution；
- Reaction participant 的跨包 species 引用解析；
- 直接消费 `structure_registry` 的 accepted Structure links；
- source provenance 聚合与保留；
- 高中分类、搜索 token、默认 Palette 排序与 equation-mode projection；
- 无机规则集与课程投影的发布打包；
- Organic / Inorganic / Structural Chemistry 非 species 知识记录的统一 envelope/index；
- release manifest、unresolved findings 与机器验证报告。

## 身份原则

源包 ID 永久保留为 provenance/import anchor。Consolidated ID 是稳定 consumer import key；主应用可以继续将它映射到 M01 typed UUID。

未经审查的 formula/name 相同不会自动合并。跨包实体只有在明确 cross-reference、共享受信结构身份或人工 reviewed resolution 下才可共享同一 consolidated identity。

`structure_registry` 的 published `structure_id` 直接复用，不重新计算、不复制成第二套结构身份。

## Equation Lab / Reaction Builder

本包生成统一 teaching projection，支持：

- 高中分类：单质、阳离子、阴离子、酸、碱、盐、氧化物、有机物等；
- 中文名 / 别名 / 英文名 / ASCII 化学式检索；
- molecular / ionic / net-ionic 模式感知；
- 默认 Palette 优先级；
- 0..N 物种候选，而不是强行生成唯一化学答案。

收藏、拖拽顺序、最近使用、使用频率、隐藏项和自定义托盘属于应用运行时偏好，不进入本仓库。

## 目录

- `CONTRACT.md` — consolidation 的稳定边界与发布门禁
- `MAPPING.md` — 各源包到 consumer release 的映射规则
- `SOURCE_INPUTS.json` — 当前冻结源版本
- `schema/` — consumer artifact JSON Schema
- `tools/build_release.py` — deterministic release generator
- `validation/validate_release.py` — release integrity validator
- `generated/` — 机器生成 consumer artifacts；只由 generator 更新

## 发布原则

生成链必须可重复：同一 source snapshot + 同一 generator 应产生同一业务数据。发布前要求 crosswalk、Reaction 引用、Structure link、manifest/hash、教学投影和 unresolved finding 检查全部通过。
