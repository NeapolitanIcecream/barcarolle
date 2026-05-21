# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired
same-protocol generic comparator matrix, an implemented workspace ACUT adapter,
a completed Codex/Kilo matrix, a repaired Codex/Kilo follow-up matrix, observed
workspace usage accounting, and a repaired-matrix stability repeat.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
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
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The
workspace ACUT boundary is now scoreable for two real CLI harnesses on the
current 20-cell matrix, and the main Kilo non-exit, test-edit policy, and
workspace usage accounting blockers have been repaired without relaxing
verifier isolation or allowing test edits.

The repaired comparison should still be read as:

```text
Same endpoint model, different CLI harnesses.
```

It should not be read as a pure harness-effect estimate.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. The repaired matrix
is much healthier operationally, but it remains one target repository, one
small recovered Click comparator set, and a clustered task sample. Phase 1 was
refreshed from the repaired matrix but correctly keeps overall
`insufficient_evidence`.

## Threats To Validity

- One primary target repository.
- Small repaired matrix sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Workspace pricing now uses observed token usage where harness JSON is
  available, but provider-billed dollars remain unknown.
- Kilo `strict-final` completion repeated successfully with `0/10` Kilo
  timeout rows in the stability repeat.
- `toolz__hist__010` package export scope remains a recurring policy boundary:
  the stability repeat produced two out-of-scope package export violations
  after the review kept those files outside the certified task boundary.

## Next Smallest Useful Experiment

Keep `proceed_regression_benchmark`. The next useful step is a small
second-repository pilot or additional certified task diversity. The current
stability repeat improves operational confidence, but the evidence remains too
small and clustered for predictive-validity or tuning-feedback claims.
