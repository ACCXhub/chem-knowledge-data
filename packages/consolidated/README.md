# Consolidated chemistry knowledge package

`packages/consolidated/` 是 `chem-wiki` 的统一 consumer-ready 高中化学知识数据层。

当前稳定发布：**`consolidated-1.0.0` / `READY_FOR_APP_IMPORT`**。

它不重写四个源包，而是把各源包已经发布/完成的稳定边界转换为一套可直接导入应用的统一发布物。

## Frozen inputs

- `packages/inorganic/` — v1.0.1，`READY_FOR_CONSOLIDATION`
- `packages/organic/` — v0.2.0，完整性复核完成
- `packages/structure_registry/` — `structure-registry-foundation-1.0.1`，published Structure canonical owner
- `packages/structural_chemistry/` — `structural-chemistry-v1.0.2`，`READY_FOR_CONSOLIDATION`

`SOURCE_INPUTS.json` 固定 source release commit；独立审计进一步对这些 commit 中实际被消费的源文件逐一计算 SHA-256。源包后续升级通过新的 source snapshot / consolidated revision 接入，不在已发布 1.0.0 上静默漂移。

## Release contents

`consolidated-1.0.0` 当前包含：

- 309 species 与 309 source crosswalks；
- 69 accepted Structure links；
- 183 reactions；
- 309 teaching/search/Equation Lab projections；
- 637 non-species knowledge records；
- inorganic rules 与三类 curriculum projections；
- 13 个显式 informational findings；
- 0 review / 0 blocking finding。

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

## Identity and Structure

源包 ID 永久保留为 provenance/import anchor。Consolidated ID 是稳定 consumer import key；主应用可以继续将它映射到 M01 typed UUID。

未经审查的 formula/name 相同不会自动合并。跨包实体只有在明确 cross-reference、共享受信结构身份或 reviewed resolution 下才可共享同一 consolidated identity。

`structure_registry` 的 published `structure_id` 直接复用，不重新计算、不复制成第二套结构身份。Structure Registry 的历史 source ID 与当前源包 ID 不一致时，只允许在有结构身份、价态和来源证据一致的 reviewed bridge 下重绑定；v1.0.0 已收敛 `copper-2 → copper-ii`、`iron-2 → iron-ii`、`iron-3 → iron-iii` 三条历史链接，因此 69/69 accepted links 均进入 consumer release。

## Equation Lab / Reaction Builder

统一 teaching projection 支持：

- 高中分类：单质、阳离子、阴离子、酸、碱、盐、氧化物、有机物等；
- 中文名 / 别名 / 英文名 / ASCII 化学式检索；
- molecular / ionic / net-ionic 模式感知；
- 默认 Palette 优先级；
- 0..N 物种候选，而不是强行生成唯一化学答案。

收藏、拖拽顺序、最近使用、使用频率、隐藏项和自定义托盘属于应用运行时偏好，不进入本仓库。

## Validation and reproducibility

发布链：

```bash
python -m pip install -r packages/consolidated/validation/requirements.txt
python packages/consolidated/tools/build_release.py
python packages/consolidated/tools/finalize_release.py
python packages/consolidated/validation/validate_release.py
python packages/consolidated/validation/audit_release.py
```

GitHub Actions 在发布门禁中重复执行完整链路，并对第一次与第二次生成目录做 byte-for-byte 比较。`consolidated-1.0.0` 的首发审计结果为 **0 error / 0 warning / 0 blocking / 0 review / deterministic zero-diff**。

## 目录

- `CONTRACT.md` — 稳定边界与发布门禁
- `MAPPING.md` — 各源包到 consumer release 的映射规则
- `SOURCE_INPUTS.json` — 冻结源版本与 release commit
- `schema/` — consumer artifact JSON Schema
- `tools/build_release.py` — deterministic base generator
- `tools/finalize_release.py` — 审计发布收敛与 historical link resolution
- `validation/validate_release.py` — artifact/integrity validator
- `validation/audit_release.py` — independent pre-release semantic audit
- `generated/` — consumer-ready 机器生成发布物

机器消费应以 `generated/manifest.json` 的 release/state/count/hash 为入口。
