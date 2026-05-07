# Codex CLI Transport Hardening Review

status: no_issues

## Summary

Reviewed delivered worker commit `fa80a57` in
`/Users/chenmohan/gits/barcarolle-wt-codex-cli-transport-hardening`.

No issues found. The delivery is a no-model/static transport-hardening change:
it adds a machine-readable classifier for the known redacted Responses
streaming disconnect shape and propagates sanitized inner failure metadata
through the adapter without changing raw adapter status, ledger event semantics,
budget accounting, verifier policy, retry policy, or one-primary-attempt policy.

No ACUT attempt, live BARCAROLLE model call, retry, second attempt, additional
specialist run, broad execution, further pilot attempt, large model-call batch,
or cost-ledger append was started by this review. No `cli.log` file was
inspected.

## Findings

No findings.

## Evidence

- Read the required coordinator and worker/reviewer `process.md` files first.
- Confirmed worker worktree HEAD is `fa80a57`.
- `git diff --name-only fa80a57^ fa80a57` showed only the six scoped delivery
  files:
  - `.codex-workflows/core-narrative-experiment/workers/codex-cli-transport-hardening/process.md`
  - `experiments/core_narrative/reports/codex_cli_transport_hardening.md`
  - `experiments/core_narrative/tools/acut_patch_adapter.py`
  - `experiments/core_narrative/tools/codex_cli_patch_command.py`
  - `experiments/core_narrative/tools/test_acut_patch_adapter.py`
  - `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `codex_cli_patch_command.py` classifies the sanitized stdout/stderr shape only
  from already-redacted captured text, records `responses_streaming_disconnect`,
  `/responses`, reconnect metadata, and explicit `messages_recorded: false` /
  `content_recorded: false`, and does not persist message bodies.
- Generic nonzero exits, timeouts, unsafe patch content, exit-0 empty-diff
  outcomes, and verifier-eligible successful patches remain distinct in code
  and targeted checks.
- `acut_patch_adapter.py` reads the inner `--summary-output` only after command
  completion, preserves raw `command_failed` status and ledger event for
  nonzero/no-patch outcomes, and carries the sanitized inner failure class into
  raw adapter output, normalized `infra_failed` metadata, and ledger metadata.
- The transport-hardening report honestly records that no safe non-streaming
  Codex CLI transport switch was established by local no-model discovery.

Checks run:

- `git diff --check fa80a57^ fa80a57 -- <scoped paths>` passed.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py` passed, 5 tests.
- `PYTHONDONTWRITEBYTECODE=1 python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed, 4 tests.
- `PYTHONPYCACHEPREFIX=/private/tmp/barcarolle-reviewer-pycache python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/acut_patch_adapter.py` passed.
- Extra command-no-model success-path check passed: safe workspace edit produced
  `command_completed`, `verifier_ready_patch_available: true`, and ledger event
  `command_completed` without writing a normalized infra-failure result.
- Filtered no-secret scan over the six changed files passed with `cli.log`
  excluded and no credential-token, bearer-token, full-URL, IP-shaped, or
  runtime hostname findings.
- Worker worktree was clean after checks; reviewer worktree was clean before
  writing this review artifact and process update.

## Required Closure

The coordinator may integrate the transport-hardening delivery and this review
artifact before deciding any later bounded execution hypothesis. Any later live
execution still requires a separate explicit coordinator decision.
