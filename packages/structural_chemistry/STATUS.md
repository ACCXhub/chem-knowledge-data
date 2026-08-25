# STATUS

- package: `structural_chemistry`
- release: `structural-chemistry-v1.0.0`
- state: **READY_FOR_CONSOLIDATION**
- owner: `chatgpt-web-structural-chemistry`
- canonical records: **269**
- curriculum scope: 高中选择性必修“物质结构与性质”核心范围
- atomic configurations: 1—36 complete
- blockers: none

## Validation gates

- 全局本包 ID 唯一；
- source key 全部存在；
- 11 个 canonical record family schema 均存在；
- 1—36号原子序数完整且唯一；
- Cr / Cu 特殊电子排布显式保留；
- concept relation 引用全部可解析；
- bonding interaction concept / scope 全部可解析；
- VSEPR AXE pattern 唯一且电子域计数自洽；
- structure-property general trend 必须带 qualifier；
- exam tag concept refs 可解析；
- 8 个课程范围节点都有 coverage 证据；
- manifest 计数与数据文件一致；
- 示例 formula 不作为 canonical identity。

当前包可作为 consolidation 新输入；`packages/structure_registry/` 仍为 canonical `structure_id` owner。
