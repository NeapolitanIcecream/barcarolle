# Phase 1 Next Research Decision

Generated: `2026-05-23T11:32:39+00:00`.

## Main Conclusion

This two-repo Phase 1 pilot did not establish predictive validity and should be reported as a negative or underpowered pilot before spending on more validation.

Primary decision label: `report_two_repo_negative_or_underpowered_pilot`.

## Evidence

- Policy violation count is 1 and the violation remains a benchmark boundary failure, not a scoreable fail.
- Attrs H_future scoreable pass rate is 1/7, while attrs B_eval is 7/8.
- The attrs H_future collapse spans all four planned tasks by at least one non-pass outcome.
- Pooled B_eval to pooled H_future absolute error is 0.341667.
- The preserved preregistered pooled MAE is 0.479167.
- Wilson intervals are wide with only two repos and 15 H_future scoreable cells.

## Strongest Alternative Explanation

Attrs may be an outlier or may have a later-window task-family shift that unweighted B_eval did not represent.

## Why This Branch

Reporting is the branch that answers the proposal honestly with the evidence already available. Weighted analysis or third-repo supply may be useful follow-up work, but neither can turn the current two-repo result into predictive-validation evidence inside this local-only runbook.

## Alternatives

| Decision | Status | Reason |
|---|---|---|
| `report_two_repo_negative_or_underpowered_pilot` | `selected` | The confirmed policy violation is genuine, attrs H_future collapse remains broad after excluding the non-scoreable cell, and uncertainty analysis shows the pilot is both negative and underpowered. |
| `build_weighted_compiler_analysis_before_more_paid_validation` | `defer_until_after_reporting` | Task strata and time-window shift are plausible, but current safe metadata does not isolate a weighting fix strongly enough to supersede reporting the negative/underpowered pilot. |
| `mine_third_repo_clean_supply_without_paid_acut` | `not_selected` | A third repo could test whether attrs is an outlier only after future scoreable holdout cells; local supply alone would not change the immediate two-repo conclusion. |
| `blocked_pending_user_protocol_or_budget_decision` | `not_selected` | The next useful work can be completed locally as a clear research-facing pilot report. |

## Claim Boundary

Must not claim:

- `predictive_validity_established`
- `production_benchmark_ranking`
- `pure_harness_effect`
- `attrs_policy_violation_repaired`
- `third_repo_paid_validation_completed`
- `third_repo_as_new_predictive_evidence_without_paid_holdout`

No paid ACUT or paid LLM calls were made. The decision does not recommend
rerunning the confirmed policy violation inside this runbook.
