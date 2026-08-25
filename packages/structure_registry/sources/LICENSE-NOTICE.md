# 化学结构管理数据许可与署名说明

Structure Registry 保存 source-neutral 的事实型化学结构记录及 provenance。

- ChEBI 作为 evidence 使用的材料遵循 **CC BY 4.0** 署名要求。
- Crystallography Open Database 数据以 **CC0** 分发；即使 COD 数据本身为 CC0，provenance 中仍应保留原始晶体学作者 / 文献归属。
- RDKit 代码 / 工具遵循 BSD-3-Clause，仅用于可重复的 derivation 与 validation。
- PubChem 用作事实型 structure / identifier evidence source；canonical dataset 不复制其来源 prose、images 或 depositor-specific expressive content。

每条 canonical record 保留相应 source provenance。新增来源时必须更新 `sources/registry.json`，并在导入可再分发内容前重新确认其当前许可条件。
