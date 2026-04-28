You are a reviewer for delivered Wave 0 workstreams in the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Reviewer repo: /Users/chenmohan/gits/barcarolle-wt-wave0-reviewer
Reviewer branch: codex/core-exp-wave0-reviewer
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment
Process file: /Users/chenmohan/gits/barcarolle-wt-wave0-reviewer/.codex-workflows/core-narrative-experiment/workers/wave0-reviewer/process.md

Do not edit production experiment artifacts. Inspect delivered files and worker process files. Write your review only to:
- .codex-workflows/core-narrative-experiment/reviews/wave0-review.md
- .codex-workflows/core-narrative-experiment/workers/wave0-reviewer/process.md

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Update your process.md at start, after meaningful phases, and before exit. Mark status: delivered only when the review is complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.

Delivered worker worktrees and commits:
- repo-scout: /Users/chenmohan/gits/barcarolle-wt-repo-scout at commit 9b5dbbe
- schema-toolsmith: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith at commit a9824ba
- acut-matrix: /Users/chenmohan/gits/barcarolle-wt-acut-matrix at commit dcbdc1e
- general-benchmark: /Users/chenmohan/gits/barcarolle-wt-general-benchmark at commit 54a07ae

Task:
1. Read the plan, shared experiment brief, worker contract, coordinator.md, and each delivered worker process.md.
2. Inspect the delivered artifacts in each worker worktree. Do not inspect `cli.log`.
3. Focus on experimental validity, reproducibility, leakage risk, broken artifact contracts, ownership violations, missing handoff information, and whether the coordinator can safely integrate the Wave 0 branches.
4. Write `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md` in this format:

```markdown
# Wave 0 Review

status: no_issues | issues_found | blocked

## Summary
...

## Findings
1. ...

## Integration Recommendation
...

## Required Closure
...
```

5. If issues are found, make them actionable and attribute each to the owning worker.
6. Self-check that your review file exists and that your process.md is current.
7. Commit only your review/process changes on your reviewer branch if delivery succeeds. Do not push.
