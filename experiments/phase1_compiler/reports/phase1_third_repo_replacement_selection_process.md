# Phase 1 Third Repo Replacement Selection Process

Status: in progress.

Generated: 2026-05-22T05:51:50Z.

No paid LLM calls were made. No paid ACUT calls were made.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `7e97c7264de7bd5c3703663da56af7fe17e78ebb`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Candidate order: `boltons`, then `attrs`

Previous replacement trigger matched the runbook:

- repair/remine decision: `replace_third_repo_before_paid_acut`
- recommended next runbook: `select_replacement_third_repo_and_locally_certify_without_paid_acut`
- previous Itsdangerous hardened benchmark candidates: `0`
- predictive validity: `false`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `67 passed in 1.76s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `22 passed in 0.33s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

The runbook's raw, workspace, external repo, venv, and cache paths are not
tracked by Git.
