# Local Bakeoff Ablation

Best local candidate: `temporal_recent_baseline`.
Mainline recommendation: `keep_repo_stratified_as_mainline`.

| Design | Variants | MAE | Improvement | Worst max gap | Miss rate | Stable |
| --- | --- | --- | --- | --- | --- | --- |
| block_plus_shrinkage_weighted | 1 | 0.354167 | -0.888891 | 0.458334 | 0.5 | False |
| block_randomized_stratified | 5 | 0.2875 | -0.533333 | 0.625 | 0.4 | False |
| coverage_constrained_unweighted | 1 | 0.3125 | -0.666667 | 0.375 | 0.5 | False |
| old_weighted_target_profile | 1 | 0.531451 | -1.834405 | 0.748092 | 0.5 | False |
| repo_stratified_by_target_profile | 1 | 0.1875 | 0.0 | 0.25 | 0.0 | False |
| repo_unweighted_same_budget | 1 | 0.1875 | 0.0 | 0.25 | 0.0 | False |
| seeded_random_same_budget | 5 | 0.2375 | -0.266667 | 0.75 | 0.3 | False |
| temporal_recent_baseline | 1 | 0.0 | 1.0 | 0.0 | 0.0 | False |

Local evidence is too sparse and seed-sensitive to promote a new weighted or blocked compiler over the simple stratified baseline.
