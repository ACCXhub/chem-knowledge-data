# Structure 数据许可与署名说明

本包保存来源中立的结构事实记录，并为每条记录保留 provenance。

- **ChEBI**：作为证据使用的内容受 **CC BY 4.0** 署名要求约束。
- **Crystallography Open Database（COD）**：数据库数据按 **CC0** 分发；即使数据本身为 CC0，仍应在 provenance 中保留原始晶体学文献 / 作者信息。
- **RDKit**：代码与工具采用 BSD-3-Clause，仅用于可复现的结构派生与校验。
- **PubChem**：作为结构与标识符事实证据来源使用；canonical 数据集不复制其说明性 prose、图片或 depositor-specific expressive content。

每条 canonical record 都保留字段级或记录级来源信息。新增来源时，应同步更新 `sources/registry.json`，并在导入可再分发内容前核对该来源当前有效的许可与使用条款。
