# STATUS

- package: `structural_chemistry`
- release: `structural-chemistry-v1.0.2`
- state: **READY_FOR_CONSOLIDATION**
- owner: `chatgpt-web-structural-chemistry`
- canonical records: **291**
- curriculum scope: 高中选择性必修“物质结构与性质”三个主题完整范围
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
- 11 个课程范围节点都有 coverage 证据；
- 第三主题固定覆盖多尺度结构、超分子、原子/分子光谱、X射线衍射、结构证据、结构模型演进和结构导向设计；
- 三个结构研究方法概念必须保留 IUPAC Gold Book 来源；
- 结构证据必须存在指向结构模型演进的 evidence-driven relation；
- manifest 计数与数据文件一致；
- 示例 formula 不作为 canonical identity。

当前包可作为 consolidation 输入；`packages/structure_registry/` 仍为 canonical `structure_id` owner。
