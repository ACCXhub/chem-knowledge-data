# Structure track contract

`packages/structure/` 是仓库内 chemical Structure 的 canonical owner。

## Write ownership

只有 Structure workstream 修改 `packages/structure/**`。其他 workstream 可以读取 published `structure_id`、accepted links 与 deferrals，但不复制或重建 canonical SMILES / InChI / InChIKey。

## Owned data

Structure owns:

- source-neutral deterministic `structure_id`
- structure scope 与 formal charge
- discrete molecule / ion 的 canonical + isomeric SMILES
- Standard InChI / InChIKey（适用时）
- formula-unit identity（不把离子晶体伪装成分子）
- teaching-level polymer repeat-unit abstraction
- deterministic derived descriptors
- external structure identifiers 与 provenance
- Structure-side cross-track link acceptance
- unresolved structure deferrals

Structure does not own curriculum taxonomy, canonical Substance teaching names, Reaction, Experiment, Phenomenon, Concept, Question or ExamTag.

## Public cross-track seam

稳定读取面：

- `structure_id`
- `structure_scope`
- `molecular_formula`
- `formal_charge`
- canonical/isomeric SMILES when applicable
- Standard InChI/InChIKey when applicable
- `repeat_unit_smiles` + attachment points for polymer repeat units
- validation/review status
- external IDs/provenance
- accepted `entity_ref ↔ structure_id` links
- explicit deferrals

调用方保存 `structure_id`，不复制完整 Structure record。

## Identity

External IDs such as PubChem CID, ChEBI ID or COD ID are evidence, never canonical IDs.

1. 有 valid Standard InChI：`structure_id = UUIDv5(frozen_namespace, "inchi:" + StandardInChI)`。
2. 无 Standard InChI 的受控抽象（例如 polymer repeat unit）：使用 scope + normalized representation + formal charge 生成 deterministic UUIDv5。
3. 同一 representation 必须稳定生成相同 ID。

Frozen namespace:

`c9d2c469-8557-5661-ae35-950cde95e61f`

## Structure scopes

- `molecule`
- `ion`
- `formula_unit`
- `polymer_repeat_unit`
- `coordination_entity`
- `crystal`
- `other`

### Formula unit

化学式不是分子结构。NaCl、Na2SO4、sodium oleate 等离子型实体可发布 formula-unit identity / InChI，但 canonical molecular SMILES 保持为空。

### Polymer repeat unit

Repeat unit 使用两个 dummy attachment points 表示链连接位点，例如 polyethylene `*CC*`。它只是教学/拓扑抽象：

- 不代表完整 polymer molecule；
- 不声明 chain length / molecular weight / terminal groups；
- tacticity 或 stereochemical information 未定义时保持未定义；
- Standard InChI/InChIKey 不用于 repeat-unit identity。

## Source/normalization policy

- PubChem：结构标识与外部 CID 证据。
- ChEBI：curated cross-check。
- COD：crystal scope。
- InChI standard：标准结构标识。
- RDKit：normalization/validation/descriptor tool，不是 authority source。
- Organic/Inorganic 源包只提供跨包 identity/coverage demand；它们不成为 Structure representation 的第二 canonical owner。

## Publication

只有 `validation.status == valid` 且 `validation.review_status == published` 的 record 可作为 accepted link target。

Source conflict、stereo ambiguity、heterogeneous/macromolecular identity 等不能静默猜测，必须留下 explicit deferral。

## Parallel work

Organic / Inorganic 可以提出 structure demand；最终 structure record、scope、ID 和 accepted link 由本包拥有。Consolidation 消费这些结果，不反向改写 Structure identity。
