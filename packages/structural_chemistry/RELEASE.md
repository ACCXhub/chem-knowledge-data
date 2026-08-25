# Release structural-chemistry-v1.0.1

高中结构化学数据包的课程范围完整性修订。

## 本次修订

`v1.0.0` 已建立原子结构、化学键、VSEPR/杂化、分子结构与极性、分子间作用力、晶体、配位与结构—性质关系的主干数据。本次复核发现教育部高中化学课程标准“物质结构与性质”的第三主题“研究物质结构的方法与价值”尚未形成独立 curriculum projection。

`v1.0.1` 补齐：

- 原子—分子—超分子—聚集态多尺度结构；
- 超分子结构教学概念；
- 原子光谱、分子光谱、X射线衍射等结构研究方法；
- 实验事实/测量证据与结构模型的关系；
- 结构—性质知识服务新物质、新材料设计的教学关系；
- 对应 typed relations、exam tags、curriculum scope 与 coverage evidence。

## 发布规模

- canonical records: **289**
- concepts: **61**
- relations: **69**
- exam tags: **26**
- curriculum scope nodes: **11**

## 边界

本修订只完善高中结构化学教学知识与课程投影。`packages/structure_registry/` 仍是机器可用 Structure identity 与表示的 canonical owner；Substance/Ion/Reaction 等业务身份继续由其对应包负责。
