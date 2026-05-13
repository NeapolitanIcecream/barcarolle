# M6 Rescue-Prep Completion Audit

Status: `complete_for_protocol_prep`  
Generated at: `2026-05-13T00:00:00+08:00`  
Objective source: local planning memo, not committed

## Objective Restatement

Advance the next experiment without rewriting M5-W2 or running G to chase a reversal. The concrete deliverable is M6 rescue-prep:

- preserve M5-W2 as a negative result;
- run no-new-model-call M5-W2 failure forensics;
- freeze a M5 to M6 decision note;
- scaffold `cheap-click-rbench-calibrated-v1` with an RBench-derived repair playbook and leakage audit;
- preregister a W3 held-out protocol and gates;
- do not run W3 primary, R3, or ACUT G in this phase.

## Prompt-To-Artifact Checklist

| Requirement | Evidence | Status |
|---|---|---|
| Do not rewrite M5-W2 or modify primary scores | `experiments/core_narrative/reports/2026-05-13_m5_w2_m6_transition_decision.md`; `experiments/core_narrative/results/m5_w2_primary/summary.json` still reports `w2_primary_complete_gate_failed` | complete |
| No-new-call task separation matrix | `experiments/core_narrative/results/m5_w2_primary/task_separation_matrix.json`; counts are 3 ceiling, 5 floor, 2 separator | complete |
| Patch/reference overlap audit for deep vs cheap generic | `experiments/core_narrative/results/m5_w2_primary/patch_reference_overlap_audit.json`; 20 rows, no raw patch content copied | complete |
| Treatment delivery audit | `experiments/core_narrative/results/m5_w2_primary/treatment_delivery_audit.json`; 10/10 deep specialist runs passed, 10/10 cheap generic negative controls passed | complete |
| Near-miss review packet without changing primary score | `experiments/core_narrative/results/m5_w2_primary/near_miss_blind_review.json`; status `packet_prepared_unscored`, 10 rows, `primary_scores_modified=false` | complete |
| Failure forensics report | `experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md` | complete |
| Freeze M5 decision note | `experiments/core_narrative/reports/2026-05-13_m5_w2_m6_transition_decision.md` | complete |
| Add `cheap-click-rbench-calibrated-v1` | `experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml` | complete |
| Same cheap model tier/budget/tools/network as cheap generic | ACUT manifest uses `openai/gpt-5.4-mini`, 3600s, 18 turns, 64000 tokens, 10 test commands, one attempt, no retries, network disabled | complete |
| RBench-derived repair playbook | `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/repair_playbook.json` and `context_prompt.md` | complete |
| Playbook manifest | `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json` | complete |
| Leakage audit | `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/leakage_audit.json`; status `passed_for_protocol_prep` | complete |
| Context pack loader smoke | `experiments/core_narrative/results/m6_context_pack_load_smoke_20260513.json`; status `passed`, all expected sections present, no model call | complete |
| W3 held-out protocol with 16-20 Click tasks design | `experiments/core_narrative/configs/m6_w3_protocol.yaml`; target is 20 tasks with five 4-task family quotas | complete |
| W3 disjointness constraints | `m6_w3_protocol.yaml` lists excluded RBench, RWork-v1, and W2 anchors | complete |
| W3 admission criteria | `m6_w3_protocol.yaml` requires no-op fail, reference pass, behavior verifier, non-leaking statement, and disjoint anchors before primary | complete |
| W3 gates | `m6_w3_protocol.yaml` preregisters +4/20 over cheap generic, greater than static deep specialist, greater than frontier generic for candidate status | complete |
| Do not run W3 primary before protocol and leakage audit | No `experiments/core_narrative/results/m6_w3_primary/` directory exists; protocol status is `protocol_preregistered_no_primary_run` | complete |
| Do not run R3 or ACUT G | `m6_w3_protocol.yaml` marks R3 and ACUT G as not authorized in this phase | complete |

## Verification

Commands run:

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m6_rescue_prep.py \
  --output experiments/core_narrative/results/m6_rescue_prep_20260513.json
```

Result: completed, 0 model calls, primary scores not modified.

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/validate_acut_manifest.py \
  experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml \
  --output experiments/core_narrative/results/m6_validate_acut_20260513.json
```

Result: passed, 1 valid manifest, 0 invalid.

```bash
PYTHONPATH=experiments/core_narrative/tools python3 -m unittest \
  experiments/core_narrative/tools/test_m6_rescue_prep.py \
  experiments/core_narrative/tools/test_m5_w2_workspace_runner.py \
  experiments/core_narrative/tools/test_apply_source_derived_url_policy.py \
  experiments/core_narrative/tools/test_workspace_mode_runner.py \
  experiments/core_narrative/tools/test_rgw_status_semantics.py
```

Result: 31 tests passed.

## Residual Boundary

This completes M6 rescue-prep, not W3 execution. Concrete W3 tasks are still unmaterialized and must be selected, admitted, and leakage-checked in a later phase before any W3 primary run. That is intentional under the objective: W3 primary is not authorized until protocol and leakage prep are complete.
