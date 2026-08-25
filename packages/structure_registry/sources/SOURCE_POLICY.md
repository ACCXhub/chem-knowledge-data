# 化学结构管理来源策略

## 权威角色

Structure Registry 的 canonical records 保持 source-neutral：外部数据库提供 evidence，不直接定义 dataset IDs。

1. **PubChem**：广覆盖的 compound structure identifiers 与 CID evidence。
2. **ChEBI**：curated entity structure evidence / cross-check。
3. **Crystallography Open Database (COD)**：仅用于 crystal-scope evidence。
4. **IUPAC / InChI standard**：结构标识标准；Standard InChI 使用 `InChI=1S/`。
5. **RDKit**：normalization、validation 与 deterministic derivation 工具，不是 authority source。
6. **Organic / Inorganic / Structural Chemistry source packages**：只提供跨包 identity / coverage demand，不成为竞争性的 Structure owner。

## 冲突策略

- 实质性来源冲突进入 `needs_review` 或 explicit deferral。
- 一个来源不能静默覆盖另一个来源。
- source-specific payload 与描述性 prose 保留在 canonical records 之外。
- canonical factual fields 保持最小，并保留 source locator / retrieval context。

## Formula policy

`molecular_formula` 用于机器比较：

- Hill ordering；
- formal charge 不写进 formula，而是单独保存；
- dummy attachment atoms 不计入 formula；
- 面向用户的常规化学式显示由 Organic / Inorganic / Structural Chemistry 等教学知识包负责。

跨包公式比较因此基于组成语义，而不是直接比较显示字符串。

## Scope policy

- `molecule`：离散中性分子实体。
- `ion`：离散带电实体。
- `formula_unit`：离子型 / 盐类的化学式单元；disconnected salt SMILES 不作为 molecular canonical SMILES 发布。
- `polymer_repeat_unit`：具有两个 attachment points 的教学 / 拓扑重复单元，不是完整 polymer molecule。
- `coordination_entity`：有明确 metal-ligand connectivity evidence 的配位实体。
- `crystal`：有 crystallographic evidence 的晶体结构记录。
- `other`：经审核的例外 scope。

## Polymer policy

当教学身份与 repeat connectivity 明确时可以发布 polymer repeat unit。若 chain length、terminal groups、relevant stereochemistry / tacticity 尚未固定，完整 polymer identity 保持 deferred。Repeat unit 不分配 Standard InChI / InChIKey。
