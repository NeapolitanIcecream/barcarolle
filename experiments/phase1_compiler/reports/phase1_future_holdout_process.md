# Phase 1 Future Holdout Validation Process

Status: in progress.

Generated: 2026-05-22T07:40:03Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `3967a7a4d3cb467773b18b1d59a0755eb13f1720`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed only after design freeze: `true`
- Paid ACUT calls made in preflight: `false`
- Required endpoint env after sourcing `~/.zshrc`: present
- Cutoff primary axis: `repo_task_time`
- Model release/snapshot date role: `contamination_guard_only`
- Default embargo gap: `14` days

Current boundary matched the runbook:

- Boltons paid smoke decision: `boltons_paid_smoke_complete_ready_for_phase1_validation_design`
- Recommended next runbook: `write_phase1_validation_design_and_future_holdout_runbook`
- Current Phase 1 closeout predictive validity: `false`

Current cost reconciliation:

- call count: `123`
- usage observed rate: `0.9431`
- observed-or-conservative estimated cost: `37.6472432`
- total stop cap: `80.00`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.76s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `28 passed in 0.34s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Raw, workspace, external repo, venv, and cache paths are not tracked by Git.

No paid calls have been made in this runbook.

## Step 1 Future Holdout Config

Created `experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml`.

Config properties:

- claim scope: `future_holdout_design_not_predictive_validity`
- predictive validity established: `false`
- primary cutoff axis: `repo_task_time`
- model release/snapshot date role: `contamination_guard_only`
- model snapshot status: `unknown_until_recorded`
- embargo gap: `14` days
- previous ACUT outcomes disallowed in clean validation: `true`
- Humanize validation-grade use: diagnostic-only unless source provenance is repaired
- generic comparators excluded from target holdout
- paid ACUT concurrency: `1`
- total observed-or-conservative stop cap: `80.00`
