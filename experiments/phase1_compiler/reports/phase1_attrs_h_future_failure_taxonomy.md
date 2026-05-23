# Phase 1 Attrs H_future Failure Taxonomy

Generated: `2026-05-23T11:27:56+00:00`.

## Observed Outcomes

- Attrs H_future scoreable pass rate: `1/7` = `0.142857`.
- Attrs H_future verified fails: `6`.
- Attrs H_future policy violations: `1`.
- Failed on both scoreable adapters: `attrs__hist__012, attrs__hist__013`.
- Passed on one adapter and failed on one adapter: `attrs__hist__023`.
- Policy violation task: `attrs__hist__027`.

## Concentration Checks

| Check | Result |
|---|---|
| `by_module_or_package` | _funcs: 0/1 pass, 1 policy, _make: 1/4 pass, 0 policy, _next_gen: 0/2 pass, 0 policy |
| `by_task_type` | runtime_behavior_with_docs_and_tests: 0/5 pass, 1 policy, runtime_behavior_with_tests: 1/2 pass, 0 policy |
| `by_source_context_kind` | problem_context: 1/7 pass, 1 policy |
| `by_source_context_ref_kind` | issue: 1/5 pass, 1 policy, pull_request: 0/2 pass, 0 policy |
| `by_changed_file_count` | 2: 1/2 pass, 0 policy, 3: 0/2 pass, 0 policy, 4: 0/2 pass, 0 policy, 5: 0/1 pass, 1 policy |
| `by_test_file_count` | 1: 1/7 pass, 1 policy |
| `by_adapter` | codex_workspace: 0/4 pass, 0 policy, kilo_workspace: 1/3 pass, 1 policy |
| `by_time_window` | 2020-09: 0/4 pass, 0 policy, 2021-02: 1/2 pass, 0 policy, 2021-03: 0/1 pass, 1 policy |
| `by_scope_clarity` | pass: 1/7 pass, 1 policy |
| `by_policy_boundary` | policy_violation: 0/0 pass, 1 policy, scoreable_outcome: 1/7 pass, 0 policy |

## Interpretation

- Breadth: attrs H_future failure is broad, not tied to one task.
- Adapter pattern: both adapters have scoreable failures; Codex is worse on attrs H_future.
- Benchmark scope: the `attrs__hist__027` / `kilo_workspace` policy violation is real, but it is only one non-scoreable cell and does not explain the six verified fails.
- Task-family shift: plausible but not proven from the safe metadata. Change size, test count, source context status, and scope clarity do not isolate a single obvious stratum.
- Spending implication: this taxonomy supports more local analysis before any paid validation decision.

## Claim Boundary

This report does not claim root cause, pure harness effect, repaired policy violation, predictive validity, or production ranking.
