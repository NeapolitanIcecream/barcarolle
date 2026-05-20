# Click M3 Predictivity Matrix Gate Report

Date: 2026-05-09

## Scope

This is a no-model consumer of existing Click evidence. It inspects M2 scoreability and Scorecard v0 before any M3 predictivity work. No model or provider API call was made by this step.

Machine-readable output:

- `experiments/core_narrative/results/click_m3_predictivity_matrix_gate_20260509.json`

## Gate Decision

M2 live scoreability gate status: `blocked`.  
M2 claim status: `scoreability_gate_not_met`.  
M3 live experiments run: `False`.

Blockers:

- `m2_claim_status_not_passed` (observed_claim_status `scoreability_gate_not_met`, required_claim_status `scoreability_gate_passed`)
- `m2_live_path_gate_not_passed` (path_id `patch_or_files_v1_live`, gate_status `failed`, patch_ready_coverage `0.0`, invalid_submission_rate `0.833333`, clean_replay_disagreement_count `0`)
- `m2_live_path_gate_not_passed` (path_id `structured_files_json_v1_live`, gate_status `failed`, patch_ready_coverage `0.333333`, invalid_submission_rate `0.666667`, clean_replay_disagreement_count `0`)
- `no_model_path_not_sufficient_for_m3` (path_id `patch_or_files_v1_no_model`, reason `no-model paths are instrumentation baselines, not live scoreability gates`)

| M2 path | Kind | Cells | Status counts | Patch-ready | Invalid rate | Gate |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `patch_or_files_v1_live` | live | 6 | `infra_failed`: 1, `invalid_submission`: 5 | 0.0% | 83.3% | `failed` |
| `patch_or_files_v1_no_model` | no-model | 6 | `failed`: 6 | 100.0% | 0.0% | `passed` |
| `structured_files_json_v1_live` | live | 6 | `failed`: 2, `invalid_submission`: 4 | 33.3% | 66.7% | `failed` |

The no-model path is an instrumentation baseline and does not satisfy the live scoreability gate for M3.

## Denominators Preserved

| Split | Fixed cells | Canonical present | Canonical missing | Scoreable |
| --- | ---: | ---: | ---: | ---: |
| `rbench` | 32 | 32 | 0 | 32 |
| `rwork` | 24 | 24 | 0 | 24 |

M2 fixed denominator: `6`.

## G Score

G_score predictivity status: `unavailable_direct_acut_scoring_required`.  
Scorecard availability: `unavailable_blocked`.  
Public leaderboard proxy used: `False`.

G_score predictivity remains unavailable unless direct ACUT scoring exists. No proxy or zero-fill score is used here.

## Claim Boundary

This artifact records a gate/blocker and denominator snapshot only. It does not assert capability uplift, task-solving improvement, ranking reversal, or any license/admission/authorization outcome.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/click_m3_predictivity_matrix.py \
  --output experiments/core_narrative/results/click_m3_predictivity_matrix_gate_20260509.json \
  --report experiments/core_narrative/reports/2026-05-09_click_m3_predictivity_matrix_gate_report.md
```
