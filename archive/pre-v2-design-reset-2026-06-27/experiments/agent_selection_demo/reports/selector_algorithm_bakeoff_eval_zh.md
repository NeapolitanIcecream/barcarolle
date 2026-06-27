# Selector Algorithm Bakeoff Eval

生成日期：2026-06-14

## Scope

Development sources: `boltons_demo_development, phase1_blocked_split_heldout_development, phase1_repo_specific_earliest_time_bucket_cutoff_development`。
Final source excluded from tuning: `phase1_original_three_repo_split_heldout_final_candidate`。
Decision wrapper v2 thresholds: `{'action_margin': 0.05, 'bootstrap_iterations': 1000, 'confidence_level': 0.8, 'lcb_tolerance': 0.0, 'min_common_valid': 8, 'tie_epsilon': 0.05}`。

## Results

| Config | Validated | Coverage | False | Regret | TopPair | MAE | Rel MAE |
| --- | --- | --- | --- | --- | --- | --- | --- |
| hrd_v3_70_30 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.122643 | 0.186529 |
| hrd_v3_60_40 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.131902 | 0.125115 |
| hrd_v3_50_50 | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.131902 | 0.125115 |
| hrd_v3_70_30_no_caps | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.137795 | 0.086028 |
| cod_lite | 1.0 | 1.0 | 0.0 | 0.0 | 1.0 | 0.142087 | 0.05756 |
| flc | 0.666667 | 1.0 | 0.333333 | 0.133333 | 0.666667 | 0.214815 | -0.424833 |
| hrd_v3_70_30_no_recency | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.128704 | 0.146327 |
| rsq_v2_no_recency | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.136869 | 0.09217 |
| saes_lite | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.140741 | 0.066488 |
| informativeness_only | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.163889 | -0.087049 |
| ro_lsp | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.164647 | -0.092077 |
| rsq_v2 | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.170202 | -0.128922 |
| rsq_v2_no_caps | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.170202 | -0.128922 |
| representative_only | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.170202 | -0.128922 |
| hrd_v3_70_30_flc_rep | 0.666667 | 0.666667 | 0.0 | 0.0 | 1.0 | 0.184259 | -0.22216 |

## Top candidates

Top 3 by decision quality: `hrd_v3_70_30, hrd_v3_60_40, hrd_v3_50_50`。
Development winner: `hrd_v3_70_30`，validated recommendation rate `1.0`，coverage `1.0`，false recommendation rate `0.0`。

## Random comparison

Strongest random by MAE: `module_stratified_random`。
Winner MAE: `0.122643`；strong random MAE mean: `0.150765`；relative improvement: `0.186529`。

## Ablations

- Representative-only: implemented via RSQ v2 representative arm.
- Informativeness-only: implemented via metadata_informativeness fallback.
- Historical outcome features: not run as a final-eligible ablation because no leakage-safe historical Agent-disagreement feature is available.
- Recency: rsq_v2_no_recency and hrd_v3_70_30_no_recency.
- Caps: rsq_v2_no_caps and hrd_v3_70_30_no_caps.
- Wrapper comparison: both wrappers evaluated on each selector config.

MAE 是辅助 tie-breaker；本表按 Agent-selection decision quality 排序。
