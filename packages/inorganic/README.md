# Inorganic package

高中无机化学 consumer-ready canonical data package。

当前 v1 构建范围：

`Element teaching projection → Ion / polyatomic group → Substance → Reaction → Phenomenon / Experiment → Concept → ExamTag`

并附带 Equation Lab / Reaction Builder 可直接消费的规则层。

## v1 release candidate

| 类型 | 数量 |
|---|---:|
| 元素教学投影 | 48 |
| 离子 / 原子团 | 57 |
| 无机物质 | 194 |
| 反应 | 151 |
| 现象 | 63 |
| 实验 | 31 |
| 概念 | 64 |
| 考点标签 | 32 |
| **canonical records** | **640** |

另外包含 7 组规则数据：

- 溶解性；
- 强弱电解质 / 离子方程式拆写；
- 常见氧化态；
- 金属活动性；
- 焰色试验；
- 常见离子/气体定性检验；
- Equation Lab 受控组合与 palette。

## Layout

```text
packages/inorganic/
├── data/                       # v0.1 base + v1 extensions
├── rules/                      # consumer rule projections
├── curriculum/                 # 高中课程覆盖映射
├── schema/                     # machine-readable contracts
├── sources/                    # source registry + source review
├── validation/                 # chemistry/reference validators
├── DATA_POLICY.md
├── IMPORT_CONTRACT.md
├── STATUS.md
└── manifest.json
```

## Canonical boundaries

- `Reaction` 始终是一等实体，反应物/生成物由 participant 列表表达，不把反应退化成 `Substance → Substance` 普通边。
- dataset `id` 是跨版本稳定导入键；主应用仍把它映射到已有 typed UUID identity。
- 完整 Element 权威事实继续由主应用 M02 Element Data pipeline 拥有，本包只提供高中教学投影。
- `packages/organic/` 和 `packages/structure/` 分别拥有有机知识和结构 canonical identity；本包不复制它们。
- Mechanism、atom mapping、bond diff 不由无机 v1 推测生成。
- `exam_tag` 是稳定教学标签，不代表真实高考概率或动态 ExamHeat。

## Equation Lab contract

无机 v1 支持结构化方程式输入：

1. 默认 palette 展示高中常见元素、离子/原子团和高频无机物种；其余元素通过展开/搜索获取。
2. 离子化合物根据 canonical charge 计算最简电中性整数比，多原子团在需要时自动加括号。
3. Fe、Cu、Mn、Cr、Sn、Pb 等多价元素返回 canonical 候选，不自动猜唯一价态。
4. 共价物种只从 canonical species 候选库选择，不根据任意元素组合凭空造分子。
5. molecular / ionic / net-ionic 三种模式使用不同 projection；离子拆写同时受相态、强弱电解质和溶解性规则约束。
6. 存储层保持 ASCII 化学式；前端负责数字下标、电荷上标和相态排版。

## Validate

```bash
python packages/inorganic/validation/validate_v1.py
```

v1 validator 覆盖：全局 ID、source key、跨实体引用、离子投影电荷/组成、反应原子与总电荷守恒、净离子守恒、双向 phenomenon 引用、experiment/concept/exam-tag 引用、rule/coverage 引用和 manifest 计数。

来源与许可边界见 `DATA_POLICY.md`、`sources/source_registry.json` 与 `sources/SOURCE_REVIEW.md`。
