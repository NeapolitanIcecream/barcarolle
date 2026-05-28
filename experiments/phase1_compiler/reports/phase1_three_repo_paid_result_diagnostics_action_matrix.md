# Three-Repo Paid Result Diagnostics Action Matrix

Status: `complete`.

What happened: each explanation target was mapped to evidence and a next-action category.
Why it matters: the next work should address adapter reporting and source/split design before buying precision cells.
Action suggested next: no-paid adapter stratification, with source-context hardening and blocked split design as secondary no-paid work.

- Completed paid decision changed: `False`.
- Primary no-paid next action: `stratify_or_separate_adapter_reporting`.
- Paid action after no-paid fixes: `expand_precision_target_paid_replication`.

## Matrix

- `bookkeeping_or_metric_error`: `not_supported`, confidence `high`, action `no_design_change_needed_yet` (`no_paid`).
- `small_sample_noise`: `supported`, confidence `high`, action `expand_precision_target_paid_replication` (`paid_after_no_paid_fixes`).
- `split_imbalance`: `partially_supported`, confidence `medium`, action `redesign_split_with_block_randomization` (`no_paid`).
- `task_statement_quality`: `inconclusive`, confidence `low`, action `harden_task_generator_or_source_context` (`no_paid`).
- `source_context_thinness`: `partially_supported`, confidence `medium`, action `harden_task_generator_or_source_context` (`no_paid`).
- `verifier_or_environment_issue`: `not_supported`, confidence `medium`, action `no_design_change_needed_yet` (`no_paid`).
- `adapter_behavior_difference`: `supported`, confidence `high`, action `stratify_or_separate_adapter_reporting` (`no_paid`).
- `outlier_task_or_task_family`: `partially_supported`, confidence `medium`, action `redesign_split_with_block_randomization` (`no_paid`).
