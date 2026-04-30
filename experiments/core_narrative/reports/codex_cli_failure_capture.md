# Codex CLI Failure Capture

Status: delivered for focused review

## Summary

`experiments/core_narrative/tools/codex_cli_patch_command.py` now preserves a
structured, non-secret failure record in its summary JSON for inner
`codex exec` outcomes that fail, time out, or complete without a usable
workspace patch.

No live BARCAROLLE model call, ACUT attempt, retry, second attempt, additional
specialist run, further pilot attempt, broad execution, or large model-call
batch was started for this repair.

## Captured Fields

The live summary now includes:

- `codex_exec.stdout_artifact` and `codex_exec.stderr_artifact`, written under
  the run artifact directory as redacted text files.
- `codex_exec.stdout_bytes` and `codex_exec.stderr_bytes`.
- `workspace_patch`, a content-free check using the same tracked
  `git diff --binary --no-ext-diff HEAD` scope as the outer adapter patch
  collector.
- `failure_capture`, with `present`, `failure_class`, command exit code,
  timeout flag, command duration, timeout budget, stdout/stderr artifact paths,
  bounded stdout/stderr tails, patch usability metadata, and explicit
  redaction-policy flags.

The coarse `failure_class` values are:

- `timeout`
- `nonzero_exit`
- `no_workspace_patch`
- `unsafe_patch_content`
- `git_executable_not_found`
- `git_diff_failed`
- `patch_state_unavailable`

`failure_capture.cli_log_required_for_review` is `false`, and
`failure_capture.cli_log_inspected` is `false`.

## Redaction Policy

Failure stdout/stderr artifacts and tail snippets are redacted before being
written or recorded. The capture path redacts resolved required LLM environment
values, bearer-token-shaped values, common provider-token-shaped values, full
URLs, hostname-shaped values, and IP-address-shaped values.

The summary continues to avoid prompt content, credential values, resolved
endpoint values, and full base URL values. The generated command recorded in
the summary remains the display-safe command with the BARCAROLLE provider
override represented by source environment variable name rather than by a
resolved endpoint value.

## No-Model Verification

Focused no-model regression coverage was added in
`experiments/core_narrative/tools/test_codex_cli_patch_command.py`.

The tests use a fake `codex` executable. The fake binary returns a controlled
bundled model catalog for `codex debug models --bundled`, then exercises live
harness mode without contacting a real model:

- nonzero inner `codex exec` exit records `failure_capture.failure_class` as
  `nonzero_exit`, preserves redacted stdout/stderr artifacts and bounded tails,
  and does not require `cli.log`.
- exit-zero progress-only execution records `failure_capture.failure_class` as
  `no_workspace_patch` while preserving the outer adapter contract that the
  command itself exits zero and lets the adapter classify the empty patch.

Verification commands run:

```bash
python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py
```

## Coordinator Gate

Recommended next gate: run a focused reviewer on this no-model harness repair.
If reviewed cleanly, the coordinator may consider one later explicitly
authorized bounded pilot attempt using the repaired harness. No further live
model call should start until that review and a separate coordinator execution
decision are recorded.
