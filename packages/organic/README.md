# Organic package

高中有机化学知识数据包，当前版本 **v0.2.0**。

本包按中国高中化学课程范围组织有机化学知识，后续由 consolidation 与 `packages/inorganic/**`、`packages/structure/**` 对齐统一 ID、结构链接和跨包物种引用。

## 覆盖内容

- 有机物身份、别名、分子式与教学分类；
- 官能团与 C=C / C≡C 等课程结构特征；
- 烃、烃的衍生物、糖类、氨基酸/蛋白质、油脂、核酸；
- 同分异构、顺反异构、简单命名与有机结构确定；
- 质谱、红外光谱、核磁共振氢谱及多证据结构推断；
- 取代、加成、消去、氧化、酸碱、酯化、水解、发酵、加聚和缩聚等代表性反应；
- 有机合成路线、单体/链节、聚合物结构—性质与材料类别；
- 实验、宏观现象、概念与课程覆盖证据；
- PubChem / ChEBI 等外部身份交叉引用和 provenance。

当前规模、复核结果和质量门见 [`STATUS.md`](STATUS.md)，机器可读入口见 [`package.yaml`](package.yaml)。

## 数据入口

- `data/curriculum_coverage.yaml`：可度量的课程采集边界；
- `data/coverage_evidence.yaml`：课程要求到实体/关系的覆盖证据；
- `data/*substances.yaml`：代表性有机物；
- `data/*reactions.yaml`：代表性反应与条件；
- `data/concepts.yaml`、`data/structure_concepts.yaml`、`data/biomolecule_concepts.yaml`、`data/applied_concepts.yaml`：概念网络；
- `data/experiments.yaml`、`data/phenomena.yaml`：实验与宏观现象；
- `data/identity_crossrefs.yaml`：外部身份的唯一包内 owner；
- `data/identity_deferrals.yaml`：结构/立体化学/聚合物等需要跨包统一的问题；
- `sources/registry.yaml`：数据源角色与使用边界；
- `schema/`：数据与元数据 JSON Schemas；
- `validation/`：结构、引用、身份、分子式、反应守恒和清单校验。

## 数据边界

Canonical SMILES、InChI/InChIKey、SMARTS、构象、立体化学规范化和结构派生描述符由 `packages/structure/**` 负责。无机反应参与物使用跨包 species key，统一实体 ID 由 consolidation 解析。

分子式只表达组成，不作为 chemical identity；因此正丁烷/异丁烷、顺反 2-丁烯、乙酸/甲酸甲酯、葡萄糖/果糖以及淀粉/纤维素保持独立实体。蛋白质、核酸和复杂材料以适合高中知识图谱的类别/概念表达，具体离散结构交给相应 canonical owner。

## 验证

```bash
python -m pip install -r packages/organic/validation/requirements.txt
python packages/organic/validation/validate_package.py
python packages/organic/validation/validate_identity_coverage.py
python packages/organic/validation/validate_manifest.py
```

GitHub Actions `Validate organic package` 对同一组质量门执行持续验证。v0.2 完成后本包进入只读状态，等待 consolidation。
