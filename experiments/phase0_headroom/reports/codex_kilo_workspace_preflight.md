# Codex Kilo Workspace Preflight

Status: `workspace_acut_smoke_complete`.

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `fd673bec`.
- Comparison design: `same_model_cross_harness`.
- Preferred model: `gpt-5.4-mini`.
- Adapter config: `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Matrix config: `experiments/phase0_headroom/configs/codex_kilo_workspace_matrix.yaml`.
- Required endpoint env present: `true`.
- Endpoint host hash: `9952174049b2`.
- Local subscription fallback: `disabled`.
- Provider fallback outside `LLM_BASE_URL` and `LLM_API_KEY`: `disabled`.
- Generic same-protocol scoreable tasks: `4`.

## Eligibility

- `codex_workspace`: `codex_eligible`; smoke scoreable cells `2/2`.
- `kilo_workspace`: `kilo_eligible`; smoke scoreable cells `1/2`.

## Evidence

The initial Codex proof was tested with a temporary `CODEX_HOME`, `--ignore-user-config`, `openai_base_url` sourced from `LLM_BASE_URL`, and `OPENAI_API_KEY` mapped from `LLM_API_KEY`. The non-scoreable proof prompt did not complete: the CLI attempted the Responses websocket/stream path and ended with a stream completion failure. Later diagnosis showed this was a configuration issue, not endpoint unavailability.

The initial Kilo proof was tested with temporary HOME/config state and only `LLM_BASE_URL` plus `LLM_API_KEY` as the source credentials. Provider/model configuration reached the configured endpoint path, but the request was rejected because the attempted mapping did not attach an authentication header.

The smoke subset has run. The full workspace matrix has not run.

## Post-Run Diagnosis

A later isolated diagnosis showed that Codex is endpoint-capable when configured through a custom `model_provider` rather than `openai_base_url` alone. The working pattern sets `env_key="LLM_API_KEY"`, uses a `/v1` `base_url`, sets `wire_api="responses"`, and sets `supports_websockets=false`.

The Codex status is therefore updated in the adapter config to `codex_eligible` for endpoint proof only. No scoreable workspace task-solving call has been run.

Detailed note: `experiments/phase0_headroom/reports/codex_endpoint_failure_diagnosis.md`.

## Kilo Post-Run Diagnosis

A later isolated diagnosis showed that Kilo is endpoint-capable when configured through the documented `openai-compatible` provider shape. The working pattern puts `apiKey: "{env:LLM_API_KEY}"` and a `/v1` `baseURL` under `provider.openai-compatible.options`, defines `gpt-5.4-mini` under `provider.openai-compatible.models`, and runs `kilo run` with `--model openai-compatible/gpt-5.4-mini`.

The Kilo status is therefore updated in the adapter config to `kilo_eligible` for endpoint proof. A non-scoreable temporary workspace dry-run also succeeded, but no scoreable workspace ACUT task has been run.

Detailed note: `experiments/phase0_headroom/reports/kilo_endpoint_diagnosis.md`.

## Workspace Command Template Dry-Run

Both adapters now have configured command templates that invoke repo-local wrapper scripts through `uv run --project experiments/phase0_headroom`.

- `codex_workspace`: temporary git workspace dry-run returned code `0`, changed only `target.txt`, and left `target.txt` as `PONG\n`.
- `kilo_workspace`: temporary git workspace dry-run returned code `0`, changed only `target.txt`, and left `target.txt` as `PONG\n`.

These dry-runs are not scoreable ACUT cells. They only prove that each wrapper reads a statement file, uses isolated endpoint config, and mutates the supplied workspace.

## Smoke Result

Smoke ran sequentially, two cells per harness:

- `codex_workspace x toolz__hist__002`: `verified_pass`.
- `codex_workspace x click__rbench__001`: `verified_fail`.
- `kilo_workspace x toolz__hist__002`: `acut_harness_error` after timeout.
- `kilo_workspace x click__rbench__001`: `verified_fail`.

Summary:

- Scheduled cells: `4`.
- Scoreable cells: `3`.
- Terminal status counts: `verified_pass=1`, `verified_fail=2`, `acut_harness_error=1`.
- Estimated smoke cost: `USD 2.0` using a conservative `USD 0.50` per-cell estimate because harness usage is not imported.
- Solver workspaces contained no hidden verifier material in the checked paths.
