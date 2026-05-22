# Phase 1 Preregistered Clean Future-Holdout Paid Validation Process

Status: in progress.

Generated: 2026-05-22T10:56:23Z.

## Step 0 Preflight And State Record

Preflight passed without paid ACUT calls.

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `276980a1048b46c878b2ccb31bdd94ec34b16b88`
- Required endpoint env after sourcing `~/.zshrc`: present
- Clean supply decision: `boltons_clean_supply_ready_for_preregistered_validation`
- Preregistration status: `frozen`
- Selected repo: `boltons`
- Existing future-holdout paid calls: `false`
- Existing `B_eval` scoreable cells: `0`
- Existing `H_future` scoreable cells: `0`
- Predictive validity established: `false`

Baseline checks:

- `git diff --check` -> passed
- `uv run --project experiments/phase1_compiler pytest -q` -> `56 passed in 0.31s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Starting worktree state was not clean because the runbook file itself was
untracked:

```text
?? docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md
```

No conflicting existing changes were found.
