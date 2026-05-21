# Codex Kilo Workspace Preflight

Status: `blocked_endpoint_proof`.

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

- `codex_workspace`: `codex_blocked_endpoint_proof`.
- `kilo_workspace`: `kilo_blocked_endpoint_proof`.

## Evidence

Codex was tested with a temporary `CODEX_HOME`, `--ignore-user-config`, `openai_base_url` sourced from `LLM_BASE_URL`, and `OPENAI_API_KEY` mapped from `LLM_API_KEY`. The non-scoreable proof prompt did not complete: the CLI attempted the Responses websocket/stream path and ended with a stream completion failure. This is not eligible for scoreable ACUT calls.

Kilo was tested with temporary HOME/config state and only `LLM_BASE_URL` plus `LLM_API_KEY` as the source credentials. Provider/model configuration reached the configured endpoint path, but the request was rejected because the provider did not attach an authentication header after the attempted mappings. This is not eligible for scoreable ACUT calls.

No smoke or full workspace matrix cells were run.
