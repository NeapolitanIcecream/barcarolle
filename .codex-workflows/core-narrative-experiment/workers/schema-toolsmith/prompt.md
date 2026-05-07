You are a Codex CLI worker in the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Worker repo: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith
Worker branch: codex/core-exp-schema-toolsmith
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment
Process file: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith/.codex-workflows/core-narrative-experiment/workers/schema-toolsmith/process.md

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Only edit your owned paths in your assigned worker repo. Update your process.md at start, after meaningful phases, and before exit. Include branch and worktree state in process.md. Mark status: delivered only when your assigned artifacts are complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.

Owned paths:
- experiments/core_narrative/schemas/**
- experiments/core_narrative/tools/**
- .codex-workflows/core-narrative-experiment/workers/schema-toolsmith/process.md

Task:
1. Read the plan, shared experiment brief, and worker contract.
2. Create minimal JSON schemas for ACUT manifests, task manifests, and run result JSON under `experiments/core_narrative/schemas/`.
3. Draft minimal Python tooling under `experiments/core_narrative/tools/`:
   - `prepare_workspace.py`
   - `run_task.py`
   - `apply_and_verify.py`
   - `summarize_results.py`
4. Keep the tools small and dependency-light. They should provide `--help`, clear errors, and structured outputs suitable for later phases.
5. Add any local helper README only if it materially improves runner usability.
6. Self-check by running syntax checks and each tool's `--help`.
7. Commit only your owned artifact changes on your worker branch if delivery succeeds. Do not push.
