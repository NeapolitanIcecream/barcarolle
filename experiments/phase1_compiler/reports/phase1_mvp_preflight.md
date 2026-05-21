# Phase 1 MVP Preflight

Generated: `2026-05-21T14:24:17Z`.

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `27e8061942a0c6c0c3b18c21591cea1e5977f652`.
- Python: `Python 3.9.6`.
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`.
- Readiness gate status: `ready_for_phase1_mvp`.
- Predictive validity established: `false`.

## Hygiene

- `git diff --check`: passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `62 passed`.
- `uv run --project experiments/phase1_compiler pytest -q`: `5 passed`.
- Ignored scoped paths are limited to caches, venvs, raw results, workspaces,
  and external repos.
- No ignored raw/workspace/external-repo/venv paths are tracked in the checked
  Phase 0 and Phase 1 scopes.
- No paid ACUT or LLM call was made during preflight.
