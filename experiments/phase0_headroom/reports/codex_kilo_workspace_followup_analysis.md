# Codex Kilo Workspace Follow-Up Analysis

The Kilo completion and policy follow-up completed on 2026-05-21. It repaired
the two main validity blockers from the completed Codex/Kilo matrix while
keeping the workspace ACUT boundary intact.

## Summary

Previous Codex/Kilo matrix:

- Scoreable cells: `9/20`.
- Kilo scoreable cells: `3/10`.
- Kilo ACUT harness errors: `6`.
- Policy violations: `5`, including `3` test-edit violations.

Follow-up repaired matrix:

- Scoreable cells: `19/20`.
- Codex scoreable cells: `10/10`.
- Kilo scoreable cells: `9/10`.
- Kilo timeout rows: `0/10`.
- Terminal statuses: `verified_pass=7`, `verified_fail=12`,
  `policy_violation=1`.
- Policy violations: `1`, and it was not a test edit.
- `G_mini` scoreable cells: `8/8`.
- Estimated follow-up spend: `USD 14.50` across probe, smoke, and repaired
  matrix cells.

## Kilo Completion

Kilo completion is operationally repaired for this Phase 0 protocol. The local
diagnosis found that all six previous Kilo `acut_harness_error` rows had
non-empty diffs and adapter timeouts, rather than endpoint failure. The
`strict-final` wrapper prompt then produced:

- completion probe: `3/3` non-timeout and scoreable;
- policy smoke: `3/3` Kilo non-timeout and scoreable;
- repaired matrix: `0/10` Kilo timeout rows, `9/10` scoreable.

This does not prove that every Kilo task will exit under all prompts, but it
does repair the observed non-interactive failure mode enough for the current
benchmark protocol.

## Statement Policy

Statement-policy rendering is repaired. Solver-visible statements now separate
editable implementation paths from non-editable paths. Test/regression-coverage
scope lines are rendered as verifier-only non-editable notes, and the benchmark
policy still rejects tests and out-of-scope edits.

Evidence:

- Phase 0 tools tests cover Click editable paths, Click test-path
  non-editability, Toolz scope preservation, and test-edit rejection.
- Policy smoke had `0/4` Click test-edit policy violations.
- Repaired matrix had `0` test-edit policy violations.

The only repaired-matrix policy violation was Kilo editing out-of-scope Toolz
export files for `toolz__hist__010`: `toolz/__init__.py` and
`toolz/curried/__init__.py`.

## Phase 1

Phase 1 artifacts were refreshed from
`experiments/phase0_headroom/results/codex_kilo_workspace_followup_score_table.csv`.
The weighted score summary identifies both ACUTs, imports `20` cells, treats
`19` as compatible, leaves the policy violation incompatible, and preserves
overall `insufficient_evidence`.

No predictive-validity claim is introduced.

## Decision

The follow-up supports continuing as a stronger regression-benchmark compiler.
It does not yet support `proceed_predictive`: the sample is still small, the
task set is clustered, and the Click `G_mini` cells are useful comparator cells
rather than evidence of cross-repo predictive validity.

Recommended decision remains:

```text
proceed_regression_benchmark
```

## Next Smallest Useful Experiment

Keep the repaired protocol and run a stability-focused next step before any
larger predictive claim:

- preserve Kilo `strict-final` as the default Kilo workspace ACUT mode;
- add a small policy refinement or package-export allowance review for
  `toolz__hist__010`;
- run a second repaired matrix repeat or a second target-repository pilot to
  measure run-to-run stability and reduce task clustering.
