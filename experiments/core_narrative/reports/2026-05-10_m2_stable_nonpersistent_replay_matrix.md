# M2 Stable Nonpersistent Replay Matrix

Date: 2026-05-10

## Scope

- Patch-or-files fixed denominator: `6`.
- Patch-or-files no-model control denominator: `6`.
- Anchored input-record denominator: `5`.
- New model calls in this package: `0`.
- This is verifier-attemptability and artifact-channel accounting only.

## Aggregate

- Category counts: `{'missing_raw_artifact': 1, 'model_output_invalid_submission': 9, 'nonpersistent_verifier_attempt': 1, 'verifier_ready_persisted_patch_artifact': 6}`.
- Verifier-attemptable count: `7` (41.2%).
- Persisted patch-artifact attemptable count: `6`.
- Nonpersistent verifier attempts: `1`.
- Prior failures becoming verifier-attemptable: `1`.
- Missing raw artifacts: `1`.

## By Contract

| Contract | Rows | Attemptable | Persisted patch | Nonpersistent | Model invalid | Infra | Missing raw | Cleanup blockers | Became attemptable |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| `anchored-search-replace-json-v3` | 5 | 1 | 0 | 1 | 4 | 0 | 0 | 0 | 1 |
| `patch-or-files-v1` | 12 | 6 | 6 | 0 | 5 | 0 | 1 | 0 | 0 |

## Matrix

| Source | Mode | ACUT | Task | Category | Owner | Class | Channel | Became attemptable |
| --- | --- | --- | --- | --- | --- | --- | --- | ---: |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-generic-swe` | `click__rwork__003` | `model_output_invalid_submission` | `model_output` | `invalid_unified_diff` | `not_attempted` | `False` |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-generic-swe` | `click__rwork__004` | `model_output_invalid_submission` | `model_output` | `invalid_unified_diff` | `not_attempted` | `False` |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-generic-swe` | `click__rwork__006` | `model_output_invalid_submission` | `model_output` | `apply_patch_context_mismatch` | `not_attempted` | `False` |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-click-specialist` | `click__rwork__003` | `model_output_invalid_submission` | `model_output` | `unsafe_generated_text` | `not_attempted` | `False` |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-click-specialist` | `click__rwork__004` | `model_output_invalid_submission` | `model_output` | `apply_patch_context_mismatch` | `not_attempted` | `False` |
| `patch_or_files_v1_live` | `no_model_historical_replay` | `cheap-click-specialist` | `click__rwork__006` | `missing_raw_artifact` | `infrastructure` | `missing_raw_response_artifact` | `not_attempted` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-generic-swe` | `click__rwork__003` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-click-specialist` | `click__rwork__003` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-generic-swe` | `click__rwork__004` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-click-specialist` | `click__rwork__004` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-generic-swe` | `click__rwork__006` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `patch_or_files_v1_no_model` | `existing_no_model_control` | `cheap-click-specialist` | `click__rwork__006` | `verifier_ready_persisted_patch_artifact` | `candidate_patch` | `None` | `verifier_ready_patch_artifact` | `False` |
| `anchored_contract_live_smoke` | `historical_live` | `cheap-generic-swe` | `click__rwork__006` | `model_output_invalid_submission` | `model_output` | `search_replace_old_occurrence_mismatch` | `not_attempted` | `False` |
| `anchored_occurrence_repair_live_smoke` | `historical_live` | `cheap-generic-swe` | `click__rwork__006` | `model_output_invalid_submission` | `model_output` | `unsafe_generated_text` | `not_attempted` | `False` |
| `unsafe_artifact_repair_live_smoke` | `historical_live` | `cheap-generic-swe` | `click__rwork__006` | `model_output_invalid_submission` | `model_output` | `unsafe_generated_text` | `not_attempted` | `False` |
| `nonpersistent_channel_replay` | `no_model_replay` | `cheap-generic-swe` | `click__rwork__006` | `nonpersistent_verifier_attempt` | `candidate_patch` | `unsafe_generated_text` | `nonpersistent_preapplied_workspace` | `True` |
| `nonpersistent_channel_live_smoke` | `historical_live` | `cheap-generic-swe` | `click__rwork__006` | `model_output_invalid_submission` | `model_output` | `None` | `verifier_ready_patch_artifact_clean_apply_blocked` | `False` |

## Blockers

- `anchored_search_replace_fixed_grid_inputs_insufficient`: expected `6` anchored grid cells, observed `1`; missing `5`.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_repaired_parser_replay.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --path-id patch_or_files_v1_live \
  --run-prefix m2_stable_nonpersistent_replay_matrix_patch_or_files_20260510 \
  --force \
  --output experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_patch_or_files_replay_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_patch_or_files_replay.md

PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_stable_nonpersistent_replay_matrix.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --patch-replay experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_patch_or_files_replay_20260510.json \
  --output experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix.md
```

## Claim Boundaries

This report does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.
