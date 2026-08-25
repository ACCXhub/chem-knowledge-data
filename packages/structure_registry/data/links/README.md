# 已接受的实体 ↔ Structure 链接

本目录保存其他知识包实体与 Structure Registry 中 canonical `structure_id` 的稳定映射。

当前正式文件：

- `inorganic.jsonl`
- `organic.jsonl`

调用方应使用这些 accepted links，而不是根据 formula、SMILES 或外部数据库 ID 自行重建 `structure_id`。

新增实体缺少结构时，在调用方自己的工作区按 `../../schema/structure-request.schema.json` 提交 request，由 Structure Registry owner 统一处理并发布新的 accepted link。
