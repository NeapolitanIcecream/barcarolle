# Phase 1 Policy Violation Triage Process

Status: Step 0 preflight recorded.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `ad5e20e325c5917f0ea01e53068a0b58d6c2873d`.
- Existing untracked paths before this runbook:
  - `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
  - `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`
- Versions: Python `3.9.6`, `uv 0.11.16`, `codex-cli 0.133.0`, `kilo 7.3.1`.
- Current decision is `two_repo_paid_validation_complete_insufficient_evidence`.
- Current blocker is exactly one policy violation: `attrs__hist__027` / `kilo_workspace` in `H_future`.
- Score row records `policy_violation`, `scoreable_cell=False`, `harness_error=True`.
- Submission changed paths are `conftest.py` and `src/attr/_make.py`.
- Verifier detail records `submission_edited_out_of_scope_paths` with violating path `src/attr/_make.py`.
- The package inspection artifact for the attrs H_future Kilo batch is `ready`, includes the blocker task, and made no paid ACUT calls.
- No paid calls were made in this preflight.

Baseline checks:

- `git diff --check`: passed.
- `uv run --project experiments/phase1_compiler pytest -q`: 69 passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: 75 passed.
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`: valid.

Next step: confirm and repair the policy-violation detail reporting join if the metrics artifact still drops verifier details.

## Step 1 Reporting Repair

- Confirmed the reporting bug in `phase1_future_holdout.py`: policy violation rows were joined to verifier detail with the loop split label `h_future`, while verifier rows use the score split label `H_future`.
- Added a focused regression test for preserving `submission_edited_out_of_scope_paths` and `["src/attr/_make.py"]`.
- Recomputed two-repo metrics and decision from the frozen prefixes.
- Policy violation count remains `1`.
- The metrics artifact now preserves the verifier harness error and changed path detail.
- No paid calls were made.

Checks:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_future_holdout.py`: 15 passed.
- `uv run --project experiments/phase1_compiler pytest -q`: 70 passed.
- `git diff --check`: passed.

## Step 2 Triage Facts

- Created `phase1_policy_violation_triage_bounded_rerun.yaml`.
- Created sanitized triage JSON and Markdown artifacts.
- Raw patch content and ACUT transcripts were not copied into committed artifacts.
- The factual triage records `src/attr/_make.py` as outside the current package metadata, certified changed files, and target-commit changed files.
- Classification remains deferred to Step 3.

## Step 3 Classification

- Classification: `confirmed_acut_policy_violation_no_rerun`.
- The violating path `src/attr/_make.py` is not supported by certified changed files, allowed code paths, target-commit changed files, candidate code files, or the sanitized solver-visible source context.
- The benchmark-side bug found so far is reporting-only and has already been repaired.
- Scope metadata is not classified as wrong.
- Deterministic replay is not allowed under this classification.
- Paid rerun is not allowed under this classification.
- Predictive validity remains unclaimable while the policy violation count is `1`.

## Step 4A Close Without Rerun

- Recomputed two-repo metrics and decision from the original frozen prefixes.
- Rebuilt and validated the Phase 1 MVP closeout.
- Recorded the repair decision as `confirmed_policy_violation_validation_remains_insufficient`.
- Added the repair decision as a closeout sidecar so the final closeout does not recommend rerunning the same confirmed policy violation.
- Policy violation count remains `1`.
- H_future scoreable cells remain `15`.
- Predictive validity remains `false`.
- Production ranking remains `not_produced`.
- No deterministic replay was performed.
- No paid rerun was performed.

Checks:

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_compiler.py`: 19 passed.
- `uv run --project experiments/phase1_compiler pytest -q`: 71 passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: 75 passed.
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`: valid.
- `git diff --check`: passed.

## Step 8 Final Closeout

Terminal state: `confirmed_policy_violation_validation_remains_insufficient`.

The single attrs H_future policy violation is a genuine ACUT boundary violation, not a benchmark task-scope metadata bug. The benchmark-side reporting bug was repaired so verifier detail is preserved in the two-repo metrics. No deterministic replay or paid rerun was performed.

Final metrics:

- Policy violation count: `1`.
- H_future scoreable cells: `15`.
- Predictive validity established: `false`.
- Production ranking: `not_produced`.

Next recommendation: analyze attrs H_future generalization and decide whether to report the two-repo result as negative or underpowered, or mine a third repo. Do not rerun the same confirmed policy-violation cell.
