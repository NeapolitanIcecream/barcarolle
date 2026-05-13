# M6-W3 Freeze Integrity Audit

Status: `passed`
Generated at: `2026-05-13T15:27:33.903747Z`

## Scope

This is a 0-model audit before W3 primary execution. It verifies frozen W3 denominator artifacts, protocol synchronization, context-pack leakage boundaries, remote availability, and execution readiness.

No W3 primary, R3, or ACUT G run is authorized or performed by this audit.

## Counts

- Candidate count: `40`
- Accepted candidate count: `28`
- Primary task count: `20`
- Reserve task count: `5`
- Admission sheet count: `40`

## Checks

| ID | Status | Evidence |
|---|---|---|
| `freeze.primary_manifest` | `passed` | `{"exists": true, "manifest_task_count": 20, "observed_task_count": 20, "path": "experiments/core_narrative/configs/tasks/rwork_click_w3.yaml", "status": "admitted_frozen"}` |
| `freeze.reserve_manifest` | `passed` | `{"exists": true, "manifest_task_count": 5, "observed_task_count": 5, "path": "experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml", "status": "reserve_admitted_frozen"}` |
| `admission.summary_counts` | `passed` | `{"admitted_candidate_count": 28, "candidate_count": 40, "exists": true, "path": "experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json", "primary_task_count": 20, "reserve_task_count": 5, "status": "denominator_frozen_primary_not_run"}` |
| `admission.primary_sheet_coverage` | `passed` | `{"accepted_sheet_count": 20, "invalid_smoke_task_ids": [], "missing_anchor_record_task_ids": [], "missing_digest_task_ids": [], "missing_sheet_task_ids": [], "reference_digest_mismatch_task_ids": [], "task_count": 20}` |
| `admission.primary_smoke_records` | `passed` | `{"checked_task_count": 20, "invalid_smoke_task_ids": []}` |
| `admission.primary_digest_records` | `passed` | `{"checked_task_count": 20, "missing_digest_task_ids": [], "reference_digest_mismatch_task_ids": []}` |
| `admission.primary_anchor_records` | `passed` | `{"checked_task_count": 20, "missing_anchor_record_task_ids": []}` |
| `denominator.disjoint_anchors` | `passed` | `{"overlaps": {}, "primary_anchor_count": 24, "prior_manifest_anchor_counts": {"experiments/core_narrative/configs/tasks/rbench_click.yaml": 14, "experiments/core_narrative/configs/tasks/rwork_click.yaml": 8, "experiments/core_narrative/configs/tasks/rwork_click_v2.yaml": 20, "experiments/core_narrative/configs/tasks/rwork_click_v2_reserve.yaml": 5}}` |
| `public.statement_redaction` | `passed` | `{"checked_paths": ["experiments/core_narrative/tasks/click/w3/click__w3__001/public/statement.md", "experiments/core_narrative/tasks/click/w3/click__w3__002/public/statement.md", "experiments/core_narrative/tasks/click/w3/click__w3__003/public/statement.md", "experiments/core_narrative/tasks/click/w3/click__w3__004/public/statement.md", "experiments/core_narrative/tasks/click/w3/click__w3__005/public/statement.md", "experiments/core_narrative/tasks/click/w3/click__w3__006/public/statement.md"...` |
| `context.hash_match` | `passed` | `{"acut_config": "experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml", "acut_pack_hash": "b1b1ee40b72be5912ea07ac76d6ae6689edb2f3a930c5e2479ea6f71ffc0de85", "context_manifest": "experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json", "context_manifest_pack_hash": "b1b1ee40b72be5912ea07ac76d6ae6689edb2f3a930c5e2479ea6f71ffc0de85"}` |
| `context.leakage_w3_false` | `passed` | `{"forbidden_true_flags": {}, "leakage_audit_status": "passed_for_protocol_prep"}` |
| `protocol.denominator_status` | `passed` | `{"accepted_task_count": 20, "metadata_sync": {"note": "Admission artifacts froze the denominator; this protocol update only synchronizes preregistered metadata.", "source_of_truth": "experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json", "synced_at": "2026-05-13T14:18:08.649605Z", "task_reselection_performed": false, "w3_primary_run_performed": false}, "path": "experiments/core_narrative/configs/m6_w3_protocol.yaml", "protocol_status": "protocol_synced_denominato...` |
| `readiness.freeze_controls` | `passed` | `{"primary_acut_order": ["cheap-generic-swe", "cheap-click-deep-specialist-v2", "cheap-click-rbench-calibrated-v1", "frontier-generic-swe"], "primary_infra_policy": {"acut_specific_retry_allowed": false, "best_of_n_allowed": false, "global_infra_only": true, "requires_documented_global_exclusion_before_scoring": true}, "primary_seed": "m6-w3-primary-20260513-denominator-v1", "primary_status_mapping_keys": ["no_diff", "timeout", "unsafe_or_scope_violation", "verified_fail", "verified_pass", "ve...` |
| `boundary.no_w3_r3_or_g_run` | `passed` | `{"admission_summary_flags": {"acut_g_run": false, "model_calls_made": 0, "r3_run": false, "w3_primary_run": false}, "forbidden_result_paths_existing": []}` |
| `readiness.cost_ledger_writable` | `passed` | `{"error": null, "ledger_exists": true, "ledger_path": "experiments/core_narrative/results/cost_ledger.jsonl", "parent_writable_probe_passed": true, "required_before_acut_execution": true}` |
| `readiness.workspace_and_source_url_tests` | `passed` | `{"command": ["/Applications/Xcode.app/Contents/Developer/usr/bin/python3", "-m", "unittest", "experiments/core_narrative/tools/test_workspace_mode_runner.py", "experiments/core_narrative/tools/test_apply_source_derived_url_policy.py"], "exit_code": 0, "stderr_tail": "..................\n----------------------------------------------------------------------\nRan 18 tests in 7.506s\n\nOK\n", "stdout_tail": ""}` |
| `remote.same_commit_artifacts` | `passed` | `{"checked_paths": ["experiments/core_narrative/configs/tasks/rwork_click_w3.yaml", "experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml", "experiments/core_narrative/configs/tasks/rwork_click_w3_candidates.yaml", "experiments/core_narrative/configs/m6_w3_protocol.yaml", "experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json", "experiments/core_narrative/results/m6_w3_admission_20260513.json", "experiments/core_narrative/results/m6_w3_admission/adm...` |

## Output Boundary

- This audit does not change the W3 denominator.
- This audit does not run models.
- If status is `passed`, W3 primary may be run as a separate step under the frozen seed, ACUT order, scoring map, and infra policy.
