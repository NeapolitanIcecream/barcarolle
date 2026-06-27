# Local Bakeoff Validation Results

Validation mode: `pseudo_future_validation`.
True rolling-origin support: `too_small_for_stable_true_rolling_origin`.

| Design | Variants | MAE mean | MAE min | MAE max | Worst max gap | Miss rate |
| --- | --- | --- | --- | --- | --- | --- |
| block_plus_shrinkage_weighted | 1 | 0.354167 | 0.354167 | 0.354167 | 0.458334 | 0.5 |
| block_randomized_stratified | 5 | 0.2875 | 0.1875 | 0.4375 | 0.625 | 0.4 |
| coverage_constrained_unweighted | 1 | 0.3125 | 0.3125 | 0.3125 | 0.375 | 0.5 |
| old_weighted_target_profile | 1 | 0.531451 | 0.531451 | 0.531451 | 0.748092 | 0.5 |
| repo_stratified_by_target_profile | 1 | 0.1875 | 0.1875 | 0.1875 | 0.25 | 0.0 |
| repo_unweighted_same_budget | 1 | 0.1875 | 0.1875 | 0.1875 | 0.25 | 0.0 |
| seeded_random_same_budget | 5 | 0.2375 | 0.0625 | 0.625 | 0.75 | 0.3 |
| temporal_recent_baseline | 1 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 |

No design is promoted from a single favorable seed or one repo only.
