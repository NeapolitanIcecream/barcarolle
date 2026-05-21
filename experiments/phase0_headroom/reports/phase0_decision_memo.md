# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired
same-protocol generic comparator matrix, an implemented workspace ACUT adapter,
a completed Codex/Kilo matrix, and a repaired Codex/Kilo follow-up matrix.

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
- Follow-up estimated spend: `USD 14.50`.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The
workspace ACUT boundary is now scoreable for two real CLI harnesses on the
current 20-cell matrix, and the main Kilo non-exit and test-edit policy
blockers have been repaired without relaxing verifier isolation or allowing
test edits.

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
- Pricing uses conservative estimates rather than endpoint billing data for
  workspace harness calls.
- Kilo `strict-final` repaired the observed completion failure, but should be
  repeated for stability before scale-up.
- One repaired-matrix policy violation remains for `toolz__hist__010`, where
  Kilo edited out-of-scope package export files.

## Next Smallest Useful Experiment

Keep `proceed_regression_benchmark`. The next useful step is a stability and
scope-refinement pass: repeat the repaired matrix or run a second target-repo
pilot, and separately review whether package export files should be allowed for
tasks like `toolz__hist__010` without weakening the test-edit policy.
