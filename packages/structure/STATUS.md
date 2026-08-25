# Structure 数据包状态

**状态：** COMPLETE_FOUNDATION_V1 / PUBLISHED / LOCKED（基础版完成 / 已发布 / 已锁定）

**Owner：** Structure canonical owner

**写入范围：** `packages/structure/**`

**发布版本：** `structure-foundation-1.0.0`

**发布日期：** 2026-08-25

## 当前完成情况

在目前已经稳定的跨包输入范围内，Structure 基础版已经完成：

- Organic v0.1：**50/50** 个实体都已经由完整身份 link 或显式 deferral 交代；
- 当前 Inorganic 离子 seed：**23/23** 个离子已经建立结构链接；
- 共发布 **87** 条 canonical Structure：46 个分子、24 个离子、12 个化学式单元、5 个聚合物重复单元；
- canonical 数据可以由固定证据确定性重建；
- molecule、ion、formula unit、polymer repeat unit 具有明确不同的语义；
- 立体化学、完整聚合物、大分子身份等未解决情况使用显式 deferral，不通过猜测补齐；
- 下游工作流已有稳定的 link / deferral 接口。

## 最新验证

工作分支 GitHub Actions 运行 `32809697660` 成功；Pull Request 运行 `32809798607` 又独立重建了一次完整发布数据，并在合并前通过了“生成结果无 diff”的可复现性检查。

```text
built 87 structures; inorganic links=23; organic links=46; organic deferrals=9
OK: formula_unit=12, ion=24, molecule=46, polymer_repeat_unit=5; total=87; unique_ids=87; inorganic=23/23; organic=50/50
Ran 16 tests
OK
```

PR #3 已 squash merge 到 `main`，合并提交为 `db02499d04475b3f710e7399b4e0a3dbaeea198e`。合并后重新核对 `main` 的 canonical manifest，确认：dataset version=`structure-foundation-1.0.0`、schema=`1.2.0`、总记录数=87、Inorganic link=23、Organic link=46、Organic deferral=9。

## 后续按证据增量扩展的内容

下面这些不是当前基础版“漏做”，而是需要后续证据或正式请求后再新增：

- Inorganic 工作流今后发布的新稳定 Substance 对应结构；
- 没有明确金属—配体连接证据的配位实体；
- 没有晶体学证据 / 请求的 crystal record；
- 链长、端基、tacticity 未指定时的完整 polymer identity；
- 教学实体身份尚未固定时的 fructose / alanine 等立体化学表示。

其他工作流继续把 `packages/structure/**` 视为只读，通过文档约定的 integration seam 使用已发布的 `structure_id`、link 和 deferral。
