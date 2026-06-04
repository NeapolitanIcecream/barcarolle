# Codex Endpoint Failure Diagnosis

Status: `codex_eligible`.

This post-run diagnosis explains why the initial Codex workspace endpoint proof failed and records the working configuration pattern. It used isolated temporary `CODEX_HOME` directories and did not modify the user's local Codex environment.

## What Failed

The initial proof used the built-in OpenAI provider with only `openai_base_url` overridden. With that shape, Codex attempted the Responses websocket path and then an HTTP streaming fallback, but the local recording proxy showed that requests to `/v1/responses` did not include an `Authorization` header. Against the real endpoint, this produced an invalid-token failure after the websocket path failed.

Do not use `openai_base_url` alone for this endpoint.

## What Worked

Codex completed a non-scoreable `PONG` probe against the real endpoint with:

- `model_provider` set to a custom provider.
- `model_providers.<id>.base_url` set to `LLM_BASE_URL` with a `/v1` suffix.
- `model_providers.<id>.env_key` set to `LLM_API_KEY`.
- `model_providers.<id>.wire_api` set to `responses`.
- `model_providers.<id>.supports_websockets` set to `false`.

The successful probe returned `turn.completed`, emitted `PONG`, and reported usage. No workspace task-solving call was run.

## Required Codex Pattern

Use this shape for future Codex endpoint-backed probes or workspace harness commands:

```sh
codex exec --ignore-user-config --ephemeral --json \
  --model gpt-5.4-mini \
  -c 'model_provider="llm_endpoint"' \
  -c 'model_providers.llm_endpoint.name="LLM endpoint"' \
  -c 'model_providers.llm_endpoint.base_url="<LLM_BASE_URL_WITH_/v1>"' \
  -c 'model_providers.llm_endpoint.env_key="LLM_API_KEY"' \
  -c 'model_providers.llm_endpoint.wire_api="responses"' \
  -c 'model_providers.llm_endpoint.supports_websockets=false'
```

Do not write `LLM_API_KEY` into config files. Let Codex read it through `env_key`.

## Implication

The Codex endpoint blocker was a configuration issue, not endpoint or model unavailability. Kilo was investigated separately in `experiments/phase0_headroom/reports/kilo_endpoint_diagnosis.md`.
