# Process

status: delivered
updated: 2026-04-28T09:38:37+08:00

## Summary

Delivered the general benchmark basis for `G_score`. The selected basis is a direct-run SWE-Bench Pro Public 22-task slice, frozen by dataset snapshot, data hash, evaluator revision, and deterministic per-repository hash selection. Public leaderboard scores are explicitly marked as background only, not `G_score` evidence.

## Owned Paths

- `experiments/core_narrative/configs/general_benchmark.yaml`
- `experiments/core_narrative/reports/general_benchmark_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/general-benchmark/process.md`

## Files Changed Or Inspected

- `.codex-workflows/core-narrative-experiment/workers/general-benchmark/process.md` inspected and updated.
- `docs/experiments/core-narrative-experiment-plan.md` inspected.
- `.codex-workflows/core-narrative-experiment/shared/experiment-brief.md` inspected.
- `.codex-workflows/core-narrative-experiment/shared/worker-contract.md` inspected.
- `.codex-workflows/core-narrative-experiment/workers/general-benchmark/prompt.md` inspected.
- `experiments/core_narrative/configs/general_benchmark.yaml` inspected and updated.
- `experiments/core_narrative/reports/general_benchmark_notes.md` created.
- `experiments/core_narrative/README.md` inspected.

## Current Blockers

None.

## Git State

branch: codex/core-exp-general-benchmark
worktree: /Users/chenmohan/gits/barcarolle-wt-general-benchmark
worktree state before delivery commit: only owned artifact changes present

## Handoff

Artifacts are self-checked. YAML parses successfully. The only execution limitation is that this worker cannot materialize concrete SWE-Bench Pro instance IDs because local network access is blocked; the manifest freezes a deterministic selection rule and requires the coordinator to materialize and lock the IDs before any ACUT run.
