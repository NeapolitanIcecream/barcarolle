# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired
same-protocol generic comparator matrix, an implemented workspace ACUT adapter,
a completed Codex/Kilo matrix, a repaired Codex/Kilo follow-up matrix, observed
workspace usage accounting, and a repaired-matrix stability repeat.
It now also has a bounded second-repository humanize pilot and a Phase 1
readiness gate.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Second target repository: `humanize`.
- Generic comparator source: active Click R0 packages under
  `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Workspace ACUT adapter config:
  `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Kilo completion mode: `strict-final`.
- Current scoreable protocol: workspace ACUT adapter with Git-diff capture,
  policy gate, and fresh verifier replay.
- Actual provider-billed cost: `null` because endpoint/harness responses did
  not expose billing dollars.
- Canonical workspace cost report:
  `experiments/phase0_headroom/reports/workspace_cost_usage_report.md`.

## Evidence Summary

- Certified same-repo Toolz tasks: `6`.
- Same-protocol `G_mini` Click comparator tasks: `4`.
- Original Codex/Kilo matrix: `9/20` scoreable, Kilo `3/10` scoreable,
  `6` Kilo ACUT harness errors, `5` policy violations.
- Follow-up completion probe: Kilo `3/3` non-timeout and scoreable.
- Follow-up policy smoke: `6/6` scoreable, `0/4` Click test-edit policy
  violations, Kilo `3/3` non-timeout.
- Repaired Codex/Kilo matrix: `19/20` scoreable.
- Repaired Codex: `10/10` scoreable.
- Repaired Kilo: `9/10` scoreable, `0/10` timeout rows.
- Repaired `G_mini`: `8/8` scoreable.
- Repaired terminal statuses: `verified_pass=7`, `verified_fail=12`,
  `policy_violation=1`.
- Repaired follow-up observed-token spend: `USD 5.64126960`.
- Stability repeat matrix: `18/20` scoreable.
- Stability Codex: `9/10` scoreable.
- Stability Kilo: `9/10` scoreable, `0/10` timeout rows.
- Stability `G_mini`: `8/8` scoreable.
- Stability terminal statuses: `verified_pass=7`, `verified_fail=11`,
  `policy_violation=2`.
- Stability observed-token spend: `USD 4.70140020`.
- Second-repo release: `humanize_phase0_pilot`, `pilot_grade`, `12`
  certified tasks.
- Second-repo workspace matrix: `8/8` scoreable, `0` policy violations,
  `0` Kilo timeout rows.
- Second-repo terminal statuses: `verified_pass=3`, `verified_fail=5`.
- Second-repo observed-token spend: `USD 2.37855060`.
- Total workspace usage ledger: `77` calls, usage observed rate `0.9221`,
  observed-or-conservative estimated spend `USD 22.55295780`.
- Phase 1 readiness gate: `ready_for_phase1_mvp`.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## Follow-Up Artifacts

- Cost report:
  `experiments/phase0_headroom/reports/workspace_cost_usage_report.md`.
- Workspace usage ledger:
  `experiments/phase0_headroom/results/workspace_usage_ledger.jsonl`.
- Parallelism policy:
  `experiments/phase0_headroom/configs/parallelism_policy.yaml`.
- Scope review:
  `experiments/phase0_headroom/reports/toolz_hist_010_scope_review.md`.
- Stability analysis:
  `experiments/phase0_headroom/reports/codex_kilo_workspace_stability_analysis.md`.
- Humanize pilot analysis:
  `experiments/phase0_headroom/reports/humanize_workspace_pilot_analysis.md`.
- Phase 1 readiness gate:
  `experiments/phase0_headroom/reports/phase1_readiness_gate.md`.

Cost accounting changed the repaired follow-up from a conservative `USD 10.00`
estimate to an observed-token `USD 5.64126960` estimate, a `USD 4.35873040`
reduction. The stability repeat changed from a conservative `USD 10.00`
estimate to an observed-token `USD 4.70140020` estimate, a `USD 5.29859980`
reduction.

Paid ACUT concurrency remains `1`; cross-harness paid parallelism remains
disabled. `toolz__hist__010` package export edits remain out-of-scope for the
certified task boundary. A repaired-matrix stability repeat was run. A bounded
humanize pilot then certified a second repository and ran an `8`-cell Codex/Kilo
workspace matrix.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler and
starting Phase 1 MVP implementation as a multi-repo compiler effort. The
workspace ACUT boundary is now scoreable for two real CLI harnesses on the
current Toolz/Click matrix and on a bounded humanize second-repo matrix. The
main Kilo non-exit, test-edit policy, workspace usage accounting, and
second-repo certification blockers have been repaired without relaxing verifier
isolation or allowing test edits.

The repaired comparison should still be read as:

```text
Same endpoint model, different CLI harnesses.
```

It should not be read as a pure harness-effect estimate.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. The repaired matrix
and humanize pilot are much healthier operationally, but they remain small and
clustered task samples. Phase 1 readiness is about compiler MVP implementation,
not validation. The Phase 1 import must continue to keep overall
predictive-validity evidence as `insufficient_evidence`.

## Threats To Validity

- One primary target repository.
- One bounded second target repository, not a broad repository sample.
- Small repaired matrix sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Workspace pricing now uses observed token usage where harness JSON is
  available, but provider-billed dollars remain unknown.
- Kilo `strict-final` completion repeated successfully with `0/10` Kilo
  timeout rows in the stability repeat.
- `toolz__hist__010` package export scope remains a recurring policy boundary:
  the stability repeat produced two out-of-scope package export violations
  after the review kept those files outside the certified task boundary.
- Humanize source context used compact commit-message fallback for all
  `16` reviewed contexts because GitHub PR back-links were unavailable.

## Next Action

Keep `proceed_regression_benchmark`. Start Phase 1 MVP implementation with the
allowed scope from `experiments/phase0_headroom/results/pre_phase1_gate.json`:
multi-repo compiler MVP, source-adapter and certification infrastructure,
workspace ACUT import and score tables, and readiness/hygiene reports. Do not
claim predictive validity, a pure harness effect, or a production benchmark
ranking.
