# 化学结构管理包状态

**Status:** COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED

**Owner:** 化学结构管理（Structure Registry）canonical owner

**Write scope:** `packages/structure_registry/**`

**Release:** `structure-foundation-1.0.0`

**Published:** 2026-08-25

## 完成状态

当前稳定输入范围内，Structure Registry foundation 已完成：

- Organic v0.1：**50/50** 个实体由 accepted full-identity links 或 explicit deferrals 明确处理；
- current Inorganic ion seed：**23/23** ions linked；
- **87** 条 canonical Structure：46 molecules、24 ions、12 formula units、5 polymer repeat units；
- canonical 数据可由 pinned evidence 确定性重建；
- formula unit、ion、molecule、polymer repeat unit 语义分离；
- 未解决 stereochemical / polymer / macromolecular identity 使用 explicit deferral，而不是猜测结构；
- 下游通过稳定 link / deferral seam 消费数据。

## 重命名说明

原包路径 `packages/structure/` 已改为：

`packages/structure_registry/`

中文名称统一为“化学结构管理”，用于与高中“结构化学”包 `packages/structural_chemistry/` 明确区分。此次重命名不改变既有 `structure_id`、SMILES、InChI、InChIKey、schema 或 canonical 化学身份。

## 验证

foundation 发布已经通过独立 CI 重建、strict validation、unit tests 与 generated-data reproducibility gate：

```text
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50
Ran 16 tests
OK
```

## 证据边界下的未来增量

以下内容属于未来 additive release，不是 foundation 遗漏：

- Inorganic 新稳定 Substance 的结构请求；
- 有明确 metal–ligand connectivity evidence 的 coordination entities；
- 有 crystallographic evidence 的 crystal records；
- chain length / end groups / tacticity 明确后的 full polymer identities；
- teaching/source identity 完成消歧后的 stereochemical identities。

其他 workstream 必须继续把 `packages/structure_registry/**` 视为只读，并通过已发布 `structure_id` / link / deferral 使用结构事实。
