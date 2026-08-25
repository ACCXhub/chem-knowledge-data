# 化学结构管理包状态

**Status:** COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED

**Owner:** `chatgpt-web-structure-registry`

**Write scope:** `packages/structure_registry/**`

**Release:** `structure-registry-foundation-1.0.1`

**Published:** 2026-08-25

**Audited main integration:** `d8a0d62c4b408c62836de108841afa6e54dcf1b5`

## 当前稳定内容

Structure Registry foundation 保持 **87** 条 canonical Structure：46 molecules、24 ions、12 formula units、5 polymer repeat units。

跨包数字按发布时冻结输入解释：

- Organic v0.1 snapshot：**50/50** 个实体由 accepted full-identity links 或 explicit deferrals 明确处理；
- Inorganic 23-ion seed snapshot：**23/23** ions linked。

这些数字不覆盖 Organic / Inorganic 后续 audit 的实时状态。新稳定实体通过 request seam 进入下一次增量 Structure Registry release。

## v1.0.1 独立重审结果

本轮重审收敛了重命名、发布契约和数据完整性上的实际缺口：

- 4 个 schema `$id` 从旧 `packages/structure/` 切换到 `packages/structure_registry/`；
- link / deferral evidence 不再引用已删除旧路径；
- cross-track schema 可表达 `structural_chemistry` requester；
- manifest dataset identity 与 release version 统一为 Structure Registry 命名；
- 移除可覆盖当前 canonical release 的历史 `build_seed.py` 与 obsolete seed evidence；
- `resolved` structure request 必须携带 `resolved_structure_id`，未 resolved request 不得提前声明结果；
- manifest 必须完整登记全部发布数据文件；
- formula unit 的组成与净电荷从 Standard InChI 反向核验；
- molecule / ion scope 与净 formal charge 建立硬一致性约束；
- link / deferral ID 必须按冻结 UUIDv5 规则可复算；
- `ion_structure`、`formula_unit`、`repeat_unit_structure`、`polymorph` 等 relation 与目标 Structure scope 建立一致性校验。

## 身份稳定性

本次没有重新定义已有化学实体：

- frozen `structure_id` namespace 不变；
- 已发布 87 条 canonical Structure 的身份不重新分配；
- SMILES / InChI / InChIKey 不因包重命名重算身份；
- molecule / ion / formula_unit / polymer_repeat_unit 的结构语义保持不变；
- formula unit 继续不伪装为离散分子；
- 未解决 stereochemical / polymer / macromolecular identity 继续使用 explicit deferral。

## 最终验证门禁

正式只读 CI 执行：

```text
python packages/structure_registry/pipelines/build_release.py
python packages/structure_registry/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure_registry/tests -v
git diff --exit-code -- packages/structure_registry/data
```

最终审计套件为 **27 tests**，并要求 deterministic rebuild 后 canonical data zero-diff。

## 未来增量

以下内容需要新的可靠 evidence 或新的稳定跨包实体后再增量发布：

- Inorganic 新稳定 Substance / Ion 的结构请求；
- Organic review 结束后的新增或修订 identity requests；
- Structural Chemistry 需要解析到 canonical Structure 的新示例；
- 有明确 metal–ligand connectivity evidence 的 coordination entities；
- 有 crystallographic evidence 的 crystal records；
- chain length / end groups / tacticity 明确后的 full polymer identities。

其他 workstream 把 `packages/structure_registry/**` 视为只读，通过 published `structure_id` / link / deferral 使用结构事实。
