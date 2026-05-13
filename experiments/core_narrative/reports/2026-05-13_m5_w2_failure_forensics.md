# M5-W2 Failure Forensics

Status: `completed_no_new_model_calls`  
Generated at: `2026-05-13T11:52:29.570552Z`  
Source summary: `experiments/core_narrative/results/m5_w2_primary/summary.json`

## Bottom Line

The M5-W2 negative result is preserved. This report does not change primary scores, rerun ACUTs, or reinterpret the preregistered gate.

- `cheap-click-deep-specialist-v2`: 5 / 10
- `cheap-generic-swe`: 5 / 10
- `frontier-generic-swe`: 4 / 10
- Context delivery audit: `completed`
- Near-miss packet status: `packet_prepared_unscored`

## Task Separation

Classification counts: `{"ceiling": 3, "floor": 5, "separator": 2}`.

| Task | Family | Class | Passes |
|---|---|---:|---:|
| `click__rwork__101` | option/default/envvar/flag_value semantics | `ceiling` | 4 / 4 |
| `click__rwork__102` | option/default/envvar/flag_value semantics | `floor` | 0 / 4 |
| `click__rwork__103` | option/default/envvar/flag_value semantics | `separator` | 3 / 4 |
| `click__rwork__104` | CliRunner/testing/input-output isolation | `ceiling` | 4 / 4 |
| `click__rwork__105` | CliRunner/testing/input-output isolation | `ceiling` | 4 / 4 |
| `click__rwork__106` | prompt/termui/output rendering | `floor` | 0 / 4 |
| `click__rwork__107` | prompt/termui/output rendering | `floor` | 0 / 4 |
| `click__rwork__108` | type conversion / parameter normalization | `separator` | 3 / 4 |
| `click__rwork__109` | type conversion / parameter normalization | `floor` | 0 / 4 |
| `click__rwork__110` | mixed integration | `floor` | 0 / 4 |

## Treatment Delivery

Deep specialist runs checked: 10; passed: 10.
Cheap generic negative-control runs checked: 10; passed: 10.
The audit uses redacted prompt metadata: context pack id/hash markers and section-presence checks, not raw prompt content.

## Patch / Reference Overlap

Rows generated: 20. Candidate and reference patch contents are not copied into public artifacts.
The `same_conceptual_fix_proxy` field is automated and conservative; blind review can fill the near-miss scores later without changing primary scoring.

## Artifacts

- task_separation_matrix: `experiments/core_narrative/results/m5_w2_primary/task_separation_matrix.json`
- patch_reference_overlap_audit: `experiments/core_narrative/results/m5_w2_primary/patch_reference_overlap_audit.json`
- near_miss_blind_review: `experiments/core_narrative/results/m5_w2_primary/near_miss_blind_review.json`
- treatment_delivery_audit: `experiments/core_narrative/results/m5_w2_primary/treatment_delivery_audit.json`
- failure_forensics_report: `experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md`

## Claim Boundary

These diagnostics support M6 design only. They do not rescue M5-W2 as positive evidence, do not alter the W2 fixed denominator, and do not authorize W3 primary execution.
