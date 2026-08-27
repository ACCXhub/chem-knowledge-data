# thermochemistry

高中化学物态与热化学数据包。

本包引用现有 consolidated `species_id`，不建立第二套 Substance / Ion / Structure / Reaction identity。

## Canonical data families

- `data/species_phase_facts.jsonl`：标准物态、可选教学物态与物态条件。
- `data/species_thermochemistry.jsonl`：`species_id + phase` 下的标准摩尔生成焓 `ΔfH°`、标准摩尔生成 Gibbs 能 `ΔfG°`、标准摩尔熵 `S°`、定压摩尔热容 `Cp°`。
- `data/phase_transitions.jsonl`：熔化、汽化、升华等相变焓。
- `data/bond_enthalpies.jsonl`：用于教学估算的键焓参考值。

## Consumer rule

反应热计算的优先级固定为：

1. 参与物种与物态均有 `ΔfH°` 时，使用标准生成焓求反应焓；
2. 物态变化后重新选择对应 `species_id + phase` 数据；
3. 仅在标准生成焓覆盖不足、且结构/键变化可解释时，才使用 `bond_enthalpies` 做近似估算；
4. 键焓结果必须标示为 estimate，不能与基于生成焓的 thermochemical result 混为一谈。

## Sources

首版机器数据使用固定版本的 Cantera/NASA thermodynamic datasets。Cantera 采用 BSD 3-Clause 风格许可证；NASA 多项式保留原始来源、源文件和系数备注。外部源只用于热化学事实，不取得本项目物种身份所有权。

## Standard state

首版计算基准为 `T = 298.15 K`、标准压力 `p° = 1 bar`。NASA 多项式的参考压力语义按来源保留；应用层若展示标准态，必须显示数据记录中的 reference condition。
