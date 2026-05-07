# Process

status: delivered
updated: 2026-04-29T14:39:25+08:00

## Summary

Updated the active 2x2 ACUT model routes from bare IDs to provider-prefixed
IDs after no-secret diagnostics identified the repeated live-request failure
as a model route/name mismatch. The 2x2 design, shared harness, budget caps,
one-primary-attempt policy, and no-secret logging contract are unchanged.

## Changed Paths

- `experiments/core_narrative/configs/acuts/frontier-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/frontier-click-specialist.yaml`
- `experiments/core_narrative/configs/acuts/cheap-generic-swe.yaml`
- `experiments/core_narrative/configs/acuts/cheap-click-specialist.yaml`
- `experiments/core_narrative/reports/model_route_diagnostic.md`
- `experiments/core_narrative/results/normalized/model_route_health_20260429T1437.json`
- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `.codex-workflows/core-narrative-experiment/coordinator.md`

## Diagnostic Record

Parent no-secret diagnostics established that required env vars are present,
DNS/TCP/TLS are OK, `/models` returns HTTP 2xx, and bare model IDs are not
routable through the configured endpoint while provider-prefixed IDs are.

The focused health check used only `BARCAROLLE_LLM_API_KEY` and
`BARCAROLLE_LLM_BASE_URL`, sent no response text to artifacts, and recorded no
credential values, bearer tokens, resolved secrets, full base URLs, hostnames,
or IP addresses. It used token caps of `16` for both provider-prefixed route
probes and received HTTP 2xx for:

- `openai/gpt-5.4-mini`
- `openai/gpt-5.5`

The diagnostic calls were ledgered as `llm_route_health_check` records. The
cumulative estimated ledger total after the checks is USD `6.0008`.

## Current Blockers

Focused review is required before any further ACUT execution. No broad
execution, retry, second attempt, specialist ACUT run, or large batch is
authorized.

## Handoff

Start a focused reviewer to inspect the active ACUT model IDs, health-check
artifact, ledger records, and no-secret reporting. If review passes, the next
coordinator step may record a separate explicit decision for exactly one
bounded pilot attempt. Do not inspect any `cli.log` file.
