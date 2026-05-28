# Three-Repo Threshold Preregistration

What happened: success, failure, scoreability, endpoint, policy, and cost-accounting thresholds were preregistered.

Why it matters: paid validation results need fixed rules before paid cells run.

```json
{
  "cost_latency_accounting_required": true,
  "minimum_scoreability_rate": 0.95,
  "non_scoreable_cell_handling": "preregistered_taxonomy_and_excluded_from_pass_denominator",
  "paid_endpoint_required": "LLM_BASE_URL + LLM_API_KEY",
  "policy_violations_max": 0,
  "primary_gap_threshold": 0.15,
  "raw_oracle_exposure_allowed": false
}
```

Success rule: Success requires zero policy violations, endpoint compliance, scoreability >= 0.95, complete cost/latency accounting, and primary absolute gap <= 0.15.

Failure rule: Failure is any policy violation, raw oracle exposure, endpoint noncompliance, scoreability below 0.95, incomplete accounting, or primary gap above 0.15.

Underpowered evidence rule: If the recommended paid batch is run without the full release candidate, label the result pilot-only even when gates pass.

Predictive validity is not claimed before paid validation.
