# M6-W3 Admission Completion Audit

Status: `complete`
Generated at: `2026-05-13T14:18:08Z`

## Objective Restatement

Advance the next experiment from the local planning memo only through M6-W3 task admission: construct a fresh held-out Click W3 candidate pool, smoke-test admission, freeze a 20-task denominator and reserve order, and do not run W3 primary, R3, or ACUT G.

## Prompt-to-Artifact Checklist

| Requirement | Evidence | Result |
|---|---|---|
| Do not modify M5-W2 primary scores | No `m5_w2_primary` files are modified in git status; W3 artifacts are under `configs/tasks/rwork_click_w3*`, `results/m6_w3_admission*`, `tasks/click/w3`, and M6 report/tool paths. | Passed |
| Do not use M5-W2 ACUT outputs, failed patches, near-miss scores, or W3 target/reference/verifier outputs for calibration | `results/m6_w3_admission/admission_summary_20260513.json` records `model_calls_made: 0` and `selection_used_acut_outputs: false`; manifests disallow M5-W2 ACUT outputs and W3 reference patches/verifiers in ACUT context. | Passed |
| Construct 30-40 W3 candidates | `configs/tasks/rwork_click_w3_candidates.yaml` has `candidate_count: 40`; `results/m6_w3_admission/admission_sheets.json` has 40 sheets. | Passed |
| Five primary families, four tasks each | `results/m6_w3_admission/admission_summary_20260513.json` records four primary tasks for each family: option/default/envvar/flag, CliRunner/testing/io, prompt/termui/output rendering, type conversion/normalization, parser/mixed. | Passed |
| Admission sheet fields for every candidate | Completion audit script verified all 40 sheets contain source anchor, changed-file anchor set, family, statement digest, reference patch digest, hidden verifier digest, no-op result, reference result, leakage result, disjointness result, human difficulty rating, and patch complexity band. | Passed |
| Admission oracle: no-op fails and reference passes | Audit verified every accepted candidate has no-op verifier `status: failed`, no-op exit code `1`, reference oracle `reference_passed`, and reference verifier exit code `0`; no accepted exit code `4/5` collection errors remain. | Passed |
| Public statement behavior only; no implementation diff | Audit found no `diff --git`, hunk marker, or reference-patch marker in primary public statements. | Passed |
| Disjoint from RBench, RWork-v1, W2 primary, and W2 reserve anchors | Audit compared primary and reserve W3 anchors with `rbench_click.yaml`, `rwork_click.yaml`, `rwork_click_v2.yaml`, and `rwork_click_v2_reserve.yaml`; overlaps were empty. | Passed |
| Freeze 20 primary tasks | `configs/tasks/rwork_click_w3.yaml` has `status: admitted_frozen`, `task_count: 20`, and 20 materialized task packs under `tasks/click/w3/click__w3__001` through `click__w3__020`. | Passed |
| Freeze reserve ordering | `configs/tasks/rwork_click_w3_reserve.yaml` has `status: reserve_admitted_frozen`, `task_count: 5`, and `freeze.reserve_ordering: manifest_order`. | Passed |
| Freeze deterministic run seed, ACUT run order, status mapping, and infra rerun policy | Primary and reserve manifests include `freeze.deterministic_run_seed: m6-w3-primary-20260513-denominator-v1`, ACUT order, status mapping, and infra policy with no ACUT-specific retry or best-of-N. | Passed |
| Produce named deliverables | Produced `configs/tasks/rwork_click_w3.yaml`, `configs/tasks/rwork_click_w3_reserve.yaml`, `reports/2026-05-13_m6_w3_admission_report.md`, and JSON files under `results/m6_w3_admission/`. | Passed |
| Do not run W3 primary, R3, or ACUT G | Summary records `w3_primary_run: false`, `r3_run: false`, `acut_g_run: false`; no `results/m6_w3_primary` or `results/m6_r3` directory exists. | Passed |

## Verification Commands

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m6_w3_task_admission.py \
  --output experiments/core_narrative/results/m6_w3_admission_20260513.json
```

Result: `status: denominator_frozen_primary_not_run`, `candidate_count: 40`, `accepted: 28`, `rejected: 12`, `primary_task_count: 20`, `reserve_task_count: 5`.

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest \
  experiments/core_narrative/tools/test_m6_w3_task_admission.py \
  experiments/core_narrative/tools/test_m6_rescue_prep.py \
  experiments/core_narrative/tools/test_m5_w2_workspace_runner.py \
  experiments/core_narrative/tools/test_apply_source_derived_url_policy.py \
  experiments/core_narrative/tools/test_workspace_mode_runner.py \
  experiments/core_narrative/tools/test_rgw_status_semantics.py
```

Result: 47 tests passed.

## Claim Boundary

This completes W3 denominator admission and freeze only. It does not produce W3 primary scores, R3 results, ACUT G results, or any NFL-style support claim.
