You are the `acut-matrix` revision worker for the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Worker repo: /Users/chenmohan/gits/barcarolle-wt-acut-matrix
Worker branch: codex/core-exp-acut-matrix
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment
Process file: /Users/chenmohan/gits/barcarolle-wt-acut-matrix/.codex-workflows/core-narrative-experiment/workers/acut-matrix/process.md
Feedback file: .codex-workflows/core-narrative-experiment/workers/acut-matrix/review-feedback-1.md

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Only edit your owned paths in your assigned worker repo. Update your process.md at start, after meaningful phases, and before exit. Include branch and worktree state in process.md. Mark status: delivered only when your assigned artifacts are complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.

Owned paths:
- experiments/core_narrative/configs/acuts/**
- experiments/core_narrative/reports/acut_matrix_notes.md
- .codex-workflows/core-narrative-experiment/workers/acut-matrix/**

Task:
1. Read the plan, shared worker contract, your delivered process.md, and `review-feedback-1.md`.
2. Normalize all seven ACUT YAML manifests to the canonical top-level contract while preserving the intended configuration contrasts.
3. Update `experiments/core_narrative/reports/acut_matrix_notes.md` with the manifest contract and validation notes.
4. If useful, inspect the schema worker's current ACUT schema, but do not edit that worktree.
5. Run and record self-check commands in process.md.
6. Commit only your owned changes on `codex/core-exp-acut-matrix`. Do not push.
