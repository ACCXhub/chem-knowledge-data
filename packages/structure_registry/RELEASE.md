# 化学结构管理发布：structure-registry-foundation-1.0.1

状态：**PUBLISHED / LOCKED**

包路径：`packages/structure_registry/`

本版本是 `structure-foundation-1.0.0` 在包重命名后的**契约与可追溯性修正版本**。现有 87 条 canonical Structure 的化学身份保持不变，不重新分配 `structure_id`，不改变已验证的 SMILES / InChI / InChIKey。

Schema：

- `structure-record 1.2.0`
- `structure-link 1.2.0`
- `structure-deferral 1.1.0`
- `structure-request 1.2.0`

本次 schema patch 主要修正 `structure_registry` 路径身份，并允许 `structural_chemistry` 作为正式 requester track。

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

## v1.0.1 审计修正

- 包内 4 个 JSON Schema `$id` 全部切换到 `packages/structure_registry/schema/`。
- `structure-request`、`structure-link`、`structure-deferral` 正式支持 `structural_chemistry` requester。
- link / deferral 的 repo-relative evidence 从已删除的 `packages/structure/...` 修正为 `packages/structure_registry/...`。
- strict validator 新增 schema identity 与 evidence-path existence 检查。
- manifest dataset identity 改为 `chem-knowledge-data/structure_registry`。
- 发布版本统一为 `structure-registry-foundation-1.0.1`。
- 移除会覆盖当前 canonical data / manifest 的历史 `build_seed.py` 活动入口及对应 obsolete seed evidence。
- 新增 `coordination/claims/structure_registry.yaml`，正式登记本包 ownership。

## 完整性门禁

严格 validator 检查：

- JSON Schema 与 schema `$id`
- deterministic Structure / link / deferral IDs
- duplicate Structure IDs、InChIKeys、external IDs
- SMILES parse / sanitization
- formula 与 formal-charge consistency
- Standard InChI / InChIKey consistency
- formula-unit no-fake-molecule rule
- polymer repeat-unit attachment points 与 deterministic fallback identity
- accepted-link target existence / scope
- repo-relative evidence path 存在性
- frozen Organic / Inorganic coverage completeness
- manifest dataset identity、counts、per-file record counts 与 SHA-256

## 发布边界

`packages/structure_registry/**` 继续作为 locked canonical owner。未来新增结构通过稳定的新实体 / structure request / 新证据触发增量 release。

其他包不得按 formula、SMILES 或外部 CID 自行重算并创建第二套 canonical `structure_id`。
