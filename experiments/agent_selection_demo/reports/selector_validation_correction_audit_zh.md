# Selector Validation Correction Audit

生成日期：2026-06-14

## 结论

之前的 `hrd_70_30`, `k=10` 结果必须 relabel 为：

```text
hypothesis_generating_selector_development_result
```

它是有用的开发证据，但不是 independent validation。

## 为什么不能当作最终证明

主要问题不是数值错了，而是验证边界不干净：

- selector family、variant choice 和 final story 都使用了同一批 boltons Selection/Holdout evidence；
- `hrd_70_30` 是在看过 boltons Holdout 后被选成最终故事的；
- final task subset 没有在独立 final outcome source 前冻结；
- HRD 的 “disagreement” arm 没有使用 leakage-safe historical Agent-disagreement data，而是用了 `metadata_cluster_density_difficulty_proxy` fallback。

因此，原结果只能说明 HRD-style selector 值得进入 corrected validation。它不能证明 selector 会在新 final slice 上泛化。

## 旧结果保留的数值

| Slice | Codex + GPT | Kilo + GPT | Kilo mini | Kilo Claude |
| --- | ---: | ---: | ---: | ---: |
| Development Selection | `7/10` | `9/10` | `7/10` | `7/10` |
| Already-used Holdout | `5/10` | `9/10` | `6/10` | `8/10` |

Doubled-timeout top-2 repeat：Codex + GPT `6/10`，Kilo + GPT `9/10`。

Development-slice recommendation regret 是 `0.0`。Development-slice MAE 是 `0.100000`，strong stratified-random k=10 mean MAE 是 `0.151700`。

这些数字可以作为 development evidence 使用，但不能作为 independent proof 使用。

## 需要重解释的 artifacts

- `experiments/agent_selection_demo/reports/selector_agent_selection_demo_story_zh.md`
- `experiments/agent_selection_demo/reports/selector_evolution_closeout_zh.md`
- `experiments/agent_selection_demo/results/selector_evolution_closeout.json`
- `experiments/agent_selection_demo/results/selector_final_eval.json`
- `experiments/agent_selection_demo/results/selector_final_preregistration.json`
- `experiments/agent_selection_demo/results/selector_hrd_eval.json`
- `experiments/agent_selection_demo/results/selector_decision_eval.json`

本 package 已直接更新 reader-facing story 和 closeout，把旧结果标为 development/hypothesis evidence。

## 仍然可复用的资产

- selector task table 和 outcome matrix construction；
- uniform、quality-filtered、stratified random baselines；
- RSQ selector；
- HRD implementation，但 fallback arm 必须叫 `metadata_informativeness`，不能叫 leakage-safe Agent disagreement；
- shared recommend/abstain/need-more-evidence decision wrapper；
- paired small-sample decision metrics 和 random-baseline summaries。

## 不能从旧结果 claim

- independent selector validation；
- HRD generalizes to unseen final slices；
- Kilo + GPT mainline 是 generally best Agent；
- full predictive validity；
- cross-repository selector superiority；
- global Agent/model ranking。

## 下一步

继续执行 correction runbook：先 inventory independent no-paid/fresh paid final-validation sources，然后在 final outcome join 或 paid cells 前 freeze corrected protocol。
