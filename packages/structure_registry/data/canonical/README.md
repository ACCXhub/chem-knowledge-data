# Canonical 化学结构记录

本目录按 `structure_scope` 拆分已发布的 canonical records：

- `molecules.jsonl`
- `ions.jsonl`
- `formula_units.jsonl`
- `polymer_repeat_units.jsonl`

`coordination_entity` 与 `crystal` 已由 schema 支持，但当前 release 没有发布记录，因为在缺少明确配位连接或晶体学证据时不会构造结构。

当前记录均为 `published + valid`、source-neutral、deterministic-ID records。

重建与验证：

```text
python ../../pipelines/build_release.py
python ../../validation/validate_dataset.py --strict
```
