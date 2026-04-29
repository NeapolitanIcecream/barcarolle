# Model Route Diagnostic

updated: 2026-04-29T14:39:25+08:00
status: delivered_for_review

## Summary

The repeated bounded pilot failures were narrowed to an LLM model route/name
mismatch, not missing environment, transport failure, or credit exhaustion.
The active 2x2 ACUT model IDs now use provider-prefixed routes:

- cheap tier: `openai/gpt-5.4-mini`
- frontier tier: `openai/gpt-5.5`

The 2x2 design, shared harness, budget caps, one-primary-attempt policy, and
no-secret logging contract are unchanged.

## No-Secret Diagnostic Basis

Parent coordination diagnostics reported:

- required environment variables are present;
- DNS, TCP, and TLS checks pass;
- `/models` returns HTTP 2xx;
- bare model IDs `gpt-5.4-mini` and `gpt-5.5` are not routable through the
  configured endpoint;
- `/models` lists provider-prefixed IDs `openai/gpt-5.4-mini` and
  `openai/gpt-5.5`;
- minimal chat probes with token caps at or above 16 succeeded for both
  provider-prefixed IDs.

This report records only route classes, model IDs, status classes, and token
counts. It does not record credential values, bearer tokens, resolved secrets,
full base URLs, hostnames, IP addresses, or response text.

## Focused Health Check

Artifact:
`experiments/core_narrative/results/normalized/model_route_health_20260429T1437.json`

The coordinator ran one focused no-secret health check for each provider-
prefixed active model ID using `max_completion_tokens` or
`max_output_tokens` equal to `16`. Both probes returned HTTP 2xx. Response text
was not recorded.

Estimated diagnostic spend was ledgered in
`experiments/core_narrative/results/cost_ledger.jsonl` as
`llm_route_health_check` records:

- `model_route_health__openai_gpt_5_4_mini__20260429T1437`
- `model_route_health__openai_gpt_5_5__20260429T1437`

The cumulative estimated ledger total after the health check is USD `6.0008`.

## Execution Policy

No ACUT pilot attempt, retry, specialist run, broad execution, or large batch
was started by this diagnostic. Resuming execution requires focused review of
the model route fix and then a separate explicit coordinator decision for
exactly one bounded pilot attempt.
