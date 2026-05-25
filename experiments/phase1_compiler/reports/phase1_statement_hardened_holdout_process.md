# Phase 1 Statement-Hardened Holdout Process

Generated: `2026-05-25T02:04:56Z`.

## Preflight

- Branch: `codex/restart-benchmark-compiler`.
- HEAD: `ea46ef60375edce0ec8a5840533b69753771c4a9`.
- Python: `Python 3.11.13` via `uv run --project experiments/phase1_compiler python --version`.
- uv: `uv 0.11.16 (Homebrew 2026-05-21 aarch64-apple-darwin)`.
- Paid ACUT calls made: `false`.
- Paid LLM calls made: `false`.
- Raw artifacts committed: `false`.

## Existing Unrelated Working Tree Paths

These paths were present before this preregistration run and were not touched by Step 0:

- `docs/experiments/phase-1-statement-hardened-holdout-preregistration-runbook.md`
- `docs/experiments/phase-1-attrs-generalization-third-repo-decision-runbook.md`
- `docs/experiments/phase-1-attrs-h-future-statement-quality-audit-runbook.md`
- `docs/experiments/phase-1-autonomous-overnight-two-repo-research-runbook.md`
- `docs/experiments/phase-1-policy-violation-triage-bounded-rerun-runbook.md`

## Boundary

The proposal boundary read for this run is narrow: Barcarolle is a target-repository benchmark compiler. Its contribution is selecting, weighting, splitting, calibrating, and quality-controlling a repo-specific benchmark release so it can predict future target-repo work.

Historical paid score tables are immutable inputs. This local run cannot establish predictive validity because it does not run any new paid validation.

## Locked Inputs

- `/Users/chenmohan/Downloads/barcarolle-research-0519.md`: `sha256:19bb010214ff464c905b9441d2bac347c233e46ff498c91cd0d9f1b287ac6f79`
- `experiments/phase1_compiler/results/phase1_attrs_h_future_evidence_status.json`: `sha256:1089b20131f9e93f7c31ee85657dbf69eeb6dd7fe2ad9b3df6aedfae930b4a57`
- `experiments/phase1_compiler/results/phase1_attrs_h_future_task_design_audit.json`: `sha256:6ba20e230146c325ee9e213266e06c8b3f05bbdab05ac86b962c0c94d83d4ca9`
- `experiments/phase1_compiler/results/phase1_attrs_h_future_statement_sensitivity.json`: `sha256:93aa0f1e87025c5ad8a0e228a488e3f9af8e6f3c56fe0022304e586e2d5d5e03`
- `experiments/phase1_compiler/results/phase1_attrs_h_future_statement_preview.json`: `sha256:d9fcafde5de7bac30fd14b3b6c646ee93287653856cdd2e7ba0ba40c43649344`
- `experiments/phase1_compiler/results/phase1_two_repo_task_outcome_matrix.json`: `sha256:3b07105d919d97ecc24be3230a89a602fde1bae39393ee3fe4be41de2eb80bc7`
- `experiments/phase0_headroom/tools/statement_quality.py`: `sha256:3c0f6443897a25c731abb83964e24087a12affcb47e52fa3a4657a52ab680694`

## Step Status

- Step 0 preflight and evidence lock: completed.
- Step 1 durable preregistration tooling: completed.
- Step 2 candidate inventory: completed.
- Step 3 candidate screen: completed.
- Step 4 release previews: completed.
- Step 5 manifest or blocker: completed with blocker.
- Step 6 preregistration: completed with no-preregistration report because no manifest was frozen.
- Step 7 validation branch decision: completed.
- Step 8 closeout: completed.

## Commits Created

- `8a359599` Record statement-hardened preregistration preflight
- `0a30426c` Add statement-hardened preregistration tooling
- `74eb08c4` Build statement-hardened candidate inventory
- `979b8c63` Screen statement-hardened holdout supply
- `8706ea03` Render statement-hardened release previews
- `6510c9aa` Record statement-hardened release blocker
- `a5bd9a6d` Write statement-hardened preregistration
- `e64ad023` Decide statement-hardened validation branch
- Record statement-hardened preregistration closeout, in the closeout commit that writes this final process report.

## Tests And Checks

- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_statement_hardened_preregistration.py`: passed, `7 passed`.
- `uv run --project experiments/phase1_compiler pytest -q experiments/phase1_compiler/tests/test_phase1_attrs_statement_quality_audit.py experiments/phase1_compiler/tests/test_phase1_clean_outcome_unseen_supply_mining.py experiments/phase0_headroom/tools/test_workspace_acut_run.py`: passed, `42 passed`.
- `git diff --check`: passed before each commit and before the closeout commit.

## Final Decision

- Paid calls made: `false`.
- Raw artifacts committed: `false`.
- Release frozen: `false`.
- Preregistration written: `false`.
- No-preregistration report written: `true`.
- Primary decision: `replacement_supply_needed_before_paid_validation`.
- Paid validation blocked: `true`.
- Next runbook path: `docs/experiments/phase-1-statement-hardened-replacement-supply-runbook.md`.

The local screen found only `4` eligible candidates without using paid outcomes: `2` attrs B_eval-eligible tasks and `2` boltons B_eval-eligible tasks. It found `0` eligible H_future tasks for both repos under the strict statement-quality gate. The required two-repo release shape therefore cannot be frozen locally.
