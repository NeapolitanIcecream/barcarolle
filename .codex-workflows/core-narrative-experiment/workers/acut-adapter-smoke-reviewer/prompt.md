# ACUT Adapter Smoke Review

You are the focused reviewer for the Barcarolle core narrative experiment ACUT adapter smoke delivery.

Repository context:

- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Reviewer worktree: `/Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke-reviewer`
- Delivered worker worktree: `/Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke`
- Delivered worker branch: `codex/core-exp-acut-adapter-smoke`
- Delivered worker commit: `3b2f820`
- Coordinator file: `.codex-workflows/core-narrative-experiment/coordinator.md`
- Delivered worker process: `/Users/chenmohan/gits/barcarolle-wt-acut-adapter-smoke/.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke/process.md`

Hard workflow constraints:

- Do not inspect any `cli.log` files.
- Do not edit production experiment artifacts, source files, configs, raw results, normalized results, or reports.
- Do not start broad ACUT execution, ACUT model calls, or patch-generation attempts against a live model.
- Do not write credential values, bearer tokens, resolved secrets, or full base URL values anywhere.
- Review through the delivered worktree and process files only; the review output belongs in this reviewer worktree.

Owned output paths:

- `.codex-workflows/core-narrative-experiment/reviews/acut-adapter-smoke-review.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/process.md`

Review scope:

1. Verify the delivered commit and changed-file scope for `acut-adapter-smoke`.
2. Review `experiments/core_narrative/tools/acut_patch_adapter.py` and relevant existing gate/ledger helpers it calls.
3. Confirm the adapter command path uses only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for LLM access.
4. Confirm missing required LLM env vars block before command execution and record a ledger entry.
5. Confirm budget/ledger gating occurs before command execution and appends one ledger record per dry-run, blocked attempt, or future patch-generation attempt.
6. Confirm emitted artifacts and reports do not contain credential values, bearer tokens, resolved secrets, or full base URL values.
7. Confirm unsafe CLI args containing credential-like keys or full URL values are rejected/redacted before result persistence.
8. Confirm the smoke checks are no-model-call checks only and broad execution/model calls remain not started.
9. Check for integration blockers that would prevent the coordinator from merging this delivery before explicit execution start.

Allowed verification:

- Read files in the delivered worker worktree except `cli.log`.
- Run no-model-call static checks, parsers, `git diff --check`, and local dry-run probes if they cannot consume LLM budget.
- Inspect Git metadata and status.

Deliverable format:

Write `.codex-workflows/core-narrative-experiment/reviews/acut-adapter-smoke-review.md`:

```markdown
# ACUT Adapter Smoke Review

status: no_issues | issues_found | blocked
reviewed_worker_commit: <short hash>
updated: <Asia/Shanghai timestamp>

## Summary
...

## Findings
1. ...

## Required Closure
...

## Checks Run
- ...
```

If there are no findings, write `None.` under Findings and Required Closure.

Update `.codex-workflows/core-narrative-experiment/workers/acut-adapter-smoke-reviewer/process.md` before and after review. When complete, set `status: delivered`, include findings count, changed/inspected files, checks run, and handoff. Commit only your owned output paths on branch `codex/core-exp-acut-adapter-smoke-reviewer`.
