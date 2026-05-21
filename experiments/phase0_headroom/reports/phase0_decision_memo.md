# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired same-protocol generic comparator matrix, and an implemented workspace ACUT adapter. A Codex/Kilo cross-harness workspace preflight was added; later diagnosis resolved both endpoint proofs through isolated provider configurations, non-scoreable command-template dry-runs passed for both wrappers, and the 4-cell smoke subset completed.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Generic comparator source: active Click R0 packages under `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- Workspace ACUT adapter config: `experiments/phase0_headroom/configs/acut_workspace_adapter.yaml`.
- Workspace ACUT preflight: `blocked_no_acut_command`.
- Codex/Kilo workspace ACUT config: `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Codex/Kilo workspace ACUT preflight: `workspace_acut_smoke_complete`.
- Codex workspace status: `codex_eligible`; smoke scoreable cells `2/2`.
- Kilo workspace status: `kilo_eligible`; smoke scoreable cells `1/2`.
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
- Workspace ACUT task-solving calls recorded: `4` Codex/Kilo smoke cells.
- Workspace ACUT incremental spend: `USD 2.0` estimated.
- Codex/Kilo workspace ACUT scoreable cells recorded: `3`.
- Codex/Kilo workspace ACUT estimated scoreable-run spend: `USD 2.0`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run same-repo and generic comparator cells, and separate verified failures from harness or invalid-output outcomes. The workspace adapter now supplies the intended scoreable ACUT boundary and can isolate multiple harnesses once real endpoint-backed harness commands are proven.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. Matrix A is too small and too harness-sensitive to justify moving to `proceed_predictive`, and the Codex/Kilo workspace evidence is only a 4-cell smoke subset.

## Threats To Validity

- One primary target repository.
- Small Matrix A sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.
- Workspace adapter smoke completed, but the full matrix remains gated on clarifying result reuse versus double-counting smoke rows.
- Codex CLI proof initially failed when using `openai_base_url` alone; post-run diagnosis showed a custom `model_provider` with `env_key="LLM_API_KEY"` and `supports_websockets=false` completes against the endpoint.
- Kilo proof initially failed because the attempted config did not attach authentication; post-run diagnosis showed the documented `openai-compatible` provider with `apiKey: "{env:LLM_API_KEY}"` completes against the endpoint and passes a temporary workspace edit dry-run.

## Next Smallest Useful Experiment

Clarify the full-matrix result protocol so smoke rows are either intentionally reused or not double-counted, then run the 20-cell Codex/Kilo matrix if the cost projection remains within budget.
