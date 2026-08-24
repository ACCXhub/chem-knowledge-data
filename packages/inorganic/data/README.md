# Inorganic data lifecycle

当前 `seed/` 中的记录是**候选种子数据**，用于先建立高中无机知识覆盖面和稳定实体身份，不等同于最终 published canonical 数据。

状态流：

`candidate → reviewed → published`

进入 `published` 前至少需要：

1. schema 校验；
2. 化学式、组成与电荷一致性校验；
3. 至少一个可追溯结构化来源完成字段核验；
4. 中文教学名称与高中课程语境复核；
5. 重复实体/别名冲突检查；
6. 涉及反应时完成元素守恒，离子反应同时完成电荷守恒。

当前并行阶段优先扩大正确覆盖面；跨无机/有机/结构的统一 ID 和最终 canonical merge 在 consolidation 阶段进行。
