# Agent Tuning Phase 2 selection_dev validation

生成日期：2026-06-15T02:33:26+00:00

- Paid cells: `8`
- Estimated cost: `$0.7125438`
- Paired net wins: `0`
- Non-regressing gate: `True`

| Condition | Pass | Scoreable | Invalid | Cost | Median latency |
| --- | --- | --- | --- | --- | --- |
| baseline | 1 | 4 | 0 | 0.23297655 | 65.2 |
| tuned | 1 | 4 | 0 | 0.47956725 | 72.246 |

## Pair matrix

| Task | Baseline | Baseline pass | Tuned | Tuned pass |
| --- | --- | --- | --- | --- |
| boltons__supply_expansion_20260526__001 | verified_fail | False | verified_fail | False |
| boltons__supply_expansion_20260526__004 | verified_fail | False | verified_fail | False |
| boltons__supply_expansion_20260526__006 | verified_pass | True | verified_pass | True |
| boltons__supply_expansion_20260526__107 | verified_fail | False | verified_fail | False |
