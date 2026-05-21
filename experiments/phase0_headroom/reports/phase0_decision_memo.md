# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired
same-protocol generic comparator matrix, an implemented workspace ACUT adapter,
and a completed Codex/Kilo cross-harness workspace matrix.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Generic comparator source: active Click R0 packages under
  `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Canonical measured ledger:
  `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- Workspace ACUT adapter config:
  `experiments/phase0_headroom/configs/acut_workspace_adapter.yaml`.
- Codex/Kilo workspace ACUT config:
  `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Codex/Kilo workspace ACUT status: `workspace_acut_matrix_complete`.
- Codex workspace status: `codex_eligible`; full matrix scoreable cells `6/10`.
- Kilo workspace status: `kilo_eligible`; full matrix scoreable cells `3/10`.
- Estimated measured endpoint spend: `USD 0.32927100`.
- Codex/Kilo workspace estimated incremental spend: `USD 10.0`.
- Actual provider-billed cost: `null` because the endpoint/harness responses
  did not expose billing dollars.

## Evidence Summary

- Certified same-repo tasks after source-adapter repair: `6`.
- Same-protocol `G_mini` comparator tasks: `4`.
- Generic comparator protocol: `scoreable_same_protocol`.
- Matrix A scoreable endpoint cells: `2`.
- Matrix A harness or invalid-output cells: `8`.
- Measured endpoint calls recorded: `12`.
- Input tokens: `85467`.
- Cached input tokens: `0`.
- Output tokens: `4858`.
- Usage observed rate for direct endpoint calls: `1.0`.
- Cost per direct scoreable cell: `0.1646355`.
- Workspace ACUT task-solving calls recorded: `20`.
- Workspace ACUT scoreable cells recorded: `9`.
- Workspace ACUT terminal statuses: `verified_pass=4`, `verified_fail=5`,
  `policy_violation=5`, `acut_harness_error=6`.
- Workspace ACUT `G_mini -> W_real` availability: `true`.
- Workspace ACUT `G_mini + B_real -> W_real` availability: `true`.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The
endpoint path can discover models, record token usage, run same-repo and
generic comparator cells, and separate verified failures from harness or
invalid-output outcomes. The workspace adapter now supplies the intended
scoreable ACUT boundary and can isolate multiple real CLI harnesses.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. The workspace matrix
is scoreable enough to be useful, but it is too small and too dominated by
harness behavior to justify moving to `proceed_predictive` or
`proceed_tuning_feedback`.

The Codex/Kilo comparison should be read as:

```text
Same endpoint model, different CLI harnesses.
```

It should not be read as a pure harness-effect estimate.

## Threats To Validity

- One primary target repository.
- Small Matrix A sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Pricing uses conservative estimates rather than endpoint billing data for
  workspace harness calls.
- Codex policy violations frequently came from out-of-scope edits such as test
  modifications.
- Kilo's non-interactive mode is not consistently exiting after some tasks even
  when its workspace contains implementation diffs.
- Kilo docs and local help support `kilo run --auto`, but this host's installed
  `kilo 7.3.1` help does not expose every flag currently listed in online docs.

## Next Smallest Useful Experiment

Run a non-scoreable Kilo completion experiment before another paid matrix:
compare the current prompt with a stricter final-answer-and-exit prompt, and
only then decide whether wrapper-side JSON event monitoring should treat
`session.idle` plus a captured diff as a successful terminal state.
