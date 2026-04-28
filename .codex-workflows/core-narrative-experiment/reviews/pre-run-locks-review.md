# Pre-Run Locks Review

status: no_issues

## Summary

Both pre-run locks close their scoped gates.

`repo-runtime-lock` locks the primary repository to `pallets/click` commit
`8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`, uses the ignored
`experiments/core_narrative/external_repos/click` checkout, records plausible
clone/install/smoke/full pytest timings with passing results, and keeps the
revised default at 8 `RBench`, 6 `RWork`, and one primary attempt per task.
Fallbacks were not needed after the primary succeeded.

`general-benchmark-lock` records anonymous fetch/cache of the pinned SWE-Bench
Pro parquet, verifies SHA256
`c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8`, locks
exactly six `G_score` IDs from the recorded salt and selection rule, and keeps
one primary attempt per ACUT/task. Cache and reader environment artifacts are
ignored by Git. Docker availability is recorded, and no evaluator scoring or
broad ACUT execution was started.

The two delivery commits modify only their expected process/config/report files,
so the Wave 0 r5 LLM access, cost, redaction, and patch-artifact gates were not
reopened or changed. Broad ACUT execution remains blocked pending coordinator
review/integration.

## Findings

1. No issues found.

## Required Closure

None.

## Self-Checks

- Read the required coordinator and worker process files; did not inspect any
  `cli.log` file and did not make ACUT model calls.
- Confirmed delivery commit `029fbdf` changes only the repo-runtime process,
  `target_repositories.yaml`, and `repo_scout_notes.md`.
- Confirmed delivery commit `88acbad` changes only the general-benchmark-lock
  process, `general_benchmark.yaml`, and `general_benchmark_notes.md`.
- Verified the ignored Click checkout is ignored by `.gitignore`, appears only
  as ignored in Git status, and resolves to the recorded commit.
- Parsed `target_repositories.yaml` and confirmed locked status, concrete
  40-character checkout commit, 8 `RBench`, 6 `RWork`, and one primary attempt
  per task.
- Verified the cached parquet path and temporary reader venv are ignored by
  `.gitignore`.
- Recomputed the cached parquet SHA256 and confirmed it matches the required
  hash.
- Recomputed the six locked `G_score` IDs from the pinned parquet using only the
  `repo` and `instance_id` columns, the recorded salt, and the recorded
  selection rule; the recomputed rows matched the YAML lock exactly.
- Checked result artifacts in the general-lock worktree; only the existing
  ledger/placeholders were present, with no broad raw scoring output.
- Ran count-only high-confidence credential pattern scans over the two workers'
  changed artifacts; no matches were found.
