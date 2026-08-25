# Structure 数据目录说明

Canonical Structure record 按 `../schema/structure-record.schema.json` 校验。

## 当前基础发布版

`structure-foundation-1.0.0` 是针对当前冻结的 Organic v0.1 与当前 Inorganic 离子 seed 的 Structure 基础发布版。

规范结构覆盖：

- **46** 个离散中性分子；
- **24** 个离散离子；
- **12** 个盐 / 离子化合物的化学式单元；
- **5** 个聚合物重复单元抽象；
- **0** 个配位实体：在没有明确 metal–ligand 连接证据前不发布；
- **0** 个晶体结构：在没有晶体学证据前不发布。

当前共 **87** 条 canonical Structure record。精确数量与文件哈希以确定性生成后的 `manifest.json` 为准。

## Canonical 数据文件

使用 JSON Lines，便于流式读取、版本 diff 与逐条校验：

- `canonical/molecules.jsonl`
- `canonical/ions.jsonl`
- `canonical/formula_units.jsonl`
- `canonical/polymer_repeat_units.jsonl`

**化学式不自动等于分子结构。** `formula_unit` 与 `polymer_repeat_unit` 的语义都和离散 molecule 明确区分。

## 跨包接入数据

Structure 还发布以下显式接入记录：

- `links/inorganic.jsonl`：Inorganic 实体 → Structure 的 accepted link；
- `links/organic.jsonl`：Organic 实体 → Structure 的 accepted link，包括重复单元抽象；
- `deferrals/organic.jsonl`：无法安全固定的立体化学 / 大分子 / 完整聚合物身份；
- `coverage.json`：确定性的跨包覆盖汇总。

调用方应使用这些正式 link，不要把 SMILES、InChI 或 InChIKey 复制到自己的包中形成另一套真值。

## 分子式约定

`molecular_formula` 采用 `hill_no_charge`，用于机器比较：

- 使用 Hill ordering；
- `formal_charge` 单独存储；
- 聚合物 dummy attachment atom 不计入分子式；
- 面向学生的常规化学式排版仍由调用方知识包负责。

## 发布状态

- `draft`：已采集 / 派生，但还不是稳定数据；
- `reviewed`：化学与 provenance 校验通过，但尚未开放为稳定引用；
- `published`：可供跨包稳定引用；
- `rejected`：拒绝发布，仅在审计 / 调试有价值时保留。

只有 `validation.status == valid` 且 `validation.review_status == published` 的记录才是稳定 Structure record。

## 重建与验证

Canonical release 由固定证据与冻结的跨包目标确定性生成：

```text
python packages/structure/pipelines/build_release.py
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

CI 会执行同一套流程。Structure 工作分支允许自动提交确定性生成的数据；Pull Request 必须证明重新生成后不存在未提交 diff，保证发布数据可复现。
