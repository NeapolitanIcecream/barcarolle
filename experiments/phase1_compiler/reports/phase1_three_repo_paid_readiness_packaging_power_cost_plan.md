# Three-Repo Power And Cost Plan

What happened: two paid batch options were costed from committed historical cost evidence.

Why it matters: a later paid runbook needs visible budget and stop conditions before spending.

Recommended option: `primary_pilot`.

| Option | Tasks | Cells | Cost range USD |
| --- | ---: | ---: | --- |
| small_pilot | 18 | 36 | {'lower': 11.16, 'conservative': 18.0} |
| primary_pilot | 60 | 120 | {'lower': 37.21, 'conservative': 60.0} |

Evidence boundary: Both options are pilot-grade. They can test operational readiness and compare designs, but this packaging runbook does not claim precision-target predictive validity.

Stop conditions:
- endpoint_proof_missing
- projected_total_cost_exceeds_budget_approved_for_later_runbook
- scoreability_rate_below_0.95
- policy_violation_count_above_0
- raw_oracle_exposure_detected
- cost_latency_accounting_incomplete
