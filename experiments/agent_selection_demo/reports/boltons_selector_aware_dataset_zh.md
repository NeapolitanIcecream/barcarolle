# Boltons selector-aware dataset

生成时间：`2026-06-16T03:16:03+00:00`。

- Task features: `experiments/agent_selection_demo/results/boltons_selector_aware_task_features.csv`。
- Outcome matrix: `experiments/agent_selection_demo/results/boltons_selector_aware_outcome_matrix.csv`。
- Displayed tasks with outcomes: `50`。
- Complete task outcome rows: `50`。
- Outcome rows: `200`。
- Unused manifest rows without outcome matrix cells: `7`。

## Feature leakage status

- `metadata_informativeness` 在每个 origin 的历史池内重新计算，避免使用未来任务分布。
- `policy_outcome_value`、`verified_pass`、`terminal_status` 只在 selected task IDs 冻结后 join。

## Selector eligibility

| Selector | Status | Reason |
| --- | --- | --- |
| cod_lite | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| flc | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_50_50 | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_60_40 | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_70_30 | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_70_30_flc_rep | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_70_30_no_caps | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| hrd_v3_70_30_no_recency | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| informativeness_only | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| representative_only | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| ro_lsp | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| rsq_v2 | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| rsq_v2_no_caps | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| rsq_v2_no_recency | leakage_safe_final_eligible | metadata-only selection over historical candidate rows |
| saes_lite | leakage_safe_final_eligible | sequential replay observes only seed-batch outcomes selected from the historical pool before choosing the second batch |

数据集只读取 committed sanitized final matrix 和 task manifest；没有新 paid cells，也没有读取 raw prompts/completions/workspaces。
