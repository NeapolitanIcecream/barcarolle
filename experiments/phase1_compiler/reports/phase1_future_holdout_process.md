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

## Step 2 Clean-Supply And Cutoff Tooling

Added deterministic future-holdout tooling:

- `experiments/phase1_compiler/tools/phase1_future_holdout.py`
- `experiments/phase1_compiler/tests/test_phase1_future_holdout.py`

Implemented commands:

- `audit-supply`
- `design-cutoff`
- `preregister`
- `score`

Tooling behavior covered by tests:

- repo-time sorting with aware timestamps
- embargo calculation between `T_compile_end` and `T_holdout_start`
- exclusion of tasks with previous ACUT outcomes
- exclusion of Humanize validation-grade use while it remains diagnostic-only
- fallback from preferred to minimum counts
- blocker output when clean supply is insufficient
- unknown model snapshot permits repo-time holdout only and blocks contamination-proof claims

Verification:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_future_holdout.py` -> `7 passed in 0.01s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `35 passed in 0.30s`

No paid calls have been made in this step.

## Step 3 Clean Supply Audit

Ran:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_future_holdout.py audit-supply --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Result:

- selected repos: none
- clean supply ready: `false`
- blockers: `no_repo_has_minimum_clean_outcome_unseen_supply`

Repo summary:

| Repo | Certified | Benchmark-grade | Previous ACUT outcome seen | Clean outcome-unseen |
| --- | ---: | ---: | ---: | ---: |
| `boltons` | 16 | 7 | 7 | 0 |
| `toolz` | 6 | 6 | 6 | 0 |

The current benchmark-grade Boltons and Toolz tasks are not clean future-holdout
tasks because they already have workspace ACUT outcomes. No paid validation
cells are allowed on this branch.

## Step 4 Cutoff Plan

Ran `design-cutoff` to record a deterministic blocked cutoff plan.

Cutoff result:

- selected repos: none
- model snapshot status: `unknown`
- repo-time holdout not contamination-proof: `true`
- `boltons`: blocked by `insufficient_clean_outcome_unseen_supply`
- `toolz`: blocked by `insufficient_clean_outcome_unseen_supply`

Because no repo has minimum clean outcome-unseen supply, Steps 5 through 8 are
skipped and the runbook proceeds directly to Step 9 without paid validation.

## Step 9 Score And Decide

Ran:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_future_holdout.py score --config experiments/phase1_compiler/configs/phase1_future_holdout_validation.yaml
```

Decision:

- primary label: `future_holdout_supply_blocked`
- paid ACUT calls made: `false`
- selected repos: none
- `B_eval` task ids: none
- `H_future` task ids: none
- `B_eval` scoreable cells: `0`
- `H_future` scoreable cells: `0`
- policy violations: `0`
- observed-or-conservative estimated cost: `37.6472432`
- incremental observed-or-conservative cost in this runbook: `0.0`
- predictive validity established: `false`
- production ranking: `not_produced`
- recommended next runbook: `mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout`

## Step 10 Phase 1 Boundary Refresh

Updated the Phase 1 closeout boundary so
`phase1_future_holdout_decision.json` is imported as sidecar evidence.

Rebuilt and validated:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py build-mvp --config experiments/phase1_compiler/configs/phase1_mvp.yaml
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Validation returned `status=valid`.

Closeout state:

- predictive validity established: `false`
- production ranking status: `not_produced`
- paid smoke sidecar evidence: `available_as_operational_smoke_evidence`
- future holdout sidecar evidence: `available_as_future_holdout_sidecar_evidence`
- next runbook recommendation: `mine_and_certify_fresh_outcome_unseen_tasks_for_future_holdout`
