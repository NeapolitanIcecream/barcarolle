# Sphinx paid-cell accounting

生成时间：`2026-06-17T11:37:16+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

baseline discovery 使用 `4` Agents。默认 window 下 naive baseline discovery 是 `(20 selected + 20 future) * 4 = 160` cells/window，不再使用旧的 ambiguous `80 cells/window` 作为总数。

## Per-window accounting

| Origin | Selected cells | Future cells | Naive baseline | Later tuning formula |
| --- | --- | --- | --- | --- |

Total naive baseline discovery cells: `0`。

## Deduplication

- known future holdout unique task-Agent cells: `0`
- selected unique task count range depends on next selector: `[0, 0]`
- selected+future unique task-Agent cells range depends on next selector: `[0, 0]`
- exact selected dedup status: `unknown_until_next_preregistration_selector_freezes_selected_task_ids`

## Later before/after tuning

- full formula: `(20 selected + 20 future) * 2 variants = 80 cells/window when using the default window sizes`
- selected-first gate formula: `20 selected * 2 variants = 40 cells/window before any future gate`
- authorization: `future_plan_only_not_authorized_by_this_no_paid_run`

本 artifact 只做 accounting reconciliation，不授权 paid baseline discovery 或 tuning。
