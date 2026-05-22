# Phase 1 Autonomous Overnight Two-Repo Process

## Step 0 Preflight

Runbook:
`docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`.

Recorded environment:

- branch: `codex/restart-benchmark-compiler`
- HEAD: `99bfab15f5507d5a75803a8830cfa2f4a290a7f8`
- generated at: `2026-05-22T15:44:16Z`
- Python: `python` command not available; `python3 --version` returned `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- codex: `codex-cli 0.133.0`
- kilo: `7.3.1`

Endpoint check:

- sourced `~/.zshrc` before checking
- `LLM_BASE_URL` present: yes
- `LLM_API_KEY` present: yes
- values printed: no

Frozen design check:

- second repo decision: `two_repo_future_holdout_design_frozen_ready_for_paid_validation`
- selected repos: `boltons`, `attrs`
- selected second repo: `attrs`
- two-repo preregistration status: `frozen`
- paid second-repo ACUT calls made: `false`
- predictive validity established: `false`
- planned attrs B_eval tasks: `attrs__hist__001`, `attrs__hist__003`, `attrs__hist__004`, `attrs__hist__008`
- planned attrs H_future tasks: `attrs__hist__012`, `attrs__hist__013`, `attrs__hist__023`, `attrs__hist__027`
- planned attrs cells: `8` B_eval, `8` H_future
- existing Boltons paid evidence: `8` B_eval scoreable cells, `8` H_future scoreable cells, `0` policy violations

Baseline validation:

- `git diff --check`: pass
- `uv run --project experiments/phase1_compiler pytest -q`: `65 passed in 0.36s`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `74 passed in 2.14s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`: `status=valid`

Worktree note:

- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md` was untracked at preflight start and is treated as user-provided input.

Initial branch selection:

The preflight evidence supports continuing toward Branch B, the paid gates path,
after the required local metadata consistency check. No paid calls were made in
Step 0.

## Step 1 Metadata Repair

The runbook's known issue was present:

- `phase1_second_repo_clean_supply_process.md` recorded attrs anchors scanned as `388`.
- `phase1_second_repo_clean_supply_candidate_inventory.json` and its Markdown report recorded anchors scanned as `0`.

Root cause:

- `certify-second-repo` rewrote the second-repo candidate inventory after local
  certification.
- That path did not pass mining anchors into `second_repo_inventory_payload`, so
  the helper replaced mining-stage anchor and first-filter counts with empty
  values.

Repair:

- Added a regression test for preserving prior mining counts during certification inventory rewrites.
- Updated `second_repo_inventory_payload` to preserve prior `anchors_scanned`
  and `first_filter_counts` when certification updates the inventory without
  rerunning mining.
- Updated `certify-second-repo` to read the existing candidate inventory and to
  pass candidates, contexts, certification rows, reviews, and prior mining
  counts into the rebuilt inventory.

Regenerated local artifacts without paid calls:

- `mine-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`
- `certify-second-repo --config experiments/phase1_compiler/configs/phase1_second_repo_clean_outcome_unseen_supply.yaml --repo-id attrs`

Post-repair counts:

- anchors scanned: `388`
- selected candidate rows: `48`
- source context rows: `48`
- local certification attempts: `48`
- local certification status counts: `certified=21`, `near_certified=27`
- promoted clean attrs candidates: `18`

No paid ACUT or paid LLM calls were made in Step 1.
