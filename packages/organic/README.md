# Organic package

高中有机化学知识数据包，当前版本 **v0.1.0 / COMPLETE**。

本包按中国高中化学课程范围独立整理，之后再与 `packages/inorganic/**` 和 `packages/structure/**` 做统一 ID、结构链接和跨包物种对齐。

## 覆盖内容

- 有机物与教学分类；
- 官能团与不饱和结构特征；
- 烃、烃的衍生物、糖类、氨基酸/蛋白质、油脂、核酸概念；
- 加成、取代、消去、氧化、酯化、水解、发酵、加聚和缩聚等高中代表性反应；
- 实验、宏观现象、概念与课程覆盖关系；
- PubChem / ChEBI 等外部身份交叉引用；
- provenance、JSON Schema、引用完整性和课程覆盖校验。

当前规模与验证结果见 [`STATUS.md`](STATUS.md)，机器可读入口见 [`package.yaml`](package.yaml)。

## 数据入口

- `data/curriculum_coverage.yaml`：课程采集边界；
- `data/coverage_evidence.yaml`：课程要求到具体实体/关系的覆盖证据；
- `data/*substances.yaml`：代表性有机物；
- `data/*reactions.yaml`：反应关系；
- `data/concepts.yaml`、`data/structure_concepts.yaml`、`data/biomolecule_concepts.yaml`：概念网络；
- `data/experiments.yaml`、`data/phenomena.yaml`：实验与宏观现象；
- `data/identity_crossrefs.yaml`：已核验外部身份；
- `data/identity_deferrals.yaml`：明确留给结构/合并阶段处理的身份问题；
- `sources/registry.yaml`：数据源及用途；
- `schema/`：包内 JSON Schemas；
- `validation/`：自动校验。

## 边界

Canonical SMILES、InChI/InChIKey、SMARTS、构象和结构派生描述符由 `packages/structure/**` 负责；无机反应物/产物暂以跨包 key 引用；本包不从方程式推断 atom mapping、bond diff 或 mechanism。

分子式不是化学实体身份，因此同分异构体以及淀粉/纤维素等相同经验式记录不会被自动合并。蛋白质、核酸和复杂材料也不会为了“填数据”而伪造单一固定分子式。

## 验证

```bash
python -m pip install -r packages/organic/validation/requirements.txt
python packages/organic/validation/validate_package.py
python packages/organic/validation/validate_identity_coverage.py
```

GitHub Actions `Validate organic package` 已对 v0.1 数据闭环通过验证。当前包保持只读，等待后续 consolidation。
