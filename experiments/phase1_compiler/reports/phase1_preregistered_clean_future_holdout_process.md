# Phase 1 Preregistered Clean Future-Holdout Paid Validation Process

Status: in progress.

Generated: 2026-05-22T10:56:23Z.

## Step 0 Preflight And State Record

Preflight passed without paid ACUT calls.

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `276980a1048b46c878b2ccb31bdd94ec34b16b88`
- Required endpoint env after sourcing `~/.zshrc`: present
- Clean supply decision: `boltons_clean_supply_ready_for_preregistered_validation`
- Preregistration status: `frozen`
- Selected repo: `boltons`
- Existing future-holdout paid calls: `false`
- Existing `B_eval` scoreable cells: `0`
- Existing `H_future` scoreable cells: `0`
- Predictive validity established: `false`

Baseline checks:

- `git diff --check` -> passed
- `uv run --project experiments/phase1_compiler pytest -q` -> `56 passed in 0.31s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Starting worktree state was not clean because the runbook file itself was
untracked:

```text
?? docs/experiments/phase-1-preregistered-clean-future-holdout-paid-validation-runbook.md
```

No conflicting existing changes were found.

## Step 1 Clean-Overlay Workspace Task Loading

Tooling support passed without paid ACUT calls.

Added run configs:

- `experiments/phase1_compiler/configs/phase1_preregistered_clean_future_holdout_paid_validation.yaml`
- `experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml`

Updated workspace ACUT tooling:

- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- `experiments/phase0_headroom/tools/test_workspace_acut_run.py`

Sanitized diagnostic artifacts:

- `experiments/phase0_headroom/results/phase1_future_holdout_package_inspection_package_inspection.json`
- `experiments/phase0_headroom/reports/phase1_future_holdout_package_inspection_package_inspection.md`
- `experiments/phase1_compiler/results/phase1_preregistered_clean_future_holdout_tooling_check.json`
- `experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_tooling_check.md`

Package inspection:

- status: `ready`
- package count: `8`
- missing task ids: `none`
- evidence level: `clean_supply_overlay_sidecar`
- paid ACUT calls made: `false`

Selected task ids:

```text
boltons__clean_ext__001
boltons__clean_ext__008
boltons__clean_ext__010
boltons__hist__011
boltons__clean_ext__017
boltons__hist__022
boltons__hist__023
boltons__hist__027
```

Canonical Boltons release, canonical Boltons certified tasks, and the hardening
overlay were not modified.

Validation:

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_workspace_acut_run.py` -> `18 passed in 1.74s`
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_future_holdout.py` -> `9 passed in 0.01s`
- `git diff --check` -> passed

## Step 2 Local Dry-Run And Paid Entry Gate

Paid entry gate passed without paid ACUT calls.

Adapter preflights:

| Prefix | Adapter | Endpoint proof | Required env | Status |
| --- | --- | --- | --- | --- |
| `phase1_future_holdout_b_eval_codex_preflight` | `codex_workspace` | `codex_eligible` | `true` | `ready` |
| `phase1_future_holdout_b_eval_kilo_preflight` | `kilo_workspace` | `kilo_eligible` | `true` | `ready` |
| `phase1_future_holdout_h_future_codex_preflight` | `codex_workspace` | `codex_eligible` | `true` | `ready` |
| `phase1_future_holdout_h_future_kilo_preflight` | `kilo_workspace` | `kilo_eligible` | `true` | `ready` |

Non-paid split inspections matched the frozen preregistration:

- `B_eval`: `boltons__clean_ext__001`, `boltons__clean_ext__008`, `boltons__clean_ext__010`, `boltons__hist__011`
- `H_future`: `boltons__clean_ext__017`, `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`

Existing prefix summaries:

- `phase1_future_holdout_b_eval_score_table.csv`: header-only, `0` data rows
- `phase1_future_holdout_h_future_score_table.csv`: header-only, `0` data rows

Cost gate:

- projected cells: `16`
- conservative per-cell estimate: `USD 0.50`
- projected incremental spend: `USD 8.00`
- current observed-or-conservative cumulative spend: `USD 37.6472432`
- projected cumulative after preferred batch: `USD 45.6472432`
- total stop cap: `USD 80.00`
- paid parallelism: disabled

Next step may run the paid `B_eval` batch sequentially.

## Step 3 Paid B_eval Batch

Paid `B_eval` batch complete.

Scheduled cells:

- Codex adapter: `4`
- Kilo adapter: `4`
- Total: `8`

Terminal status counts:

- `verified_pass`: `7`
- `verified_fail`: `1`

Scoreability and policy:

- scoreable cells: `8/8`
- non-scoreable cells: `0`
- policy violations: `0`
- solver hidden/oracle filename scan: no matches under solver workspaces

Per-adapter results:

- `codex_workspace`: `4/4` scoreable, `4` verified pass
- `kilo_workspace`: `4/4` scoreable, `3` verified pass, `1` verified fail

Usage and cost:

- prefix usage observed rate: `1.0000`
- prefix observed-or-conservative cost: `USD 4.4760882`
- cumulative workspace usage observed rate: `0.9466`
- cumulative observed-or-conservative cost: `USD 42.1233314`
- cumulative stop cap: `USD 80.00`

The `H_future` batch may proceed.

## Step 4 Paid H_future Batch

Paid `H_future` batch complete.

Scheduled cells:

- Codex adapter: `4`
- Kilo adapter: `4`
- Total: `8`

Terminal status counts:

- `verified_pass`: `7`
- `verified_fail`: `1`

Scoreability and policy:

- scoreable cells: `8/8`
- non-scoreable cells: `0`
- policy violations: `0`
- solver hidden/oracle filename scan: no matches under solver workspaces

Per-adapter results:

- `codex_workspace`: `4/4` scoreable, `3` verified pass, `1` verified fail
- `kilo_workspace`: `4/4` scoreable, `4` verified pass

Usage and cost:

- prefix usage observed rate: `1.0000`
- prefix observed-or-conservative cost: `USD 4.8642324`
- cumulative workspace usage observed rate: `0.9496`
- cumulative observed-or-conservative cost: `USD 46.9875638`
- cumulative stop cap: `USD 80.00`

The paid Boltons clean future-holdout pilot has complete score tables for both
splits and may proceed to metrics and decision import.

## Step 5 Metrics And Decision

Future-holdout scoring and Phase 1 MVP boundary import passed.

Prediction metrics:

- `B_eval` cells: `8`
- `B_eval` scoreable cells: `8`
- `B_eval` pass rate: `0.875`
- `H_future` cells: `8`
- `H_future` scoreable cells: `8`
- `H_future` pass rate: `0.875`
- absolute error per adapter: `codex_workspace=0.25`, `kilo_workspace=0.25`
- MAE: `0.25`
- policy violations: `0`

Decision:

- primary label: `boltons_clean_future_holdout_pilot_complete_insufficient_sample`
- paid ACUT calls made: `true`
- selected repos: `boltons`
- `B_eval` scoreable cells: `8`
- `H_future` scoreable cells: `8`
- policy violations: `0`
- incremental observed-or-conservative cost: `USD 9.3403206`
- cumulative observed-or-conservative cost: `USD 46.9875638`
- predictive validity established: `false`
- blockers: `predictive_validity_min_target_repos_not_met`, `predictive_validity_min_holdout_scoreable_cells_not_met`
- recommended next runbook: `mine_second_repo_clean_outcome_unseen_supply_for_two_repo_validation`

MVP closeout was rebuilt and validated with the paid future-holdout sidecar
evidence. The closeout recommendation now follows the paid future-holdout
decision.

Validation:

- `uv run --project experiments/phase1_compiler pytest -q` -> `57 passed in 0.37s`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `74 passed in 2.21s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`
- `git diff --check` -> passed
