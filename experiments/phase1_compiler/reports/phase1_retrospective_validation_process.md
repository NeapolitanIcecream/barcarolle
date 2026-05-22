# Phase 1 Retrospective Validation And Clean Supply Process

Status: in progress.

Generated: 2026-05-22T08:12:58Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `d8e2673b5cd68ba39f202ffbe8f5640799f5a7c0`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Retrospective evidence level: `outcome_seen_retrospective_locked`
- Retrospective paid ACUT calls allowed: `false`
- Clean-supply paid ACUT calls allowed only after clean-supply gate: `true`
- Required endpoint env after sourcing `~/.zshrc`: present

Strict future-holdout blocker matched the runbook:

- decision: `future_holdout_supply_blocked`
- recommended next runbook: `mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout`
- Boltons clean outcome-unseen count: `0`
- Toolz clean outcome-unseen count: `0`

Current cost reconciliation:

- call count: `123`
- usage observed rate: `0.9431`
- observed-or-conservative estimated cost: `37.6472432`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 4.89s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `35 passed in 0.84s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Raw, workspace, external repo, venv, and cache paths are not tracked by Git.

No paid calls have been made in this runbook.

## Step 1 Config

Created `experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml`.

Config properties:

- claim scope: `retrospective_locked_validation_not_clean_future_holdout`
- primary retrospective evidence level: `outcome_seen_retrospective_locked`
- strict holdout evidence level: `clean_future_holdout`
- retrospective paid ACUT calls: disabled
- retrospective inclusion rule: use all primary eligible outcome-seen rows
- primary retrospective prefixes:
  - Toolz: `codex_kilo_workspace_followup`
  - Boltons: `phase1_validation_boltons_paid_smoke`, `phase1_validation_boltons_paid_extension`
- diagnostic-only result prefixes include Toolz stability repeats and Humanize holdout/smoke/stability prefixes
- Humanize and generic comparators are excluded from primary validation
- clean-supply candidate source: current Boltons manual-review-required candidates
- clean-supply paid ACUT calls: disabled until clean supply is ready
- predictive validity established: `false`

## Step 2 Retrospective Validation Tooling

Added deterministic retrospective validation tooling:

- `experiments/phase1_compiler/tools/phase1_retrospective_validation.py`
- `experiments/phase1_compiler/tests/test_phase1_retrospective_validation.py`

Implemented commands:

- `plan`
- `score`
- `review-clean-supply`
- `decide`

Tooling behavior covered by tests:

- outcome-seen rows are allowed only under the retrospective evidence level
- Click and Humanize are excluded from primary target validation
- Toolz stability repeat is diagnostic-only
- B_real/W_real pass-rate error calculation
- non-scoreable rows do not enter pass-rate denominators
- predictive validity is never claimed by the retrospective metrics payload

Verification:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_retrospective_validation.py` -> `6 passed in 0.01s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `41 passed in 0.34s`

No paid calls have been made in this step.
