# Review To Worker

status: issues_found

## Summary
Reviewed the current PR #1 branch for local PR readiness. Runner clean verification, regression tests, JSON artifacts, cost ledger reconciliation, PR body consistency, and temporary clean replay of the nine live patches all checked out. One PR-readiness issue remains: the non-raw whitespace diff check fails.

## Findings
1. `.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/prompt.md:69` and `.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/run_reviewer.sh:14` add extra blank lines at EOF. `git diff --check origin/main...HEAD -- ':!experiments/core_narrative/results/raw/**'` exits nonzero with those two findings, which contradicts the worker handoff's clean non-raw whitespace check and can fail any CI or maintainer gate that runs `git diff --check`.

## Required Closure
Remove the extra blank EOF lines from the two workflow files, then rerun `git diff --check origin/main...HEAD -- ':!experiments/core_narrative/results/raw/**'`. No live API calls are needed.
