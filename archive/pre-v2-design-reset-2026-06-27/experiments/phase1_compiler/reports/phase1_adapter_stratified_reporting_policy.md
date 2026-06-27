# Adapter-Stratified Reporting Policy

Status: `complete`.

What happened: the reporting rule now requires adapter-level evidence before any pooled cross-harness summary.
Why it matters: Codex and Kilo results can differ even under the same model, so a single pooled headline can hide a harness effect.
Action suggested next: generate adapter-stratified score, paired-disagreement, cost, and latency summaries from committed artifacts.

## Required Rule

- Adapter-level results must be shown before pooled adapter summaries.
- A pooled cross-harness result must not be the only headline.
- A pooled result can be primary only when it was preregistered before outcomes.
- Otherwise, pooled results are secondary or retrospective diagnostic evidence.
- The completed three-repo paid pilot remains pilot evidence only.
- This run does not change the completed paid pilot decision.

## Required Adapter Metrics

- `adapter_id`
- `cell_count`
- `scoreable_count`
- `non_scoreable_count`
- `pass_count`
- `pass_rate`
- `pass_rate_by_repo`
- `pass_rate_by_split`
- `pass_rate_by_repo_and_split`
- `b_eval_h_future_gap`
- `policy_violation_count`
- `observed_token_estimated_cost_usd`
- `conservative_token_estimated_cost_usd`
- `actual_provider_billed_cost_usd`
- `cost_per_cell_usd`
- `usage_observed_rate`
- `median_latency_seconds`

## Required Paired-Task Metrics

- `paired_task_count`
- `both_pass`
- `both_fail`
- `adapter_a_only_pass`
- `adapter_b_only_pass`
- `disagreement_count`
- `disagreement_rate`
- `exact_count_summary`

## Cost Language

- Token-estimated cost is an estimate from observed token usage.
- Provider-billed exact cost can be claimed only when `actual_provider_billed_cost_usd` is available.
- If `actual_provider_billed_cost_usd` is null, the report must say provider-billed exact cost is unavailable.

## Validation

- Policy valid: `True`.
- Failed checks: `[]`.
