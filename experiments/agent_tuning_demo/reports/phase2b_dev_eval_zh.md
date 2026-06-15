# Agent Tuning Phase 2b dev evaluation

Generated at: `2026-06-15T03:37:45+00:00`.

- Paid cells: `18`
- Estimated cost: `$0.8974602`
- Future gate decision: `stop_dev_gate_not_positive`
- Chosen artifact hash: `None`

## Candidate results

| Candidate | Pass | Scoreable | Invalid | Net wins | Cost ratio | Gate |
| --- | --- | --- | --- | --- | --- | --- |
| tuned_candidate_1 | 4 | 6 | 0 | 0 | 1.0843 | False |
| tuned_candidate_2 | 4 | 6 | 0 | 0 | 0.9211 | False |

## Pair matrix: tuned_candidate_1

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__clean_ext__001 | verified_pass | True | verified_pass | True |
| boltons__clean_ext__008 | verified_pass | True | verified_pass | True |
| boltons__clean_ext__010 | verified_pass | True | verified_pass | True |
| boltons__hist__006 | verified_fail | False | verified_fail | False |
| boltons__hist__007 | verified_pass | True | verified_pass | True |
| boltons__supply_expansion_20260526__107 | verified_fail | False | verified_fail | False |

## Pair matrix: tuned_candidate_2

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__clean_ext__001 | verified_pass | True | verified_pass | True |
| boltons__clean_ext__008 | verified_pass | True | verified_pass | True |
| boltons__clean_ext__010 | verified_pass | True | verified_pass | True |
| boltons__hist__006 | verified_fail | False | verified_fail | False |
| boltons__hist__007 | verified_pass | True | verified_pass | True |
| boltons__supply_expansion_20260526__107 | verified_fail | False | verified_fail | False |
