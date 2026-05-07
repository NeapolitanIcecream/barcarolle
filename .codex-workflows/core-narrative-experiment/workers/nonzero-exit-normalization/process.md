# Process

status: delivered
updated: 2026-05-01T17:27:10+08:00

## Summary

Focused no-model harness repair worker for the reviewed nonzero-exit
`command_failed` path in `acut_patch_adapter.py`.

Pilot 004, pilot 005, and pilot 006 all reached the same cheap
Click-specialist cell, injected the reviewed specialist context pack, made
exactly one live model call, and ended before verifier with inner status
`codex_exec_failed`, zero-byte patch output, and one ledger append. Pilot 006
adds reviewed `failure_capture` / `workspace_patch` evidence sufficient to
classify the repeated failure without reading `cli.log`.

This worker must not start an ACUT attempt, live BARCAROLLE model call, retry,
second attempt, additional specialist ACUT run, broad execution, further pilot
attempt, or large model-call batch.

## Owned Paths

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_nonzero_exit_normalization.md`
- `experiments/core_narrative/results/raw/nonzero_exit_normalization*/**`
- `experiments/core_narrative/results/normalized/nonzero_exit_normalization*.json`
- `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/**`

## Branch / Worktree

- Branch: `codex/core-exp-nonzero-exit-normalization`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization`
- tmux session: `bcx-nonzero-exit-normalization`

## Scope

- Keep the reviewed empty-patch gate and unsafe-patch distinction intact.
- Improve the outer adapter result contract for nonzero-exit inner-command
  failures that do not yield a verifier-ready patch.
- Prefer stable structured normalization/classification over coordinator-local
  special casing of missing normalized files.
- Verification must be no-model only.

## Current Blockers

None.

## Changed Files

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_nonzero_exit_normalization.md`
- `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/process.md`

## Verification

- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`:
  passed, 3 tests.
- `python3 experiments/core_narrative/tools/test_codex_cli_patch_command.py`:
  passed, 4 tests.
- `python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py`:
  blocked by sandboxed macOS Python cache creation outside the writable
  worktree before project compilation.
- `PYTHONPYCACHEPREFIX=/tmp/nonzero-exit-normalization-pycache python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py`:
  passed.
- `git diff --check`: passed.

## Activity Log

- 2026-05-01T17:19:56+08:00: Worker dispatched from the coordinator after
  pilot 004/005/006 coordinator-local triage confirmed the structured evidence
  is sufficient and another live attempt on the same specialist cell is not
  justified yet. Read coordinator and relevant worker/review process files
  first. Do not inspect `cli.log`.
- 2026-05-01T17:27:10+08:00: Delivered focused no-model repair. Added
  regression coverage for a non-timeout nonzero inner-command exit with a
  zero-byte safe patch artifact, preserving exit-0 empty-diff and unsafe-patch
  distinctions. No ACUT attempt, live BARCAROLLE model call, retry, second
  attempt, additional specialist ACUT run, broad execution, further pilot
  attempt, large model-call batch, cost-ledger append, or `cli.log` inspection
  occurred.

## Handoff

The adapter now writes a normalized `infra_failed` result for
`command_failed` / nonzero-exit / no-verifier-ready-patch outcomes with
metadata `failure_class: nonzero_exit`, `no_patch_generated: false`, and
`verifier_ready_patch_available: false`. The raw adapter status and ledger
event remain `command_failed`; exit-0 empty diff remains `no_patch_generated`;
unsafe patch rejection remains distinct; timeout remains distinct.

Recommended next coordinator gate: focused no-model review before integration.
Any later live pilot attempt still requires a separate explicit coordinator
execution decision.
