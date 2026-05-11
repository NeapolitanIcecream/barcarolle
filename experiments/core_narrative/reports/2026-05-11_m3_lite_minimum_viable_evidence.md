# M3-lite Minimum Viable Evidence

Date: 2026-05-11

## Scope Reset

M3-lite is research-grade minimum viable evidence, not a product gate. Clean-room replay is recorded when available but is not required for research-scoreability. This artifact does not issue or imply license, admission, authorization, capability-uplift, ranking-reversal, or G_score-predictivity claims.

Protocol: `experiments/core_narrative/configs/m3_lite_mve_matrix.yaml`. Matrix: `3` ACUTs, `4` RBench tasks, `4` RWork tasks.

Score input set digest: `3d59aca652f9412fcdee0e0f553f823ca7234536f4ae067ae6228bb4da0e1ce2`

## Partial G/R/W

G_score availability: `unavailable_blocked`. Unavailable G_score is reported as `None`, not zero.

| ACUT | G | R fixed pass | W fixed pass | R verified n | W verified n |
|---|---:|---:|---:|---:|---:|
| cheap-generic-swe | n/a | 50.0% | 25.0% | 4 | 1 |
| cheap-click-specialist | n/a | 50.0% | 25.0% | 4 | 1 |
| frontier-click-specialist | n/a | 50.0% | 25.0% | 3 | 2 |

R outcomes: `verified_pass`: 6, `verified_fail`: 5, `invalid_submission`: 1. Fixed-denominator pass rate: `0.5`.

W outcomes: `verified_pass`: 3, `verified_fail`: 1, `invalid_submission`: 8. Fixed-denominator pass rate: `0.25`.

## M2.5 Recovery

Recovered M2.5 records: `6`. Research-scoreable records: `4`. Persisted patches: `4`. Final workspace diffs: `4`. Outcome counts: `no_research_scoreable_patch`: 2, `produced_patch_replay_invalid`: 4.

These M2.5 records are work-product evidence. They are not blended into verified W_score unless verifier or review evidence supports that stronger conclusion.

## Story Impact

Status: `not_established`.

M3-lite advances measurement readiness and partial R/W inspection, but it does not establish the NFL ranking-reversal story because G_score is unavailable and W evidence remains limited.

## Limitations

- G_score is unavailable in this MVE, so no G/R/W ranking reversal can be claimed.
- The W slice is small and contains invalid-submission/output-contract failures that remain visible in the denominator.
- M2.5 recovery can show persisted patches or final workspace diffs, but replay-invalid records remain weaker than verified passes or blinded review.
- Existing artifacts include historical runner limitations; this report separates measurement recovery from task capability.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m3_lite_mve_research_scorecard.py --matrix experiments/core_narrative/configs/m3_lite_mve_matrix.yaml --scorecard-v1 experiments/core_narrative/results/scorecard_v1_before_predictivity_20260510.json --m2-5-summary experiments/core_narrative/results/m2_5_workspace_diff_summary_20260510.json --output experiments/core_narrative/results/m3_lite_mve_research_scorecard_20260511.json --m2-5-output experiments/core_narrative/results/m3_lite_m2_5_recovery_20260511.json --report experiments/core_narrative/reports/2026-05-11_m3_lite_minimum_viable_evidence.md
```
