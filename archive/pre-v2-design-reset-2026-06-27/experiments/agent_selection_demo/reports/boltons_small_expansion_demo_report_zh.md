# Boltons small expansion demo report

生成时间：`2026-06-15T14:39:30+00:00`。

## What changed

本次把 boltons demo 从旧的 `20` Selection tasks / `10` Holdout tasks 展示，扩展为严格按 `task_time` 排序的 `30` Selection tasks / `20` later-check tasks。新增任务来自 Phase 1 v2 no-paid certification 已证明 release-eligible 的 boltons target commits；没有切换到 attrs、click 或其他 fallback repository。

## Final counts

- Displayed tasks: `50` (`30` Selection + `20` later-check)。
- Displayed cells: `200`。
- New paid cells: `88` / hard cap `140`。
- Reused committed cells: `112`。
- Scoreable cells: `196`。

## Selection vs later-check matrix

| Agent | Selection | Later | Later-Selection |
| --- | --- | --- | --- |
| Codex + GPT mainline | 0.366667 | 0.75 | 0.383333 |
| Kilo + GPT mainline | 0.666667 | 0.8 | 0.133333 |
| Kilo + GPT low-cost | 0.448276 | 0.736842 | 0.288566 |
| Kilo + Claude Sonnet | 0.517241 | 0.894737 | 0.377495 |

## Strict chronological diagnostics

- Origins: `4`。
- MAE mean: `0.213418`。
- Top-rank agreement: `0.5`。
- Mean/max regret: `0.033742` / `0.094737`。
- Same-budget random mean MAE: `0.238985`。

## Cost and usage caveats

Cost values are estimated from adapter token usage when available and conservative per-cell estimates when usage is missing. They are not actual billing unless `billed_cost_usd` is populated.

## Supported PPT claim

On boltons, the expanded target-repo benchmark can compare complete Agents on a larger time-ordered Selection/later-check matrix, make an auditable recommendation, and evaluate how that recommendation behaves on later tasks. Strict chronological historical checks provide directional evidence that this is a measurable predictive-evaluation problem.

## Unsupported claims

- Predictive validity is proven.
- The selected Agent is globally best.
- Boltons results generalize to all repositories.
- The selector is statistically superior or optimal.
- Raw cost estimates are actual billing when usage coverage is incomplete.
