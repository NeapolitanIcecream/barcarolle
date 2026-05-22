# Phase 1 Preregistered Clean Future-Holdout Tooling Check

Status: passed.

Generated: 2026-05-22T11:04:30Z.

## Loader Behavior

- Clean-overlay task ids selectable by `--task-id`: `true`
- Frozen package count: `8`
- Missing task ids: `none`
- Evidence level recorded for selected packages: `clean_supply_overlay_sidecar`
- Canonical Boltons release unchanged: `true`
- Canonical hardening overlay unchanged: `true`
- Paid ACUT calls made: `false`

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

The workspace runner now loads the clean-supply overlay from the explicit
sidecar paths in
`experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml`.
It constructs `TaskPackage` rows with benchmark-side metadata for task time,
base commit, target commit, changed files, test files, sanitized context,
allowed public context refs, original hardening status, and promotion rationale.

Solver-visible statements for clean-ext tasks are built from sanitized public
problem context, allowed context refs, editable implementation paths, and test
command metadata. A non-paid statement check found no target commit or
`diff --git` leakage across the 8 selected packages.

## Validation

- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools/test_workspace_acut_run.py` -> `18 passed in 1.74s`
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_future_holdout.py` -> `9 passed in 0.01s`
- `git diff --check` -> passed
- Diff for canonical release, canonical certified tasks, and hardening overlay -> empty

## Changed Files

- `experiments/phase0_headroom/configs/phase1_preregistered_clean_future_holdout_workspace_matrix.yaml`
- `experiments/phase0_headroom/reports/phase1_future_holdout_package_inspection_package_inspection.md`
- `experiments/phase0_headroom/results/phase1_future_holdout_package_inspection_package_inspection.json`
- `experiments/phase0_headroom/tools/test_workspace_acut_run.py`
- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- `experiments/phase1_compiler/configs/phase1_preregistered_clean_future_holdout_paid_validation.yaml`
- `experiments/phase1_compiler/reports/phase1_preregistered_clean_future_holdout_tooling_check.md`
- `experiments/phase1_compiler/results/phase1_preregistered_clean_future_holdout_tooling_check.json`
