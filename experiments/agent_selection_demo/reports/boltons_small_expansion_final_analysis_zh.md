# Boltons small expansion final analysis

生成时间：`2026-06-15T14:31:46+00:00`。

- Selection tasks: `30`；later-check tasks: `20`。
- Final displayed cells: `200`；new paid cells: `88`；reused committed cells: `112`。
- Selection recommendation: `kilo_gpt_5_4`。
- Later-check top Agent: `kilo_claude_sonnet_4_6`。
- Selection/later top agreement: `不一致`。
- Recommendation regret on later-check: `0.094737`。

## Final Selection vs later-check matrix

| Agent | Selection | Selection cells | Later | Later cells | Later-Selection |
| --- | --- | --- | --- | --- | --- |
| Codex + GPT mainline | 0.366667 | 11/30 | 0.75 | 15/20 | 0.383333 |
| Kilo + GPT mainline | 0.666667 | 20/30 | 0.8 | 16/20 | 0.133333 |
| Kilo + GPT low-cost | 0.448276 | 13/29 | 0.736842 | 14/19 | 0.288566 |
| Kilo + Claude Sonnet | 0.517241 | 15/29 | 0.894737 | 17/19 | 0.377495 |

## Replacement rule

原始 Holdout 中 top-2 Agent 的 doubled-timeout rows 在 active matrix 中替换旧 rows；非 top-2 Agent 和从旧 Selection 迁入 later-check 的任务继续使用已提交的 scoreable rows。Phase 1 v2 旧 low-cost rows 因 Agent ID / active policy 不完全一致，未作为四-Agent demo rows 复用。

## Interpretation

这是 presentation-oriented boltons demo expansion。它支持在更大的时间有序 Selection/later-check matrix 上做一次可审计 Agent 选型，并检查该推荐在后续任务上的表现；不支持跨仓库、全局 Agent 排名或 predictive-validity proof。
