# Process

status: working
updated: 2026-05-01T17:19:56+08:00

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

## Activity Log

- 2026-05-01T17:19:56+08:00: Worker dispatched from the coordinator after
  pilot 004/005/006 coordinator-local triage confirmed the structured evidence
  is sufficient and another live attempt on the same specialist cell is not
  justified yet. Read coordinator and relevant worker/review process files
  first. Do not inspect `cli.log`.

## Handoff

Update this file before meaningful phases. If the normalized-result contract
cannot be repaired or verified without a live BARCAROLLE model call, set
`status: blocked`, explain the concrete no-model blocker, and stop.
