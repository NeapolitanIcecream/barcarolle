# Codex Kilo Workspace Preflight

Status: `partially_blocked_endpoint_proof`.

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `fd673bec`.
- Comparison design: `same_model_cross_harness`.
- Preferred model: `gpt-5.4-mini`.
- Adapter config: `experiments/phase0_headroom/configs/acut_workspace_adapters.yaml`.
- Required endpoint env present: `true`.
- Endpoint host hash: `9952174049b2`.
- Local subscription fallback: `disabled`.
- Provider fallback outside `LLM_BASE_URL` and `LLM_API_KEY`: `disabled`.
- Generic same-protocol scoreable tasks: `4`.

## Eligibility

- `codex_workspace`: `codex_eligible` after post-run diagnosis; no scoreable workspace task-solving call run.
- `kilo_workspace`: `kilo_blocked_endpoint_proof`.

## Evidence

The initial Codex proof was tested with a temporary `CODEX_HOME`, `--ignore-user-config`, `openai_base_url` sourced from `LLM_BASE_URL`, and `OPENAI_API_KEY` mapped from `LLM_API_KEY`. The non-scoreable proof prompt did not complete: the CLI attempted the Responses websocket/stream path and ended with a stream completion failure. Later diagnosis showed this was a configuration issue, not endpoint unavailability.

Kilo was tested with temporary HOME/config state and only `LLM_BASE_URL` plus `LLM_API_KEY` as the source credentials. Provider/model configuration reached the configured endpoint path, but the request was rejected because the provider did not attach an authentication header after the attempted mappings. This is not eligible for scoreable ACUT calls.

No smoke or full workspace matrix cells were run.

## Post-Run Diagnosis

A later isolated diagnosis showed that Codex is endpoint-capable when configured through a custom `model_provider` rather than `openai_base_url` alone. The working pattern sets `env_key="LLM_API_KEY"`, uses a `/v1` `base_url`, sets `wire_api="responses"`, and sets `supports_websockets=false`.

The Codex status is therefore updated in the adapter config to `codex_eligible` for endpoint proof only. No scoreable workspace task-solving call has been run, and the Kilo adapter remains blocked.

Detailed note: `experiments/phase0_headroom/reports/codex_endpoint_failure_diagnosis.md`.
