# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence in addition to the earlier certification and same-repo scoring chain.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Generic comparator source: archived Click R0 metadata.
- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- Estimated measured endpoint spend: `USD 0.11133000`.
- Actual provider-billed cost: `null` because the endpoint response did not expose billing dollars.

## Evidence Summary

- Certified same-repo tasks after source-adapter repair: `6`.
- Mini release status: `benchmark_grade_candidate`.
- Generic comparator protocol: `blocked_metadata_only` with `0` same-protocol `G_mini` tasks.
- Calibration scoreable same-repo cells: `2`.
- Calibration harness or invalid-output cells: `2`.
- Measured endpoint calls recorded: `6`.
- Input tokens: `32425`.
- Cached input tokens: `0`.
- Output tokens: `937`.
- Usage observed rate: `1.0`.
- Cost per scoreable cell: `0.055665`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run a measured same-repo calibration batch, and separate verified failures from harness or invalid-output outcomes.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. The generic comparator remains blocked, so `G_mini -> W_real` and `G_mini + B_real -> W_real` comparisons are unavailable.

## Threats To Validity

- One primary target repository.
- Small calibration batch.
- `G_mini` comparator tasks are metadata-only under the measured endpoint protocol.
- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## Next Smallest Useful Experiment

Run `repair_generic_comparator_first` by materializing at least three Phase 0-compatible `G_mini` tasks before any second ACUT or larger same-repo scale-up.
