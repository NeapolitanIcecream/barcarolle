# Process

status: blocked
updated: 2026-04-28T12:27:17+08:00

## Summary

General benchmark pre-run lock is blocked. The upstream 22-task basis is internally inconsistent with the revised default six-task run profile, so the owned config/report now record the six-task default, one primary attempt per ACUT/task, the pinned dataset snapshot/hash/evaluator revision, and the exact materialization blocker. Concrete IDs were not invented.

## Owned Paths

- `experiments/core_narrative/configs/general_benchmark.yaml`
- `experiments/core_narrative/reports/general_benchmark_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`

## Files Changed Or Inspected

- `.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`
- `experiments/core_narrative/configs/general_benchmark.yaml`
- `experiments/core_narrative/reports/general_benchmark_notes.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle-wt-general-benchmark/.codex-workflows/core-narrative-experiment/workers/general-benchmark/process.md`
- local Hugging Face cache paths checked; no `ScaleAI/SWE-bench_Pro` cache present
- local worktrees/temp paths checked; no `SWE-bench_Pro`, `SWE-bench_Pro-os`, or pinned parquet copy present

## Current Blockers

- Cannot materialize `G_score` IDs: shell network cannot resolve `datasets-server.huggingface.co`, `huggingface.co`, or `github.com`; no local pinned dataset copy is present.
- Cannot verify originally proposed local Docker fallback: Docker daemon is not reachable.
- Browser-accessible dataset pages expose the pinned row count and pointer hashes, but not the complete 731-row `(repo, instance_id)` population needed to compute the deterministic six-task selection.

## Handoff

Blocked delivery recorded in owned artifacts. Smallest next action: provide or fetch `ScaleAI/SWE-bench_Pro` `default/test` at Hugging Face revision `7ab5114912baf22bb098818e604c02fe7ad2c11f` with parquet SHA256 `c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8`, then compute the locked IDs with the recorded salt and selection rule.
