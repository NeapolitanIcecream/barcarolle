# Statement-Hardened Paid Validation Process

Status: `complete`.

## Steps Completed

- Step 0 preflight and approval record: complete.
- Step 1 statement-hardened workspace loading: complete.
- Step 2 local entry gate: complete.
- Step 3 attrs B_eval paid batch: complete.
- Step 4 attrs H_future paid batch: complete.
- Step 5 boltons B_eval paid batch: complete.
- Step 6 boltons H_future paid batch: complete.
- Step 7 paid metrics and decision: complete.
- Step 8 closeout: complete.

## Commits Created

- `2a7ee526` Record statement-hardened paid validation preflight.
- `ede1d078` Support statement-hardened packages in workspace validation.
- `4836605c` Record statement-hardened paid entry gate.
- `4b89e8b3` Run statement-hardened attrs B_eval batch.
- `829b3f08` Run statement-hardened attrs H_future batch.
- `4ae18ad6` Run statement-hardened boltons B_eval batch.
- `451029da` Run statement-hardened boltons H_future batch.
- `9c003562` Compute statement-hardened paid metrics and decision.
- `bb4953d6` Align PR body summary test with sanitizer limit.

## Verification

- `git diff --check`: passed.
- `uv run --project experiments/phase1_compiler pytest -q`: passed, 142 tests.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: passed, 75 tests.

## Paid Cell Summary

- Paid ACUT calls made: `true`.
- Planned paid cells: `32`.
- Completed paid cells: `32`.
- Scoreable paid cells: `32`.
- Terminal status counts: `verified_pass=21`, `verified_fail=11`.
- Policy violation count: `0`.
- Timeout count: `0`.
- Harness error count: `0`.
- Invalid output count: `0`.

## Repo Splits

- `attrs/B_eval`: paid cells `8`, scoreable cells `8`, pass rate `0.75`.
- `attrs/H_future`: paid cells `8`, scoreable cells `8`, pass rate `0.5`.
- `boltons/B_eval`: paid cells `8`, scoreable cells `8`, pass rate `0.875`.
- `boltons/H_future`: paid cells `8`, scoreable cells `8`, pass rate `0.5`.

## Cost

- Usage observed for new cells: `32/32`.
- Observed-or-conservative spend for this run: `$9.9235152`.
- Conservative fallback for missing usage in this run: `$0.00`.
- Adapter costs: `codex_workspace=$5.7123912`, `kilo_workspace=$4.211124`.

## Decision

- Primary decision: `statement_hardened_paid_validation_complete_threshold_not_met`.
- Predictive validity established: `false`.
- Evidence: all paid cells completed, scoreability gate met, policy violations are zero, cost is bounded, but no preregistered quantitative predictive-validity success threshold beyond scoreability, policy, and cost gates is recorded.
- Observed B_eval to H_future gaps: `attrs=0.25`, `boltons=0.375`.
- Recommended next action: use this paid run as bounded evidence and have the coordinating session decide any follow-up runbook.

## Hygiene

- Raw artifacts committed: `false`.
- Raw solver/verifier workspaces committed: `false`.
- Raw prompts, completions, transcripts, target diffs, and raw logs committed: `false`.
- Old paid result repaired: `false`.
- `attrs__hist__027` old policy violation repaired: `false`.
- Generated statement treated as scoreable result: `false`.
- Follow-up runbook written by worker: `false`.
