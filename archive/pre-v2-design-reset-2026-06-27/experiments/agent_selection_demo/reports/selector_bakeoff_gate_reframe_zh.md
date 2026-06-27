# Selector Bakeoff Gate Reframe

生成日期：2026-06-14

## 新 gate

这个 runbook 把主目标改成 Agent 选型决策质量：Selection 必须给出 `recommend`，并且后续 later/Holdout 支持这个选择，或者推荐 regret 不超过 `5pp`。同时要求 Selection 与 later/Holdout 的 top-pair 方向一致，并且决策质量要优于同预算强 random。

MAE 仍然报告，但只作为辅助证据。相对 MAE 改善按 `(random_MAE - selector_MAE) / random_MAE` 计算，不再作为 demo 的硬 veto。

## 当前校正结果

校正后的 Phase 1 pseudo-future block 里，Selection 上 Kilo 为 `11/18`，Codex 为 `6/18`；later/Holdout 上 Kilo 为 `16/30`，Codex 为 `7/30`。强制 top 诊断支持 Kilo，regret 为 `0.0`，top-pair 方向一致。

但旧保守 wrapper 返回 `need_more_evidence`，因为它仍然太接近 zero-loss 规则。该 slice 的 selector MAE 是 `0.088889`，强 stratified-random mean MAE 是 `0.090146`，相对改善约 `1.39%`。这说明方向有用，但还不支持“Selection 推荐 Agent 且 later/Holdout 验证”的用户故事。

## 证据分层

开发证据包括旧 boltons HRD slice、旧 `selector_hrd_eval.json`、校正后的 `selector_corrected_validation_closeout.json`，以及 source inventory。它们用于 selector family 和 wrapper v2 的开发比较。

潜在 final source 优先使用尚未参与阈值或 variant 选择的 `phase1_original_three_repo_split_heldout`。它是 no-paid committed sanitized outcome source，但 missing/non-scoreable cell 比 primary block 多，因此如果使用它，最终报告必须标成 limited no-paid final replay。`repo_specific_earliest_time_bucket_cutoff` 只适合开发 sensitivity，因为 attrs/click 的 B_eval 侧各只有 4 个任务。fresh paid attrs slice 只作为 no-paid source 不足时的 fallback，且必须使用 `LLM_BASE_URL` 和 `LLM_API_KEY`，总新 paid cells 不超过 70。

## Wrapper v2 初始网格

- `action_margin`: `0.05`, `0.10`, `0.15`
- `min_common_valid`: `8`, `12`
- `lcb_tolerance`: `0.0`, `0.05`, `0.10`
- `tie_epsilon`: `0.05`, `0.10`
- 不再要求 `losses == 0`

## Claim boundary

之前的 boltons HRD 结果继续降级为 development evidence。当前支持的是：selector family 和决策规则值得继续开发；不支持 full predictive validity、跨仓库 selector superiority、全局 Agent/model 排名，或旧 boltons slice 的独立验证。
