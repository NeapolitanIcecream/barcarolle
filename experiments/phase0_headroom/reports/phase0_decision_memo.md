# Phase 0 Decision Memo

Decision: `proceed_regression_benchmark`.

## Scope

Phase 0 evaluated whether the restart can compile and score a small target-repository benchmark slice.

- Primary target repository: `toolz`.
- Generic comparator source: archived Click R0 metadata.
- Canonical ledger: `experiments/phase0_headroom/results/cost_ledger.jsonl`.
- Estimated LLM/API spend recorded for Phase 0: `USD 60.00`.
- Exact Codex CLI cost was not observable, so the conservative projected matrix cost remains the recorded estimate.

## Evidence Summary

- Distribution mismatch rows with absolute gap >= `0.15`: `12`.
- Certification candidates attempted: `16`.
- Executable candidates: `16`.
- Source-adapter blocker: resolved. The follow-up found non-leaky issue or pre-solution discussion context for all `6` oracle-valid `toolz` anchors.
- Certified tasks after source-adapter repair: `6`.
- Near-certified tasks after repair: `0`.
- Mini release status: `benchmark_grade_candidate`.
- Release splits: `3` `B_real`, `3` `W_real`, and `4` archived Click `G_mini` comparator records.
- Headroom entry gate: passed with `12` of `12` gates passing.
- Protocol dry run: all `6` same-repo `toolz` tasks were `scoreable_same_protocol`.
- `G_mini` protocol dry run: `not_scoreable_same_protocol`.
- ACUT matrix: one Codex CLI ACUT configuration, `6` paid same-repo task attempts, `6` scoreable cells.
- Same-repo matrix result: `2` verified pass, `4` verified fail, `0` harness or invalid-output cells.

Supporting artifacts:

- `reports/phase0_source_adapter_followup_decision.md`
- `reports/phase0_headroom_matrix_decision.md`
- `results/headroom_entry_gate.json`
- `results/headroom_protocol_dry_run.json`
- `results/headroom_score_table.csv`
- `results/headroom_metrics.json`
- `releases/toolz_phase0_mini_release.json`

## What Phase 0 Supports

Phase 0 supports continuing the restart as a regression-benchmark compiler.

The evidence chain now covers target selection, candidate supply, deterministic mechanical gates, non-leaky solver-facing statements, certified mini-release assembly, protocol dry run, budget-gated ACUT execution, and verified same-repo scoring. The same-repo cells were scoreable rather than dominated by harness failure.

The useful claim is narrow: Barcarolle can produce a small certified `toolz` regression slice and run a same-repo ACUT scoring loop against it under a conservative budget gate.

## What Phase 0 Does Not Support

Phase 0 does not support predictive-validity claims.

The missing comparison is the generic comparator path. The archived Click `G_mini` tasks were not scoreable under the same Phase 0 ACUT invocation and verifier protocol, so Phase 0 did not produce `G_mini -> W_real` or `G_mini + B_real -> W_real` comparisons.

Phase 0 also does not support a final benchmark authority claim. The sample has one target repository, one ACUT configuration, six same-repo scoreable cells, and clustered task provenance.

## Threats To Validity

- One primary target repository: `toolz`.
- Six certified same-repo tasks is enough for a scoreability diagnostic, not a stable predictive estimate.
- Four of the six same-repo tasks come from one `compose` improvement thread.
- `G_mini` uses archived Click metadata and still needs same-protocol task materialization.
- Exact Codex CLI cost was not observable from the local runner.
- MAE, RMSE, Brier score, and residual-style predictive metrics are `not_applicable_underpowered`.

## Next Smallest Useful Experiment

Run `repair_generic_comparator_protocol`.

The next experiment should materialize or adapt the archived Click `G_mini` tasks, or choose another generic comparator, so the same ACUT invocation and scoring protocol can produce comparator cells. Do not spend on a second ACUT until generic comparator scoreability is fixed or explicitly waived.
