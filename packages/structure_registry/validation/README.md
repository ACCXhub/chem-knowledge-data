# Structure 数据校验标准

一条 canonical Structure record 只有在其 `structure_scope` 对应的必要检查全部通过后，才允许发布。

## 必须检查的项目

1. 通过 `schema/structure-record.schema.json` 的 JSON Schema 校验。
2. `structure_id` 必须来源中立且可确定性重建。
3. 存在机器可用结构表示时，分子式与形式电荷必须一致。
4. 存在 SMILES 时，必须通过 RDKit 解析与 sanitization。
5. Standard InChI 必须使用 `InChI=1S/`；保存的 InChIKey 必须可以从它重新推导。
6. 同时存在 SMILES 与 Standard InChI 时，两者必须描述同一个规范化后的离散实体。
7. 跨来源出现实质性差异时必须进入 `needs_review`，不得静默覆盖。
8. 持久化 RDKit 派生字段时必须记录 toolkit 与版本。
9. 重复 canonical ID、重复 InChI identity、冲突 external ID 都必须让校验失败。
10. 盐类 / 离子化合物不能仅因为存在 disconnected salt SMILES 就被发布成 molecule。
11. 聚合物重复单元必须满足规定的 attachment point 规则。
12. accepted link 的目标 Structure 必须存在、已发布且 scope 与 relation 相容。
13. manifest 中的数量、记录数与 canonical 文件 SHA-256 必须和仓库发布数据一致。
14. 当前冻结的 Organic / Inorganic 跨包目标必须全部由 accepted link 或显式 deferral 交代。

## 各结构范围的规则

- **`molecule` / `ion`**：至少需要一种机器可用的离散结构表示。
- **`formula_unit`**：formula + charge 是核心机器语义；Standard InChI 可以标识化学式单元的组成身份，但 canonical molecular SMILES 保持为空，避免把晶格化学式误当分子。
- **`polymer_repeat_unit`**：必须有明确重复连接方式和规定数量的 attachment point；它不是完整 polymer identity。
- **`coordination_entity`**：连接关系与电荷必须有明确 metal–ligand 证据。
- **`crystal`**：必须有晶体学证据；molecular SMILES 不能代表晶体结构。
- **`other`**：必须提供人工 review 说明。

## 执行命令

```bash
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

如果环境中还没有 RDKit / jsonschema，先安装 `validation/requirements.txt`。

只有 `published + valid` 的记录可以供其他工作流稳定引用。
