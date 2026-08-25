# 化学结构管理发布：structure-registry-foundation-1.0.1

状态：**PUBLISHED / LOCKED**

包路径：`packages/structure_registry/`

本版本是 `structure-foundation-1.0.0` 在包重命名后的**契约、可追溯性与完整性修正版本**。现有 87 条 canonical Structure 的化学身份保持不变，不重新分配 `structure_id`，不改变已验证的 SMILES / InChI / InChIKey。

Schema：

- `structure-record 1.2.0`
- `structure-link 1.2.0`
- `structure-deferral 1.1.0`
- `structure-request 1.2.0`

## 已发布 canonical structures

共 **87** 条：

- molecule：46
- ion：24
- formula unit：12
- polymer repeat unit：5
- coordination entity：0
- crystal：0

配位实体与晶体当前为 0 是证据边界的结果：没有合适连接或晶体学证据时不构造假记录。

## 跨包覆盖快照

以下数字表示该 release 使用的**冻结输入快照**，不是对其他包当前审核状态的实时声明。

Organic v0.1 snapshot：

- 41 个 accepted full-identity links
- 5 个 additional repeat-unit abstraction links
- 9 个 explicit full-identity deferrals
- **50 / 50 entities accounted**
- **0 unaccounted**

Inorganic 23-ion seed snapshot：

- 23 个 accepted `ion_structure` links
- **23 / 23 ions linked**
- **0 unaccounted**

phosphate Structure 继续作为额外结构覆盖保留，虽然不在该 23-ion seed snapshot 中。

## v1.0.1 独立审计修正

- 包内 4 个 JSON Schema `$id` 全部切换到 `packages/structure_registry/schema/`。
- `structure-request`、`structure-link`、`structure-deferral` 正式支持 `structural_chemistry` requester。
- link / deferral 的 repo-relative evidence 从已删除的 `packages/structure/...` 修正为 `packages/structure_registry/...`。
- manifest dataset identity 改为 `chem-knowledge-data/structure_registry`，发布版本统一为 `structure-registry-foundation-1.0.1`。
- 移除会覆盖当前 canonical data / manifest 的历史 `build_seed.py` 活动入口及 obsolete seed evidence。
- `resolved` request 与 `resolved_structure_id` 建立状态一致性约束。
- manifest 必须完整列出全部发布数据文件，不允许遗漏文件仍通过 strict validation。
- formula unit 的组成与净电荷从 Standard InChI 反向核验。
- molecule / ion scope 与净 formal charge 建立一致性校验。
- link / deferral ID 按 frozen UUIDv5 规则重新计算并校验。
- relation 与目标 Structure scope 对齐：`ion_structure → ion`、`formula_unit → formula_unit`、`repeat_unit_structure → polymer_repeat_unit`、`polymorph → crystal`。
- 新增 `coordination/claims/structure_registry.yaml`，正式登记并在审计结束后恢复只读 ownership。

## 完整性门禁

严格 validator 与回归测试覆盖：

- JSON Schema 与 schema `$id`
- deterministic Structure / link / deferral IDs
- duplicate Structure IDs、InChIKeys、external IDs
- SMILES parse / sanitization
- molecule / ion scope 与 formal charge consistency
- formula 与 formal-charge consistency
- Standard InChI / InChIKey consistency
- formula-unit Standard InChI → composition / net-charge reverse verification
- formula-unit no-fake-molecule rule
- polymer repeat-unit attachment points 与 deterministic fallback identity
- accepted-link target existence / relation-target scope
- request state / resolved target consistency
- repo-relative evidence path 存在性
- frozen Organic / Inorganic coverage completeness
- manifest dataset identity、完整 file set、counts、per-file record counts 与 SHA-256
- deterministic rebuild 后 generated data zero-diff

最终审计 CI 运行 **27 tests**。

## 发布边界

`packages/structure_registry/**` 继续作为 locked canonical owner。未来新增结构通过稳定的新实体 / structure request / 新证据触发增量 release。

其他包不得按 formula、SMILES 或外部 CID 自行重算并创建第二套 canonical `structure_id`。
