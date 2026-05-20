# General Benchmark Notes

## Basis

`G_score` remains a direct-run SWE-Bench Pro Public slice, not public leaderboard scores. The selected basis is now the revised six-task default `gscore_swebench_pro_public_6_v1`, defined in `experiments/core_narrative/configs/general_benchmark.yaml`.

The upstream general benchmark basis is still authoritative for the benchmark population, dataset snapshot, data hash, evaluator revision, visible-context rules, and anti-cherry-picking controls. The only change is the revised default run profile: 6 `G_score` tasks and one primary attempt per ACUT/task.

The pinned population is `ScaleAI/SWE-bench_Pro` `default/test` at Hugging Face revision `7ab5114912baf22bb098818e604c02fe7ad2c11f`. The data file is `data/test-00000-of-00001.parquet`, committed at `2dd05cab1572ce1d59fdc699b386692ff8e0bd29`, with SHA256 `c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8` and Xet hash `6aee72308d8c16c707416780f6d05155ec7aa7591fdf8bb715fbe1b0f9502cf3`. The evaluator remains `scaleapi/SWE-bench_Pro-os` revision `0c64e26f00b9c190432de7fc520c8ceed5c25518`.

## Materialization Status

Status: locked.

The pinned parquet was fetched anonymously from Hugging Face at revision
`7ab5114912baf22bb098818e604c02fe7ad2c11f` into the ignored cache path
`experiments/core_narrative/cache/swebench_pro/test-00000-of-00001.parquet`.
SHA256 verification matched
`c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8`.

The materialized population has 731 rows and 11 repositories. The revised
six-task default is locked to:

| Ordinal | Repo | Instance ID | Selection key prefix |
| --- | --- | --- | --- |
| 1 | `NodeBB/NodeBB` | `instance_NodeBB__NodeBB-51d8f3b195bddb13a13ddc0de110722774d9bb1b-vf2cf3cbd463b7ad942381f1c6d077626485a1e9e` | `047ff911070e` |
| 2 | `NodeBB/NodeBB` | `instance_NodeBB__NodeBB-84dfda59e6a0e8a77240f939a7cb8757e6eaf945-v2c59007b1005cd5cd14cbb523ca5229db1fd2dd8` | `0721e5783d7d` |
| 3 | `ansible/ansible` | `instance_ansible__ansible-d33bedc48fdd933b5abd65a77c081876298e2f07-v0f01c69f1e2528b935359cfe578530722bca2c59` | `017a871e5635` |
| 4 | `ansible/ansible` | `instance_ansible__ansible-984216f52e76b904e5b0fa0fb956ab4f1e0a7751-v1055803c3a812189a1133297f7f5468579283f86` | `048c1c04ca17` |
| 5 | `element-hq/element-web` | `instance_element-hq__element-web-776ffa47641c7ec6d142ab4a47691c30ebf83c2e` | `0129076119cd` |
| 6 | `element-hq/element-web` | `instance_element-hq__element-web-5dfde12c1c1c0b6e48f17e3405468593e39d9492-vnan` | `05758b206557` |

Docker/OrbStack is reachable (`orbstack`, Docker client/server `29.4.0`), but
no evaluator or ACUT scoring run was started. Smallest next action before
scored ACUT runs: run pre-ACUT gold-patch smoke evaluation for the locked
six-task slice with the pinned evaluator.

## Six-Task Selection Rule

The six-task default adapts the delivered 22-task basis without changing its selection principle:

- Group all 731 pinned rows by `repo`.
- Sort repo groups lexicographically by repo string.
- Within each repo group, sort by `sha256("barcarolle-core-narrative-gscore-v1\n" + instance_id)`, then by `instance_id`.
- Select the first two rows from each repo group in repo order until six rows are selected.
- Build the replacement reserve from all remaining rows sorted by the same hash key and `instance_id`.
- Do not inspect ACUT results, public per-task results, gold patches, or test outcomes while selecting.

No replacement IDs are recorded because no pre-ACUT global infrastructure
failure has been found. The reserve preview is recorded in
`general_benchmark.yaml`; any replacement must still be locked before the first
ACUT patch-generation run.

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
- Concrete task IDs were computed from the pinned parquet by reading only `repo`
  and `instance_id` columns, using the frozen salt and selection rule.
- No invented task IDs were added.
- No broad ACUT execution or model calls were made.
- Remaining pre-execution work is gold-patch smoke evaluation of the locked
  six-task slice, not task ID materialization.
