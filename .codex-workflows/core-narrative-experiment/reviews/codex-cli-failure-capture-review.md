# Codex CLI Failure Capture Review

status: issues_found

## Summary

Focused no-model/static review completed for delivery commit `64c5d9b`.
The implementation adds structured `failure_capture` and `workspace_patch`
metadata around inner `codex exec` outcomes, preserves the temporary
`CODEX_HOME`, BARCAROLLE provider override, provider-prefixed model catalog,
non-interactive base instructions, dry-run path, specialist context injection,
and leaves the outer adapter budget/ledger/redaction/empty-patch semantics in
place.

Two closure issues remain before this should gate a later live attempt: hostname
redaction is incomplete, and required failure modes are not covered by no-model
regression tests.

## Findings

1. `experiments/core_narrative/tools/codex_cli_patch_command.py:63` hard-codes a
   limited hostname suffix list, and
   `experiments/core_narrative/tools/codex_cli_patch_command.py:405` relies on
   that expression for stdout/stderr artifact and tail redaction. Static review
   plus a no-model synthetic check showed hostname-shaped text outside that
   suffix list is not redacted, while `failure_capture.redaction_policy` claims
   `hostnames_redacted: true`. This can leak hostnames into
   `codex_exec.stdout.txt`, `codex_exec.stderr.txt`, and bounded
   `failure_capture` tail snippets.

2. `experiments/core_narrative/tools/test_codex_cli_patch_command.py:133` and
   `experiments/core_narrative/tools/test_codex_cli_patch_command.py:180` cover
   only `nonzero_exit` and `no_workspace_patch`. The delivery reports
   `timeout` and `unsafe_patch_content` classes, and the review scope requires
   those cases to produce structured metadata, but there are no no-model
   regression tests for them. The tests also check that redacted stdout/stderr
   artifact paths exist, but they do not read the artifact files to assert that
   credential values, bearer-token-shaped strings, full URLs, hostnames, and IP
   address-shaped strings are absent.

## Verification

- Read coordinator and worker process files, plus pilot 004/005 worker/reviewer
  process files. No `cli.log` file was inspected.
- Static review of `codex_cli_patch_command.py`,
  `test_codex_cli_patch_command.py`, `codex_cli_failure_capture.md`, and the
  outer adapter empty/unsafe-patch path.
- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
  passed.
- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py` passed.
- `python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/test_codex_cli_patch_command.py`
  passed.
- `git diff --check` passed.
- No-model synthetic redaction check confirmed an unlisted-suffix
  hostname-shaped value remains unredacted.

## Required Closure

Broaden the failure-capture hostname redaction so it matches the stated policy
without relying on a narrow suffix list, and add no-model regression coverage
for timeout, unsafe patch content, and the contents of the redacted
stdout/stderr artifacts. Re-review the repair before any later live ACUT attempt
or model-call authorization.
