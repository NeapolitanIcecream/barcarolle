# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks and a repaired same-protocol generic comparator matrix.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Generic comparator source: active Click R0 packages under `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- Estimated measured endpoint spend: `USD 0.32927100`.
- Actual provider-billed cost: `null` because the endpoint response did not expose billing dollars.

## Evidence Summary

- Certified same-repo tasks after source-adapter repair: `6`.
- Same-protocol `G_mini` comparator tasks: `4`.
- Generic comparator protocol: `scoreable_same_protocol`.
- Matrix scoreable cells: `2`.
- Matrix harness or invalid-output cells: `8`.
- Measured endpoint calls recorded: `12`.
- Input tokens: `85467`.
- Cached input tokens: `0`.
- Output tokens: `4858`.
- Usage observed rate: `1.0`.
- Cost per scoreable cell: `0.1646355`.
- `G_mini -> W_real` availability: `False`.
- `G_mini + B_real -> W_real` availability: `False`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run same-repo and generic comparator cells, and separate verified failures from harness or invalid-output outcomes.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. Matrix A is too small and too harness-sensitive to justify moving to `proceed_predictive`.

## Threats To Validity

- One primary target repository.
- Small Matrix A sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.

## Next Smallest Useful Experiment

Initialize the Phase 1 compiler skeleton around task/release schemas, target profiles, stratified weighting, splits, uncertainty, and scorecards before any broader paid residual-validation run.
