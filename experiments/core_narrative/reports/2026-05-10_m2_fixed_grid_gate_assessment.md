# M2 Fixed-Grid Gate Assessment

Date: 2026-05-10

## Verdict

- Coverage/raw-input/no-raw policy gate: `passed`.
- M2 scoreability gate status: `failed`.
- Claim status: `m2_scoreability_gate_not_met_after_fixed_grid_gap_closure`.
- Assessment model calls: `0`; cost ledger mutated by assessment: `false`.
- This is scoreability and artifact-channel accounting only.

## Fixed Denominators

- Patch-or-files live fixed denominator: `6`.
- Patch-or-files historical missing raw artifacts preserved: `1`.
- Patch-or-files acquired raw inputs: `1`; remaining raw-input gaps: `0`.
- Patch-or-files no-model control denominator: `6`.
- Anchored fixed-grid cells: `6` observed of `6` expected; input records: `10`.

## Scoreability Gates

| Path | Gate | Denom | Attemptable | Attemptability | Model invalid | Invalid rate | Clean replay disagreements |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `patch_or_files_v1_live_after_gap_closure` | `failed` | 6 | 0 | 0.0% | 6 | 100.0% | 0 |
| `anchored_search_replace_fixed_grid` | `failed` | 6 | 2 | 33.3% | 4 | 66.7% | not_measured |
| `patch_or_files_v1_no_model_control` | `passed` | 6 | 6 | 100.0% | 0 | 0.0% | 0 |

## Failure And Channels

- `patch_or_files_v1_live_after_gap_closure` owner counts: `{'model_output': 6}`.
- `patch_or_files_v1_live_after_gap_closure` class counts: `{'apply_patch_context_mismatch': 2, 'invalid_unified_diff': 2, 'unsafe_generated_text': 2}`.
- `patch_or_files_v1_live_after_gap_closure` attemptability channels: `{'not_attempted': 6}`.
- `anchored_search_replace_fixed_grid` owner counts: `{'candidate_patch': 2, 'model_output': 4}`.
- `anchored_search_replace_fixed_grid` class counts: `{'none': 1, 'search_replace_old_occurrence_mismatch': 1, 'search_replace_redacted_source_mismatch': 1, 'unsafe_generated_text': 2, 'unsupported_patch_response': 1}`.
- `anchored_search_replace_fixed_grid` attemptability channels: `{'nonpersistent_preapplied_workspace': 2, 'not_attempted': 3, 'verifier_ready_patch_artifact_clean_apply_blocked': 1}`.
- `patch_or_files_v1_no_model_control` owner counts: `{'candidate_patch': 6}`.
- `patch_or_files_v1_no_model_control` class counts: `{'none': 6}`.
- `patch_or_files_v1_no_model_control` attemptability channels: `{'verifier_ready_patch_artifact': 6}`.

## Exact ACUT/Task Blockers

### `patch_or_files_v1_live_after_gap_closure`
- `cheap-click-specialist` / `click__rwork__003`: `model_output_invalid_submission`, owner `model_output`, class `unsafe_generated_text`, channel `not_attempted`.
- `cheap-click-specialist` / `click__rwork__004`: `model_output_invalid_submission`, owner `model_output`, class `apply_patch_context_mismatch`, channel `not_attempted`.
- `cheap-click-specialist` / `click__rwork__006`: `model_output_invalid_submission`, owner `model_output`, class `unsafe_generated_text`, channel `not_attempted`.
- `cheap-generic-swe` / `click__rwork__003`: `model_output_invalid_submission`, owner `model_output`, class `invalid_unified_diff`, channel `not_attempted`.
- `cheap-generic-swe` / `click__rwork__004`: `model_output_invalid_submission`, owner `model_output`, class `invalid_unified_diff`, channel `not_attempted`.
- `cheap-generic-swe` / `click__rwork__006`: `model_output_invalid_submission`, owner `model_output`, class `apply_patch_context_mismatch`, channel `not_attempted`.
### `anchored_search_replace_fixed_grid`
- `cheap-click-specialist` / `click__rwork__003`: `model_output_invalid_submission`, owner `model_output`, class `none`, channel `verifier_ready_patch_artifact_clean_apply_blocked`.
- `cheap-click-specialist` / `click__rwork__004`: `model_output_invalid_submission`, owner `model_output`, class `unsupported_patch_response`, channel `not_attempted`.
- `cheap-click-specialist` / `click__rwork__006`: `model_output_invalid_submission`, owner `model_output`, class `search_replace_redacted_source_mismatch`, channel `not_attempted`.
- `cheap-generic-swe` / `click__rwork__004`: `model_output_invalid_submission`, owner `model_output`, class `search_replace_old_occurrence_mismatch`, channel `not_attempted`.

## Cost And Model Calls

- Assessment generation: `0` new model calls, `0.0` USD estimated cost.
- Input acquisition rows: `6`; acquisition model calls: `6`.
- Acquisition provider usage observed sum: `0.361873` USD.
- Acquisition ledger estimated sum: `0.361873` USD.

## No-Raw-Unsafe Policy

- Status: `passed`.
- Matrix leakage guard: `{'contains_raw_unsafe_text': False, 'reason_counts': {}}`.
- Row policy violations: `0`.
- Assessment leakage guard: `{'contains_raw_unsafe_text': False, 'reason_counts': {}}`.

## Hard Blocker Summary

- Status: `hard_blocked_for_m2_pass_or_predictivity_claims`.
- Blocker: `live_model_output_scoreability_thresholds_not_met_after_fixed_grid_gap_closure`.
- Code-addressable blocker identified: `False`.
- Next code-addressable blocker: `None`.
- Reason: Fixed denominator and raw-input acquisition gaps are closed, but live evidence remains below attemptability coverage thresholds and above model-output invalid-submission thresholds. The assessment found no single safe code-addressable next experiment that is directly supported by this evidence and would not require new approved model calls.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_fixed_grid_gate_assessment.py \
  --matrix experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap_20260510.json \
  --output experiments/core_narrative/results/m2_fixed_grid_gate_assessment_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_fixed_grid_gate_assessment.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.
