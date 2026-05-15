# Repository-Local Rich-W20 Primary Results

Generated at: 2026-05-15 18:55 CST

## Scope

This report covers the frozen reduced-scale repository-local decision-validity pilot for Rich-W20. It does not revise the 2026-05-14 terminal boundary and does not support claims about full benchmark generation robustness.

## Completion

- Normalized results: 160 / 160
- W_star axis: 80 / 80, primary-score ready
- R axis: 80 / 80, primary-score ready
- Rerun or exclusion cells: 0
- Triage-paused cells: 0

The primary run is complete under the reduced protocol.

## Scores

| Slot | ACUT | R pass / 20 | R score | W_star pass / 20 | W_star score |
| --- | --- | ---: | ---: | ---: | ---: |
| A0 | `cheap-generic-swe` | 5 | 25.0% | 8 | 40.0% |
| A1 | `cheap-rich-inert-control-v1` | 2 | 10.0% | 9 | 45.0% |
| A3 | `cheap-rich-c-calibrated-v1` | 3 | 15.0% | 6 | 30.0% |
| A4 | `cheap-rich-localization-tool-v1` | 2 | 10.0% | 8 | 40.0% |

R selected A0. W_star best was A1. The selection regret was 1 W_star task.

## Success Criteria

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| A4 vs A0 on W_star | at least +4 tasks | 0 | fail |
| R-selected vs A0 on W_star | at least +3 tasks | 0 | fail |
| R-selected within W_star best | within 1 or 2 tasks | 1 | pass |
| Inert control guard | A1 not selected unless W_star supports it | A0 selected | pass |

The frozen success criteria were not met.

## Status Distribution

| Split | verified_pass | verified_fail | unsafe_or_scope_violation |
| --- | ---: | ---: | ---: |
| R | 12 | 66 | 2 |
| W_star | 31 | 40 | 9 |

## Interpretation

The reduced Rich-W20 primary completed cleanly after the network-related R012/A4 cell was rerun. The result does not show the intended A4 advantage over A0 on W_star. R selected the generic baseline A0, while the W_star best slot was the inert control A1. Although the R-selected slot was within one task of the W_star best, the main improvement thresholds failed.

Artifacts:

- Summary: `experiments/core_narrative/results/repository_local_rich_w20_v1/summary.json`
- Analysis JSON: `experiments/core_narrative/results/repository_local_rich_w20_v1/analysis.json`
