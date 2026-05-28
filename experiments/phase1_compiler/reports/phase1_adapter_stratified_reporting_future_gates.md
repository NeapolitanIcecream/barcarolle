# Adapter Reporting Future Gates

Status: `ready`.

What happened: future paid validation now has explicit adapter-reporting gates.
Why it matters: the next paid run should not repeat a pooled-only cross-harness headline.
Action suggested next: reference these gates before authorizing or executing any future cross-harness paid validation.

## Gates

- `adapter_reporting_policy_loaded`: The runbook names the adapter reporting policy artifact before paid outcomes are interpreted.
- `adapter_level_result_table_required`: Each adapter has cell count, scoreable count, pass rate, repo/split breakouts, policy violations, cost basis, cost per cell, usage observed rate, and median latency.
- `paired_disagreement_table_required_for_shared_tasks`: The report shows both pass, both fail, adapter A only pass, adapter B only pass, and disagreement rate.
- `cost_estimate_or_bill_status_required`: The report states whether cost is token-estimated or provider-billed, and says provider-billed exact cost is unavailable when actual_provider_billed_cost_usd is null.
- `pooled_headline_primary_only_if_preregistered`: A pooled adapter headline is primary only if the runbook preregistered that aggregate before outcomes.
- `pooled_headline_secondary_or_diagnostic_otherwise`: A pooled adapter result is clearly marked secondary or retrospective diagnostic.
- `single_acut_runs_must_name_scoreable_adapter_before_outcomes`: The runbook chooses one scoreable ACUT/adapter before outcomes and reports that adapter identity in the result table.

## Single-ACUT Rule

What happened: a single-ACUT paid run must name the scoreable adapter before outcomes.
Why it matters: a single adapter can be interpreted as one ACUT result, but the adapter identity is still part of the evidence.
Action suggested next: record the selected ACUT/adapter in the entry gate and result table.

## Cross-Harness Rule

What happened: a cross-harness paid run must show adapter-level results first and paired disagreement when adapters share tasks.
Why it matters: adapter effects can be large enough to change the apparent result.
Action suggested next: report each adapter as a separate ACUT result unless a pooled aggregate was preregistered.

## Pooled Summary Rule

- Primary pooled headline allowed: `only_if_preregistered_before_outcomes`.
- Otherwise: `secondary_or_retrospective_diagnostic`.
- Never allowed: `only_headline_for_cross_harness_paid_results`.

## Reference Targets

- `docs/experiments/phase-1-three-repo-paid-validation-runbook.md`
- `docs/experiments/phase-1-future-holdout-validation-runbook.md`
- `docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md`
- `docs/experiments/phase-1-statement-hardened-paid-validation-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-boltons-paid-acut-smoke-runbook.md`

No direct runbook/template update was made in this step because there is no single central future paid-validation template. This run does not draft or create the next runbook.
