# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 now has measured endpoint evidence for same-repo tasks, a repaired same-protocol generic comparator matrix, and an implemented workspace ACUT adapter. A Codex/Kilo cross-harness workspace preflight was added, but both candidate harnesses are blocked at endpoint proof and no scoreable workspace ACUT task-solving call has run.

- Endpoint-selected primary ACUT model: `gpt-5.4-mini`.
- Primary target repository: `toolz`.
- Generic comparator source: active Click R0 packages under `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Canonical measured ledger: `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- Workspace ACUT adapter config: `experiments/phase0_headroom/configs/acut_workspace_adapter.yaml`.
- Workspace ACUT preflight: `blocked_no_acut_command`.
- Codex/Kilo workspace ACUT config: `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Codex/Kilo workspace ACUT preflight: `blocked_endpoint_proof`.
- Codex workspace status: `codex_blocked_endpoint_proof`.
- Kilo workspace status: `kilo_blocked_endpoint_proof`.
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
- Workspace ACUT task-solving calls recorded: `0`.
- Workspace ACUT incremental spend: `USD 0`.
- Codex/Kilo workspace ACUT scoreable cells recorded: `0`.
- Codex/Kilo workspace ACUT estimated scoreable-run spend: `USD 0`.

## What Phase 0 Supports

Phase 0 supports continuing as a measured regression-benchmark compiler. The endpoint path can discover models, record token usage, run same-repo and generic comparator cells, and separate verified failures from harness or invalid-output outcomes. The workspace adapter now supplies the intended scoreable ACUT boundary and can isolate multiple harnesses once real endpoint-backed harness commands are proven.

## What Phase 0 Does Not Support

Phase 0 still does not support predictive-validity claims. Matrix A is too small and too harness-sensitive to justify moving to `proceed_predictive`, and the workspace adapter has not yet run a real ACUT smoke subset. The Codex/Kilo comparison also does not yet support cross-harness conclusions because both harnesses failed endpoint proof.

## Threats To Validity

- One primary target repository.
- Small Matrix A sample.
- Generic comparator packages are recovered from archived Click R0 material.
- Pricing uses conservative user-estimate-required rates rather than endpoint billing data.
- MAE, RMSE, and Brier score remain `not_applicable_underpowered`.
- Workspace adapter preflight is blocked until a command template proves endpoint-backed ACUT execution through `LLM_BASE_URL` and `LLM_API_KEY`.
- Codex CLI proof reached the configured endpoint path but did not complete the Responses stream.
- Kilo proof reached the configured endpoint path but did not attach authentication from the attempted `LLM_API_KEY` mappings.

## Next Smallest Useful Experiment

Resolve endpoint proof for Codex and Kilo before any scoreable workspace ACUT call. The next smallest useful run is a non-scoreable transport/auth proof that completes for each harness using only `LLM_BASE_URL` and `LLM_API_KEY`, followed by the 4-cell Codex/Kilo smoke subset only after both proofs pass.
