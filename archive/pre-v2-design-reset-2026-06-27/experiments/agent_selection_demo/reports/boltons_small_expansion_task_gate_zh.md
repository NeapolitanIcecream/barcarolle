# Boltons small expansion task gate

生成时间：`2026-06-15T10:20:07+00:00`。

## Gate result

- Combined release-ready pool: `57` tasks。
- Current demo certified tasks: `35`。
- Phase 1 v2 release-eligible boltons tasks: `35`。
- Incremental v2 target commits: `22`。
- Frozen Selection: `30` tasks。
- Frozen later-check: `20` tasks。
- Time order: Selection `2015-04-19T00:13:33-07:00` to `2019-02-12T15:15:17-05:00`; later-check `2019-02-13T12:18:00+01:00` to `2023-05-07T01:25:38+08:00`。

## Source mix

| Source | Displayed tasks |
| --- | --- |
| canonical_history | 13 |
| clean_outcome_unseen | 4 |
| phase1_three_repo_paid_validation_incremental_boltons_v2 | 22 |
| supply_expansion_20260526 | 11 |

## Role counts

| Role | Count |
| --- | --- |
| later_check | 20 |
| selection | 30 |
| smoke_or_unused | 1 |
| unused | 6 |

## Freeze artifact

- Manifest: `experiments/agent_selection_demo/results/boltons_small_expansion_task_manifest.json`。
- Manifest task rows: `57`。
- Paid Agent calls made by this gate: `false`。

Selection 和 later-check 只按真实 `task_time` 排序切分；后续 rolling-origin 诊断必须继续使用真实时间，不得把普通 heldout label 当作时间 origin。
