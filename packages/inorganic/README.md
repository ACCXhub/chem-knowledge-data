# Inorganic package

高中无机化学知识数据包。当前独立负责：

- 元素在高中无机体系中的教学投影；
- 单原子离子与常见多原子离子 / 原子团；
- 无机物质：单质、氧化物、酸、碱、盐及其他重要无机物；
- 无机反应、条件、净离子表示、现象、实验关联；
- 无机概念与高中教学标签；
- 对应来源、清洗规则与自动校验。

## v0.1 core seed

首批 canonical seed 共 **290 条**：

| 类型 | 数量 |
|---|---:|
| 元素教学投影 | 30 |
| 离子 / 原子团 | 40 |
| 无机物质 | 96 |
| 反应 | 61 |
| 现象 | 28 |
| 实验 | 12 |
| 概念 | 23 |

目录：

```text
packages/inorganic/
├── data/
├── schema/
├── sources/
├── validation/
├── DATA_POLICY.md
└── manifest.json
```

## Important boundaries

- 数据集稳定 `id` 是跨版本导入键，不替代主应用的 UUID typed IDs。
- `Reaction` 始终是一等实体 / 超边，反应参与者显式存储。
- 完整元素属性继续由主项目 M02 Element Data pipeline 负责；这里仅保存高中教学范围投影。
- 本阶段不进入有机、Structure、FunctionalGroup、Mechanism、atom mapping、bond diff 或 synthesis。

## Validate

从仓库根目录执行：

```bash
python packages/inorganic/validation/validate.py
```

当前校验覆盖全局 ID、引用完整性、盐/离子电荷、反应与净离子反应原子/电荷守恒、manifest 计数和 source key。

来源与许可策略见 `DATA_POLICY.md`、`sources/source_registry.json`。
