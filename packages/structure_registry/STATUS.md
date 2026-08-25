# 化学结构管理包状态

**Status:** COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED

**Owner:** `chatgpt-web-structure-registry`

**Write scope:** `packages/structure_registry/**`

**Release:** `structure-registry-foundation-1.0.1`

**Published:** 2026-08-25

## 当前稳定内容

Structure Registry foundation 保持 **87** 条 canonical Structure：46 molecules、24 ions、12 formula units、5 polymer repeat units。

跨包数字按发布时冻结输入解释：

- Organic v0.1 snapshot：**50/50** 个实体由 accepted full-identity links 或 explicit deferrals 明确处理；
- Inorganic 23-ion seed snapshot：**23/23** ions linked。

这些数字不覆盖 Organic / Inorganic 后续 audit 的实时状态。新稳定实体通过 request seam 进入下一次增量 Structure Registry release。

## v1.0.1 重审结果

重命名后的独立审计发现并收敛了以下契约问题：

- schema `$id` 仍指向旧 `packages/structure/` 路径；
- link / deferral evidence 仍引用已删除旧路径；
- cross-track schema 无法表达已存在的 `structural_chemistry` requester；
- manifest 机器数据集名仍为旧 `chem-knowledge-data/structure`；
- 历史 `build_seed.py` 仍能直接覆盖当前 canonical release；
- root workstream 与独立 claim 的 Organic review 状态存在不同步。

修正后，`structure_registry` 是唯一机器结构管理包；高中结构化学继续由 `packages/structural_chemistry/` 独立拥有。

## 身份稳定性

本次是契约 / 路径 / provenance / 发布元数据修正，不重新定义化学实体。

以下身份边界保持冻结：

- `structure_id` namespace 不变；
- 已发布 canonical Structure 的 SMILES / InChI / InChIKey 不因包重命名重算身份；
- molecule / ion / formula_unit / polymer_repeat_unit 的结构语义不变；
- formula unit 继续不伪装为离散分子；
- 未解决 stereochemical / polymer / macromolecular identity 继续使用 explicit deferral。

## 验证门禁

正式 CI 继续执行：

```text
build_release.py
validate_dataset.py --strict
unittest discover
生成数据 zero-diff reproducibility check
```

v1.0.1 额外加入 schema identity、cross-track requester、evidence path、release metadata 与 legacy-builder regression tests。

## 未来增量

以下内容需要新的可靠 evidence 或新的稳定跨包实体后再增量发布：

- Inorganic 新稳定 Substance / Ion 的结构请求；
- Organic review 结束后的新增或修订 identity requests；
- Structural Chemistry 需要解析到 canonical Structure 的新示例；
- 有明确 metal–ligand connectivity evidence 的 coordination entities；
- 有 crystallographic evidence 的 crystal records；
- chain length / end groups / tacticity 明确后的 full polymer identities。

其他 workstream 把 `packages/structure_registry/**` 视为只读，通过 published `structure_id` / link / deferral 使用结构事实。
