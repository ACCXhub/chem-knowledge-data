# Consolidation data

这里存放统一分支已经形成的稳定映射和预览数据；它们不是完整高中化学 release，直到 `packages/inorganic/` 达到 `READY_FOR_CONSOLIDATION`。

当前内容：

- `identity-map.jsonl`：已冻结的 source ID → consolidated UUID 映射；UUID 一经进入此文件后续不得重新生成。
- `organic-structure-links.jsonl`：Organic v0.1 与 published Structure 中通过同一已核验 PubChem CID 得到的确定性链接。
- `preview-manifest.json`：当前输入快照和完成度。

预览数据可以继续增量扩展，但不得冒充完整 consumer release。
