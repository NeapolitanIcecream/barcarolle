# Scorecard v0 From Existing Matrices

Date: 2026-05-09

## Scope

Scorecard v0 is a no-model consumer of existing evidence artifacts. It reads the canonical RBench/RWork matrices, M1.1 measurement-stabilization summary, M2 scoreability summary, unsafe-generated-text triage, and G_score gold-patch smoke when present. It does not call a model or provider API.

Machine-readable output:

- `experiments/core_narrative/results/scorecard_v0_existing_matrices_20260509.json`

## Inputs

- `rbench_canonical_matrix`: present `True`, status `loaded`, digest `1939fe69269c9515`
- `rwork_canonical_matrix`: present `True`, status `loaded`, digest `9ad111ec6675b15b`
- `measurement_stabilization_m1_1_summary`: present `True`, status `loaded`, digest `b33e4fc5ffed9449`
- `m2_scoreability_summary`: present `True`, status `loaded`, digest `3e9f04a758cf678a`
- `unsafe_generated_text_triage`: present `True`, status `loaded`, digest `00f7fd8e35334281`
- `gscore_gold_patch_smoke`: present `True`, status `loaded`, digest `e1981830bef66374`

Score input set digest: `4df2094388fb12aed276398fea45fc526286fbf4cbc7925a408cfd1f5332edab`  
Evidence input set digest: `080e830c601e2674988eaa98a8d2d7622998a4da1d7600d2afb96ac3fd8be7f7`

## Canonical Matrix Evidence

| Split | Fixed cells | Bare pass rate | Evidence states | Missing canonical cells |
| --- | ---: | ---: | --- | ---: |
| `rbench` | 32 | 65.6% | `failed`: 7, `invalid_submission`: 4, `passed`: 21 | 0 |
| `rwork` | 24 | 20.8% | `failed`: 3, `invalid_submission`: 16, `passed`: 5 | 0 |

Overall failure-owner counts: `candidate_patch`: 10, `model_output`: 20, `none`: 26.  
Overall failure-class counts: `none`: 26, `search_replace_anchor_mismatch`: 2, `search_replace_old_occurrence_mismatch`: 17, `unclassified_verifier_failure`: 10, `unsupported_patch_response`: 1.

The bare pass rate is only one view. The same denominator also contains verifier failures, invalid submissions, infrastructure evidence, and missing-run accounting. RWork in particular should not be read as only a lower pass rate; much of its evidence is invalid-submission/output-contract failure rather than clean verifier failure.

## Contract And Scoreability Evidence

M1.1 claim status: `supported`.  
M2 claim status: `scoreability_gate_not_met`.

| Path | Contract | Cells | Status counts | Patch-ready | Invalid rate | Gate |
| --- | --- | ---: | --- | ---: | ---: | --- |
| `patch_or_files_v1_live` | `patch-or-files-v1` | 6 | `infra_failed`: 1, `invalid_submission`: 5 | 0.0% | 83.3% | `failed` |
| `patch_or_files_v1_no_model` | `patch-or-files-v1` | 6 | `failed`: 6 | 100.0% | 0.0% | `passed` |
| `structured_files_json_v1_live` | `structured-files-json-v1` | 6 | `failed`: 2, `invalid_submission`: 4 | 33.3% | 66.7% | `failed` |

Unsafe triage classification counts: `prompt_or_applicator_overbreadth`: 4.  
Unsafe triage output leakage guard: `False`.

## G_score Availability

Availability: `unavailable_blocked`.  
Gold-patch basis proven: `False`.  
Public leaderboard proxy used: `False`.  
Blockers: `dataset_cache_missing`: 1, `evaluation_harness_checkout_missing`: 1.

G_score remains unavailable in this scorecard when the gold-patch smoke is blocked or missing. Scorecard v0 does not substitute public leaderboard scores and does not treat unavailable G_score as zero.

## Claim Boundary

This artifact proves that existing result matrices and summaries can be assembled into a digest-addressed, fixed-denominator diagnostic scorecard. It preserves pass/fail/invalid/infra/missing distinctions, failure owner/class distributions, contract fields, scoreability gates, unsafe triage categories, and G_score availability state.

It does not prove capability uplift, task-solving improvement, ranking reversal, G_score predictivity, or any license/admission decision. It also does not change the M2 conclusion: live scoreability is not yet restored on the selected RWork smoke.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/scorecard_v0_from_existing_matrices.py \
  --output experiments/core_narrative/results/scorecard_v0_existing_matrices_20260509.json \
  --report experiments/core_narrative/reports/2026-05-09_scorecard_v0_existing_matrices_report.md
```
