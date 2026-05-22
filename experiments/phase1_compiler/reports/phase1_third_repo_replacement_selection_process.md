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

## Step 4 Candidate Supply Screen

Ran mining for `boltons` with
`experiments/phase0_headroom/configs/third_repo_replacement_boltons_v1.yaml`.

Boltons supply screen:

- candidate count after filter: `32`
- candidates with both code and tests: `32`
- candidates missing code or tests: `0`
- maximum selected changed-line count: `235`
- subject-level maintenance/project-churn hits: `0`
- manual-review candidates: `6`

`boltons` exceeds the strong-candidate threshold, so `attrs` was not cloned or
screened. Wrote the candidate screen JSON and report.

## Step 5 Source Context

`gh auth status` showed an authenticated GitHub CLI session. Source-context
generation used sanitized PR metadata and stored no raw API responses.

Boltons source-context yield:

- statements: `32`
- reviewed non-leaky PR-context statements: `22`
- context-missing statements: `10`
- reviewed statements with `commit:` refs: `0`
- source context rows: `32`
- PR rows: `22`
- commit fallback rows: `10`

All generated statements use `Repair the boltons behavior`; none contain stale
`humanize` or `itsdangerous` behavior text. Source yield is above the strong
threshold, so no linked-issue adapter extension was needed.

## Step 6 Local Certification

Removed the ignored workspace path
`experiments/phase0_headroom/workspaces/repo_history_pilot/boltons`, then ran
local certification for `boltons`.

Boltons certification result:

- certified tasks: `16`
- near/rejected tasks: `16`
- first failing gates: `ambiguity_review=8`, `reference_pass=5`,
  `no_op_fail=3`
- commit-fallback-only benchmark-grade tasks: `0`

The repo exceeds both the minimum paid-smoke certification threshold (`4`) and
the preferred benchmark-candidate threshold (`6`). Reference failures did not
dominate, so no bounded environment variant was needed.

## Step 7 Replacement Release Assembly

Assembled and summarized the boltons release.

Release result:

- release status: `pilot_grade`
- pilot grade: `true`
- benchmark grade: `true`
- certified tasks: `16`
- B_real tasks: `8`
- W_real tasks: `8`
- claim scope: `third_repo_replacement_local_screen_not_predictive_validation`

The certified task and release artifacts contain no stale `humanize` or
`itsdangerous` behavior statements.

## Step 8 Active Replacement Selection

Selected `boltons` as the active Phase 1 third repo replacement:

- active repo: `boltons`
- selection status: `selected_local_pilot`
- source release: `experiments/phase0_headroom/releases/boltons_phase0_pilot_release.json`
- replacement for: `itsdangerous`

`attrs` remains unscreened because `boltons` passed supply, source, local
certification, and release gates. Itsdangerous artifacts remain available as
historical/replaced evidence.

## Step 9 Hardening Overlay Refresh

Reran Phase 1 hardening overlays with `boltons` as the active third repo.

Selected repo hardening summary:

- active third repo: `boltons`
- source rows: `32`
- benchmark-grade source rows: `17`
- local certified rows: `16`
- oracle aligned rows: `11`
- hardened benchmark-grade candidates: `7`
- hardened manual-review tasks: `5`
- hardened diagnostic-only tasks: `10`
- hardened rejected tasks: `10`

The active hardening summaries now cover `toolz`, `humanize`, and `boltons`.
`itsdangerous` is no longer counted as the active third repo and is recorded as
replaced by `boltons` in the hardening decision.

Hardening decision:

- primary decision: `ready_for_paid_third_repo_acut_smoke_runbook`
- recommended next runbook: `run_small_paid_third_repo_acut_smoke_with_selected_replacement_repo`
- predictive validity: `false`
