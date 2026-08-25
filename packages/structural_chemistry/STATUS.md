# Structural Chemistry 状态

**状态：** ACTIVE / FOUNDATION_BUILD

**Owner：** `chatgpt-web-structural-chemistry`

**写入范围：** `packages/structural_chemistry/**`

**版本：** `structural-chemistry-foundation-0.1.0`

## 当前目标

建立与其他数据包同等级的高中结构化学知识底座，覆盖：

- 原子轨道、能层能级与核外电子排布；
- 原子结构与元素性质的结构解释；
- 共价键、σ/π 键、键长/键角/键能、电负性与键极性；
- VSEPR、杂化、分子空间构型、极性与手性；
- 分子间作用力；
- 基础晶体类型、晶胞与堆积模型；
- 配位键、配体、配位数、简单配合物与超分子基础；
- 结构—性质关系与常见误区。

## 已锁定边界

`packages/structure_registry` 是可计算 Structure identity 的唯一 owner。本包只引用已发布 `structure_id`，不会另建 SMILES/InChI canonical truth。

`inorganic` / `organic` / `structure_registry` / `consolidated` 均作为只读输入；上游临时 review/hold 状态在发布时重新核验，不复制为本包长期事实。

## 完成标准

foundation release 需满足：

- 主课程主题全覆盖；
- 核心概念与代表性例子具有 source refs；
- geometry / crystal / coordination 等数据结构稳定；
- ID、topic、source、relation 引用可校验；
- 没有把经验规则写成无条件绝对规律；
- 没有复制教材正文、图像或第三方视觉资产；
- 包内 validator 与专属 CI 通过。
