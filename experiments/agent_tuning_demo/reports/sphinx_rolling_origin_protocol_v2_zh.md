# Sphinx rolling-origin protocol v2

生成时间：`2026-06-17T11:28:51+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

本 artifact 修正 rolling-origin 协议：每个 origin 的 selected benchmark 必须从 `history_pool_before_origin` 中选择；`future_holdout_after_origin` 是选择完成之后才用于评分的伪未来窗口，不是 selector/compiler 的输入。

旧 artifact `experiments/agent_tuning_demo/results/sphinx_rolling_origin_policy.json` 的问题：The earlier feasibility artifact used train/selected/future as three disjoint segments and carried selected-only baseline cell accounting.

## 字段定义

- `history_pool_before_origin`: All eligible certified Sphinx tasks whose task ordering position is before the origin.
- `selected_benchmark_from_history`: A selector/compiler-chosen subset of history_pool_before_origin; the future holdout is not an input.
- `future_holdout_after_origin`: The next task-time ordered certified task window after the origin, used only after selection for scoring.
- `origin_stride`: The number of certified task positions between consecutive origins.
- `selected_benchmark_size`: The number of history-pool tasks the future preregistered selector may choose for a window.
- `future_holdout_size`: The number of post-origin certified tasks used as the pseudo-future target for a window.

## 默认窗口参数

- task ordering: `task_time ascending, stable tie-break by task_id`
- origin history sizes: `[40, 60, 80]`
- origin stride: `20`
- selected benchmark size: `20`
- future holdout size: `20`

## 泄漏规则

selector 可以使用历史池内的 solver-visible 信息。禁止输入：

- future_holdout_after_origin task IDs
- future_holdout_after_origin labels
- future_holdout_after_origin Agent outcomes
- private oracle material
- verifier-only evidence beyond sanitized certification status needed to establish eligibility

`future_holdout_after_origin` 的 task IDs/outcomes 不得影响 selector/compiler。

## Score Join

After selection is frozen, join Agent outcomes for selected benchmark tasks and future holdout tasks under the same verifier policy. Private oracle material is injected only in verifier workspaces, never into selector inputs or solver workspaces. Timeout, harness error, invalid output, and no meaningful change remain failed user-visible attempts unless the next preregistration explicitly narrows a scoreable denominator.

## Metrics

- `pass_rate_prediction_error`: For origin o and Agent a: abs(mean(score[a,t] for t in selected_benchmark_from_history[o]) - mean(score[a,t] for t in future_holdout_after_origin[o])).
- `mae_across_origins`: Mean pass_rate_prediction_error over preregistered origins and Agents with complete selected/future outcome joins.
- `tuning_uplift_prediction_error`: For later paid tuning only: abs((mean(after-before on selected_benchmark_from_history[o])) - (mean(after-before on future_holdout_after_origin[o]))).

## 边界

本文件不选择最终 selector algorithm，也不授权任何付费执行。
