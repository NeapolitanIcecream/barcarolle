# Boltons selector-aware reanalysis closeout

生成时间：`2026-06-16T03:16:06+00:00`。

## Correction

旧 fixed-window 图表不是 selector evidence，因为它没有模拟用户会先用 selector 从历史池中挑预算内 benchmark。新分析在每个 origin 都先选择 task IDs，再 join 已有 outcomes。

## Winner

- Selector: `hrd_v3_70_30`。
- Budget: `k=10`。
- New paid cells used: `0`。

## Latest-origin matrix

| Agent | Selection | Future |
| --- | --- | --- |
| Kilo + Claude Sonnet | 9/10 (0.9) | 9/10 (0.9) |
| Kilo + GPT mainline | 7/10 (0.7) | 9/10 (0.9) |
| Kilo + GPT low-cost | 6/10 (0.6) | 8/10 (0.8) |
| Codex + GPT mainline | 3/10 (0.3) | 8/10 (0.8) |

## Rolling-origin metrics

- MAE mean: `0.194444`。
- Mean/max regret: `0.0` / `0.0`。
- Top-tier agreement: `1.0`。
- Top-pair direction agreement: `0.0`。

## Random baseline

- Latest strongest random: `source_recency_stratified_random`。
- Selector minus random MAE: `-0.067125`。
- Selector minus random regret: `-0.0059`。

## Supported claims

- The expanded boltons matrix can be reanalyzed without new paid cells under a selector-aware protocol.
- For each origin, selectors choose only from historical task metadata before outcomes are joined.
- Fail-inclusive pass rates treat timeout, harness error, invalid output, and no meaningful change as failed attempts.
- The final chart story should use the winning selector's origin_40 selected task IDs, not the full fixed history window.

## Unsupported claims

- Predictive validity is proven.
- The winning selector is generally best across repositories or future paid runs.
- The old fixed-window rolling-origin chart is selector evidence.
- Scoreable-only pass rates are the main user-facing result.
