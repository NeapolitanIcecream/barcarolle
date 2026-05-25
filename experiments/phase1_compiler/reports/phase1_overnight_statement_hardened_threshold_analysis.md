# Statement-Hardened Threshold Analysis

Predictive validity established: `False`.
Primary recommendation: `stratified_absolute_gap_ci` with gap threshold `0.15`.

The current run cannot establish predictive validity because no quantitative success rule was preregistered, and the observed repo gaps exceed the candidate 0.15 absolute-gap rule.

## Repo/Split Intervals

| Repo split | Pass | Cells | Pass rate | Wilson 95 |
| --- | --- | --- | --- | --- |
| attrs/B_eval | 6 | 8 | 0.75 | {"high": 0.9285, "low": 0.4093} |
| attrs/H_future | 4 | 8 | 0.5 | {"high": 0.7848, "low": 0.2152} |
| boltons/B_eval | 7 | 8 | 0.875 | {"high": 0.9776, "low": 0.5291} |
| boltons/H_future | 4 | 8 | 0.5 | {"high": 0.7848, "low": 0.2152} |

## Candidate Thresholds

| Name | Rule | Current result | Rationale |
| --- | --- | --- | --- |
| stratified_absolute_gap_ci | For each preregistered repo/split stratum, abs(B_eval pass rate - H_future pass rate) <= 0.15, with a preregistered confidence interval or precision rule and minimum scoreable cells. | fails_observed_gap_and_was_not_preregistered | This directly tests whether benchmark selection predicts future target-repo outcomes without changing the ACUT harness. |
| repo_or_task_family_rank_correlation | Across at least four repos or six task-family strata, rank correlation between B_eval and H_future pass rates >= 0.60. | not_applicable_two_repos | Useful as a secondary diagnostic, but too easy to satisfy with only two repos or unstable strata. |
| calibration_error_threshold | Mean absolute calibration error between B_eval-predicted and H_future pass rates <= 0.10, with a preregistered uncertainty rule. | fails_observed_error | Matches the benchmark-compiler claim, but needs enough strata to avoid fitting noise. |
| conditional_holdout_lower_bound | H_future pass rate must be at least max(0.55, B_eval pass rate - 0.15) in every preregistered repo. | fails_attrs_and_boltons | Simple to audit, but should be paired with scoreable-cell minimums and no post-hoc resplitting. |
