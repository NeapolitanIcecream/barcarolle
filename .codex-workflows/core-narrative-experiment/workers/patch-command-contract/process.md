# Process

status: working
updated: 2026-04-29T11:06:52+08:00

## Summary

Focused implementation started to close `patch_generation_command_gap` with a
BARCAROLLE-env-only patch-generation command path. This worker must not start
broad ACUT execution, live ACUT model calls, or live patch-generation attempts.

## Owned Paths

- `experiments/core_narrative/tools/barcarolle_patch_command.py`
- `experiments/core_narrative/reports/patch_command_contract.md`
- `experiments/core_narrative/results/normalized/patch_command_contract*.json`
- `experiments/core_narrative/results/raw/patch_command_contract*/**`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`

## Branch / Worktree

- Branch: `codex/core-exp-patch-command-contract`
- Worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

## Files Changed Or Inspected

Changed:

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/prompt.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/run_worker.sh`

Inspected:

- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/process.md`

## Current Blockers

None.

## Checks Run

- Pending.

## Handoff

Worker is running. Coordinator should wait for `status: delivered` or
`status: blocked` before starting review or requesting user input.
