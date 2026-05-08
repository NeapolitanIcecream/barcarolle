# Worker Revision 1

You are the WORKER agent revising the delivered Barcarolle follow-up NFL experiment evidence in `/Users/chenmohan/gits/barcarolle` on branch `codex/nfl-followup-experiments`.

Do not ask the user for confirmation unless blocked by missing credentials, API quota/funds, repo auth, or a truly ambiguous destructive action. Do not read coordinator/reviewer CLI logs.

## Context

Reviewer found one PR-readiness issue in `.codex-workflows/barcarolle-nfl-followup-experiments/worker/review-feedback-1.md`.

The paid live plan itself is accepted:

- `frontier-click-specialist` attempt 1 ran on Click `001`-`003`.
- attempt 2 ran across all four ACUTs on Click `001`-`003`.
- Gate 1 no-expansion decision is defensible.
- Local facility tests passed.

## Required Fix

Close the evidence-packaging contradiction without another paid model call.

The issue: `experiments/core_narrative/results/codex_nfl_live_frontier_specialist_fill_20260508.json` and its per-run `batch_run_result.json` still expose the frontier-click task-003 fill cell as `infra_failed` / not scoreable, while the normalized source of truth and reports count it as scoreable `invalid_submission`.

Implement one of these defensible closures:

1. Regenerate or create a corrected fill batch summary from existing normalized/raw artifacts and point the report/evidence package at it.
2. Or explicitly mark the original fill batch and per-run batch result as stale/non-scoring, exclude them from scoring/gate inputs, and make the reports point reviewers to the normalized source of truth.

Prefer a machine-readable corrected artifact if practical. Do not spend any live/API calls for this revision.

## Verification

After the fix, run:

- artifact consistency smoke for the corrected evidence path;
- `PYTHONDONTWRITEBYTECODE=1 python3 -m unittest test_run_task.py test_codex_nfl_experiment_runner.py test_openclaw_direct_runner.py test_codex_nfl_direct_runner.py test_codex_nfl_gate0_preflight.py` from `experiments/core_narrative/tools`;
- `git diff --check -- . ':(exclude)experiments/core_narrative/results/raw/**'`.

Update `.codex-workflows/barcarolle-nfl-followup-experiments/worker/process.md` with `status: delivered`, files changed, verification, and a concise handoff.
