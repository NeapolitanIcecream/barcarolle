# Phase 1 Third Repo Replacement Selection Decision

Decision: `ready_for_paid_third_repo_acut_smoke_runbook`.

Paid LLM calls made: `false`. Paid ACUT calls made: `false`.

## Selection

Screened repos: `boltons`.

Selected repo: `boltons`, replacing `itsdangerous`.

`boltons` was accepted because it produced strong local evidence:

- candidates after filter: `32`
- reviewed non-leaky source statements: `22`
- locally certified tasks: `16`
- release status: `pilot_grade`
- benchmark grade flag: `true`
- B_real tasks: `8`
- W_real tasks: `8`
- hardened benchmark-grade candidates: `7`

`attrs` was not cloned or screened because `boltons` passed supply, source,
certification, release, and hardening gates.

## Paid Smoke Readiness

The next runbook may run a small paid third-repo ACUT smoke batch for `boltons`.
This runbook did not run paid ACUT cells and did not make experiment LLM calls.

Predictive validity remains `false`; no production benchmark ranking was
produced.

## Prohibited Claims

- `predictive_validity_established`
- `future_holdout_predictive_validity`
- `production_benchmark_ranking`
- `pure_harness_effect`
- `paid_acut_validation_completed`
- `replacement_repo_benchmark_grade_if_source_or_oracle_gates_fail`
