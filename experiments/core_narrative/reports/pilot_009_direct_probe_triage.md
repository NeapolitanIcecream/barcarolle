# Pilot 009 Direct Probe Triage

status: no_scoreable_result_new_direct_signal
updated: 2026-05-07T01:24:00+08:00
run_id: `pilot_009__frontier-generic-swe__click__rbench__001__attempt1`
related_decision: `.codex-workflows/core-narrative-experiment/decisions/post-option-c-direct-probe-readiness.md`
related_process: `.codex-workflows/core-narrative-experiment/workers/pilot-009-direct-probe/process.md`

## Summary

Pilot 009 executed exactly one authorized live Option C direct probe through
`acut_patch_adapter.py` plus `barcarolle_patch_command.py` for
`frontier-generic-swe` on `click__rbench__001`.

The direct path did **not** repeat the prior direct-command redacted `gaierror`
family from pilots 001/002/003, and it did **not** use the Codex CLI Responses
streaming path that failed in pilots 006/007/008. It reached a live model
response. The response was rejected before workspace mutation because the
generated unified diff failed `git apply --check` validation (`corrupt patch at
line 12`). No verifier-ready patch existed, so no verifier ran and no scoreable
ACUT result was produced.

## Result Facts

- Adapter status: `command_failed`.
- Normalized status: `infra_failed`.
- Inner direct command status: `error`.
- Inner direct command error: `generated unified diff failed git apply validation`.
- Patch artifact: zero bytes; no unsafe content detected.
- Verifier-ready patch: false.
- Verifier run: false.
- Ledger: exactly one record appended for the run id, event `command_failed`.
- Cumulative estimated cost after the run: USD `41.0008` across 12 ledger records.
- Secret scan: 13 owned text artifacts scanned; zero required env value, bearer-token, secret-like, full URL, or IPv4 hits.
- No `cli.log` content was inspected.
- No retry, second attempt, additional specialist run, broad execution, further pilot, or large batch was started.

## Interpretation

The post-pilot-008 blocker has moved: Option C direct transport is no longer
blocked at DNS/`gaierror` for this frontier generic probe, but the experiment
still lacks a verifier-ready patch. The next obstacle is patch response
contract/prompt robustness for direct model output, not the previously repeated
network-resolution failure.

This is not a capability result for `frontier-generic-swe`: the task never
reached verifier. It is also not evidence that the ranking-reversal hypothesis
holds or fails.

## Immediate No-Model Hardening Completed

Pilot 009 exposed a metadata issue: the inner `barcarolle_patch_command.py`
summary reported `model_call_made: false` in the error path after a live model
response was received but rejected during patch validation. The outer adapter
and ledger correctly recorded the live model call.

A no-model regression hardening was added so future direct runs record
`model_call_made: true` and `model_response_received: true` when a live model
response is rejected after receipt. This does not alter the historical pilot 009
artifacts.

## Next Safe Step

Do not run another live probe by habit. Before any further live spend, prepare
and review a no-model direct-output-contract hardening hypothesis, such as a
stricter response schema, prompt format, or parser/repair gate that can be
mock-tested against malformed diffs without weakening the ACUT control contract.
