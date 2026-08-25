# Structural Chemistry 状态

**状态：** ACTIVE / FOUNDATION_BUILD

**Owner：** `chatgpt-web-structural-chemistry`

**写入范围：** `packages/structural_chemistry/**`

**版本：** `structural-chemistry-foundation-0.1.0`

## 当前目标

建立与其他数据包同等级的高中结构化学知识底座，覆盖：

- 原子结构与元素性质的结构解释；
- 共价键、σ/π 键、键极性；
- VSEPR、杂化、分子空间构型与极性；
- 分子间作用力；
- 四类基础晶体模型；
- 配位键、配体、配位数与简单配合物；
- 结构—性质关系与常见误区。

## 已锁定边界

`packages/structure` 仍是可计算 Structure identity 的唯一 owner。本包只引用已发布 `structure_id`，不会另建 SMILES/InChI canonical truth。

`inorganic` / `organic` / `consolidated` 均作为只读输入。

## 完成标准

foundation release 需满足：

- 主课程主题全覆盖；
- 核心概念与代表性例子具有 source refs；
- geometry / crystal / coordination 数据结构稳定；
- ID、topic、source、relation 引用可校验；
- 没有把经验规则写成无条件绝对规律；
- 没有复制教材正文、图像或第三方视觉资产。
