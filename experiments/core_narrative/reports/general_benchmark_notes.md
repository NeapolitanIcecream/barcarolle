# General Benchmark Notes

## Basis

`G_score` remains a direct-run SWE-Bench Pro Public slice, not public leaderboard scores. The selected basis is now the revised six-task default `gscore_swebench_pro_public_6_v1`, defined in `experiments/core_narrative/configs/general_benchmark.yaml`.

The upstream general benchmark basis is still authoritative for the benchmark population, dataset snapshot, data hash, evaluator revision, visible-context rules, and anti-cherry-picking controls. The only change is the revised default run profile: 6 `G_score` tasks and one primary attempt per ACUT/task.

The pinned population is `ScaleAI/SWE-bench_Pro` `default/test` at Hugging Face revision `7ab5114912baf22bb098818e604c02fe7ad2c11f`. The data file is `data/test-00000-of-00001.parquet`, committed at `2dd05cab1572ce1d59fdc699b386692ff8e0bd29`, with SHA256 `c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8` and Xet hash `6aee72308d8c16c707416780f6d05155ec7aa7591fdf8bb715fbe1b0f9502cf3`. The evaluator remains `scaleapi/SWE-bench_Pro-os` revision `0c64e26f00b9c190432de7fc520c8ceed5c25518`.

## Materialization Status

Status: blocked.

Concrete task IDs were not materialized. The pinned dataset rows are not available in the local Hugging Face cache or local worktrees, shell network cannot resolve the dataset or evaluator hosts, and Docker is not running for the local evaluator fallback. The browser-accessible Hugging Face pages verify the public dataset metadata, row count, and pointer hashes, but they expose only preview rows, not the complete 731-row `(repo, instance_id)` population required to compute the deterministic selection.

Smallest next action: provide or fetch the pinned parquet file above, verify its SHA256, then compute the six locked IDs with the frozen salt `barcarolle-core-narrative-gscore-v1` before any ACUT patch-generation run.

## Six-Task Selection Rule

The six-task default adapts the delivered 22-task basis without changing its selection principle:

- Group all 731 pinned rows by `repo`.
- Sort repo groups lexicographically by repo string.
- Within each repo group, sort by `sha256("barcarolle-core-narrative-gscore-v1\n" + instance_id)`, then by `instance_id`.
- Select the first two rows from each repo group in repo order until six rows are selected.
- Build the replacement reserve from all remaining rows sorted by the same hash key and `instance_id`.
- Do not inspect ACUT results, public per-task results, gold patches, or test outcomes while selecting.

No replacement IDs are recorded because no primary IDs are locked yet and no gold-patch smoke evaluation could be run.

## Anti-Cherry-Picking Controls

- Freeze the dataset snapshot, evaluator revision, selection salt, and slice algorithm before ACUT runs.
- Select by hash over `instance_id`, stratified only by repository.
- Run the same locked task IDs, visible context fields, budget policy, evaluator, and scoring formula for every ACUT.
- Count patch apply failures, invalid submissions, timeouts, verification failures, and ACUT runtime errors as zero.
- Allow replacement only for global infrastructure failures found by gold-patch smoke tests before ACUT scoring begins.
- Do not drop tasks after seeing ACUT results.
- Treat public leaderboard scores as background only; they must not decide task inclusion, ACUT rank, or post-hoc interpretation.

## Self-Check

- Revised default is recorded as 6 `G_score` tasks and one primary attempt per ACUT/task.
- Dataset snapshot, data hash, row count, and evaluator revision are explicit.
- No invented task IDs were added.
- No broad ACUT execution or model calls were made.
- The remaining blocker is access to the pinned dataset rows and evaluator infrastructure needed to compute and smoke-test the concrete IDs.
