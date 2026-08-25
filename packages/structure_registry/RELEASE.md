# 化学结构管理发布：structure-foundation-1.0.0

状态：**PUBLISHED / LOCKED**

包路径：`packages/structure_registry/`

Schema：

- `structure-record 1.2.0`
- `structure-link 1.1.0`
- `structure-deferral 1.0.0`

## 已发布 canonical structures

共 **87** 条：

- molecule：46
- ion：24
- formula unit：12
- polymer repeat unit：5
- coordination entity：0
- crystal：0

配位实体与晶体当前为 0 是证据边界的结果：没有合适连接或晶体学证据时不构造假记录。

## 跨包覆盖

Organic `COMPLETE_V0_1`：

- 41 个 accepted full-identity links
- 5 个 additional repeat-unit abstraction links
- 9 个 explicit full-identity deferrals
- **50 / 50 Organic substances accounted**
- **0 unaccounted**

Current Inorganic ion seed：

- 23 个 accepted `ion_structure` links
- **23 / 23 ions linked**
- **0 unaccounted**

phosphate Structure 继续作为额外结构覆盖保留，虽然不在当前 23-ion inorganic seed snapshot 中。

## 完整性门禁

严格 validator 检查：

- JSON Schema
- deterministic Structure / link / deferral IDs
- duplicate Structure IDs、InChIKeys、external IDs
- SMILES parse / sanitization
- formula 与 formal-charge consistency
- Standard InChI / InChIKey consistency
- formula-unit no-fake-molecule rule
- polymer repeat-unit attachment points 与 deterministic fallback identity
- accepted-link target existence / scope
- Organic / Inorganic coverage completeness
- manifest counts、per-file record counts 与 SHA-256

## 验证证据

`structure-foundation-1.0.0` 已通过 GitHub Actions 重建、严格验证、单元测试和 generated-data no-diff reproducibility gate。

```text
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50
Ran 16 tests
OK
```

包重命名为 `structure_registry` 只改变管理边界与路径，不改变既有 `structure_id`、schema 字段或 canonical 化学结构身份。

`packages/structure_registry/**` 继续作为 locked canonical owner。未来新增结构通过稳定的新实体 / structure request / 新证据触发增量 release。
