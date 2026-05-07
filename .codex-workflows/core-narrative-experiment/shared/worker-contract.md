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

## LLM Access And Budget Rules

Workers that perform, prepare, review, or launch ACUT execution must read `.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`.

- ACUT execution must use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for LLM access.
- Never record credential values, bearer tokens, provider secrets, resolved API keys, or full base URL values in Git, `process.md`, CLI logs, run results, reports, prompts, or review files.
- ACUT execution must block before any model call if either required environment variable is missing.
- ACUT execution must block before any model call if cost ledgering is missing, unavailable, or projected to exceed the USD `$300` hard cap.
- The USD `$240` soft stop requires an explicit coordinator decision before starting new ACUT patch-generation runs.
- Future execution workers must use `experiments/core_narrative/configs/llm_access.yaml` and append cost records to `experiments/core_narrative/results/cost_ledger.jsonl`.
- The default run profile is four core ACUTs, 6 `G_score` tasks, 8 `RBench` tasks, 6 `RWork` tasks, and one primary attempt per ACUT/task.

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
