# Selector Decision Wrapper v2 Eval

生成日期：2026-06-14

## Rule

v2 推荐规则：Selection top margin 达到 action margin；common valid tasks 达到下限；paired wins 大于 paired losses；bootstrap LCB 不低于 `-lcb_tolerance`。它不再要求 `losses == 0`。

## Selected thresholds

- Action margin: `0.1`。
- Min common valid: `8`。
- LCB tolerance: `0.1`。
- Tie epsilon: `0.05`。

## Development score

- Formula: `validated_recommendation_rate - 2.0*false_recommendation_rate - mean_recommendation_regret + 0.05*correct_abstain_rate`。
- Wrapper score: `0.758333`。
- Recommendation coverage: `0.708333`。
- Validated recommendation rate: `0.708333`。
- False-recommendation rate: `0.0`。
- Mean recommendation regret: `0.0`。

## Top threshold rows

| Rank | Margin | Min common | LCB tol | Tie eps | Score | Validated | Coverage | False | Regret |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.1 | 8 | 0.1 | 0.05 | 0.758333 | 0.708333 | 0.708333 | 0.0 | 0.0 |
| 2 | 0.1 | 8 | 0.1 | 0.1 | 0.758333 | 0.708333 | 0.708333 | 0.0 | 0.0 |
| 3 | 0.05 | 8 | 0.1 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |
| 4 | 0.1 | 8 | 0.0 | 0.05 | 0.716667 | 0.666667 | 0.666667 | 0.0 | 0.0 |
| 5 | 0.1 | 8 | 0.0 | 0.1 | 0.716667 | 0.666667 | 0.666667 | 0.0 | 0.0 |

## Boundary

Threshold search excluded final source `phase1_original_three_repo_split_heldout_final_candidate`. MAE remains auxiliary; this search optimizes demo decision quality first.
