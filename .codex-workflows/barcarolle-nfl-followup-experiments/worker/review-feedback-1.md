# Review To Worker

status: issues_found

## Summary
The paid live plan was executed and the Gate 1 no-expansion decision is defensible: the frontier specialist fill ran on Click 001-003, attempt 2 covers all four ACUTs on Click 001-003, no Click 004-008 expansion artifacts exist, costs reconcile to the reported USD 1.222660 follow-up provider-usage total, and the local facility tests pass. One evidence-packaging issue remains before this is PR-ready.

## Findings
1. The fill batch artifact still records the frontier-click task-003 fill cell as `infra_failed` and not scoreable, while the normalized source of truth and reports count it as scoreable `invalid_submission`. This is broader than the report's current "stale aggregate" caveat: `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json` has `infra_failed` in the aggregate at lines 8/24/28, embeds the task-003 normalized row as `"status": "infra_failed"` at line 863, and exposes the top-level result as `"scoreable": false` / `"status": "infra_failed"` at lines 921-922. The per-run raw `batch_run_result.json` has the same stale fields and null model-call/provider-response metadata, while `experiments/core_narrative/results/normalized/codex_nfl_live_frontier_specialist_fill_20260508__frontier-click-specialist__click__rbench__003__attempt1.json` reports `"status": "invalid_submission"` at line 54 and the fill summary reports 3 scoreable cells. Because the evidence package lists the stale fill batch as a raw batch artifact, downstream reviewers can get contradictory fill counts and infra-failure rates from the delivered evidence.

## Required Closure
Regenerate or reconcile the fill batch evidence without another paid model call so the PR has one machine-readable source of truth. Either update/create a corrected fill batch summary from the existing normalized/raw provider-response artifacts and point the report/evidence package at it, or explicitly mark the original fill batch and its per-run `batch_run_result.json` as stale beyond just the aggregate and exclude them from scoring/gate inputs. Then rerun the artifact consistency smoke and the focused unit suite.
