# Phase 1 Attrs H_future Statement-Risk Sensitivity

Generated: `2026-05-25T01:34:18Z`.

These views are sensitivity analysis only. They do not correct, repair, rerun, or overwrite the paid result.

## Summary

- Original attrs H_future remains `0.142857` pass rate over `7` scoreable cells.
- Material statement-quality risk tasks: `4`.
- Strict clean statement view: `insufficient_clean_attrs_h_future_evidence`.

## Views

### original_attrs_h_future

- Included tasks: `['attrs__hist__012', 'attrs__hist__013', 'attrs__hist__023', 'attrs__hist__027']`.
- Excluded tasks: `[]`.
- Scoreable cells: `7`.
- Verified pass/fail: `1/6`.
- Policy violations: `1`.
- Pass rate: `0.142857`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': 0.732143}`.
- Interpretation: `original_paid_observation_preserved_as_1_of_7_scoreable_pass`.

### exclude_policy_violation_only

- Included tasks: `['attrs__hist__012', 'attrs__hist__013', 'attrs__hist__023', 'attrs__hist__027']`.
- Excluded tasks: `[]`.
- Scoreable cells: `7`.
- Verified pass/fail: `1/6`.
- Policy violations: `1`.
- Pass rate: `0.142857`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': 0.732143}`.
- Interpretation: `policy_violation_cell_remains_non_scoreable_so_scoreable_metric_matches_original`.

### exclude_highest_risk_task_013

- Included tasks: `['attrs__hist__012', 'attrs__hist__023', 'attrs__hist__027']`.
- Excluded tasks: `['attrs__hist__013']`.
- Scoreable cells: `5`.
- Verified pass/fail: `1/4`.
- Policy violations: `1`.
- Pass rate: `0.2`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': 0.675}`.
- Interpretation: `sensitivity_only_not_corrected_score; removing the highest PR-context risk task still leaves attrs H_future far below B_eval`.

### exclude_highest_risk_tasks_013_027

- Included tasks: `['attrs__hist__012', 'attrs__hist__023']`.
- Excluded tasks: `['attrs__hist__013', 'attrs__hist__027']`.
- Scoreable cells: `4`.
- Verified pass/fail: `1/3`.
- Policy violations: `0`.
- Pass rate: `0.25`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': 0.625}`.
- Interpretation: `sensitivity_only_not_corrected_score; remaining evidence is smaller and still below B_eval`.

### strict_clean_statement_only

- Included tasks: `[]`.
- Excluded tasks: `['attrs__hist__012', 'attrs__hist__013', 'attrs__hist__023', 'attrs__hist__027']`.
- Scoreable cells: `0`.
- Verified pass/fail: `0/0`.
- Policy violations: `0`.
- Pass rate: `None`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': None}`.
- Interpretation: `insufficient_clean_attrs_h_future_evidence`.

### all_statement_risk_excluded

- Included tasks: `[]`.
- Excluded tasks: `['attrs__hist__012', 'attrs__hist__013', 'attrs__hist__023', 'attrs__hist__027']`.
- Scoreable cells: `0`.
- Verified pass/fail: `0/0`.
- Policy violations: `0`.
- Pass rate: `None`.
- Comparison to attrs B_eval: `{'attrs_b_eval_pass_rate': 0.875, 'attrs_b_eval_scoreable_cells': 8, 'attrs_b_eval_verified_fail': 1, 'attrs_b_eval_verified_pass': 7, 'absolute_pass_rate_gap_vs_attrs_b_eval': None}`.
- Interpretation: `insufficient_clean_attrs_h_future_evidence`.

## Boundary

Excluding questionable tasks is a diagnostic sensitivity view, not a corrected score. If clean statement evidence is empty or too small, the correct conclusion is insufficient clean attrs H_future evidence.
