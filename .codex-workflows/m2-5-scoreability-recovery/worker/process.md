# Worker Process

status: delivered
updated_at: 2026-05-10 18:35 CST

## Revision 1 Scope
Addressed reviewer feedback only:
- Fix M2.5 normalized metadata consistency so patch availability/persistence comes from the workspace-diff collection, clean replay attempted comes from actual verifier invocation, replay failures are separate, and unsafe adapter attribution is preserved.
- Fix generated M2.5 reproduction commands so they include delivered flags such as `--force` and `--skip-noop-check`, with live rerun gating called out explicitly.
- Add the requested invalid-submission regression test, rerun focused M2.5/R0/S1 tests, and regenerate affected M2.5 artifacts.

## Summary
Revision 1 closes the M2.5 evidence-hygiene issues. Normalized live results now keep patch availability and persistence tied to the collected workspace diff, while clean replay status is tied to verifier invocation and can independently report `invalid_submission`. The unsafe live adapter cell now preserves adapter unsafe-patch attribution even though the follow-up workspace collection is empty after restore.

Live M2.5 remains failed, not passed: `claim_status=failed`, fixed denominator `6`, attemptability/patch-ready `4/6 = 0.666667`, invalid submissions `6/6 = 1.0`, clean replay disagreements `4`, failure owners `candidate_patch:4`, `model_output:2`, failure classes `unsafe_patch_content:1`, `no_workspace_patch:1`, `none:4`. No new live adapter/model calls were made in Revision 1; live JSON/Markdown was refreshed deterministically from existing raw artifacts.

## Files Changed / Artifacts
- .codex-workflows/m2-5-scoreability-recovery/worker/process.md
- experiments/core_narrative/tools/m2_5_workspace_diff_runner.py
- experiments/core_narrative/tools/test_m2_5_workspace_diff_runner.py
- experiments/core_narrative/results/m2_5_workspace_diff_synthetic_20260510.json
- experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_synthetic.md
- experiments/core_narrative/results/m2_5_workspace_diff_noop_20260510.json
- experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_noop.md
- experiments/core_narrative/results/m2_5_workspace_diff_summary_20260510.json
- experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_scoreability_recovery.md
- experiments/core_narrative/results/raw/m2_5_workspace_diff_{synthetic,noop,live}_20260510__*/
- experiments/core_narrative/results/normalized/m2_5_workspace_diff_{synthetic,noop,live}_20260510__*.json

## Verification
- PASS: regression-first focused test initially failed before the code fix: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_5_workspace_diff_runner.M25WorkspaceDiffRunnerTests.test_invalid_clean_replay_preserves_patch_availability_and_replay_failure`
- PASS: focused M2.5 suite: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_5_workspace_diff_runner`
- PASS: focused/relevant M2.5/R0/S1 suite: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=experiments/core_narrative/tools python3 -B -m unittest experiments.core_narrative.tools.test_m2_5_workspace_diff_runner experiments.core_narrative.tools.test_click_r0_release_hygiene experiments.core_narrative.tools.test_scorecard_v1_before_predictivity experiments.core_narrative.tools.test_m2_scoreability_summary experiments.core_narrative.tools.test_scorecard_v0_from_existing_matrices experiments.core_narrative.tools.test_run_task experiments.core_narrative.tools.test_prepare_workspace experiments.core_narrative.tools.test_acut_patch_adapter experiments.core_narrative.tools.test_m2_unsafe_artifact_repair`
- PASS: `python3 -m py_compile experiments/core_narrative/tools/m2_5_workspace_diff_runner.py experiments/core_narrative/tools/test_m2_5_workspace_diff_runner.py experiments/core_narrative/tools/click_r0_release_hygiene.py experiments/core_narrative/tools/scorecard_v1_before_predictivity.py`
- PASS: `git diff --check`
- PASS: synthetic no-model M2.5 fixture run: attemptability/patch-ready 1.0, invalid_submission_rate 0.0, clean replay disagreement 0.
  Command: `PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_5_workspace_diff_runner.py --mode synthetic --run-prefix m2_5_workspace_diff_synthetic_20260510 --output experiments/core_narrative/results/m2_5_workspace_diff_synthetic_20260510.json --report experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_synthetic.md --force`
- PASS(expected fail gate): noop M2.5 fixture run classified separately as `reserved_generated_artifact_only`, attemptability 0.0, invalid_submission_rate 1.0.
  Command: `PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_5_workspace_diff_runner.py --mode noop --run-prefix m2_5_workspace_diff_noop_20260510 --output experiments/core_narrative/results/m2_5_workspace_diff_noop_20260510.json --report experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_noop.md --skip-noop-check --force`
- COMPLETE(failed gate): live M2.5 fixed 6-cell artifacts refreshed from existing raw artifacts; no live adapter/model call rerun.
  Command: `PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_5_workspace_diff_runner.py --mode live --run-prefix m2_5_workspace_diff_live_20260510 --output experiments/core_narrative/results/m2_5_workspace_diff_summary_20260510.json --report experiments/core_narrative/reports/2026-05-10_m2_5_workspace_diff_scoreability_recovery.md --force`

## Open Questions / Known Risks
- Live scoreability is failed, not passed and not provider/env-blocked. Do not broaden live spend without a new coordinator decision.
- Four live cells produced non-empty workspace diffs and invoked clean replay, but clean replay returned `invalid_submission`; one live cell had unsafe patch content preserved from adapter attribution; one live cell produced no workspace patch.
- Scorecard v1 is explicitly pre-predictivity. It records G_score as unavailable/blocked, not zero, and does not treat failed scoreability cells as capability failures.
- Existing unrelated untracked `.wrangler/` and `docs/research/barcarolle-research-report-2026-05-10.md` were left untouched.

## Handoff Summary
Ready for reviewer. The two closure issues are addressed: normalized M2.5 metadata no longer conflates verifier outcome with patch availability, and generated reports include exact delivered reproduction flags with live budget/env gating called out. Live M2.5 still fails the gate: attemptability `0.666667` is below `0.70`, invalid submission rate `1.0` is above `0.25`, and clean replay disagreement count is `4` above `0`.
