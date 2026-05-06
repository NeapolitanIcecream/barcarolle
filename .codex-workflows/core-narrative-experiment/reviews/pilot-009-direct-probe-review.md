# Pilot 009 Direct Probe Review

status: no_issues
updated: 2026-05-07T01:24:00+08:00

## Summary

The integrated pilot 009 artifacts match the coordinator authorization: exactly
one live Option C direct probe ran for
`pilot_009__frontier-generic-swe__click__rbench__001__attempt1`, with no retry,
second attempt, specialist ACUT run, broad execution, further pilot, or large
batch. The run is not scoreable because no verifier-ready patch was produced.

The direct path reached a live model response and did not repeat the prior
redacted `gaierror` direct-command family. It failed before verifier because the
generated unified diff was invalid for `git apply --check`.

## Checks Performed

- Parsed `adapter_result.json`, `patch_command_summary.json`, normalized result JSON, and the cost ledger.
- Confirmed exactly one ledger record for the run id; ledger record count is 12 and cumulative estimated cost is USD `41.0008`.
- Confirmed adapter status `command_failed`, normalized status `infra_failed`, patch size `0`, and `verifier_ready_patch_available: false`.
- Confirmed no verifier artifacts beyond adapter stdout/stderr handoff were produced for a verifier run.
- Ran scoped no-secret scan over 13 owned text artifacts: zero required env value hits, bearer-token hits, secret-like hits, full URL hits, or IPv4 hits.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_barcarolle_patch_command.py` passed: 7 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed: 4 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py` passed: 5 tests.
- `python3 -m py_compile experiments/core_narrative/tools/barcarolle_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` passed.
- `git diff --check` passed.
- Did not inspect any `cli.log`.

## Findings

1. No integration-blocking issues found.

## Notes

Pilot 009 exposed a non-blocking metadata gap in the inner direct command error
summary: after receiving a live model response that failed patch validation, the
inner summary marked `model_call_made: false`. The adapter/ledger were already
correct. The coordinator closed this with no-model regression hardening for
future runs; historical pilot 009 artifacts remain unchanged.

## Recommendation

Accept pilot 009 as an integrated non-scoreable direct-probe result. Do not run
another live probe until a reviewed no-model direct-output-contract hardening
hypothesis exists.
