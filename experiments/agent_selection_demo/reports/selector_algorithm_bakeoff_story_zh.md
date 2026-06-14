# Selector Algorithm Bakeoff Story

生成日期：2026-06-14

## 这次试了什么

本次 bakeoff 实现并比较了 RSQ v2、FLC、HRD v3、COD-lite、RO-LSP、SAES-lite，以及 uniform、quality-filtered、source/recency stratified、module stratified random baselines。

主 gate 改成 Agent 选型决策质量：Selection 是否能推荐一个 Agent，later/Holdout 是否验证这个选择。MAE 仍然报告，但不是硬 veto。

## 开发集结果的读法

开发 bakeoff 表中，`hrd_v3_70_30` 的 decision-quality 指标排在第一：validated recommendation rate `1.0`，recommendation coverage `1.0`，false-recommendation rate `0.0`。它的 MAE 是 `0.122643`，强 random MAE mean 是 `0.150765`，相对改善 `18.65%`。

COD-lite 也达到 validated recommendation rate `1.0`，但 MAE 是 `0.142087`，低于 HRD v3 `70/30` 的 MAE signal。最终 demo 报告不把 COD-lite 作为主算法，也不把 COD-lite 和 HRD 写成双主线。COD-lite 只保留为 bakeoff 表中的普通候选项；demo 主线使用 HRD v3 `70/30`，因为它已经足够支撑一个可解释、可运行、可审计的 Agent 选型故事。

## Bakeoff final replay 作为附录证据

Bakeoff final replay 使用没有参与阈值和 variant 选择的 `phase1_original_three_repo_split_heldout`，标记为 limited no-paid final replay。该 replay 的 selector 是 `hrd_v3_70_30`，k=`10` per repo，决策规则是 wrapper v2：

- action margin: `0.10`
- min common valid: `8`
- lcb tolerance: `0.10`
- tie epsilon: `0.05`
- 不要求 zero loss

Selection 推荐 `kilo_workspace`。Selection 通过率为 Codex `5/26`，Kilo `14/26`。later/Holdout 通过率为 Codex `16/40`，Kilo `22/40`。推荐 regret 是 `0.0`，top-pair direction agreement 为 `True`。

## Random baseline 和 MAE

最终 replay 没有严格打败最强 decision random baseline。最强 random decision baseline 是 `source_recency_stratified_random`，validated recommendation rate 也是 `1.0`，false-recommendation rate 也是 `0.0`，mean regret 也是 `0.0`。因此最终结论是 tie，不是 strict beat。

MAE 没有严格赢：selector MAE `0.109615`，强 random MAE mean `0.106711`，相对改善 `-2.72%`，MAE beats/ties random share `0.454`。

## 现在能讲什么

可以讲：算法 bakeoff 提供了候选 selector 的对比表；HRD v3 `70/30` 是 bakeoff 表 leader，也是最终 demo 主线。COD-lite 是其中一个普通候选。HRD final demo 的核心证据见 `selector_final_eval_zh.md` 和 `final_agent_selection_demo_package_zh.md`。

不能讲：COD-lite 是最终 demo 主算法；不能讲任一 selector 严格优于最强 same-budget random；不能讲 full predictive validity、跨仓库 selector superiority、全球最佳 Agent/model 排名。
