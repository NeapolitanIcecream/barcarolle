# Codex Kilo Workspace Stability Analysis

The repaired matrix repeat completed on 2026-05-21 with result prefix
`codex_kilo_workspace_stability`.

## Stability Result

- Scheduled cells: `20/20`.
- Scoreable cells: `18/20`.
- Terminal statuses: `verified_pass=7`, `verified_fail=11`,
  `policy_violation=2`.
- Codex scoreable cells: `9/10`.
- Kilo scoreable cells: `9/10`.
- Kilo timeout rows: `0/10`.
- Click test-edit policy violations: `0`.
- Usage observed rate: `1.0`.
- Observed-token cost estimate: `USD 4.70140020`.
- Conservative fallback estimate: `USD 10.00`.
- Provider-billed dollars: `null`.

Step 7A acceptance passes: every scheduled cell has a terminal status,
scoreable cells are `18/20`, Kilo timeout rows remain `0/10`, Click test-edit
policy violations remain `0`, and the stability cost summary uses
observed-token accounting.

## Comparison To Repaired Follow-Up

The previous repaired follow-up had `19/20` scoreable cells with terminal
statuses `verified_pass=7`, `verified_fail=12`, and `policy_violation=1`.
The stability repeat had one fewer scoreable cell because both harnesses edited
an out-of-scope package export path on `toolz__hist__010`.

Changed terminal outcomes:

- Codex `toolz__hist__001`: `verified_pass` to `verified_fail`.
- Codex `toolz__hist__004`: `verified_fail` to `verified_pass`.
- Codex `toolz__hist__010`: `verified_pass` to `policy_violation`.
- Kilo `toolz__hist__004`: `verified_fail` to `verified_pass`.

Stable outcomes:

- `G_mini` Click tasks remained scoreable and all verified fail, which is the
  expected comparator direction for these recovered tasks.
- Kilo completion stayed repaired: no Kilo timeout rows appeared in the repeat.
- Test-edit policy stayed repaired: no Click test-edit policy violations
  appeared in the repeat.

## Scope Interpretation

The two stability policy violations are consistent with
`experiments/phase0_headroom/reports/toolz_hist_010_scope_review.md`.
Package export files remain outside the certified `toolz__hist__010` task
boundary. The repeat therefore strengthens the evidence that this is a
recurring scope-policy behavior, not a Kilo completion failure.

## Decision Impact

The repeat supports continuing Phase 0 as a measured regression-benchmark
compiler. It does not support predictive-validity claims: the evidence is still
one primary target repository, one small recovered Click comparator set, and a
clustered task sample.

The next smallest useful experiment is a small second-repository pilot or
additional certified task diversity before making harness-selection or
predictive claims.
