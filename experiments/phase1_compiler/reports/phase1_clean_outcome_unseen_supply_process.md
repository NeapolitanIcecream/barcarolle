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

## Step 1 Configure Continued Mining

Created `experiments/phase1_compiler/configs/phase1_clean_outcome_unseen_supply_mining.yaml`.

Config properties:

- claim scope: `clean_supply_mining_not_predictive_validation`
- predictive validity established: `false`
- paid ACUT calls: disabled
- paid LLM calls: disabled
- primary repo: `boltons`
- backup repo: `attrs`
- minimum clean split: `B_real >= 2`, `W_real >= 2`
- future-holdout minimum: `B_eval >= 2`, `H_future >= 2`
- prior clean supply overlay: `experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json`
- future-holdout overlay integration evidence level: `clean_supply_overlay_sidecar`

## Step 2 Continued Mining Tooling

Implemented `experiments/phase1_compiler/tools/phase1_clean_outcome_unseen_supply_mining.py`
and tests in
`experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py`.

Local test result:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py` -> `7 passed`

The tool rejects outcome-seen task ids, outcome-seen target commits,
solution-exposure rows, project-heavy ambiguous rows, and commit-message-only
rows. It writes only sanitized issue/PR context summaries and command hash
records, not raw GitHub responses or raw command logs.

## Step 3 Mine Boltons Supply

Ran:

- `phase1_clean_outcome_unseen_supply_mining.py audit-state`
- `phase1_clean_outcome_unseen_supply_mining.py mine-boltons`
- `phase1_clean_outcome_unseen_supply_mining.py review-candidates`

Generated:

- `experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_candidates.jsonl`
- `experiments/phase0_headroom/candidate_sources/boltons_clean_outcome_unseen_supply_source_context.jsonl`
- `experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_certified_tasks.jsonl`
- `experiments/phase0_headroom/certified_tasks/boltons_clean_outcome_unseen_supply_review_records.jsonl`
- `experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_candidate_inventory.json`
- `experiments/phase1_compiler/results/phase1_clean_outcome_unseen_supply_review.json`
- `experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_candidate_inventory.md`
- `experiments/phase1_compiler/reports/phase1_clean_outcome_unseen_supply_review.md`

Boltons mining result:

- reviewed candidates: `28`
- promoted clean extension candidates: `4`
- promoted task ids: `boltons__clean_ext__001`, `boltons__clean_ext__008`, `boltons__clean_ext__010`, `boltons__clean_ext__017`
- repaired source contexts: `issue:231`, `issue:240`, `issue:252`, `issue:319`
- rejected blocker counts include `previous_acut_outcome_seen=7`, `previous_acut_target_commit_seen=7`, `solution_exposure_risk=5`, `scope_context_project_heavy_or_ambiguous=1`
- cutoff feasibility for `boltons`: `clean_validation_ready=true`
- predictive validity established: `false`

Because Boltons supply is cutoff-feasible, attrs backup screening is skipped.

No paid calls have been made in this runbook.
