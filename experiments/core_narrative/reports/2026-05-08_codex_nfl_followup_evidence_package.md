# 2026-05-08 Codex NFL Follow-up Evidence Package

status: `ready_for_review`
branch: `codex/nfl-followup-experiments`
prepared: 2026-05-08 Asia/Shanghai
scope: Barcarolle core-narrative RBench Click follow-up

## Current State

The requested follow-up live sequence ran and produced scoreable evidence for the stabilized Click 001-003 matrix.

- `frontier-click-specialist` attempt 1 fill: 2 passed, 1 `invalid_submission`.
- Full attempt 2 across 4 ACUTs and 3 tasks: 9 passed, 2 failed, 1 `invalid_submission`.
- Baseline plus follow-up: 24 scoreable cells, 17 passed, 5 failed, 2 `invalid_submission`, 0 infra failures in normalized source of truth.
- Gate 1 failed on clean patch replay, so Click 004-008 was not run.

Use the corrected fill evidence artifact and normalized artifacts for scoring. The corrected fill artifact is derived from the normalized per-run records and explicitly marks the original fill batch JSON plus the task-003 per-run `batch_run_result.json` as stale, non-scoring audit outputs.

## Final Score Table

| ACUT | Attempt 1 on 001-003 | Attempt 2 on 001-003 | Combined |
|---|---|---|---|
| `cheap-generic-swe` | 2 passed / 1 failed | 2 passed / 1 failed | 4/6 passed |
| `frontier-generic-swe` | 2 passed / 1 failed | 3 passed / 0 failed | 5/6 passed |
| `cheap-click-specialist` | 2 passed / 1 failed | 2 passed / 1 failed | 4/6 passed |
| `frontier-click-specialist` | 2 passed / 1 invalid | 2 passed / 1 invalid | 4/6 passed |

Task-level attempt-2 contrast:

| Task | Attempt-2 result |
|---|---|
| `click__rbench__001` | all 4 ACUTs passed |
| `click__rbench__002` | all 4 ACUTs passed |
| `click__rbench__003` | `frontier-generic-swe` passed; cheap generic and cheap specialist failed; frontier click was invalid submission |

## Gate Decision

Gate 1 artifact: `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json`.

Decision: `failed_stop_no_expansion`.

Reason: `frontier-click-specialist` on task 003 produced model-output search/replace ambiguity in both attempt 1 and attempt 2. Those cells are scoreable `invalid_submission` results, but they do not satisfy `all_runs_have_clean_patch_replay == true`.

Skipped spend: 20 expansion calls for Click 004-008 across the four core ACUTs.

## Evidence Manifest

| Purpose | Path |
|---|---|
| Follow-up report | `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_experiment_report.md` |
| Evidence package | `experiments/core_narrative/reports/2026-05-08_codex_nfl_followup_evidence_package.md` |
| Gate 1 decision | `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json` |
| Gate 0 preflight v2 | `experiments/core_narrative/results/codex_nfl_gate0_preflight_v2_20260508.json` |
| Mock smoke v2 | `experiments/core_narrative/results/codex_nfl_mock_smoke_followup_v2_20260508.json` |
| Frontier specialist fill corrected evidence | `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_corrected_20260508.json` |
| Frontier specialist fill stale batch audit output | `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json` |
| Attempt-2 batch | `experiments/core_narrative/results/codex_nfl_live_2x2_attempt2_20260508.json` |
| Combined normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_followup_summary_20260508.json` |
| Cost reconciliation | `experiments/core_narrative/results/codex_nfl_followup_cost_reconciliation_2026-05-08.json` |
| Cost ledger | `experiments/core_narrative/results/cost_ledger.jsonl` |
| Raw live artifacts | `experiments/core_narrative/results/raw/codex_nfl_live_*20260508*/` |

Every live raw run directory includes prompt, prompt snapshot, redacted provider response, runner result, command summaries, verifier output where applicable, and patch artifacts when the model produced a verifier-ready patch. Normalized follow-up results include manifest/verifier/prompt digests and cost-accounting summaries.

## Cost State

| Cost item | USD |
|---|---:|
| Cumulative calibrated ledger before follow-up paid live calls | 0.716208 |
| Follow-up paid live provider-usage cost | 1.222660 |
| Latest cumulative ledger estimated cost | 1.938868 |
| Observed provider-usage cost sum | 1.938868 |
| Actual billed/invoiced cost observed | unknown |

Provider-reported usage cost is retained for budget accounting, but it is not invoice proof.

## NFL Story Impact

This follow-up strengthens the NFL framing for Click 001-003: the box score is not enough, because task 003 separates ordinary verifier failures, API plumbing misses, one frontier-generic recovery, and output-contract invalid submissions.

It also limits the claim. The slice is still small, Click 004-008 was not run, and `frontier-click-specialist` task 003 did not yield replayable patches. The next work should either revise the gate to accept invalid submissions as film evidence or make the output contract more robust before spending expansion calls.
