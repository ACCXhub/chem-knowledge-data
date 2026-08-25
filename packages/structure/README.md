# Structure package

化学结构与结构派生数据包，也是仓库内 **Structure canonical owner**。

当前发布：**`structure-foundation-1.0.0`**。本包已经覆盖当前 Organic v0.1 与 Inorganic ion seed 的结构接缝；其他工作流只读 published `structure_id`，不得在自己的包里复制、修补或重建 canonical Structure。

## Ownership

本包独立负责：

- source-neutral `structure_id`
- molecule / ion / formula unit / polymer repeat unit 的结构表示
- canonical / isomeric SMILES（仅适用于离散分子或离子）
- Standard InChI / InChIKey（适用时）
- polymer repeat-unit attachment-point 表示
- 结构规范化、校验与可再生成描述符
- 外部结构 ID 与 provenance
- 跨包 `entity_ref ↔ structure_id` 接受关系
- 无法安全归一化的结构 deferral

不负责无机/有机教学分类，也不拥有 Reaction / Experiment / Phenomenon / Concept。

## Current release

`data/manifest.json` 是机器可读发布清单：

- 46 molecules
- 24 ions
- 12 formula units
- 5 polymer repeat units
- 87 canonical structures
- Organic v0.1：50 / 50 Substance 全部被 primary/formula-unit link 或显式 deferral 覆盖
- Inorganic current ion seed：23 / 23 全部有 accepted ion-structure link

五个 polymer repeat units 是教学结构抽象，不代表具有固定链长、端基、分子量或 tacticity 的完整聚合物分子。

## Canonical entry points

- `CONTRACT.md`：ownership、ID 与表示规则
- `INTEGRATION.md`：其他包如何引用 Structure
- `schema/structure-record.schema.json`
- `schema/structure-link.schema.json`
- `schema/structure-deferral.schema.json`
- `sources/pubchem_evidence.jsonl`
- `sources/cross_track_targets.json`
- `data/canonical/*.jsonl`
- `data/links/*.jsonl`
- `data/deferrals/*.jsonl`
- `data/coverage/*.json`
- `data/manifest.json`
- `validation/validate_dataset.py`
- `RELEASE.md` / `STATUS.md`

## Rebuild and validate

```bash
python packages/structure/pipelines/build_seed.py
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

`build_seed.py` 的历史文件名为兼容保留；它现在重建完整 foundation release，而不是旧的 33-record seed。

## Parallel rule

`WORKSTREAMS.md` 将本包标记为 `PUBLISHED / LOCKED` 时，只有 Structure canonical owner 修改 `packages/structure/**`。无机、有机、consolidation 只消费 published IDs / links / deferrals；新增需求通过结构 request seam 提交，不在调用方内部造第二份结构事实。
