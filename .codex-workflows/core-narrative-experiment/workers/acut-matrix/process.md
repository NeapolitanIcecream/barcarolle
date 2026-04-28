# Process

status: delivered
updated: 2026-04-28T09:38:54+08:00

## Summary

Delivered and locally committed seven frozen ACUT manifests plus ACUT matrix notes. YAML parsing, required-field, model/provider, operator, general-benchmark-basis, null score-field, and staged whitespace checks passed.

## Owned Paths

- `experiments/core_narrative/configs/acuts/**`
- `experiments/core_narrative/reports/acut_matrix_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-matrix/process.md`

## Files Changed Or Inspected

- `docs/experiments/core-narrative-experiment-plan.md` inspected
- `.codex-workflows/core-narrative-experiment/shared/experiment-brief.md` inspected
- `.codex-workflows/core-narrative-experiment/shared/worker-contract.md` inspected
- `.codex-workflows/core-narrative-experiment/workers/acut-matrix/prompt.md` inspected
- `.codex-workflows/core-narrative-experiment/workers/acut-matrix/process.md` updated
- `experiments/core_narrative/configs/general_benchmark.yaml` inspected
- `experiments/core_narrative/configs/target_repositories.yaml` inspected
- `experiments/core_narrative/configs/acuts/minimal-context-baseline.yaml` created
- `experiments/core_narrative/configs/acuts/general-benchmark-optimized.yaml` created
- `experiments/core_narrative/configs/acuts/repo-context-heavy.yaml` created
- `experiments/core_narrative/configs/acuts/higher-budget-repo-depth.yaml` created
- `experiments/core_narrative/configs/acuts/lower-budget-fast-path.yaml` created
- `experiments/core_narrative/configs/acuts/retrieval-sparse-symbolic.yaml` created
- `experiments/core_narrative/configs/acuts/retrieval-history-augmented.yaml` created
- `experiments/core_narrative/reports/acut_matrix_notes.md` created

## Current Blockers

None.

## Git State

branch: codex/core-exp-acut-matrix
worktree: /Users/chenmohan/gits/barcarolle-wt-acut-matrix
state: owned artifact changes only; self-check passed; delivery commit created locally; not pushed

## Handoff

Ready for coordinator review. The matrix contains seven ACUTs covering minimal context, general-benchmark optimization, repository-heavy context, higher budget, lower budget, sparse symbolic retrieval, and history-augmented retrieval. No public benchmark scores are claimed in the manifests.
