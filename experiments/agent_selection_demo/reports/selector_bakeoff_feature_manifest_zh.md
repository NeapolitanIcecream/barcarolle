# Selector Bakeoff Feature Manifest

生成日期：2026-06-14

## Artifacts

- Task features: `experiments/agent_selection_demo/results/selector_bakeoff_task_features.csv`。
- Outcome matrix: `experiments/agent_selection_demo/results/selector_bakeoff_outcome_matrix.csv`。
- Feature rows: `281`；outcome rows: `622`。

## Sources

| Source | Rows |
| --- | --- |
| boltons_demo_development | 30 |
| phase1_blocked_split_heldout_development | 60 |
| phase1_original_three_repo_split_heldout_final_candidate | 96 |
| phase1_repo_specific_earliest_time_bucket_cutoff_development | 95 |

## Leakage mask

| Field | Status |
| --- | --- |
| development_outcome_difficulty | development_outcome_only |
| development_outcome_disagreement | development_outcome_only |
| historical_difficulty | metadata_only |
| historical_disagreement | leakage_safe_historical_outcome |
| metadata_informativeness | metadata_only |
| pairwise_informativeness | leakage_safe_historical_outcome |
| policy_outcome_value | not_allowed_for_final |

final selector scoring 只允许使用 `metadata_only` 字段。本次没有 leakage-safe historical current-Agent disagreement，也没有 leakage-safe historical generic-Agent disagreement；因此 informative arm 必须称为 `metadata_informativeness`。

Final source `phase1_original_three_repo_split_heldout_final_candidate` 的 development outcome feature columns 保持空值：`True`。

## Audit conclusion

Final selector scoring may use only fields with metadata_only status in this bakeoff; leakage-safe historical outcome fields are listed but unavailable.
