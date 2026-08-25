# Release structural-chemistry-v1.0.2

高中结构化学数据包发布后质量审计修订。

## 本次修订

`v1.0.1` 已补齐教育部高中化学课程标准“物质结构与性质”的三个主题。本次不再扩展课程范围，只修两项质量问题：

1. 将原子光谱、分子光谱、X射线衍射三个结构研究方法概念的术语交叉核对提升到 IUPAC Gold Book；
2. 把课程标准中“物质结构认识随新的实验事实与研究技术不断发展”的要求落实为 `结构模型的演进` 概念，并建立 `结构证据 → 推动修正 → 结构模型演进` 的 typed relation。

validator 同步锁定上述 IUPAC provenance 和证据驱动模型演进关系，避免后续回归。

## 发布规模

- canonical records: **291**
- concepts: **62**
- relations: **70**
- exam tags: **26**
- curriculum scope nodes: **11**

## 边界

本修订只完善高中结构化学教学知识、来源质量和课程投影。`packages/structure_registry/` 仍是机器可用 Structure identity 与表示的 canonical owner；Substance/Ion/Reaction 等业务身份继续由对应包负责。
