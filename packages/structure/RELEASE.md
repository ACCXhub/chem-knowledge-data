# Structure 发布说明：structure-foundation-1.0.0

状态：**PUBLISHED / LOCKED（已发布 / 已锁定）**

Schema：

- `structure-record 1.2.0`
- `structure-link 1.1.0`
- `structure-deferral 1.0.0`

## 已发布的规范结构数据

共 **87** 条：

- 分子（`molecule`）：46
- 离子（`ion`）：24
- 化学式单元（`formula_unit`）：12
- 聚合物重复单元（`polymer_repeat_unit`）：5
- 配位实体（`coordination_entity`）：0
- 晶体结构（`crystal`）：0

配位实体和晶体记录为 0 是有意保留的边界：没有明确的金属—配体连接证据或晶体学证据时，不为了凑数量编造结构。

## 跨包覆盖情况

Organic `COMPLETE_V0_1`：

- 41 条完整身份 accepted link；
- 5 条额外的聚合物重复单元抽象 link；
- 9 条完整身份显式 deferral；
- **50 / 50 个 Organic Substance 已全部交代清楚**；
- **0 个未处理实体**。

当前 Inorganic 离子 seed：

- 23 条 accepted `ion_structure` link；
- **23 / 23 个离子已全部连接**；
- **0 个未处理离子**。

此外，phosphate Structure 仍保留为有效的额外覆盖，即使它不在当前 23 个无机离子 seed 快照中。

## 完整性校验

严格 validator 会检查：

- JSON Schema；
- Structure / link / deferral ID 的确定性；
- 重复 Structure ID、InChIKey 和外部 ID；
- SMILES 解析与 sanitization；
- 分子式与形式电荷一致性；
- Standard InChI / InChIKey 一致性；
- formula unit 不伪装成 molecule；
- 聚合物重复单元连接点与 fallback identity；
- accepted link 的目标是否存在、已发布且 scope 正确；
- Organic / Inorganic 覆盖完整性；
- manifest 数量、各文件记录数与 SHA-256。

## 验证证据

GitHub Actions **Validate structure package** 的工作分支运行 `32809697660` 已在 Python 3.13 下成功完成，依赖固定为 `rdkit==2025.9.4` 与 `jsonschema==4.25.1`。

```text
build_release.py
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9

validate_dataset.py --strict
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50

python -m unittest discover -s packages/structure/tests -v
Ran 16 tests
OK
```

Pull Request 阶段运行 `32809798607` 又独立完成了一次同样的重建、严格验证、测试以及“重新生成后无 diff”的可复现性检查。

PR #3 已 squash merge 到 `main`，合并提交为 `db02499d04475b3f710e7399b4e0a3dbaeea198e`。合并后重新读取 `main` 的 manifest，确认版本为 `structure-foundation-1.0.0`、schema 为 `1.2.0`，共 87 条结构、23 条 Inorganic link、46 条 Organic link、9 条 Organic deferral。

`packages/structure/**` 继续作为锁定的 Structure canonical owner。后续只在出现新的稳定跨包实体 / structure request 或新的可靠证据时发布增量版本，不做无边界的数据堆量。
