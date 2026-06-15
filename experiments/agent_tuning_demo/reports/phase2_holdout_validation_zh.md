# Agent Tuning Phase 2 holdout validation

生成日期：2026-06-15T02:42:19+00:00

- Paid cells: `12`
- Estimated cost: `$0.6142311`
- Paired net wins: `0`
- Non-regressing gate: `True`

| Condition | Pass | Scoreable | Invalid | Cost | Median latency |
| --- | --- | --- | --- | --- | --- |
| baseline | 5 | 6 | 0 | 0.3224709 | 32.081 |
| tuned | 5 | 6 | 0 | 0.2917602 | 34.701 |

## Pair matrix

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__clean_ext__017 | verified_pass | True | verified_pass | True |
| boltons__hist__019 | verified_fail | False | verified_fail | False |
| boltons__hist__020 | verified_pass | True | verified_pass | True |
| boltons__hist__022 | verified_pass | True | verified_pass | True |
| boltons__hist__023 | verified_pass | True | verified_pass | True |
| boltons__hist__024 | verified_pass | True | verified_pass | True |
