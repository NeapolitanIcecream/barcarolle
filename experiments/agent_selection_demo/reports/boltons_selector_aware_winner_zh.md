# Boltons selector-aware winner

生成时间：`2026-06-16T03:16:06+00:00`。

- Winning selector: `hrd_v3_70_30`。
- Budget: `k=10`。
- Latest origin: `origin_40` (`40` history tasks, future starts `2021-05-15T00:08:53-07:00`)。
- Decision state: `recommend`。
- Forced recommended Agent: `kilo_claude_sonnet_4_6`。
- Future top Agent: `kilo_claude_sonnet_4_6`。
- Recommendation regret: `0.0`。
- MAE: `0.225`。

## Latest-origin selected Selection vs Future

| Agent | Selection | Future | Ranks |
| --- | --- | --- | --- |
| Kilo + Claude Sonnet | 9/10 (0.9) | 9/10 (0.9) | 1 -> 1 |
| Kilo + GPT mainline | 7/10 (0.7) | 9/10 (0.9) | 2 -> 2 |
| Kilo + GPT low-cost | 6/10 (0.6) | 8/10 (0.8) | 3 -> 4 |
| Codex + GPT mainline | 3/10 (0.3) | 8/10 (0.8) | 4 -> 3 |

## Selected task IDs

`boltons__hist__013, boltons__supply_expansion_20260526__001, boltons__supply_expansion_20260526__093, boltons__supply_expansion_20260526__095, boltons__v2__128, boltons__v2__141, boltons__v2__142, boltons__v2__144, boltons__v2__169, boltons__v2__170`

该 winner 不使用固定 40-task history pass rate；Selection 是 selector 在前 40 个历史任务中选出的预算内 task IDs。
