# Process

status: delivered
updated: 2026-04-28T15:13:51+08:00

## Summary

Prepared the budget-constrained core subset run manifest without starting broad ACUT execution or model calls. The manifest records the active four-core-ACUT slice, task counts, one-primary-attempt policy, LLM environment variable names only, budget caps, ledger requirements, and locked pre-run inputs.

## Owned Paths

- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `.codex-workflows/core-narrative-experiment/workers/execution-planner/process.md`

## Files Changed Or Inspected

Changed:

- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `.codex-workflows/core-narrative-experiment/workers/execution-planner/process.md`

Inspected:

- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle-wt-pre-run-lock-reviewer/.codex-workflows/core-narrative-experiment/workers/pre-run-lock-reviewer/process.md`
- `/Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock/.codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/process.md`
- `/Users/chenmohan/gits/barcarolle-wt-general-lock/.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`

## Current Blockers

None for execution planning. Broad ACUT execution remains not started.

## Handoff

Next allowed step is no-model preflight work for concrete RBench/RWork task manifests and any infrastructure smoke checks. Do not start ACUT model calls until the coordinator explicitly records execution start.
