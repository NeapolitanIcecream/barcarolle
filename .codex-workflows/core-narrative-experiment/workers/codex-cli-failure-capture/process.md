# Process

status: delivered
updated: 2026-04-30T16:03:04+08:00

## Summary

Focused no-model harness diagnostic/repair worker for Codex CLI failure capture
and artifact preservation after reviewed pilot 004 and pilot 005 both ended
`codex_exec_failed` with zero-byte patches.

This worker must not start an ACUT attempt, live BARCAROLLE model call, retry,
second attempt, additional specialist ACUT run, broad execution, further pilot
attempt, or large model-call batch.

## Owned Paths

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/reports/codex_cli_failure_capture.md`
- `experiments/core_narrative/results/raw/codex_cli_failure_capture*/**`
- `experiments/core_narrative/results/normalized/codex_cli_failure_capture*.json`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/**`

## Branch / Worktree

- Branch: `codex/core-exp-codex-cli-failure-capture`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-codex-cli-failure-capture`

## Current Blockers

None.

## Revision 1

Focused reviewer `codex-cli-failure-capture-reviewer` reported
`issues_found` in commit `a07c65c`.

Revision 1 scope is no-model only:

- broaden hostname redaction beyond the narrow suffix list so the stated
  `hostnames_redacted: true` policy is accurate for structured failure capture,
  stdout/stderr artifacts, and bounded tail snippets
- add no-model regression coverage for timeout and unsafe patch content
- assert the contents of redacted stdout/stderr artifacts do not contain
  credential values, bearer-token-shaped strings, full URLs, hostnames, or IP
  address-shaped strings

No ACUT attempt, live BARCAROLLE model call, retry, second attempt, additional
specialist ACUT run, broad execution, further pilot attempt, or large
model-call batch is authorized.

Revision 1 delivered:

- replaced fixed-suffix hostname capture redaction with a generic DNS-label
  hostname-shape redactor used for redacted stdout/stderr artifacts and bounded
  failure tails
- added no-model regression coverage for `timeout` and
  `unsafe_patch_content`
- added artifact/tail assertions that credential values,
  bearer-token-shaped strings, full URLs, hostname-shaped values, and
  IP-address-shaped values are absent after redaction
- preserved temporary `CODEX_HOME`, BARCAROLLE provider override,
  provider-prefixed model catalog, non-interactive base instructions, dry-run,
  specialist context injection, and the outer adapter budget/ledger/redaction
  contract

## Changed Files

- `experiments/core_narrative/tools/codex_cli_patch_command.py`
- `experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- `experiments/core_narrative/reports/codex_cli_failure_capture.md`
- `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture/process.md`

## Verification

- PASS: `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- PASS: `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
- PASS: `python3 -m py_compile experiments/core_narrative/tools/codex_cli_patch_command.py experiments/core_narrative/tools/test_codex_cli_patch_command.py`
- PASS: `git diff --check`

All verification was no-model. No live BARCAROLLE model call, ACUT attempt,
retry, second attempt, additional specialist ACUT run, broad execution, further
pilot attempt, or large model-call batch was started. No record was appended to
`experiments/core_narrative/results/cost_ledger.jsonl`.

No `cli.log` file was inspected.

## Handoff

Focused no-model revision 1 repair delivered for Codex CLI failure capture.

The inner Codex CLI summary now records `failure_capture` and `workspace_patch`
metadata for nonzero exits, timeouts, unsafe patch content, and exit-zero
no-workspace-patch outcomes. Redacted stdout/stderr artifacts are written under
the command artifact directory, and bounded redacted tail snippets are included
only in the structured failure capture. Hostname redaction no longer depends on
a fixed suffix list. The outer adapter budget, ledger, redaction, empty-patch,
and normalized-result contract is unchanged.

Recommended next step: run a focused reviewer before any later coordinator
decision to authorize another bounded live attempt.
