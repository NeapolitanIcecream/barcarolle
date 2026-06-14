# Selector Decision Wrapper v2 Eval

生成日期：2026-06-14

## Rule

v2 现在是 user-facing ranking wrapper：Selection pass-rate 排名先行；top Agent 明确领先时推荐；多个 Agent 落在 tie epsilon 内时输出 top tier；只有 common-valid support 不足、缺 outcome row 或基础设施失败导致无法比较时才输出 insufficient data。paired wins/losses 和 bootstrap LCB 保留为证据字段，不再作为推荐 veto。

## Selected thresholds

- Action margin: `0.05`。
- Min common valid: `8`。
- LCB tolerance: `0.0`。
- Tie epsilon: `0.05`。

## Development score

- Formula: `validated_recommendation_rate - 2.0*false_recommendation_rate - mean_recommendation_regret + 0.05*correct_abstain_rate`。
- Wrapper score: `0.719048`。
- Recommendation coverage: `0.875`。
- Validated recommendation rate: `0.833333`。
- False-recommendation rate: `0.047619`。
- Mean recommendation regret: `0.019048`。

## Top threshold rows

| Rank | Margin | Min common | LCB tol | Tie eps | Score | Validated | Coverage | False | Regret |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 1 | 0.05 | 8 | 0.0 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |
| 2 | 0.05 | 8 | 0.05 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |
| 3 | 0.05 | 8 | 0.1 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |
| 4 | 0.1 | 8 | 0.0 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |
| 5 | 0.1 | 8 | 0.05 | 0.05 | 0.719048 | 0.833333 | 0.875 | 0.047619 | 0.019048 |

## Boundary

Threshold search excluded final source `phase1_original_three_repo_split_heldout_final_candidate`. MAE remains auxiliary; this search optimizes demo decision quality first.
