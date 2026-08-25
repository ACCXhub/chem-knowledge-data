# Structure 数据流水线

本目录负责 Structure 数据的抓取、规范化、ID 生成与确定性构建。流水线本身保持来源中立。

- `ids.py`：生成数据集内部的确定性 ID。
- `fetch_pubchem.py`：可选的 PubChem 证据抓取器；只抓 evidence，不直接写 canonical 数据。
- `normalize_rdkit.py`：解析 / sanitize 离散结构，并生成 Standard InChI / InChIKey、canonical / isomeric SMILES、Hill/no-charge formula、formal charge 与确定性描述符。
- `non_discrete.py`：处理 formula unit、polymer repeat unit 等非普通离散分子结构范围。
- `build_release.py`：从仓库内固定的 evidence 与跨包目标重建当前完整 Structure foundation release。
- `build_seed.py`：历史兼容入口；保留旧文件名，但现在指向完整 foundation rebuild，而不是早期 33 条 seed。

## 重建

```bash
python packages/structure/pipelines/build_release.py
python packages/structure/validation/validate_dataset.py --strict
python -m unittest discover -s packages/structure/tests -v
```

重建当前发布版不依赖网络连接，因为发布所需的最小来源证据已经固定在 `packages/structure/sources/` 中。

## 新数据进入规则

网络新抓取的数据不能自动进入 `published`：

1. 先保存为 source evidence；
2. 经过规范化与化学校验；
3. 处理来源冲突与结构歧义；
4. 通过 review；
5. 最后才进入 canonical release 与跨包 accepted link。

这样外部 API 的变化不会直接污染已发布的 Structure 数据。
