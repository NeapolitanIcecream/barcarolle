# Scorecard v1 Before Predictivity

Date: 2026-05-10

## Scope

Scorecard v1 is a no-model, pre-predictivity, admission-safe diagnostic artifact. It separates verified outcomes from invalid submissions, infrastructure failures, missing coverage, and policy invalidity. It does not reinterpret failed scoreability cells as task capability failures.

Score input set digest: `0e8c1ff04cc624cad29a95da8b4fafa7bf92fa9f069aca5a3d1a9d9c5202aad7`
Evidence input set digest: `3e478e39812ac1ab3e489592e4f3319053bfe4c67c042f5f3e45fd3af92393bf`

## Outcomes

- Fixed denominator entries: `80`
- Outcome classes: `verified_pass`: 26, `verified_fail`: 18, `invalid_submission`: 35, `infra_failed`: 1
- Attemptability score: `0.6`
- Verified correctness rate: `0.590909`
- Fixed-denominator pass rate: `0.325`

## G_score

Availability: `unavailable_blocked`. G_score value is `None` because unavailable G_score is not treated as zero.

## Claim Boundary

This artifact does not claim ranking reversal, R_score > G_score predictivity, task-solving improvement, capability uplift, admission, license, or authorization.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/scorecard_v1_before_predictivity.py \
  --output experiments/core_narrative/results/scorecard_v1_before_predictivity_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_scorecard_v1_before_predictivity.md
```
