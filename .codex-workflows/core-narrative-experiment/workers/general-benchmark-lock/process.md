# Process

status: delivered
updated: 2026-04-28T14:34:02+08:00

## Summary

General benchmark pre-run lock is closed for task ID materialization. The pinned SWE-Bench Pro parquet was downloaded anonymously, SHA256 matched the required hash, and the revised six-task `G_score` default was materialized from the recorded salt/selection rule without inventing IDs. Docker/OrbStack is reachable; no evaluator or ACUT scoring run was started.

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
- `experiments/core_narrative/cache/swebench_pro/test-00000-of-00001.parquet` created as an ignored local cache
- `experiments/core_narrative/cache/swebench_pro/.venv` created as an ignored local pyarrow/pyyaml reader environment

## Current Blockers

None for task ID materialization. Pre-ACUT gold-patch smoke evaluation remains a future execution-readiness step before scored ACUT runs.

## Rerun Progress

- 2026-04-28T14:26:47+08:00: Restarted pre-run lock after environment recovery signal. Will fetch pinned SWE-Bench Pro parquet anonymously unless rate-limited; no IDs will be invented.
- 2026-04-28T14:34:02+08:00: Downloaded pinned parquet, verified SHA256 `c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8`, confirmed 731 rows and 11 repos, and locked six `G_score` IDs from the recorded rule.

## Self-Checks

- `curl -L --fail --retry 3 --retry-delay 2` downloaded the pinned parquet anonymously in 2.52s.
- `shasum -a 256 experiments/core_narrative/cache/swebench_pro/test-00000-of-00001.parquet` matched the required SHA256.
- `git check-ignore -v experiments/core_narrative/cache/swebench_pro/test-00000-of-00001.parquet experiments/core_narrative/cache/swebench_pro/.venv` confirmed local cache artifacts are ignored.
- `ruby -e 'require "yaml"; ...'` confirmed `general_benchmark.yaml` parses, status is `locked`, and six locked IDs are recorded.
- Pyarrow selection verification read only `repo` and `instance_id` columns and confirmed the YAML locked IDs/selection keys match the deterministic rule: 731 rows, 11 repos, 6 locked IDs.
- `docker context show` returned `orbstack`; Docker client/server versions are `29.4.0`.
- `git diff --check` passed.

## Handoff

General benchmark task ID lock delivered. Broad ACUT execution remains blocked until coordinator review/integration and any required pre-ACUT gold-patch smoke decision.
