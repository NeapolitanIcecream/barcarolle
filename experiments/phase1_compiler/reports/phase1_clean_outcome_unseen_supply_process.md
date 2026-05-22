# Phase 1 Clean Outcome-Unseen Supply Mining Process

Status: in progress.

Generated: 2026-05-22T10:11:10Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `5a78deec99e1276507f8a3e2655319affedda1c4`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed: `false`
- Direct paid LLM calls allowed: `false`
- Paid ACUT calls made: `false`
- Direct paid LLM calls made: `false`
- Predictive validity established: `false`

Previous clean B_real extension state matched the runbook:

- decision: `clean_supply_breal_extension_still_blocked`
- recommended next runbook: `continue_mining_clean_outcome_unseen_supply`
- clean supply ready: `false`
- promoted `B_real`: `boltons__hist__011`
- promoted `W_real`: `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- minimum clean split: `B_real >= 2`, `W_real >= 2`

Stale future-holdout supply state:

- clean supply ready: `false`
- selected repos: none
- blocker: `no_repo_has_minimum_clean_outcome_unseen_supply`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.82s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `47 passed in 0.33s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

No paid calls have been made in this runbook.
