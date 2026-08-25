# 化学结构管理数据布局

canonical structure records 按 `../schema/structure-record.schema.json` 校验。

## Foundation release

`structure-foundation-1.0.0` 是当前 Organic v0.1 与 Inorganic ion seed 所需的完整 Structure Registry foundation。

当前 canonical coverage：

- **46** 个离散中性分子
- **24** 个离散离子
- **12** 个盐 / 离子型物质的 formula units
- **5** 个 polymer repeat-unit abstractions
- **0** 个 coordination entities（没有明确 metal–ligand evidence 时不发布）
- **0** 个 crystal records（没有 crystallographic evidence 时不发布）

因此当前 release 共 **87 条 canonical Structure records**。精确数量与文件 hash 由 `manifest.json` 管理。

## Canonical records

JSON Lines 文件：

- `canonical/molecules.jsonl`
- `canonical/ions.jsonl`
- `canonical/formula_units.jsonl`
- `canonical/polymer_repeat_units.jsonl`

化学式不自动等于分子结构。formula-unit 与 polymer-repeat-unit scope 有独立语义，不能与离散 molecule 混用。

## 跨包产物

Structure Registry 还发布：

- `links/inorganic.jsonl`：accepted Inorganic entity → Structure links
- `links/organic.jsonl`：accepted Organic entity → Structure links，包括 repeat-unit abstractions
- `deferrals/organic.jsonl`：明确未解决的 stereochemical / macromolecular / full-polymer identity
- `coverage.json`：确定性的跨包覆盖摘要

调用方应使用这些 link，而不是复制 SMILES、InChI 或 InChIKey 形成第二份结构真值。

## Formula convention

`molecular_formula` 使用 `hill_no_charge` 做机器比较：

- Hill ordering
- formal charge 单独保存
- polymer dummy attachment atoms 不计入 formula
- 面向教学的常规化学式排版归调用知识包负责

## Publication states

- `draft`：已采集 / 派生，但尚不稳定
- `reviewed`：化学与 provenance 检查通过，尚未进入稳定公开 seam
- `published`：可供跨包稳定引用
- `rejected`：仅在审计 / 调试有价值时保留

只有 `validation.status == valid` 且 `validation.review_status == published` 的记录是稳定 Structure record。

## 重建

```text
python packages/structure_registry/pipelines/build_release.py
python packages/structure_registry/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure_registry/tests -v
```

CI 使用同一套流程验证。包路径已统一为 `packages/structure_registry/`；高中结构化学知识位于独立的 `packages/structural_chemistry/`。
