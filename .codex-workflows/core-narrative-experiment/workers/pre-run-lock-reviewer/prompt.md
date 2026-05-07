# Pre-Run Locks Review Prompt

You are the focused reviewer for the Barcarolle core narrative experiment pre-run locks.

Reviewer repo path: `/Users/chenmohan/gits/barcarolle-wt-pre-run-lock-reviewer`
Reviewer branch: `codex/core-exp-pre-run-lock-reviewer`

Delivered workers under review:

- repo-runtime-lock worktree: `/Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock`
- repo-runtime-lock delivery commit: `029fbdf`
- general-benchmark-lock worktree: `/Users/chenmohan/gits/barcarolle-wt-general-lock`
- general-benchmark-lock delivery commit: `88acbad`

Do not inspect any `cli.log` file. Do not make ACUT model calls. Do not write credential values, bearer tokens, resolved secrets, or full base URL values into Git, process files, logs, reports, or results.

## Read First

- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock/.codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/process.md`
- `/Users/chenmohan/gits/barcarolle-wt-general-lock/.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`

Then inspect only the config/report/tooling files needed to validate the two delivered locks.

## Review Scope

Check repo-runtime-lock:

- `pallets/click` is locked to a concrete commit.
- The ignored local checkout path is used and not staged.
- Runtime/install/smoke/full pytest commands are recorded with plausible timings and passing results.
- The revised default repo-specific slice remains 8 `RBench`, 6 `RWork`, one primary attempt each.
- Fallbacks were not needed after primary success.

Check general-benchmark-lock:

- The pinned SWE-Bench Pro parquet was fetched/cached without requiring HF token.
- SHA256 matches `c8cd7115496ad4e9a8b21d088cef576a65bf821bb542b24336f13f714cef13f8`.
- Locked `G_score` task IDs are computed from the pinned parquet using only the recorded salt/selection rule, with no invented IDs and no inspection of gold patches/test patches/test outcomes.
- The revised default is exactly 6 `G_score` tasks and one primary attempt per ACUT/task.
- Cache artifacts and temporary reader environments are ignored by Git.
- Docker availability is recorded, but no evaluator scoring or broad ACUT execution was started.

Check shared constraints:

- LLM access/cost/redaction gates from Wave 0 r5 are not reopened or modified.
- Broad ACUT execution remains blocked until coordinator integrates/reviews both locks and explicitly starts execution.
- No credentials or resolved secrets are persisted.

## Output

Write `.codex-workflows/core-narrative-experiment/reviews/pre-run-locks-review.md`:

```markdown
# Pre-Run Locks Review

status: issues_found | no_issues | blocked

## Summary
...

## Findings
1. ...

## Required Closure
...

## Self-Checks
...
```

If no issues remain, set `status: no_issues` and make `Required Closure` say `None`.

Update your `process.md` before and after meaningful phases. At the end, set `status: delivered` or `status: blocked`, summarize the review, list changed/inspected files, and include a handoff summary. Commit only owned review/process files on `codex/core-exp-pre-run-lock-reviewer`. Do not push.
