# Phase 1 Attrs Generalization Process

Generated: `2026-05-23T11:19:25Z`.

## Step 0 Preflight

This runbook is local-only. It does not permit paid ACUT calls, paid LLM calls,
rerunning `attrs__hist__027`, or rerunning any existing scoreable cell.

Repository state was recorded at branch `codex/restart-benchmark-compiler`,
HEAD `aef2dfa69c20f776267327df3caf123be88bb7ff`. `uv` is available as
`uv 0.11.16`; `python` is not on `PATH`, but `uv run --project
experiments/phase1_compiler python --version` reports `Python 3.11.13`.

Existing untracked paths were recorded and not committed as part of this step:

- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

Current decisions were confirmed without changing conclusions:

- Two-repo future holdout remains `two_repo_paid_validation_complete_insufficient_evidence`.
- The confirmed policy violation remains `attrs__hist__027` / `kilo_workspace`.
- Predictive validity remains `false`.
- Production ranking remains `not_produced`.
- The stale advice to repair/rerun the policy violation has already been
  superseded by the policy-violation repair decision recommending attrs
  generalization analysis or local third-repo mining without rerunning the
  confirmed violation.

Proposal alignment: the next work must support benchmark compiler predictive
validity, uncertainty, or clean evidence boundaries. It must not optimize for
task-count yield, leaderboard ranking, or ACUT harness behavior.

Baseline checks passed:

- `uv run --project experiments/phase1_compiler pytest -q`: `71 passed`.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `75 passed`.
- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml`: `valid`.
- `git diff --check`: passed.
