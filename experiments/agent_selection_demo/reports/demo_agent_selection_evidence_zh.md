# Demo Agent-selection Evidence

生成日期：2026-06-14

## 结论

Package 5 在 doubled-timeout policy 下完成了新的 top-2 repeat evidence：

- 新 paid cells：`20`
- 候选：`Codex + GPT mainline`、`Kilo + GPT mainline`
- 任务：同一批 10 个 frozen `mahmoud/boltons` holdout tasks
- timeout：adapter `1800s`，outer workspace `1860s`
- scoreable：`20/20`
- 结果：Codex `6/10`，Kilo `9/10`

这说明 demo facility 可以给出可用的 Agent-selection evidence：不只看 selection set，还能在可靠性门禁后用 fresh holdout/repeat 检查推荐是否站得住。当前 `boltons` top-2 evidence leader 是 `Kilo + GPT mainline`，但这不是全局 Agent 排名。

## Selection / holdout matrix

| Agent | Selection pass | Selection scoreable pass rate | Holdout pass | Holdout pass rate | Abs error |
| --- | ---: | ---: | ---: | ---: | ---: |
| Codex + GPT mainline | `15/20` | `0.750000` | `5/10` | `0.500000` | `0.250000` |
| Kilo + GPT mainline | `15/20` | `0.750000` | `9/10` | `0.900000` | `0.150000` |
| Kilo + Claude Sonnet | `14/18` scoreable | `0.777778` | `8/10` | `0.800000` | `0.022222` |
| Kilo + GPT low-cost | `13/18` scoreable | `0.722222` | `6/10` | `0.600000` | `0.122222` |

Selection-to-holdout MAE using scoreable pass rates: `0.136111`.

用 scheduled pass rates 计算的同一矩阵 MAE 是 `0.137500`。主报告沿用 `rolling_origin_eval_slices.csv` 的 scoreable pass-rate口径，因为它对 non-scoreable cells 不把模型质量失败和基础设施失败混在一个 pass-rate 分母里。

## Old repeat vs doubled-timeout repeat

| Evidence slice | Codex + GPT mainline | Kilo + GPT mainline | Interpretation |
| --- | ---: | ---: | --- |
| Original selection | `15/20` | `15/20` | quality tie |
| Original holdout | `5/10` | `9/10` | holdout favors Kilo |
| Old `900s` top-2 repeat | `7/10` scoreable | `0/0` scoreable from 3 timeout rows | Kilo path blocked by timeout |
| New `1800s` top-2 repeat | `6/10` scoreable | `9/10` scoreable | repeat favors Kilo; both scoreable |

New doubled-timeout repeat details:

| Agent | Completed | Scoreable | Verified pass | Pass rate | Median latency | p90 latency | Usage observed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Codex + GPT mainline | `10` | `10` | `6` | `0.600000` | `145.059s` | `429.747s` | `10/10` |
| Kilo + GPT mainline | `10` | `10` | `9` | `0.900000` | `50.418s` | `69.513s` | `10/10` |

Top-2 selection-to-doubled-repeat MAE:

```text
(abs(0.75 - 0.60) + abs(0.75 - 0.90)) / 2 = 0.150000
```

Holdout-to-doubled-repeat MAE:

```text
(abs(0.50 - 0.60) + abs(0.90 - 0.90)) / 2 = 0.050000
```

## Reliability-gated status

| Agent | Status | Basis |
| --- | --- | --- |
| Codex + GPT mainline | scoreable | selection、holdout、old repeat、new doubled-timeout repeat 均可评分 |
| Kilo + GPT mainline | scoreable under doubled timeout | Package 4 smoke/debug gate passed；Package 5 repeat `10/10` scoreable |
| Kilo + Claude Sonnet | historical holdout scoreable | 不在 top-2 doubled repeat 中重新运行 |
| Kilo + GPT low-cost | historical selection had unscoreable cells | 不在 top-2 doubled repeat 中重新运行 |

Kilo 的旧 `900s` repeat timeout 仍是历史事实；它不再阻断本次 demo story，因为新的 `1800s` reliability gate 和 top-2 repeat 已经完成并可评分。

## Recommendation rule after cost-inconclusive handling

修正后的规则：

1. 先要求 reliability-gated scoreability；非可评分 timeout 不当作模型质量分数。
2. 比较 selection、fresh holdout 和 repeat 的 verified pass rate。
3. 只有在同一 evidence slice 中 usage coverage 可比时，才用 cost 破平。

按这个规则解释旧 selection：

- Codex + GPT mainline 与 Kilo + GPT mainline 在 selection 上同为 `15/20`；
- old selection 的 Kilo cost 是 missing-usage conservative estimate，Codex 是 observed token estimate；
- 因此原 Codex cost tie-break 是 cost-inconclusive，不能当成可靠的 production-value winner。

按当前 reliability-gated top-2 evidence：

- original holdout：Kilo `9/10`，Codex `5/10`；
- doubled-timeout repeat：Kilo `9/10`，Codex `6/10`；
- doubled-timeout repeat 的 usage 覆盖为两者 `10/10` observed。

因此，今天能给出的目标仓库结论是：在 `mahmoud/boltons` 的 top-2 candidate evidence 中，`Kilo + GPT mainline` 是 reliability-gated evidence leader；不要把它写成跨仓库、跨模型或全局 Agent 排名。

## Usable today

- Facility 能运行完整 Agent、捕获 diff、干净重放 hidden verifier，并记录 quality/cost/latency/failure category。
- Selection matrix 暴露了 top-2 quality tie 和旧 cost tie-break 的脆弱性。
- Holdout 和 doubled-timeout repeat 都支持同一个 target-repo observation：Kilo + GPT mainline 在这批新任务上领先 Codex + GPT mainline。
- 新 repeat 让旧 Kilo timeout blocker 不再吞掉 demo 的 Agent-selection story。

## Cannot claim

- 不能 claim Kilo、Codex、GPT 或 Claude 的全局强弱排名。
- 不能 claim predictive validity 已经证明。
- 不能 claim 所有 Kilo paths 都稳定；这里只验证了 `Kilo + GPT mainline` 的本次 doubled-timeout top-2 path。
- 不能用旧 selection cost 估算做可靠成本赢家，因为 usage coverage 当时不可比。

## Paid accounting

| Package | New paid cells |
| --- | ---: |
| Package 4 Kilo reliability gate | `1` |
| Package 5 doubled-timeout top-2 repeat | `20` |
| Runbook total so far | `21` |
| Runbook cap | `42` |
