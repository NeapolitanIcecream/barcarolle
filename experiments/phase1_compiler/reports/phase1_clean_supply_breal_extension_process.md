# Phase 1 Clean Supply B_real Extension Process

Status: in progress.

Generated: 2026-05-22T08:40:23Z.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`
- Starting HEAD: `23cb0e04e9461c448d5dfb47ba64bc1970ea8e91`
- Python: `Python 3.9.6`
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`
- Paid ACUT calls allowed: `false`
- Direct paid LLM calls allowed: `false`
- Required missing split: `B_real`
- Predictive validity established: `false`

Current blocker matched the runbook:

- retrospective decision: `retrospective_validation_complete_clean_supply_still_blocked`
- recommended next runbook: `mine_additional_clean_outcome_unseen_supply`
- current promoted `B_real`: `boltons__hist__011`
- current promoted `W_real`: `boltons__hist__022`, `boltons__hist__023`, `boltons__hist__027`
- minimum clean split: `B_real >= 2`, `W_real >= 2`

Baseline checks passed:

- `git diff --check`
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` -> `69 passed in 1.66s`
- `uv run --project experiments/phase1_compiler pytest -q` -> `41 passed in 0.27s`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

Raw, workspace, external repo, venv, and cache paths are not tracked by Git.

No paid calls have been made in this runbook.

## Step 1 Config

Created `experiments/phase1_compiler/configs/phase1_clean_supply_breal_extension.yaml`.

Config properties:

- claim scope: `clean_supply_extension_not_predictive_validation`
- predictive validity established: `false`
- paid ACUT calls: disabled
- paid LLM calls: disabled
- target repo: `boltons`
- missing split: `B_real`
- minimum clean split: `B_real >= 2`, `W_real >= 2`
- first candidate: `boltons__hist__014`
- current candidate blocker: `scope_context_project_heavy_or_ambiguous`
- output mode: overlay evidence, not canonical release mutation

## Step 2 Tooling And Tests

Implemented `experiments/phase1_compiler/tools/phase1_clean_supply_breal_extension.py`
and added focused tests in
`experiments/phase1_compiler/tests/test_phase1_clean_supply_breal_extension.py`.

Local test result:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_clean_supply_breal_extension.py` -> `6 passed`

## Step 3 Candidate Audit

Generated:

- `experiments/phase1_compiler/results/phase1_clean_supply_breal_candidate_audit.json`
- `experiments/phase1_compiler/reports/phase1_clean_supply_breal_candidate_audit.md`

Audit result:

- existing promoted clean supply remains `B_real=1`, `W_real=3`
- `boltons__hist__014` remains manual review required
- `boltons__hist__006` and `boltons__hist__013` remain rejected for clean holdout because of `solution_exposure_risk`
- no outcome-seen task is recommended for promotion

## Step 4 Boltons 014 Review

Generated:

- `experiments/phase1_compiler/results/phase1_clean_supply_boltons_014_review.json`
- `experiments/phase1_compiler/reports/phase1_clean_supply_boltons_014_review.md`

Decision:

- promotion decision: `keep_manual_review_required`
- blocker: `scope_context_project_heavy_or_ambiguous`
- sanitized public context summary: `Tox GH Action`
- public body summary available: `false`

The behavior-level task would require inferring from patch/tests rather than
from non-leaky public problem context, so it was not promoted.

## Step 5 Extension Mining

Generated extension namespace artifacts:

- `experiments/phase0_headroom/candidate_sources/boltons_clean_supply_breal_extension_candidates.jsonl`
- `experiments/phase0_headroom/certified_tasks/boltons_clean_supply_breal_extension_reviews.jsonl`
- `experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_mining.json`
- `experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_mining.md`

Result:

- evaluated `boltons__hist__006` and `boltons__hist__013`
- promoted extension tasks: `0`
- both rows remain rejected for `solution_exposure_risk`

## Step 6 Overlay And Decision

Generated:

- `experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_overlay.json`
- `experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_overlay.md`
- `experiments/phase1_compiler/results/phase1_clean_supply_breal_extension_decision.json`
- `experiments/phase1_compiler/reports/phase1_clean_supply_breal_extension_decision.md`

Decision:

- primary decision: `clean_supply_breal_extension_still_blocked`
- recommended next runbook: `continue_mining_clean_outcome_unseen_supply`
- clean supply ready: `false`
- newly promoted tasks: `0`
- predictive validity established: `false`

## Step 7 Phase 1 Compiler Boundary

Updated `phase1_mvp_closeout` to import the clean-supply B_real extension
decision as sidecar evidence only.

Validation result:

- `uv run --project experiments/phase1_compiler pytest -q` -> `47 passed`
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` -> `status=valid`

No paid calls have been made in this runbook.
