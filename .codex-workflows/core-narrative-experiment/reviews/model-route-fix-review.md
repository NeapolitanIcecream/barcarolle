# Model Route Fix Review

status: no_issues

## Summary

Focused review of delivered commit `d354071` found no issues in the model-route fix. The active 2x2 ACUT configs now use provider-prefixed model IDs, the shared 2x2 controls remain intact, and execution remains blocked pending this review plus a separate explicit coordinator decision for exactly one bounded pilot attempt.

## Findings

No issues found.

## Evidence

- The four active ACUT configs set cheap-tier models to `openai/gpt-5.4-mini` and frontier-tier models to `openai/gpt-5.5`.
- `git diff d354071^ d354071` shows the four ACUT config changes are limited to the `model:` values. The shared harness, wall budget, turn cap, token cap, test cap, and retry policy remain `codex_cli`, `3600`, `18`, `64000`, `10`, `primary_attempts: 1`, and `retries_allowed: false` across all four active ACUTs.
- The run manifest records `model_calls_allowed: false`, `model_calls_allowed_scope: none_until_model_route_fix_review_passes`, `broad_acut_execution_started: false`, and `required_before_next_pilot_attempt: focused_review_no_issues_and_explicit_one_attempt_start_decision`.
- The health-check artifact records `all_provider_prefixed_routes_ok: true`, token caps of `16`, HTTP 2xx status classes for `openai/gpt-5.4-mini` and `openai/gpt-5.5`, and `pilot_attempt_started: false`, `broad_acut_execution_started: false`, and `large_batch_started: false`.
- `experiments/core_narrative/results/cost_ledger.jsonl` parses as JSONL. Commit `d354071` appended exactly two `llm_route_health_check` records, one for each provider-prefixed route, and the cumulative estimated cost after the second health check is USD `6.0008`, below the USD `240` soft stop and USD `300` hard cap.
- Scoped artifacts and coordination files record only environment variable names, booleans, model IDs, status classes, token counts, and cost estimates. A scoped scan found no full URL, bearer-token, standalone `sk-` credential, or IPv4-address pattern; hostname and base-URL fields are recorded only as non-secret booleans or redaction-policy flags.

## Required Closure

The coordinator may integrate this review before recording a separate one-attempt execution decision. Broad ACUT execution, large batches, retries, second attempts, and specialist ACUT runs remain blocked unless and until the coordinator separately authorizes exactly one bounded pilot attempt.
