# Worker Process

status: delivered
updated_at: 2026-05-08 02:29 UTC / 10:29 CST

## Summary
Revision 1 closes the evidence-packaging contradiction without any additional live/API calls. The fill scoring path now points to a corrected machine-readable artifact derived from normalized per-run results; the original fill batch JSON and task-003 raw `batch_run_result.json` are explicitly marked as stale, non-scoring audit outputs.

## Files Changed / Artifacts Produced
- `.codex-workflows/barcarolle-nfl-followup-experiments/worker/process.md`
- `experiments/core_narrative/tools/openclaw_direct_runner.py`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/run_task.py`
- `experiments/core_narrative/tools/codex_nfl_gate0_preflight.py`
- `experiments/core_narrative/tools/test_openclaw_direct_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_direct_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_gate0_preflight.py`
- `experiments/core_narrative/tools/test_run_task.py`
- `experiments/core_narrative/configs/tasks/rbench_click.yaml`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__003/verifier/run.sh`
- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/results/codex_nfl_gate0_preflight_20260508.json`
- `experiments/core_narrative/results/codex_nfl_gate0_preflight_v2_20260508.json`
- `experiments/core_narrative/results/codex_nfl_mock_smoke_followup_20260508.json`
- `experiments/core_narrative/results/codex_nfl_mock_smoke_followup_v2_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_budget_gate_frontier_click_attempt1_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_budget_gate_attempt2_sequence_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_budget_gate_attempt2_post_preflight_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_budget_gate_fill_post_preflight_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_budget_gate_attempt2_after_fill_20260508.json`
- `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json`
- `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_corrected_20260508.json`
- `experiments/core_narrative/results/codex_nfl_live_2x2_attempt2_20260508.json`
- `experiments/core_narrative/results/codex_nfl_followup_cost_reconciliation_2026-05-08.json`
- `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json`
- `experiments/core_narrative/results/normalized/codex_nfl_frontier_specialist_fill_summary_20260508.json`
- `experiments/core_narrative/results/normalized/codex_nfl_attempt2_summary_20260508.json`
- `experiments/core_narrative/results/normalized/codex_nfl_followup_summary_20260508.json`
- Per-run normalized follow-up JSON artifacts under `experiments/core_narrative/results/normalized/codex_nfl_live_*20260508*.json`
- Raw preflight, smoke, and live artifacts under `experiments/core_narrative/results/raw/codex_nfl_*20260508*/`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_experiment_report.md`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_evidence_package.md`

## Live Calls / Cost Status
- Live calls planned before expansion gate: 15.
- Live calls completed: 15.
- Revision 1 live calls completed: 0.
- Fill result: 2 passed, 1 model-output `invalid_submission`, normalized infra failures 0.
- Attempt-2 result: 9 passed, 2 failed, 1 model-output `invalid_submission`, infra failures 0.
- Expansion calls started: 0. Expansion calls skipped: 20.
- Cost status:
  - Prior calibrated cumulative before follow-up paid live calls: USD 0.716208.
  - Fill provider-usage cost: USD 0.442095.
  - Attempt-2 provider-usage cost: USD 0.780565.
  - Follow-up paid live provider-usage cost: USD 1.222660.
  - Latest cumulative ledger/provider-usage sum: USD 1.938868.
  - Actual billed/invoiced cost observed: unknown.

## Verification
- Corrected fill evidence consistency smoke: passed. It checked `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_corrected_20260508.json` against normalized fill rows and report/gate references.
- `cd experiments/core_narrative/tools && PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_run_task.py test_codex_nfl_experiment_runner.py test_openclaw_direct_runner.py test_codex_nfl_direct_runner.py test_codex_nfl_gate0_preflight.py` (30 tests passed)
- JSON parse checks for the corrected fill evidence artifact and updated Gate 1 decision artifact.
- `git diff --check -- . ':(exclude)experiments/core_narrative/results/raw/**'`

## Open Questions / Known Risks
- First failed Gate 0 and first failed mock smoke are intentionally retained as audit artifacts.
- The historical fill batch aggregate still exists for audit, but it is no longer a scoring/gate input and is machine-marked stale in the corrected fill evidence artifact.
- Gate 1 failed because two frontier-click task-003 cells had no verifier-ready patch for clean replay.
- `docs/draft/barcarolle-leadership-report.md` is an unrelated untracked file present in the worktree and was not touched by this worker.

## Handoff Summary
Review the corrected fill evidence artifact, follow-up report, evidence package, normalized summaries, Gate 1 decision, and cost reconciliation. The evidence path is now internally consistent: fill task 003 is scoreable `invalid_submission`, not `infra_failed`, and no expansion spend occurred because the clean-replay gate failed.
