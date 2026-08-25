# 化学结构管理流水线

本目录负责 Structure Registry 的确定性结构处理，边界保持 source-neutral。

- `ids.py`：生成稳定 dataset IDs。
- `fetch_pubchem.py`：可选的 evidence fetcher；不会直接写 canonical data。
- `normalize_rdkit.py`：解析 / sanitize 离散结构，生成 Standard InChI/InChIKey、canonical/isomeric SMILES、Hill/no-charge formula、formal charge 与确定性 descriptors。
- `build_release.py`：从仓库内 pinned evidence 重建完整 foundation release。
- `build_seed.py`：历史兼容入口。

## 重建

```bash
python packages/structure_registry/pipelines/build_release.py
python packages/structure_registry/validation/validate_dataset.py --strict
```

重建已提交的 foundation 不要求联网，因为最小证据已经固定在 `sources/` 中。

新抓取的数据不会自动发布；新 evidence 先进入 draft / review，只有经过校验与审核的记录才成为跨包稳定引用。

本目录属于“化学结构管理”，不是高中“结构化学”教学内容。
