# Sphinx corrected rolling-origin window manifest

生成时间：`2026-06-17T11:36:32+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

certified task count `16` supports `0` corrected windows；state: `below_minimum_policy`。

Preferred policy requires `100` certified tasks for origins `40/60/80`; minimum acceptable policy requires `80` certified tasks for origins `40/60`。当前 manifest 只有 `16` tasks，因此不伪造 smaller windows。

## 规则

- ordering: `certified tasks by task_time ascending, stable tie-break by task_id`
- origin stride: `20`
- selected benchmark size: `20`
- future holdout size: `20`
- selector status: `not_chosen_in_this_runbook`

Future holdout IDs/outcomes are withheld from selector/compiler until after selected_benchmark_from_history is frozen.

## Windows

| Origin | History pool | Selected size | Future holdout | First future | Last future |
| --- | --- | --- | --- | --- | --- |

每个 JSON window 都列出 exact `history_pool_before_origin.task_ids` 和 exact `future_holdout_after_origin.task_ids`。本轮不选择 selected task IDs。
