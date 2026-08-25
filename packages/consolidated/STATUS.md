# Consolidated status

**State:** `ACTIVE / INPUTS-READY / BUILDING-FIRST-CONSUMER-RELEASE`

**Owner:** `chatgpt-web-consolidation`

## 已确认输入

- Inorganic v1.0.1：`READY_FOR_CONSOLIDATION`，642 canonical records。
- Organic v0.2.0：完整性复核完成，57 substances / 31 reactions 等稳定输入。
- Structure Registry：`structure-registry-foundation-1.0.1`，87 published Structure；accepted links 为 consolidation 的唯一 Structure 关联来源。
- Structural Chemistry：`structural-chemistry-v1.0.2`，291 canonical records，`READY_FOR_CONSOLIDATION`。

## 当前 Delta

此前 consolidation 仍按“等待无机 + Organic v0.1 + packages/structure”设计。仓库已发生三个关键变化：

1. 无机已经完成 v1.0.1；
2. Organic 已完成 v0.2.0；
3. 原 Structure 包已拆为 `structure_registry` 与 `structural_chemistry`。

当前工作因此转入首个真实 consumer release 的生成与验证，不再停留在 contract-only 阶段。

## 当前 Deliverables

- source snapshot/version pin；
- consumer species + source crosswalk；
- accepted Structure link projection；
- Reaction participant 跨包解析；
- teaching/search/Equation Lab Palette projection；
- non-species knowledge envelope/index；
- rules/curriculum consumer bundle；
- unresolved findings；
- deterministic manifest/hash；
- consolidated validation workflow。

## 发布门禁

首个 release 只有在以下条件全部满足后才进入 `READY_FOR_APP_IMPORT`：

- 所有发布 species 均可回溯到源记录；
- Reaction 必需 participant 全部解析到 consolidated species；
- Structure link 仅指向已发布 `structure_registry` 记录；
- crosswalk 无一源 ID 多目标冲突；
- formula/name 相似项不会被静默自动合并；
- teaching/search projection 不含用户运行时偏好；
- generated manifest 的 counts/hash 与文件实际内容一致；
- validator 零 blocking error。
