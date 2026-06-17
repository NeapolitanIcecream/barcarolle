# Sphinx rolling-origin policy

生成时间：`2026-06-17T10:50:13+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

主策略：`fixed_task_count_40_20_20_stride20`。基于 certification wave 的 projected certified count 为 `120`，可支持 `3` 个 projected rolling-origin windows。

## Policy

- ordering: task_time ascending over certification-expanded Sphinx task manifest
- minimum segments: `{'historical_train': 40, 'selected_benchmark': 20, 'future_validation': 20}`
- stride: `20`
- overlap: no overlap between selected benchmark and future validation within a window; historical train is cumulative

| Origin | Train | Selected | Future | Baseline cells | Tuning cells |
| --- | --- | --- | --- | --- | --- |
| origin_40 | 40 | 20 | 20 | 80 | 40 |
| origin_60 | 60 | 20 | 20 | 80 | 40 |
| origin_80 | 80 | 20 | 20 | 80 | 40 |

## Metrics

每个 window 计算 selected benchmark predicted pass rate 与 later/future actual pass rate 的 MAE：`abs(predicted_selected_pass_rate - actual_future_pass_rate)`。

若未来执行 paid tuning，再用 future segment 计算 before/after uplift error：`abs(predicted_after_minus_before_uplift - actual_future_after_minus_before_uplift)`。

## Paid Cell Estimate

- baseline discovery: `80` cells/window, `240` cells for the projected policy.
- before/after tuning: `40` cells/window, `120` cells for the projected policy.
- authorization: `not_authorized_by_this_no_paid_gate`.

## Unsupported

- Windows are projected from a 24-row certification wave, not frozen certified task manifests.
- Paid baseline discovery and before/after tuning require a separate preregistered paid runbook.
