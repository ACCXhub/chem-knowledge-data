# Structure 数据来源策略

## 来源职责

Structure record 保持来源中立。外部数据库提供证据，但不直接决定本数据集的 `structure_id`。

1. **PubChem**：提供广覆盖的化合物结构标识、CID 与结构证据。
2. **ChEBI**：提供人工整理的化学实体结构证据与交叉核验。
3. **Crystallography Open Database（COD）**：仅用于晶体结构（`crystal`）证据。
4. **IUPAC / InChI 标准**：提供结构标识标准；Standard InChI 使用 `InChI=1S/`。
5. **RDKit**：只用于规范化、校验和确定性派生，不作为事实权威来源。
6. **Organic / Inorganic 源数据包**：只提供跨包实体身份与结构需求，不成为第二个 Structure owner。

## 来源冲突处理

- 有实质性分歧时进入 `needs_review` 或显式 deferral；
- 任何来源都不能静默覆盖另一来源；
- 来源特有 payload 与说明性 prose 不直接进入 canonical record；
- canonical 字段保持精简，同时保留 source locator、retrieval context 与 provenance。

## 分子式规则

`molecular_formula` 用于机器比较，采用以下约定：

- Hill ordering；
- 形式电荷不写进 formula，而是单独存入 `formal_charge`；
- 聚合物 dummy attachment atom 不计入公式；
- 面向学生展示的常规化学式格式仍由 Organic / Inorganic 等知识包负责。

因此跨包比较优先使用 composition / 规范字段，而不是直接比较展示字符串。

## 结构范围规则

- `molecule`：离散中性分子实体。
- `ion`：离散带电实体。
- `formula_unit`：离子化合物 / 盐等的化学式单元；即使外部来源存在 disconnected salt SMILES，也不把它发布成 canonical molecular SMILES。
- `polymer_repeat_unit`：具有两个连接点的教学 / 拓扑重复单元，不代表完整聚合物分子。
- `coordination_entity`：有明确证据支持的金属—配体连接实体。
- `crystal`：有晶体学证据支持的晶体结构记录。
- `other`：经过人工审核的特殊结构范围。

## 聚合物规则

当教学身份与重复连接方式明确时，可以发布 polymer repeat unit。

完整 polymer identity 只有在链长、端基以及相关 stereochemistry / tacticity 状态都明确时才可以进一步发布。否则保持 deferral。重复单元本身有意不使用 Standard InChI / InChIKey 来冒充完整聚合物分子身份。
