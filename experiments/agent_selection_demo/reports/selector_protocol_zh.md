# Selector Protocol

生成日期：2026-06-14

## 数据集

- Task table: `experiments/agent_selection_demo/results/selector_task_table.csv`。
- Outcome matrix: `experiments/agent_selection_demo/results/selector_outcome_matrix.csv`。
- Task rows: `35`；outcome rows: `157`；policy-valid outcome rows: `157`。
- Final Selection candidate tasks: `20`；later/Holdout tasks: `10`。

## Frozen pseudo-future slice

- Origin ID: `boltons_selection_to_holdout_2026_06_14`。
- Origin time: `2022-01-16T07:08:40+08:00`。
- Candidate pool: original frozen Selection tasks (`20` tasks)。
- Later validation: original Holdout tasks (`10` tasks)。
- Top-2 repeat validation stage: `doubled_timeout_top2_repeat`。

## Leakage mask

selector 只能看到 Selection task metadata 和 frozen config；Selection outcomes、Holdout outcomes、doubled-timeout repeat outcomes 都在 task IDs 固定后才 join。

## Invalid-cell policy

solver timeout、invalid diff、normal verifier failure、policy violation 等 terminal statuses 计为 fail；只有 verifier outage、invalid task、oracle flake 计为 NA。pairwise metrics 只使用 common policy-valid cells。

## Fixed budgets and seeds

- Budgets: `[10, 20]`。
- Random seeds: `0..999`。

## Decision defaults

- Action margin: `0.05`。
- Minimum common valid selected tasks: `8`。
- Tie epsilon: `0.05`。
- Bootstrap iterations: `1000`。

这些阈值在 final evaluation 前冻结；如果后续 package 需要调整，只能在 preregistration 中明确记录，并且不能根据 final later/Holdout 结果回调。
