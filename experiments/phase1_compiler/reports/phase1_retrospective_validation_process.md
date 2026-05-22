# Phase 1 Retrospective Validation And Clean Supply Process

Status: complete.

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

## Step 3 Retrospective Locked Validation

Ran:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_retrospective_validation.py plan --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_retrospective_validation.py score --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Plan result:

- evidence level: `outcome_seen_retrospective_locked`
- included repos: `boltons`, `toolz`
- included task count: `13`
- included row count: `26`
- clean future holdout: `false`
- predictive validity established: `false`

Included task ids:

- `boltons__hist__007`
- `boltons__hist__017`
- `boltons__hist__019`
- `boltons__hist__020`
- `boltons__hist__024`
- `boltons__hist__026`
- `boltons__hist__031`
- `toolz__hist__001`
- `toolz__hist__002`
- `toolz__hist__003`
- `toolz__hist__004`
- `toolz__hist__010`
- `toolz__hist__016`

Metrics result:

- pooled MAE: `0.541667`
- scoreable cells: `24`
- policy violations: `1`
- Boltons Codex B->W absolute error: `0.25`
- Boltons Kilo B->W absolute error: `0.25`
- Toolz Codex B->W absolute error: `0.666667`
- Toolz Kilo B->W absolute error: `1.0`

This is outcome-seen retrospective evidence only. No clean future-holdout or
predictive-validity claim is made.

## Step 4 Clean Supply Candidate Review

Ran:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_retrospective_validation.py review-clean-supply --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Review result:

- clean supply extension ready: `false`
- promoted clean task ids: `boltons__hist__011`, `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- promoted B_real tasks: `boltons__hist__011`
- promoted W_real tasks: `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- kept manual-review-required: `boltons__hist__014`

Candidate decisions:

| Task | Split | Outcome seen | Decision | Reason |
| --- | --- | --- | --- | --- |
| `boltons__hist__011` | `B_real` | `false` | `promote_to_clean_benchmark_candidate` | non-leaky PR context, aligned oracle, clear enough behavioral scope |
| `boltons__hist__014` | `B_real` | `false` | `keep_manual_review_required` | `scope_context_project_heavy_or_ambiguous` |
| `boltons__hist__022` | `W_real` | `false` | `promote_to_clean_benchmark_candidate` | non-leaky PR context, aligned oracle, clear enough behavioral scope |
| `boltons__hist__023` | `W_real` | `false` | `promote_to_clean_benchmark_candidate` | non-leaky PR context, aligned oracle, clear behavioral scope |
| `boltons__hist__027` | `W_real` | `false` | `promote_to_clean_benchmark_candidate` | non-leaky PR context, aligned oracle, clear enough behavioral scope |

The minimum clean split requires at least two B_eval and two H_future tasks.
Only one B_real task was promoted, so Steps 5 through 7 are skipped and no paid
clean validation runs in this runbook.

## Step 8 Decision

Ran:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_retrospective_validation.py decide --config experiments/phase1_compiler/configs/phase1_retrospective_validation_and_clean_supply.yaml
```

Decision:

- primary label: `retrospective_validation_complete_clean_supply_still_blocked`
- retrospective evidence level: `outcome_seen_retrospective_locked`
- included retrospective repos: `boltons`, `toolz`
- retrospective pooled MAE: `0.541667`
- clean supply extension ready: `false`
- promoted clean task ids: `boltons__hist__011`, `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- optional paid clean validation ran: `false`
- policy violations in retrospective rows: `1`
- predictive validity established: `false`
- production ranking status: `not_produced`
- recommended next runbook: `mine_additional_clean_outcome_unseen_supply`

## Step 9 Phase 1 Boundary Refresh

Updated the Phase 1 closeout boundary so
`phase1_retrospective_validation_decision.json` is imported as retrospective
sidecar evidence.

Rebuilt and validated:

```bash
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py build-mvp --config experiments/phase1_compiler/configs/phase1_mvp.yaml
uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml
```

Validation returned `status=valid`.

Closeout state:

- predictive validity established: `false`
- production ranking status: `not_produced`
- strict future holdout sidecar evidence: `future_holdout_supply_blocked`
- retrospective validation sidecar evidence: `retrospective_validation_complete_clean_supply_still_blocked`
- retrospective evidence level: `outcome_seen_retrospective_locked`
- next runbook recommendation: `mine_additional_clean_outcome_unseen_supply`

## Step 10 Final Verification

Final verification passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.70s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `41 passed in 0.29s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`
- `git status --short` -> clean

Artifact hygiene:

- `git ls-files` for raw, workspace, external repo, venv, and cache paths returned no tracked files.

No push was performed.
