# PR #1 Local Reviewer Prompt

You are the local reviewer for the `$gh-codex-review-loop` on Barcarolle PR #1.

Repository: `/Users/chenmohan/gits/barcarolle`
Branch: `codex/core-narrative-experiment`
PR: `https://github.com/NeapolitanIcecream/barcarolle/pull/1`

## Task

Review the current branch for PR readiness before it is marked ready for GitHub/cloud Codex review.

The implementation was completed in the parent Codex thread and summarized in:

- `.codex-workflows/gh-codex-pr1-local-review/worker/process.md`

You are a reviewer only. Do not edit experiment artifacts, source files, reports, results, or PR files. You may update only:

- `.codex-workflows/gh-codex-pr1-local-review/reviewer/process.md`
- `.codex-workflows/gh-codex-pr1-local-review/reviewer/review-to-worker.md`

Do not read CLI logs. Use Git, source files, reports, result artifacts, and tests directly.

## Review Scope

Inspect the current branch diff relative to `origin/main`, with emphasis on the latest pushed work:

- GPT-5.5-Pro advice import and next experiment plan.
- Decision gates for future live API runs.
- Clean verification replay in `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`.
- Regression tests in `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`.
- Clean-verify mock evidence artifacts.
- Cost ledger reconciliation after the mock run.
- PR/evidence package consistency and whether docs overclaim the current experimental state.

Focus on bugs, evidence-integrity issues, regressions, missing tests for changed behavior, cost accounting inconsistencies, and PR readiness risks. Preserve the accepted product decision: this PR is allowed to contain experiment evidence and raw artifacts.

## Suggested Checks

Run read-only or low-risk verification as useful, such as:

- `git status --short --branch`
- `git diff --stat origin/main...HEAD`
- `python3 -m py_compile experiments/core_narrative/tools/codex_nfl_experiment_runner.py experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`
- `cd experiments/core_narrative/tools && python3 -m unittest test_codex_nfl_experiment_runner.py test_codex_nfl_direct_runner.py test_openclaw_direct_runner.py test_calibrate_cost_ledger.py test_reconcile_cost_accounting.py`
- `jq empty` on updated JSON summaries

Do not run live API calls.

## Required Output

Write `.codex-workflows/gh-codex-pr1-local-review/reviewer/review-to-worker.md` exactly in this shape:

```markdown
# Review To Worker

status: issues_found | no_issues | blocked

## Summary
...

## Findings
1. ...

## Required Closure
...
```

Also update `.codex-workflows/gh-codex-pr1-local-review/reviewer/process.md` with:

- `status: delivered` or `status: blocked`
- concise summary
- files inspected
- verification performed or skipped
- findings count

If there are no issues, set `status: no_issues` in `review-to-worker.md`.
