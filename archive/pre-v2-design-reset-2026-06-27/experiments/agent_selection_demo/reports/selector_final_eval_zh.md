# HRD 70/30 Agent Selection Demo Final Eval

生成日期：2026-06-14

## Selection recommendation

- Selector: `HRD v3 70/30` (`k=10`)。
- Decision state: `recommend`。
- Recommended Agent: `kilo_gpt_5_4`。
- Reason: `top_agent_pass_rate_advantage`。
- Guidance: 建议选择排名第一的 Agent；依据是 Selection 通过率领先，paired 和 bootstrap 指标只作为证据，不作为否决项。

## Agent ranking

| Rank | Agent | Selection | Rate | Gap |
| --- | --- | --- | --- | --- |
| 1 | kilo_gpt_5_4 | 9/10 | 0.9 | 0.0 |
| 2 | codex_gpt_5_4 | 7/10 | 0.7 | 0.2 |
| 3 | kilo_claude_sonnet_4_6 | 7/10 | 0.7 | 0.2 |
| 4 | kilo_gpt_5_4_mini | 7/10 | 0.7 | 0.2 |

## Evidence table

| Agent | Selection | Rate | Gap | Common | Top-Agent Pair Margin | W/L/T |
| --- | --- | --- | --- | --- | --- | --- |
| kilo_gpt_5_4 | 9/10 | 0.9 | 0.0 |  |  |  |
| codex_gpt_5_4 | 7/10 | 0.7 | 0.2 | 10 | 0.2 | 2/0/8 |
| kilo_claude_sonnet_4_6 | 7/10 | 0.7 | 0.2 | 10 | 0.2 | 2/0/8 |
| kilo_gpt_5_4_mini | 7/10 | 0.7 | 0.2 | 10 | 0.2 | 2/0/8 |

## Holdout validation

- Holdout later top: `kilo_gpt_5_4`。
- Recommendation regret: `0.0`。
- Doubled-timeout top-2 repeat top: `kilo_gpt_5_4`。
- Preferred demo terminal state achieved: `True`。
- New paid cells: `0`；new paid cost: `$0.0`。

## Selection and later pass rates

- Selection: `codex_gpt_5_4: 7/10, kilo_claude_sonnet_4_6: 7/10, kilo_gpt_5_4: 9/10, kilo_gpt_5_4_mini: 7/10`。
- Holdout: `codex_gpt_5_4: 5/10, kilo_claude_sonnet_4_6: 8/10, kilo_gpt_5_4: 9/10, kilo_gpt_5_4_mini: 6/10`。
- Doubled-timeout top-2 repeat: `codex_gpt_5_4: 6/10, kilo_gpt_5_4: 9/10`。

## Strong random comparison

- Selector MAE: `0.1`。
- Stratified random k=10 MAE mean: `0.1517`。
- Absolute improvement: `0.0517`。
- Relative improvement: `0.340804`。
- Selector beats/ties stratified-random MAE share: `1.0`。

MAE and random-baseline comparisons are auxiliary evidence for this demo report. They are not treated as the sole success gate.

## Paid boundary

No-paid final slice has complete selected-task Selection cells, complete Holdout cells for all four Agents, and complete doubled-timeout top-2 repeat cells.

## Supported claim

On the frozen boltons demo slice, the preregistered HRD 70/30 selector recommends Kilo + GPT mainline; original Holdout and doubled-timeout top-2 repeat both favor Kilo, with zero recommendation regret on the reported later slices.

## Unsupported claims

- full predictive validity
- strict selector superiority over the strongest same-budget random baseline
- cross-repository selector superiority
- global Agent or model-family ranking
