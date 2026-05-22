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

## Step 1 Replacement-Repo Support

The Phase 0 repo-history pilot remains generic for replacement repos:

- `stable_task_id("boltons", 1)` returns `boltons__hist__001`
- solver statements use the active candidate repo ID
- commit-message fallback remains diagnostic-only
- deterministic candidate filtering applies independent of repo ID
- PR metadata rows store sanitized summaries, not raw API responses

The Phase 1 hardening tool now reads the active third repo from
`phase1_third_repo_replacement_selection.yaml` when present. Without an active
selection it preserves the historical default of `itsdangerous`; with a selected
replacement it focuses overlays on `toolz`, `humanize`, and the selected repo,
while marking Itsdangerous as replaced evidence.

Regression checks:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_repo_history_pilot.py` -> `16 passed`
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_source_certification_hardening.py` -> `11 passed`

## Step 2 Replacement Configs

Created:

- `experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml`
- `experiments/phase0_headroom/configs/third_repo_replacement_attrs_v1.yaml`
- `experiments/phase1_compiler/configs/phase1_third_repo_replacement_selection.yaml`

Both repo configs point to ignored `external_repos` paths, disable paid calls,
and use local-only claim scope. The Phase 1 selection config is configured with
candidate order `boltons`, `attrs` and active selection `pending`.

Config parser checks loaded both replacement repo configs and the Phase 1
selection config successfully.

## Step 3 Candidate Repo Materialization

`experiments/phase0_headroom/external_repos/boltons` is ignored by
`.gitignore`. The repo was absent, then cloned from
`https://github.com/mahmoud/boltons.git` and fetched with tags/prune.

Boltons local repo state:

- status: `## master...origin/master`
- HEAD: `207651ee6055aabd0d9cdeac2e00140cdc208d44`
- default branch: `origin/master`

The cloned repository remains under the ignored `external_repos` path and is not
tracked by Git.
