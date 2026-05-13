# M6-W3 Task Admission Report

Status: `denominator_frozen_primary_not_run`
Generated at: `2026-05-13T14:18:08.649605Z`

## Bottom Line

Candidate pool smoked: 40. Admission counts: `{"accepted": 28, "rejected": 12}`.
Primary denominator frozen: 20 tasks. Reserve count: 5.

No W3 primary, R3, or ACUT G was run.

## Primary Family Counts

| Family | Primary tasks |
|---|---:|
| option/default/envvar/flag semantics | 4 |
| CliRunner/testing/input-output isolation | 4 |
| prompt/termui/output rendering | 4 |
| type conversion/parameter normalization | 4 |
| parser/mixed integration | 4 |

## Frozen Artifacts

- Primary manifest: `experiments/core_narrative/configs/tasks/rwork_click_w3.yaml`
- Reserve manifest: `experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml`
- Candidate pool: `experiments/core_narrative/configs/tasks/rwork_click_w3_candidates.yaml`
- Admission sheets: `experiments/core_narrative/results/m6_w3_admission/admission_sheets.json`
- Materialization summary: `experiments/core_narrative/results/m6_w3_admission/materialization_summary.json`
- Private smoke root: `experiments/core_narrative/large_artifacts/m6_w3_admission_20260513`
- Deterministic run seed: `m6-w3-primary-20260513-denominator-v1`
- ACUT run order: `["cheap-generic-swe", "cheap-click-deep-specialist-v2", "cheap-click-rbench-calibrated-v1", "frontier-generic-swe"]`

## Claim Boundary

This report freezes the W3 denominator only. It does not claim any W3 model result or NFL-style support.
