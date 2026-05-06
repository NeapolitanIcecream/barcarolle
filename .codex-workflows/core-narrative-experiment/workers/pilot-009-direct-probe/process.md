# Pilot 009 Direct Probe Process

status: delivered
updated: 2026-05-07T01:12:00+08:00

## Summary

Executing exactly one coordinator-authorized Option C direct-transport probe:
`pilot_009__frontier-generic-swe__click__rbench__001__attempt1`.

This probe uses `acut_patch_adapter.py` with `barcarolle_patch_command.py`
after `--`; it must not use `codex exec` or the Responses streaming path.
If the probe repeats the prior direct-command `gaierror`/pre-verifier no-patch
family, live execution on this path stops with a hard/repeated infra blocker.

## Owned Paths

- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/results/raw/pilot_009__frontier-generic-swe__click__rbench__001__attempt1/**`
- `experiments/core_narrative/results/normalized/pilot_009__frontier-generic-swe__click__rbench__001__attempt1.json`
- `.codex-workflows/core-narrative-experiment/workers/pilot-009-direct-probe/**`

## Branch / Worktree

- Branch: `codex/core-exp-pilot-009-direct-probe`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-pilot-009-direct-probe`

## Attempt Scope

- run_id: `pilot_009__frontier-generic-swe__click__rbench__001__attempt1`
- ACUT: `frontier-generic-swe`
- model route: `openai/gpt-5.5`
- task: `click__rbench__001`
- split: `rbench`
- attempt: `1`
- projected cost USD: `10.00`
- projected cumulative estimated cost USD: `41.0008`
- specialist context expected: false
- broad execution: false
- retry: false
- second attempt: false
- additional specialist run: false
- large batch: false

## Activity Log

- 2026-05-07T01:02:00+08:00: Process started from coordinator commit `7d8f523`. No `cli.log` file has been inspected. Preparing fresh no-secret preflight and run artifacts.

- 2026-05-07T01:03:00+08:00: Preflight passed: required BARCAROLLE env vars are present by boolean check only; values were not printed or recorded. Cost ledger parses and is writable with 11 records and cumulative estimated cost USD `31.0008`; projected cumulative after this probe is USD `41.0008`, below the USD `240` soft stop and USD `300` hard cap. ACUT `frontier-generic-swe` declares model route `openai/gpt-5.5` and specialist context is not allowed. Source cache availability checked/restored locally without network fetch.
- 2026-05-07T01:04:00+08:00: Fresh workspace prepared and direct patch command dry run completed with `model_call_made: false`. Prompt token estimate recorded in `prompt_token_estimate.json`; using conservative output token budget `64000` for the single live adapter attempt.
- 2026-05-07T01:05:00+08:00: Single authorized live adapter command returned shell exit code `0`; adapter status is `command_failed` and inner command exit code is `2`. Parsing artifacts next; no retry or second attempt will be started.

- 2026-05-07T01:12:00+08:00: Parsed artifacts successfully. The direct HTTP path reached a live model call and did not repeat the prior redacted `gaierror` family. The model response was rejected before workspace mutation because the generated unified diff failed `git apply` validation (`corrupt patch at line 12`). Adapter status is `command_failed`, normalized status is `infra_failed`, patch size is `0`, and no verifier-ready patch exists; no verifier was run. Exactly one ledger record was appended for this run id with event `command_failed`, estimated cost USD `10.00`, and cumulative estimated cost USD `41.0008`. Scoped no-secret scan covered 13 owned text artifacts and found zero required env value hits, bearer-token hits, secret-like hits, full URL hits, or IPv4 hits. No `cli.log` was inspected.

## Result

- adapter_command_ran: true, exactly once
- live_model_call_attempted: true, exactly once
- direct_transport_repeated_gaierror: false
- adapter_status: `command_failed`
- patch_command_status: `error`
- patch_command_error: `generated unified diff failed git apply validation`
- git_apply_validation_detail: `corrupt patch at line 12`
- patch_returned_or_applied: false; retained `submission.patch` is zero bytes
- verifier_ready_patch_available: false
- verifier_run: false
- normalized_status: `infra_failed`
- ledger_append_status: appended
- ledger_event: `command_failed`
- cumulative_estimated_cost_usd: `41.0008`
- no_secret_scan: passed
- cli_log_inspected: false
- broad_execution_started: false
- retry_started: false
- second_attempt_started: false
- additional_specialist_acut_run_started: false
- large_batch_started: false

## Handoff

The single authorized Option C direct probe is delivered and should not be retried. It produced a new signal: the direct transport got past the prior direct-command `gaierror` family and reached model output, but the output was not a verifier-ready patch. The next safe work is no-model triage/hardening of the direct patch response contract and/or prompt output constraints before any further live spend; do not start another live probe without a separate reviewed coordinator decision.
