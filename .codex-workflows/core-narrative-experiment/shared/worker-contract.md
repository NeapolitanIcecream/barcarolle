# Worker Contract

Every worker must follow this contract.

## Required Context

- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Workflow root: `.codex-workflows/core-narrative-experiment`
- Plan: `docs/experiments/core-narrative-experiment-plan.md`

## Rules

- You are not alone in the codebase. Other workers may be editing different worktrees and branches.
- Do not revert changes you did not make.
- Only edit your owned paths and your worker `process.md`.
- Update `process.md` at start, after meaningful phases, and before exit.
- Mark `status: delivered` only when artifacts are complete and self-checked.
- Mark `status: blocked` with exact blocker details when blocked.
- Do not inspect or depend on other workers' private intermediate files unless the coordinator explicitly assigns that handoff.
- Keep large generated artifacts, cloned repositories, dependency caches, and logs out of Git.
- Commit only your owned artifact changes on your worker branch when delivered. Do not push.

## Process File Shape

```markdown
# Process

status: working
updated: 2026-04-28T00:00:00+08:00

## Summary
...

## Owned Paths
...

## Files Changed Or Inspected
...

## Current Blockers
...

## Git State
branch: ...
worktree: ...

## Handoff
...
```
