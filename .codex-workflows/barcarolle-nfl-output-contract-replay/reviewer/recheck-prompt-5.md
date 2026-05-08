# Reviewer Recheck 5 Prompt

You are the reviewer for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This is a review-only pass for worker continuation 4. Do not edit task artifacts. Do not read worker or reviewer CLI logs. Coordinate only through `reviewer/process.md` and `reviewer/review-to-worker.md`.

## Context

Worker continuation 4 delivered a no-new-spend triage for the Click 005 and Click 008 failure clusters after the controlled Click 004-008 expansion.

The worker claims:
- No live model calls, retries, extra attempts, broader repos, or Click 009+ work were run.
- Click 005 historical box score remains `3 failed`, `1 invalid_submission`, but the 3 patch-ready verifier failures are task/verifier-semantics artifacts because the verifier asked for missing test node `test_case_insensitive_choice_returned_exactly`.
- Click 005's `cheap-click-specialist` invalid submission remains a model-output contract failure with no verifier-ready patch.
- Click 008 has 2 ordinary verifier failures around `Option(... prompt_required=...)` and 2 model-output contract invalid submissions.
- A local no-spend fixture repair was made so Click 005 hidden verifier tests now define `test_case_insensitive_choice_returned_exactly`, matching `verifier/run.sh`.
- Historical normalized artifacts still record the pre-repair verifier digest and outcomes; the report should not rewrite the old box score.

## Review Scope

Inspect the delivered artifacts and relevant source/test fixtures only as needed to verify continuation 4:
- `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_008_failure_triage_20260508.json`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__005/verifier/run.sh`
- `experiments/core_narrative/tasks/click/rbench/click__rbench__005/verifier/hidden/tests/test_options.py`
- Relevant normalized/raw artifacts only if needed to validate the triage claims.

Do not reopen previously closed decisions except where continuation 4 contradicts them.

## Checks To Perform

1. Confirm the report separates historical box score from film evidence and does not overclaim Click 005 model ability after the fixture repair.
2. Confirm the triage JSON is machine-readable, internally consistent, and matches the report/process summary for Click 005 and Click 008.
3. Confirm the Click 005 hidden test addition matches the existing `verifier/run.sh` node name and only repairs the local verifier fixture.
4. Confirm continuation 4 did not create evidence of new live model calls, retries, extra attempts, broader repos, or Click 009+ artifacts.
5. Confirm the stated next local step is appropriate: no-new-spend replay of the existing Click 005 patch artifacts against the repaired verifier, then prompt/output-contract/context repair before any new live retry.

Run read-only checks when useful. If you run commands, keep them bounded and report them.

## Required Output

Update `reviewer/process.md` with:
- `status: delivered`
- updated timestamp
- concise summary
- files inspected
- checks/tests run
- findings count
- handoff summary

Write `reviewer/review-to-worker.md` exactly in this format:

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

Use `status: no_issues` only if continuation 4 is ready for supervisor continuation or PR packaging. Use `issues_found` for concrete fixable gaps. Use `blocked` only for missing credentials, inaccessible required files, or hard infrastructure blockers.
