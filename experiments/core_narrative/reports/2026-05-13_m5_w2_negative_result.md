# M5-W2 Negative Result and Completion Audit

Status: `complete_negative_result`
Generated at: `2026-05-13T08:23:48Z`
Primary summary: `experiments/core_narrative/results/m5_w2_primary/summary.json`

## Bottom Line

M5-W2 is complete. The W2 primary matrix finished all 40 fixed-denominator cells.

The stronger Click-specific ACUT did not produce the required W separation:

| ACUT | W2 score | Status counts |
|---|---:|---|
| `cheap-generic-swe` | 5 / 10 | 5 `verified_pass`, 5 `verified_fail` |
| `cheap-click-specialist` | 4 / 10 | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |
| `cheap-click-deep-specialist-v2` | 5 / 10 | 5 `verified_pass`, 5 `verified_fail` |
| `frontier-generic-swe` | 4 / 10 | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |

The context-effect gate failed: `cheap-click-deep-specialist-v2` scored 5 / 10 and `cheap-generic-swe` scored 5 / 10, a margin of 0 tasks against the required margin of at least 2 tasks.

The NFL-candidate contrast passed in isolation: `cheap-click-deep-specialist-v2` scored 5 / 10 and `frontier-generic-swe` scored 4 / 10. This is not sufficient for candidate status because the preregistered context-effect gate failed first.

Required next action: stop and report a negative result. R2 and ACUT G were not run.

## Primary Evidence

- Final summary: `experiments/core_narrative/results/m5_w2_primary/summary.json`
- Final command output: `experiments/core_narrative/results/m5_w2_primary_summary_final_20260513.json`
- Live primary command output: `experiments/core_narrative/results/m5_w2_primary_live_20260513.json`
- Human-readable W2 summary: `experiments/core_narrative/results/m5_w2_primary/reports/w2_primary_summary.md`
- Normalized result bundle: `experiments/core_narrative/results/m5_w2_primary/normalized/`
- Raw artifact bundle: `experiments/core_narrative/results/m5_w2_primary/raw/`

Secondary W2 metrics:

- Deep vs cheap generic: 0 wins, 0 losses, 10 ties.
- Deep vs frontier generic: 1 win, 0 losses, 9 ties.
- Total matrix statuses: 18 `verified_pass`, 20 `verified_fail`, 2 `no_diff`.
- Infra reruns or exclusions: 0.
- True unsafe count: 0.
- Policy hold count: 0.

## Plan Audit

1. Freeze v1 conclusion: done.
   Evidence: `experiments/core_narrative/reports/2026-05-13_rgw_v1_decision.md`.
   Conclusion: RGW-full-workspace-v1 remains a negative / neutral baseline and is not mixed into the M5 primary denominator.

2. Add `cheap-click-deep-specialist-v2`: done.
   Evidence: `experiments/core_narrative/configs/acuts/cheap-click-deep-specialist-v2.yaml` and `experiments/core_narrative/context_packs/click_deep_specialist_v2/`.
   The context pack is task-agnostic and excludes target commits, reference patches, hidden verifiers, future history, final RWork diffs, and task-answer patterns.

3. Construct RWork-v2: done.
   Evidence: `experiments/core_narrative/configs/tasks/rwork_click_v2.yaml`, `experiments/core_narrative/configs/tasks/rwork_click_v2_reserve.yaml`, `experiments/core_narrative/tasks/click/rwork/click__rwork__101/` through `click__rwork__110/`, `experiments/core_narrative/reports/2026-05-13_m5_w2_task_admission.md`, and `experiments/core_narrative/results/m5_w2_rwork_v2_admission_smoke_20260513.json`.
   The 10 primary tasks were admitted with `reference_passes` and `no_op_fails`; four reserves were preregistered outside the primary denominator.

4. Fix future primary USV semantics: done.
   Evidence: `experiments/core_narrative/tools/apply_source_derived_url_policy.py`, `experiments/core_narrative/tools/workspace_mode_runner.py`, `experiments/core_narrative/tools/test_apply_source_derived_url_policy.py`, and `experiments/core_narrative/tools/test_workspace_mode_runner.py`.
   Model-generated URL, secret, or credential content is unsafe; source-derived URL-only content uses private verifier replay with redacted public artifacts.

5. Run W2 primary matrix: done.
   Evidence: `experiments/core_narrative/results/m5_w2_primary/summary.json`.
   The matrix used 4 ACUTs x 10 RWork-v2 tasks x 1 primary attempt, no best-of-N, deterministic shuffled order, and fixed denominator scoring. The gate failed, so the preregistered next action is to stop and not run R2 or ACUT G.

6. G only no-model readiness: done.
   Evidence: `experiments/core_narrative/results/m5_w2_g6_gold_patch_smoke_executed_20260513_abs_python.json` and `experiments/core_narrative/reports/2026-05-13_m5_w2_g6_gold_patch_smoke_executed_abs_python.md`.
   The G6 gold-patch smoke passed on 6 / 6 pinned tasks. This is not ACUT G scoring and no G score is claimed.

## Verification

The focused regression suite passed after the W2 run:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest \
  experiments/core_narrative/tools/test_m5_w2_workspace_runner.py \
  experiments/core_narrative/tools/test_apply_source_derived_url_policy.py \
  experiments/core_narrative/tools/test_workspace_mode_runner.py \
  experiments/core_narrative/tools/test_rgw_status_semantics.py
```

Result: 27 tests passed.

## Claim Boundary

This is a negative M5-W2 result for repository-specific advantage under the current Click task construction and ACUT design. It does not support an NFL reversal claim. Since the W2 context-effect gate failed, the plan is complete at the negative-result stop point, and no R2 or ACUT G execution is warranted by the preregistered protocol.
