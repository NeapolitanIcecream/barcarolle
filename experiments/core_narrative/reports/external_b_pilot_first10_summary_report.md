# External Calibrated B10 Pilot Summary

- Scope: first 10 B task ordinals across A0-A5, 60 cells total.
- Modified plan: E stopped at 30 task ordinals, B stopped at 10 task ordinals, checkpoint then pause.
- Original full E spread gate was not satisfied; B10 was run under the user-modified pilot override.
- Privacy: raw base commits, reference patches, hidden verifier inputs, candidate patches, verifier outputs, and private paths are not recorded publicly.

## Aggregate

- Cells scored: 60/60
- Resolved: 14/60 (0.233333)
- External verifier infra errors: 0
- Status counts: {'verified_fail': 46, 'verified_pass': 14}

## By ACUT Slot

| Slot | ACUT | Cells | Resolved | Rate | Infra errors | Status counts |
| --- | --- | ---: | ---: | ---: | ---: | --- |
| A0 | external-sympy-a0-gpt54-medium-concise | 10 | 2 | 0.2 | 0 | {'verified_fail': 8, 'verified_pass': 2} |
| A1 | external-sympy-a1-gpt54-low-concise | 10 | 3 | 0.3 | 0 | {'verified_fail': 7, 'verified_pass': 3} |
| A2 | external-sympy-a2-gpt54-high-concise | 10 | 3 | 0.3 | 0 | {'verified_fail': 7, 'verified_pass': 3} |
| A3 | external-sympy-a3-gpt55-high-concise | 10 | 2 | 0.2 | 0 | {'verified_fail': 8, 'verified_pass': 2} |
| A4 | external-sympy-a4-gpt54mini-high-concise | 10 | 2 | 0.2 | 0 | {'verified_fail': 8, 'verified_pass': 2} |
| A5 | external-sympy-a5-gpt54-high-rich-agents | 10 | 2 | 0.2 | 0 | {'verified_fail': 8, 'verified_pass': 2} |

## Task Rows

| Ordinal | Task | Candidate | A0 | A1 | A2 | A3 | A4 | A5 |
| ---: | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| 1 | sympy__b__001 | sympy_b_anchor_001 | 0 | 0 | 0 | 0 | 0 | 0 |
| 2 | sympy__b__003 | sympy_b_anchor_003 | 0 | 0 | 0 | 0 | 0 | 0 |
| 3 | sympy__b__004 | sympy_b_anchor_004 | 1 | 1 | 1 | 1 | 1 | 1 |
| 4 | sympy__b__005 | sympy_b_anchor_005 | 0 | 0 | 0 | 0 | 0 | 0 |
| 5 | sympy__b__006 | sympy_b_anchor_006 | 1 | 1 | 1 | 1 | 1 | 1 |
| 6 | sympy__b__007 | sympy_b_anchor_007 | 0 | 0 | 0 | 0 | 0 | 0 |
| 7 | sympy__b__008 | sympy_b_anchor_008 | 0 | 0 | 0 | 0 | 0 | 0 |
| 8 | sympy__b__010 | sympy_b_anchor_010 | 0 | 0 | 0 | 0 | 0 | 0 |
| 9 | sympy__b__012 | sympy_b_anchor_012 | 0 | 0 | 0 | 0 | 0 | 0 |
| 10 | sympy__b__014 | sympy_b_anchor_014 | 0 | 1 | 1 | 0 | 0 | 0 |

JSON artifact: `experiments/core_narrative/results/external_b_pilot/external_calibrated_b_pilot_first10_summary_20260516.json`
