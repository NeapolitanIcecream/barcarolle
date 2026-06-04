# Kilo Endpoint Diagnosis

Status: `kilo_eligible`.

This post-run diagnosis records the Kilo configuration that works with the `LLM_BASE_URL` plus `LLM_API_KEY` endpoint. All Kilo probes used temporary `HOME` and XDG config/data/cache/state directories and did not modify the user's local Kilo environment.

## Documentation Findings

Primary docs checked:

- Kilo OpenAI-compatible provider docs: https://kilo.ai/docs/providers/openai-compatible
- Kilo CLI docs: https://kilo.ai/docs/cli
- Kilo custom model docs: https://kilo.ai/docs/code-with-ai/agents/custom-models

The relevant documented shape is:

- Config files live under `~/.config/kilo/`, with `kilo.jsonc` used for provider, model, permission, and MCP settings.
- The selected model uses `provider_id/model_id` format.
- Custom OpenAI-compatible providers are configured under `provider.<provider_id>.options`.
- Provider options support `apiKey: "{env:VAR}"` and `baseURL`.
- Custom model metadata goes under `provider.<provider_id>.models.<model_id>`.
- `kilo run --auto` is the non-interactive mode, and it still respects permission configuration.
- For `kilo run`, keep the prompt before `--file <path>`. In Kilo `7.3.1`,
  `--file` is an array option; if `--file <path>` appears before the prompt,
  Kilo treats the prompt as another file path and exits with `File not found`.

## What Failed Before

The original Kilo preflight used temporary config state sourced only from `LLM_BASE_URL` and `LLM_API_KEY`, but the attempted provider/auth mapping reached the endpoint without an authentication header. That failure was a Kilo configuration-shape issue, not endpoint unavailability.

## What Worked

The working Kilo config shape is an `openai-compatible` provider with `apiKey` sourced through Kilo's environment interpolation:

```json
{
  "$schema": "https://app.kilo.ai/config.json",
  "model": "openai-compatible/gpt-5.4-mini",
  "enabled_providers": ["openai-compatible"],
  "provider": {
    "openai-compatible": {
      "options": {
        "apiKey": "{env:LLM_API_KEY}",
        "baseURL": "<LLM_BASE_URL_WITH_/v1>"
      },
      "models": {
        "gpt-5.4-mini": {
          "name": "GPT 5.4 Mini Endpoint Probe",
          "id": "gpt-5.4-mini",
          "tool_call": true,
          "reasoning": true,
          "temperature": false,
          "limit": {
            "context": 400000,
            "output": 1024
          }
        }
      }
    }
  }
}
```

Do not write `LLM_API_KEY` into config files. Let Kilo read it through `{env:LLM_API_KEY}`.

## Probe Results

- Direct endpoint check: `/v1/chat/completions` returned HTTP 200 for non-streaming and streaming `gpt-5.4-mini` calls.
- Local recording proxy: `kilo run` sent `POST /v1/chat/completions`, `stream: true`, `model: gpt-5.4-mini`, and `Authorization: Bearer <LLM_API_KEY>`.
- Local command-shape probe: both current adapter order
  `kilo run <prompt> ... --file <statement>` and
  `kilo run ... <prompt> --file <statement>` delivered the prompt plus
  statement attachment to the mocked endpoint; `kilo run ... --file=<statement>
  <prompt>` failed before any model request.
- Real endpoint Kilo proof: `kilo run --pure --format json --model openai-compatible/gpt-5.4-mini` returned code `0`, emitted `PONG`, and reported usage.
- Real endpoint workspace dry-run: in a temporary workspace, Kilo changed only `target.txt` from `before\n` to `PONG\n` and returned code `0`.

Reusable probe command:

```sh
uv run --project experiments/phase0_headroom \
  python experiments/phase0_headroom/tools/kilo_endpoint_probe.py --mode live
```

Workspace dry-run command:

```sh
uv run --project experiments/phase0_headroom \
  python experiments/phase0_headroom/tools/kilo_endpoint_probe.py --mode workspace-live
```

## Implication

Kilo is no longer blocked at endpoint proof. The remaining Codex/Kilo workspace ACUT blocker is converting the proven endpoint/provider shapes into scoreable workspace command templates and running the smoke subset.
