# Phase 1 Boltons Paid ACUT Smoke Process

Status: complete.

Generated: 2026-05-22T06:24:22Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `074c7b3a4e3bd9fd0a8a2d5341586d171c4e5f8f`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed by this runbook: `true`
- Direct paid LLM calls allowed: `false`
- Required endpoint env after sourcing `~/.zshrc`: present

Replacement readiness matched the runbook:

- decision: `ready_for_paid_third_repo_acut_smoke_runbook`
- selected repo: `boltons`
- ready for paid smoke: `true`
- hardened benchmark candidates: `7`

Selected hardened task IDs confirmed:

- `boltons__hist__007`
- `boltons__hist__017`
- `boltons__hist__019`
- `boltons__hist__020`
- `boltons__hist__024`
- `boltons__hist__026`
- `boltons__hist__031`

Current cost reconciliation before paid smoke:

- observed-or-conservative estimated cost: `31.026435`
- usage observed rate: `0.945`
- total stop cap: `60.00`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.74s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `27 passed in 0.30s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

The runbook's raw, workspace, external repo, venv, and cache paths are not
tracked by Git.

No paid calls have been made yet in this runbook.

## Step 1 Smoke Config

Created `experiments/phase1_compiler/configs/phase1_boltons_paid_acut_smoke.yaml`.

Config properties:

- selected repo: `boltons`
- smoke prefix: `phase1_validation_boltons_paid_smoke`
- extension prefix: `phase1_validation_boltons_paid_extension`
- paid ACUT calls: `enabled_small_smoke`
- direct paid LLM calls: disabled except ACUT harness internals
- required endpoint env: `LLM_BASE_URL`, `LLM_API_KEY`
- local subscription fallback: disabled
- OpenAI/provider fallback: disabled
- paid ACUT concurrency: `1`
- smoke tasks: `boltons__hist__007`, `boltons__hist__017`, `boltons__hist__024`, `boltons__hist__026`
- extension tasks: `boltons__hist__019`, `boltons__hist__020`, `boltons__hist__031`
- predictive validity established: `false`

## Step 2 Adapter Preflight

Ran adapter preflight for both workspace ACUT harnesses.

Codex preflight:

- status: `ready`
- adapter: `codex_workspace`
- endpoint proof: `codex_eligible`
- required env present: `true`
- local subscription fallback: `disabled`
- OpenAI/provider fallback: `disabled`
- blockers: `[]`

Kilo preflight:

- status: `ready`
- adapter: `kilo_workspace`
- endpoint proof: `kilo_eligible`
- required env present: `true`
- local subscription fallback: `disabled`
- OpenAI/provider fallback: `disabled`
- blockers: `[]`

No paid task-solving cells have run yet.

## Step 3 Paid Canary

Ran the canary task `boltons__hist__007` sequentially for both adapters under
the `phase1_validation_boltons_paid_smoke` prefix.

Paid cells run in this step: `2`.

Canary result:

- total cells: `2`
- scoreable cells: `2`
- terminal statuses: `verified_pass=2`
- Codex scoreable cells: `1/1`
- Kilo scoreable cells: `1/1`
- policy violations: `0`
- cost per scoreable cell: `0.50`

Usage/cost after canary:

- call count: `111`
- usage observed count: `105`
- usage observed rate: `0.9459`
- observed-or-conservative estimated cost: `32.1847776`

The canary met acceptance criteria and cost remained below the `60.00` stop cap.

## Step 4 Balanced Paid Smoke

Ran the full balanced smoke task set sequentially for both adapters under the
`phase1_validation_boltons_paid_smoke` prefix.

Paid cells in the balanced smoke prefix: `8`.

Smoke result:

- total cells: `8`
- scoreable cells: `7`
- terminal statuses: `verified_pass=7`, `invalid_output=1`
- policy violations: `0`
- B_real scoreable cells: `4/4`
- W_real scoreable cells: `3/4`
- Codex scoreable cells: `4/4`
- Kilo scoreable cells: `3/4`

Usage/cost after balanced smoke:

- call count: `117`
- usage observed count: `110`
- usage observed rate: `0.9402`
- observed-or-conservative estimated cost: `34.7027108`

The balanced smoke met acceptance criteria and cost remained below the `60.00`
stop cap.

## Step 5 Optional Hardened-Task Extension

Ran the optional extension task set sequentially for both adapters under the
`phase1_validation_boltons_paid_extension` prefix.

Paid cells in the extension prefix: `6`.

Extension result:

- total cells: `6`
- scoreable cells: `6`
- terminal statuses: `verified_pass=4`, `verified_fail=2`
- policy violations: `0`
- Codex scoreable cells: `3/3`
- Kilo scoreable cells: `3/3`

Combined smoke plus extension result:

- total cells: `14`
- scoreable cells: `13`
- policy violations: `0`

Usage/cost after extension:

- call count: `123`
- usage observed count: `116`
- usage observed rate: `0.9431`
- observed-or-conservative estimated cost: `37.6472432`
- incremental observed-or-conservative cost since preflight: `6.6208082`

The extension met acceptance criteria and cost remained below the `60.00` stop
cap.

## Step 6 Phase 1 Boundary Import

Imported the Boltons paid smoke and extension score tables into the Phase 1 MVP
scorecard as operational sidecar evidence:

- `phase1_validation_boltons_paid_smoke`: `8` rows, `7` scoreable, `0` policy violations.
- `phase1_validation_boltons_paid_extension`: `6` rows, `6` scoreable, `0` policy violations.

Updated the compiler so optional Boltons score tables are imported only when
configured. The Phase 1 compiler validation returned `status=valid`, predictive
validity stayed `false`, and production ranking stayed `not_produced`.

## Step 7 Final Smoke Decision

Wrote the final decision artifacts:

- `experiments/phase1_compiler/results/phase1_boltons_paid_acut_smoke_decision.json`
- `experiments/phase1_compiler/reports/phase1_boltons_paid_acut_smoke_decision.md`

Decision label:

- `boltons_paid_smoke_complete_ready_for_phase1_validation_design`

Recommended next runbook:

- `write_phase1_validation_design_and_future_holdout_runbook`

## Step 8 Final Verification

Final verification passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.85s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `28 passed in 0.34s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Final artifact hygiene:

- `git status --short --ignored` showed only ignored `.pytest_cache`, `.venv`, `external_repos`, `results/raw`, `tools/__pycache__`, and `workspaces` paths under the scoped experiment directories.
- `git ls-files` for raw, workspace, external repo, venv, and cache paths returned no tracked files.

No push was performed.
