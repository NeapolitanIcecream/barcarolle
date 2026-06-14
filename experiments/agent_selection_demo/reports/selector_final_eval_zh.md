# Selector Final Eval

生成日期：2026-06-14

## Final result

- Preferred terminal state achieved: `True`。
- Decision state: `recommend`。
- Recommended Agent: `kilo_gpt_5_4`。
- Holdout later top: `kilo_gpt_5_4`。
- Recommendation regret: `0.0`。
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

## Paid boundary

No-paid final slice has complete selected-task Selection cells, complete Holdout cells for all four Agents, and complete doubled-timeout top-2 repeat cells.

## Claim

On the frozen boltons demo slice, the preregistered HRD 70/30 selector recommends Kilo + GPT mainline; original Holdout and doubled-timeout top-2 repeat both favor Kilo, with zero recommendation regret on the reported later slices.
