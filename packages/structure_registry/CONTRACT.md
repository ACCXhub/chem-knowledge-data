# 结构数据包契约

`packages/structure/` 是仓库内**化学结构数据**的唯一规范来源（canonical owner）。这里负责机器可用的结构表示与结构身份，不负责高中“结构化学”课程知识。

## 写入权限

只有 Structure 工作流可以修改 `packages/structure/**`。

其他工作流可以读取已经发布的 `structure_id`、已接受的链接（accepted links）和延期记录（deferrals），但不能复制或重新生成 canonical SMILES、InChI、InChIKey，也不能建立第二套结构身份。

## 本包负责的数据

Structure 负责：

- 与外部数据库无关、可稳定重建的 `structure_id`；
- 结构范围（`structure_scope`）与形式电荷（`formal_charge`）；
- 离散分子 / 离子的 canonical SMILES 与 isomeric SMILES；
- 适用时的 Standard InChI / InChIKey；
- 化学式单元（`formula_unit`）身份，避免把离子晶体伪装成分子；
- 教学级聚合物重复单元（`polymer_repeat_unit`）抽象；
- 可确定性重建的结构描述符；
- 外部结构数据库 ID 与来源追踪（provenance）；
- 其他数据包实体与 `structure_id` 的正式接受关系；
- 无法安全归一化时的显式延期记录。

本包**不负责**：课程分类、Substance 的中文教学名称、Reaction、Experiment、Phenomenon、Concept、Question、ExamTag，也不负责高中结构化学知识点。

## 对外稳定读取接口

其他数据包可以稳定读取：

- `structure_id`
- `structure_scope`
- `molecular_formula`
- `formal_charge`
- 适用时的 canonical / isomeric SMILES
- 适用时的 Standard InChI / InChIKey
- 聚合物重复单元的 `repeat_unit_smiles` 与连接点
- 校验状态与审核状态
- 外部 ID 与 provenance
- 已接受的 `entity_ref ↔ structure_id` 链接
- 显式 deferral

调用方只保存 `structure_id` 或正式 link，不复制完整 Structure record 作为自己的真值。

## 结构身份规则

PubChem CID、ChEBI ID、COD ID 等都只是外部证据，不是本数据集的 canonical ID。

1. 有有效 Standard InChI 时：`structure_id = UUIDv5(frozen_namespace, "inchi:" + StandardInChI)`。
2. 没有 Standard InChI 的受控抽象（例如聚合物重复单元），使用 `structure_scope + normalized representation + formal_charge` 生成确定性 UUIDv5。
3. 同一规范表示必须始终生成同一个 `structure_id`。

固定命名空间：

`c9d2c469-8557-5661-ae35-950cde95e61f`

## 结构范围

- `molecule`：离散中性分子
- `ion`：离散带电粒子
- `formula_unit`：离子化合物 / 盐等的化学式单元
- `polymer_repeat_unit`：聚合物重复单元
- `coordination_entity`：具有明确金属—配体连接关系的配位实体
- `crystal`：有晶体学证据的晶体结构
- `other`：经过审核的其他特殊情况

### 化学式单元（formula unit）

**化学式不等于分子结构。**

NaCl、Na₂SO₄、硬脂酸钠等离子型实体可以拥有 formula-unit identity / InChI，但不发布成“canonical molecular SMILES”，避免把晶格中的化学式单元误说成独立分子。

### 聚合物重复单元（polymer repeat unit）

重复单元使用两个 dummy attachment points 表示链连接位置，例如 polyethylene 的 `*CC*`。

它只是一种教学 / 拓扑抽象：

- 不代表完整聚合物分子；
- 不声明链长、分子量和端基；
- tacticity 或 stereochemistry 未确定时保持未定义；
- 重复单元不使用 Standard InChI / InChIKey 作为完整聚合物身份。

## 来源与规范化规则

- **PubChem**：提供广覆盖的结构标识与 CID 证据。
- **ChEBI**：提供人工整理的结构交叉核验。
- **COD**：仅用于晶体结构证据。
- **InChI 标准**：提供标准结构标识规则。
- **RDKit**：用于规范化、校验和描述符派生，不是事实权威来源。
- **Organic / Inorganic 数据包**：只提出跨包结构需求，不成为第二个 Structure owner。

## 发布规则

只有同时满足：

- `validation.status == valid`
- `validation.review_status == published`

的 Structure record 才能作为正式 accepted link 的目标。

遇到来源冲突、立体化学歧义、异质大分子身份等情况时，不得静默猜测；必须保留明确的 deferral 或 review 状态。

## 并行协作规则

Organic / Inorganic 可以提出结构需求；最终结构记录、scope、ID 和 accepted link 由本包统一维护。Consolidation 只消费这些已发布结果，不反向重建或改写 Structure identity。
