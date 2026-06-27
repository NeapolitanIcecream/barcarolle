# Boltons small expansion paid matrix

生成时间：`2026-06-15T14:29:53+00:00`。

- Scheduled cells: `200`。
- Completed cells: `200`。
- Scoreable cells: `196`。
- New paid cells in this expansion: `88` / cap `140`。
- Reused committed cells: `112`。
- Estimated displayed-matrix cost: `$114.52136065`；fresh expansion estimated cost `$67.94032565`。

## Paid/reuse source counts

| Source | Cells |
| --- | --- |
| fresh_paid_small_expansion | 88 |
| reused_committed_paid_cell | 112 |

## Score source counts

| Source | Cells |
| --- | --- |
| fresh_paid_cell | 88 |
| reused_doubled_timeout_top2_repeat | 16 |
| reused_original_holdout_score | 16 |
| reused_original_selection_score | 80 |

## Selection ranking

| Rank | Agent | Pass rate | Scoreable |
| --- | --- | --- | --- |
| 1 | Kilo + GPT mainline | 0.666667 | 30 |
| 2 | Kilo + Claude Sonnet | 0.517241 | 29 |
| 3 | Kilo + GPT low-cost | 0.448276 | 29 |
| 4 | Codex + GPT mainline | 0.366667 | 30 |

## Later-check ranking

| Rank | Agent | Pass rate | Scoreable |
| --- | --- | --- | --- |
| 1 | Kilo + Claude Sonnet | 0.894737 | 19 |
| 2 | Kilo + GPT mainline | 0.8 | 20 |
| 3 | Codex + GPT mainline | 0.75 | 20 |
| 4 | Kilo + GPT low-cost | 0.736842 | 19 |

Replacement rule: doubled-timeout top-2 rows supersede original Holdout rows only for `codex_gpt_5_4` and `kilo_gpt_5_4` on original Holdout tasks. No separate top-2 chart is used.
