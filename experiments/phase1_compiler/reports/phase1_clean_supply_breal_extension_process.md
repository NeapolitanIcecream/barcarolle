# Phase 1 Clean Supply B_real Extension Process

Status: in progress.

Generated: 2026-05-22T08:40:23Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `23cb0e04e9461c448d5dfb47ba64bc1970ea8e91`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed: `false`
- Direct paid LLM calls allowed: `false`
- Required missing split: `B_real`
- Predictive validity established: `false`

Current blocker matched the runbook:

- retrospective decision: `retrospective_validation_complete_clean_supply_still_blocked`
- recommended next runbook: `mine_additional_clean_outcome_unseen_supply`
- current promoted `B_real`: `boltons__hist__011`
- current promoted `W_real`: `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- minimum clean split: `B_real >= 2`, `W_real >= 2`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.66s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `41 passed in 0.27s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Raw, workspace, external repo, venv, and cache paths are not tracked by Git.

No paid calls have been made in this runbook.

## Step 1 Config

Created `experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml`.

Config properties:

- claim scope: `clean_supply_extension_not_predictive_validation`
- predictive validity established: `false`
- paid ACUT calls: disabled
- paid LLM calls: disabled
- target repo: `boltons`
- missing split: `B_real`
- minimum clean split: `B_real >= 2`, `W_real >= 2`
- first candidate: `boltons__hist__014`
- current candidate blocker: `scope_context_project_heavy_or_ambiguous`
- output mode: overlay evidence, not canonical release mutation
