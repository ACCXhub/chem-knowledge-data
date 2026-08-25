# Data Policy

## Source hierarchy

1. **课程范围**：教育部《普通高中化学课程标准（2017年版2020年修订）》。
2. **原子基态电子排布**：NIST Periodic Table / NIST 原子数据。
3. **术语边界**：IUPAC Gold Book 独立术语页面。
4. **二次校验**：公开许可的通用化学教材/参考资料，只用于交叉核验事实，不复制教材正文。
5. **仓库内部结构身份**：只读使用 `packages/structure/` published release。

## Storage rules

- 只保存结构化事实、教学模型和短标签，不复制课程标准、教材或网站的长段正文/视觉资产。
- 每条记录保留 `source_refs`。
- 模型结论必须区分 `fact`、`teaching model`、`general trend`。
- 具有晶型/同分异构/配位水合差异的对象不得按 formula 去重。
- 不从 VSEPR 或杂化模型推导真实 Mechanism。
- 不把 `exam_tag` 解释成高考预测概率。

## Provenance

`source_refs` 连接 `sources/source_registry.json`。Consolidation 可以聚合来源，但不得覆盖或删除源记录 provenance。
