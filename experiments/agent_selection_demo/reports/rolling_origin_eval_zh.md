# Rolling-origin Evaluation

生成日期：2026-06-13T13:37:07+00:00

本评估从 frozen protocol 和 window inventory 读取 committed sanitized metric slices。没有运行 paid calls，也没有读取 raw prompts、raw completions、transcripts 或 workspaces。

## Primary metrics

| Design | MAE | RMSE | Signed error | Catastrophic miss | Slices |
| --- | --- | --- | --- | --- | --- |
| block_plus_shrinkage_weighted | 0.289367 | 0.32441 | -0.026633 | 0.833333 | 18 |
| block_randomized_stratified | 0.2857 | 0.325267 | -0.0303 | 0.777778 | 18 |
| completed_blocked_split_supplement | 0.140733 | 0.168746 | 0.1074 | 0.333333 | 6 |
| coverage_constrained_unweighted | 0.209011 | 0.258881 | -0.043267 | 0.555556 | 18 |
| demo_selection_set | 0.136111 | 0.158455 | 0.05 | 0.5 | 4 |
| repo_stratified_by_target_profile | 0.23435 | 0.28354 | -0.042339 | 0.555556 | 18 |
| repo_unweighted_same_budget | 0.224167 | 0.268177 | -0.024744 | 0.666667 | 18 |
| seeded_random_same_budget | 0.252499 | 0.299514 | -0.035303 | 0.733333 | 90 |
| temporal_recent_baseline | 0.2149 | 0.257954 | -0.061789 | 0.555556 | 18 |

## Baseline comparison

Best simple baseline: `temporal_recent_baseline` MAE `0.2149`.
Best Barcarolle candidate: `coverage_constrained_unweighted` MAE `0.209011`.
Candidate minus best simple MAE: `-0.005889`.
Result label: `candidate_beats_best_simple_baseline`.

## Rank and regret

Rank groups evaluated: `64`; top-rank agreement rate: `0.8125`.
Regret groups evaluated: `64`; mean regret: `0.041552`; max regret: `0.4`.

## Claim boundary

该结果最多支持 no-paid retrospective/directional evidence。即使 candidate beats best simple baseline，也不能从 retrospective artifacts 单独 claim predictive validity。
