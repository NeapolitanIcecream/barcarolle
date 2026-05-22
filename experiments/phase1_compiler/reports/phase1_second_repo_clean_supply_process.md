# Phase 1 Second-Repo Clean Supply Process

Status: in progress.

Generated: 2026-05-22T12:17:29Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `00ff5c0aab6eaa39021bac1a3ff6e98db79524cc`
- Python: `Python 3.11.13`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed: `false`
- Direct paid LLM calls allowed: `false`
- Paid ACUT calls made: `false`
- Direct paid LLM calls made: `false`
- Predictive validity established: `false`

Worktree preflight state:

- `git diff --check` passed.
- `git status --short --branch` showed only the untracked runbook file supplied for this execution.
- The branch was ahead of origin by `159` commits at preflight.

Boltons clean future-holdout pilot matched the runbook:

- decision: `boltons_clean_future_holdout_pilot_complete_insufficient_sample`
- selected repo: `boltons`
- B_eval scoreable cells: `8`
- H_future scoreable cells: `8`
- policy violations: `0`
- blockers: `predictive_validity_min_target_repos_not_met`, `predictive_validity_min_holdout_scoreable_cells_not_met`
- recommended next runbook: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`

Current Phase 1 closeout matched the required next path:

- future-holdout sidecar evidence: `available_as_future_holdout_sidecar_evidence`
- clean future-holdout scale-up status: `boltons_clean_future_holdout_pilot_complete`
- next runbook recommendation: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`
- predictive validity established: `false`

Baseline checks passed:

- `uv run --project experiments/phase1_compiler pytest -q` -> `57 passed in 0.36s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

No paid calls have been made in this runbook.
