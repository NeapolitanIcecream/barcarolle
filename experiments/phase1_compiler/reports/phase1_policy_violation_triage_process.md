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
