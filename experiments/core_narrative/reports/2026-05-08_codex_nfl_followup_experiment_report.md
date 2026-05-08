# 2026-05-08 Codex NFL Follow-up Experiment Report

status: `delivered`
updated: 2026-05-08T02:26:27Z
repo: `/Users/chenmohan/gits/barcarolle`
branch: `codex/nfl-followup-experiments`
primary_runner: `codex-nfl-batch-v1` plus `codex-nfl-direct-search-replace-v1`

## Executive Summary

The follow-up sequence completed the requested stabilization evidence and stopped before the Click 004-008 expansion. The missing `frontier-click-specialist` attempt-1 cells ran on Click 001-003, then the complete four-ACUT attempt-2 matrix ran on the same three tasks.

Outcome:

- Fill run: 3 scoreable cells, 2 passed, 1 `invalid_submission`, 0 infra failures in normalized source of truth.
- Attempt 2: 12 scoreable cells, 9 passed, 2 failed, 1 `invalid_submission`, 0 infra failures.
- Baseline plus follow-up: 24 scoreable cells, 17 passed, 5 failed, 2 `invalid_submission`.
- Gate 1 failed on `all_runs_have_clean_patch_replay == true`, so Click 004-008 was not run.

The 2x2 evidence is complete at the outcome level: 4 ACUTs by 3 tasks by 2 attempts now exists. It is not complete under the stricter clean-replay expansion prerequisite because both `frontier-click-specialist` task-003 attempts consumed provider responses but failed the model-output search/replace contract before a patch existed.

## Facility Notes

Before live spend, Gate 0 was made executable and passed on Click 001-003 after focused repairs. The first preflight and first mock smoke failed and are retained for audit; the v2 artifacts passed.

Facility changes made for this follow-up:

- Attempt-2 budget approval now flows through `--coordinator-decision-ref`.
- Run IDs are checked against raw artifacts, normalized artifacts, and the ledger before model calls.
- Normalized results now include runner identity, manifest digests, verifier digest, prompt snapshot digest, context-pack digest, clean-replay metadata, raw provider response path, model-call flag, and direct-runner cost summary.
- Click specialist ACUTs assert specialist context inclusion; generic ACUTs assert exclusion when forced.
- Task 003 verifier pre-imports `click._termui_impl` before the focused pytest node so it does not test top-level exposure as an unintended prerequisite.
- Patch collection ignores runner-owned `.core_narrative/`, `.venv/`, `.pytest_cache/`, and `__pycache__` paths.
- Search/replace old-string ambiguity is classified as model-output `invalid_submission`, not infra.

Source-of-truth note: `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_corrected_20260508.json` reconciles the fill run from normalized per-run artifacts. It marks `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json` and the task-003 raw `batch_run_result.json` as stale, non-scoring audit outputs.

## Score Summary

| Slice | Cells | Passed | Failed | Invalid submission | Infra failed | Pass rate |
|---|---:|---:|---:|---:|---:|---:|
| Baseline attempt 1 | 9 | 6 | 3 | 0 | 0 | 66.7% |
| Frontier specialist fill attempt 1 | 3 | 2 | 0 | 1 | 0 | 66.7% |
| Attempt 2 repeat | 12 | 9 | 2 | 1 | 0 | 75.0% |
| All baseline plus follow-up | 24 | 17 | 5 | 2 | 0 | 70.8% |

Attempt 2 by task:

| Task | Passed | Failed | Invalid submission | Note |
|---|---:|---:|---:|---|
| `click__rbench__001` | 4 | 0 | 0 | stable across all four ACUTs |
| `click__rbench__002` | 4 | 0 | 0 | stable across all four ACUTs |
| `click__rbench__003` | 1 | 2 | 1 | differentiating task; only `frontier-generic-swe` passed |

## Run Matrix

| Task | ACUT | Attempt | Status | Scoreable | Outcome class | Key failure class |
|---|---|---:|---|---|---|---|
| `click__rbench__001` | `cheap-generic-swe` | 1 | passed | yes | passed | - |
| `click__rbench__001` | `frontier-generic-swe` | 1 | passed | yes | passed | - |
| `click__rbench__001` | `cheap-click-specialist` | 1 | passed | yes | passed | - |
| `click__rbench__002` | `cheap-generic-swe` | 1 | passed | yes | passed | - |
| `click__rbench__002` | `frontier-generic-swe` | 1 | passed | yes | passed | - |
| `click__rbench__002` | `cheap-click-specialist` | 1 | passed | yes | passed | - |
| `click__rbench__003` | `cheap-generic-swe` | 1 | failed | yes | model/task failed | `missing_repository_affordance`, `hidden_test_inference_miss` |
| `click__rbench__003` | `frontier-generic-swe` | 1 | failed | yes | model/task failed | `missing_repository_affordance`, `hidden_test_inference_miss` |
| `click__rbench__003` | `cheap-click-specialist` | 1 | failed | yes | model/task failed | `api_plumbing_incomplete`, `hidden_test_inference_miss` |
| `click__rbench__001` | `frontier-click-specialist` | 1 | passed | yes | passed | - |
| `click__rbench__002` | `frontier-click-specialist` | 1 | passed | yes | passed | - |
| `click__rbench__003` | `frontier-click-specialist` | 1 | invalid_submission | yes | model-output invalid | `search_replace_old_occurrence_mismatch` |
| `click__rbench__001` | `cheap-generic-swe` | 2 | passed | yes | passed | - |
| `click__rbench__001` | `frontier-generic-swe` | 2 | passed | yes | passed | - |
| `click__rbench__001` | `cheap-click-specialist` | 2 | passed | yes | passed | - |
| `click__rbench__001` | `frontier-click-specialist` | 2 | passed | yes | passed | - |
| `click__rbench__002` | `cheap-generic-swe` | 2 | passed | yes | passed | - |
| `click__rbench__002` | `frontier-generic-swe` | 2 | passed | yes | passed | - |
| `click__rbench__002` | `cheap-click-specialist` | 2 | passed | yes | passed | - |
| `click__rbench__002` | `frontier-click-specialist` | 2 | passed | yes | passed | - |
| `click__rbench__003` | `cheap-generic-swe` | 2 | failed | yes | model/task failed | `api_plumbing_incomplete` |
| `click__rbench__003` | `frontier-generic-swe` | 2 | passed | yes | passed | - |
| `click__rbench__003` | `cheap-click-specialist` | 2 | failed | yes | model/task failed | `api_plumbing_incomplete` |
| `click__rbench__003` | `frontier-click-specialist` | 2 | invalid_submission | yes | model-output invalid | `search_replace_old_occurrence_mismatch` |

## Film Notes

Click 001 and 002 are now stable in the follow-up: every ACUT passed both tasks in attempt 2, and the filled `frontier-click-specialist` attempt-1 cells also passed.

Click 003 remains the useful film task:

- Attempt 1 showed score-equivalent failures with different causes: generic ACUTs missed repository affordance, while cheap specialist missed `show_choices` API plumbing.
- The verifier pre-import repair removed the accidental top-level `_termui_impl` dependency before follow-up live calls.
- Attempt 2 split the field: `frontier-generic-swe` passed, cheap generic and cheap specialist still failed at `show_choices` option construction, and `frontier-click-specialist` again emitted an ambiguous search/replace edit that could not be safely applied.

This supports the NFL-style Barcarolle story with a caveat. The box score alone says "mostly passed"; the film says task 003 distinguishes verifier repair, API plumbing, hidden-test inference, and output-contract reliability. The caveat is that two frontier specialist losses are invalid model-output contracts rather than patch-verifier losses, so they should not be collapsed into ordinary failed patches.

## Gate 1 Decision

Gate artifact: `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json`.

| Condition | Result |
|---|---|
| `infra_failed_rate == 0` | pass |
| `verifier_repair_after_live == false` | pass |
| `unclassified_failure_rate <= 20%` | pass |
| `all_runs_have_clean_patch_replay == true` | fail |
| `frontier_click_specialist_attempt1_completed == true` | pass |
| `meaningful_film_contrast_exists == true` | pass |

Decision: do not run Click 004-008. The expansion would have been 20 additional live calls, and the stop reason is clean-replay evidence integrity, not API quota, credentials, or repository auth.

## Cost Reconciliation

Cost artifact: `experiments/core_narrative/results/codex_nfl_followup_cost_reconciliation_2026-05-08.json`.

| Cost item | USD |
|---|---:|
| Cumulative calibrated ledger before follow-up paid live calls | 0.716208 |
| Fill run provider-usage cost | 0.442095 |
| Attempt-2 provider-usage cost | 0.780565 |
| Follow-up paid live provider-usage cost | 1.222660 |
| Latest cumulative ledger estimated cost | 1.938868 |
| Observed provider-usage cost sum | 1.938868 |
| Actual provider billed/invoiced cost observed | unknown |

Provider usage cost is response metadata, not invoice proof. The ledger and normalized artifacts preserve the provider-reported accounting needed for local budget gates; actual billed cost remains unknown because no invoice/billing record is present.

## Evidence Artifacts

| Purpose | Path |
|---|---|
| Gate 0 passed preflight | `experiments/core_narrative/results/codex_nfl_gate0_preflight_v2_20260508.json` |
| First failed Gate 0 audit artifact | `experiments/core_narrative/results/codex_nfl_gate0_preflight_20260508.json` |
| Passed mock smoke | `experiments/core_narrative/results/codex_nfl_mock_smoke_followup_v2_20260508.json` |
| First failed mock smoke audit artifact | `experiments/core_narrative/results/codex_nfl_mock_smoke_followup_20260508.json` |
| Frontier specialist fill corrected evidence | `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_corrected_20260508.json` |
| Frontier specialist fill stale batch audit output | `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json` |
| Attempt-2 raw batch | `experiments/core_narrative/results/codex_nfl_live_2x2_attempt2_20260508.json` |
| Fill normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_frontier_specialist_fill_summary_20260508.json` |
| Attempt-2 normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_attempt2_summary_20260508.json` |
| Combined normalized summary | `experiments/core_narrative/results/normalized/codex_nfl_followup_summary_20260508.json` |
| Gate 1 stop decision | `experiments/core_narrative/results/codex_nfl_followup_gate1_decision_20260508.json` |
| Cost reconciliation | `experiments/core_narrative/results/codex_nfl_followup_cost_reconciliation_2026-05-08.json` |
| Raw per-run artifacts | `experiments/core_narrative/results/raw/codex_nfl_live_*20260508*/` |

## Next Step

Do not expand to Click 004-008 on this evidence as-is. The next decision should be explicit:

1. If `invalid_submission` is acceptable as scoreable film without a clean replay, revise Gate 1 to say so and justify the tradeoff.
2. If clean replay is mandatory, improve the model-output contract path before more expansion spend. The smallest live follow-up would be a targeted `frontier-click-specialist` task-003 rerun after strengthening or changing the output contract, not the full Click 004-008 expansion.
3. Keep task 003 in the matrix because it is doing useful diagnostic work, but avoid letting it dominate the broader NFL claim until Click 004-008 or another repository family is sampled.
