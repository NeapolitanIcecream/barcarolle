# Selector Algorithm Bakeoff Story

生成日期：2026-06-14

## 这次试了什么

本次 bakeoff 实现并比较了 RSQ v2、FLC、HRD v3、COD-lite、RO-LSP、SAES-lite，以及 uniform、quality-filtered、source/recency stratified、module stratified random baselines。

主 gate 改成 Agent 选型决策质量：Selection 是否能推荐一个 Agent，later/Holdout 是否验证这个选择。MAE 仍然报告，但不是硬 veto。

## 开发集结果

开发 bakeoff 的 winner 是 `cod_lite`。它在 development sources 上的 validated recommendation rate 是 `1.0`，recommendation coverage 是 `1.0`，false-recommendation rate 是 `0.0`。它的 MAE 是 `0.142087`，强 random MAE mean 是 `0.150765`，相对改善 `5.756%`。

HRD v3 `70/30` 是 backup。它的 MAE 更好，`0.122643`，相对强 random 改善 `18.65%`，但 validated recommendation coverage 只有 `0.666667`。因此最终选择 `cod_lite`，理由是它更符合“能不能帮 demo 用户做 Agent 选择”的主目标。

## 最终 no-paid replay

最终 replay 使用没有参与阈值和 variant 选择的 `phase1_original_three_repo_split_heldout`，标记为 limited no-paid final replay。最终 selector 是 `cod_lite`，k=`10` per repo，决策规则是 wrapper v2：

- action margin: `0.10`
- min common valid: `8`
- lcb tolerance: `0.10`
- tie epsilon: `0.05`
- 不要求 zero loss

Selection 推荐 `kilo_workspace`。Selection 通过率为 Codex `6/27`，Kilo `17/27`。later/Holdout 通过率为 Codex `16/40`，Kilo `22/40`。推荐 regret 是 `0.0`，top-pair direction agreement 为 `True`。

## Random baseline 和 MAE

最终 replay 没有严格打败最强 decision random baseline。最强 random decision baseline 是 `source_recency_stratified_random`，validated recommendation rate 也是 `1.0`，false-recommendation rate 也是 `0.0`，mean regret 也是 `0.0`。因此最终结论是 tie，不是 strict beat。

MAE 也没有赢：selector MAE `0.128704`，强 random MAE mean `0.106711`，相对改善 `-20.61%`，MAE beats/ties random share `0.209`。

## 现在能讲什么

可以讲：在一个 limited no-paid final replay 上，Barcarolle 的 selector + wrapper v2 给出了 Agent 推荐，并且 later/Holdout 验证了这个推荐；Kilo 是 Selection 和 later/Holdout 的 top Agent，regret 为 0。

不能讲：这个 selector 严格优于最强 same-budget random；不能讲 MAE 优于 random；不能讲 full predictive validity、跨仓库 selector superiority、全球最佳 Agent/model 排名。
