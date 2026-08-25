# 化学结构管理（Structure Registry）

`packages/structure_registry/` 是仓库内**机器可用化学结构身份与结构表示**的 canonical owner。

这里管理的是 SMILES、InChI、InChIKey、`structure_id`、离子 / 分子 / 化学式单元 / 聚合物重复单元等可计算结构数据。它与高中课程中的**结构化学（Structural Chemistry）**严格分开：后者位于 `packages/structural_chemistry/`，负责原子结构、化学键、VSEPR、杂化、晶体类型及结构—性质教学知识。

当前发布版本：**`structure-foundation-1.0.0`**。

## 本包负责

- 与外部来源无关的稳定 `structure_id`
- molecule / ion / formula unit / polymer repeat unit 的结构表示
- canonical / isomeric SMILES（仅适用于离散分子或离子）
- Standard InChI / InChIKey（适用时）
- polymer repeat-unit attachment-point 表示
- 结构规范化、校验与可再生成描述符
- 外部结构 ID 与 provenance
- 跨包 `entity_ref ↔ structure_id` 接受关系
- 无法安全归一化的结构 deferral

## 本包不负责

- 高中结构化学知识点
- 无机 / 有机教学分类
- Substance 的中文教学知识
- Reaction / Experiment / Phenomenon / Concept
- 用户界面的中文名称、常规化学式排版与教学解释

## 当前发布数据

`data/manifest.json` 是机器可读发布清单：

- 46 个分子（molecule）
- 24 个离子（ion）
- 12 个化学式单元（formula unit）
- 5 个聚合物重复单元（polymer repeat unit）
- 共 87 条 canonical Structure
- Organic v0.1：50 / 50 个 Substance 全部由正式 link 或显式 deferral 覆盖
- Inorganic 当前离子 seed：23 / 23 全部有 accepted ion-structure link

5 个 polymer repeat unit 是教学级结构抽象，不代表具有固定链长、端基、分子量或 tacticity 的完整聚合物分子。

## 主要入口

- `CONTRACT.md`：ownership、ID 与结构表示规则
- `INTEGRATION.md`：其他数据包如何引用 Structure Registry
- `schema/structure-record.schema.json`
- `schema/structure-link.schema.json`
- `schema/structure-deferral.schema.json`
- `sources/`：来源策略与固定 evidence
- `data/canonical/*.jsonl`
- `data/links/*.jsonl`
- `data/deferrals/*.jsonl`
- `data/coverage.json`
- `data/manifest.json`
- `validation/validate_dataset.py`
- `RELEASE.md` / `STATUS.md`

## 重建与验证

```bash
python packages/structure_registry/pipelines/build_release.py
python packages/structure_registry/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure_registry/tests -v
```

`build_seed.py` 仅作为历史兼容入口保留；当前正式构建入口是 `build_release.py`。

## 并行协作规则

当 `WORKSTREAMS.md` 将本包标记为 `PUBLISHED / LOCKED` 时，只有化学结构管理 canonical owner 可以修改 `packages/structure_registry/**`。

无机、有机、结构化学、consolidation 只消费已发布的 `structure_id`、link 与 deferral；新增需求通过 structure request seam 提交，不在调用方内部建立第二份结构事实。

## 文档语言约定

给人阅读的说明文档以中文为主；代码、schema 字段、文件名以及 SMILES / InChI / InChIKey 等国际标准标识保持英文和标准形式。
