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

## Step 1 Outcome Matrix

Built a sanitized cell-level matrix from the four two-repo score tables and
joined safe task metadata from certification artifacts where available.

Acceptance checks passed:

- Planned cells: `32`.
- Scoreable cells: `31`.
- Policy violations: `1`.
- The single policy violation is still `attrs__hist__027` / `kilo_workspace`.
- The policy violation remains non-scoreable and is not counted as a verified fail.
- Frozen design task ids match the preregistered task ids.
- No raw verifier logs, raw patches, prompts, completions, or ACUT transcripts
  are included.

## Step 2 Attrs H_future Failure Taxonomy

Analyzed attrs H_future failures against attrs B_eval, boltons B_eval, and
boltons H_future using the sanitized matrix only.

Observed result:

- Attrs H_future scoreable pass rate: `1/7`.
- Verified fails: `6`.
- Policy violations: `1`.
- `attrs__hist__012` and `attrs__hist__013` failed on both scoreable adapters.
- `attrs__hist__023` passed on one adapter and failed on one adapter.
- `attrs__hist__027` had one scoreable fail and one non-scoreable policy
  violation.

Interpretation:

- The collapse is broad across attrs H_future tasks, not tied to one task.
- Both adapters contributed scoreable failures; Codex was worse on attrs
  H_future.
- The confirmed policy violation is a real benchmark boundary failure for one
  cell, but it does not explain the six verified fails.
- A task-family or time-window shift is plausible but not proven from the safe
  metadata.
- No paid calls were made or recommended inside this runbook step.

## Step 3 Uncertainty And Baselines

Computed Wilson 95% intervals and baseline prediction errors from scoreable
cells only.

Key results:

- Pooled B_eval pass rate: `14/16 = 0.875000`, Wilson interval
  `[0.639772, 0.965023]`.
- Pooled H_future pass rate: `8/15 = 0.533333`, Wilson interval
  `[0.301170, 0.751905]`.
- Attrs H_future pass rate: `1/7 = 0.142857`, Wilson interval
  `[0.025680, 0.513128]`.
- Pooled B_eval to pooled H_future absolute error: `0.341667`.
- Repo-specific B_eval to same-repo H_future MAE: `0.366071`.
- Adapter-specific B_eval to same-adapter H_future MAE: `0.330357`.
- Unweighted all-B_eval predictor to H_future repo/adapter MAE: `0.416667`.
- Preserved preregistered pooled MAE: `0.479167`.

Conclusion: the pilot is both negative and underpowered. The point estimates do
not support predictive validity, while the two-repo sample and 15 scoreable
H_future cells leave wide uncertainty intervals.

## Step 4 Next Research Decision

Selected primary decision label:
`report_two_repo_negative_or_underpowered_pilot`.

Rationale:

- The confirmed policy violation is genuine and remains non-scoreable.
- Attrs H_future collapse remains broad after excluding the non-scoreable cell.
- The uncertainty analysis shows the pilot is both negative and underpowered.
- Third-repo local supply could be useful later, but it would not become
  predictive-validation evidence without future scoreable holdout cells.
- Weighted analysis could be a follow-up, but current safe metadata does not
  isolate a strong enough weighting explanation to supersede reporting the
  two-repo result now.

No paid calls were made. The decision does not recommend rerunning the
confirmed policy violation inside this runbook.
