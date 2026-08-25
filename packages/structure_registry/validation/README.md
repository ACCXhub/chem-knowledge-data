# 化学结构管理校验标准

只有通过与其 `structure_scope` 相适配的检查，canonical structure record 才能发布。

## 必须检查

1. 按 `schema/structure-record.schema.json` 做 JSON Schema validation。
2. `structure_id` 必须 source-neutral 且 deterministic。
3. 存在机器结构表示时检查 formula / charge consistency。
4. 存在 SMILES 时必须能 parse / sanitize。
5. Standard InChI 必须使用 `InChI=1S/`；存储的 InChIKey 必须可由它推导。
6. 同时存在 SMILES 与 Standard InChI 时，两者必须描述同一 normalized discrete entity。
7. 跨来源冲突进入 `needs_review`，不能静默覆盖。
8. 持久化 RDKit-derived fields 时保留 toolkit / version。
9. duplicate canonical IDs、duplicate InChI identities、conflicting external IDs 都是校验失败。
10. formula-unit salt 不能仅因为存在 disconnected salt SMILES 就作为 molecule 发布。
11. manifest record counts 与 canonical file SHA-256 必须和 release 一致。

## Scope rules

- **molecule / ion**：至少有一种机器可用的离散结构表示。
- **formula_unit**：formula + charge 为 canonical；Standard InChI 可以表示 disconnected stoichiometric identity，但不把它提升为 molecular canonical SMILES。
- **coordination_entity**：connectivity / charge 需要明确 evidence。
- **crystal**：需要 crystallographic evidence；molecular SMILES 不是 crystal representation。
- **polymer_repeat_unit**：必须满足重复单元 attachment-point 规则。
- **other**：需要 review notes。

## 命令

```bash
python packages/structure_registry/validation/validate_dataset.py --strict
```

若环境没有 RDKit / jsonschema，先安装 `validation/requirements.txt`。

只有 `published + valid` records 是其他 workstream 的稳定输入。
