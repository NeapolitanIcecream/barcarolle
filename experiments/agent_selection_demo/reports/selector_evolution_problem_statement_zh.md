# Selector Evolution Problem Statement

生成日期：2026-06-14

## 为什么旧故事还不够

上一轮 random-baseline evidence 已经说明：当前 Barcarolle candidate 的 future pass-rate MAE 低于同预算随机抽样。这支持的是“任务选择有预测信号”，不是完整的 Agent 选型故事。

Agent 选型故事需要回答另一个问题：

> Selection 推荐哪个 Agent？后来 Holdout 是否验证这个选择？

旧 Selection set 上 `Codex + GPT mainline` 和 `Kilo + GPT mainline` 都是 `15/20`。这意味着用户看到 Selection 时没有干净的质量推荐；后面的 Holdout 和 doubled-timeout repeat 支持 Kilo，只能说明旧 Selection 不足以安全推荐，而不能说明旧 selector 已经会选 Agent。

本 runbook 因此把目标拆开：

- pass-rate prediction：Selection pass rate 能否接近 later/Holdout pass rate；
- Agent-selection decision quality：Selection 是否能安全推荐、是否应 abstain、推荐后的 later regret 是否低。

## 已有 no-paid 证据

所有输入都来自已提交的 sanitized artifacts；本 package 没有新 paid calls。

| Artifact | Stage | Tasks | Agents | 说明 |
| --- | --- | ---: | ---: | --- |
| `selection_score_table.csv` | Selection | `20` | `4` | 四个 demo Agents 都有 rows；Codex/Kilo GPT mainline 各 `15/20`，低成本和 Claude 各有 `2` 个 non-scoreable selection cells |
| `holdout_score_table.csv` | Holdout | `10` | `4` | 四个 demo Agents 完整且全部 scoreable；Kilo GPT mainline `9/10`，Codex GPT mainline `5/10` |
| `doubled_timeout_top2_repeat_score_table.csv` | later repeat | `10` | `2` | top-2 Agents 完整且全部 scoreable；Kilo GPT mainline `9/10`，Codex GPT mainline `6/10` |
| `top2_repeat_score_table.csv` | old repeat | `10` | `2` | 旧 `900s` Kilo path timeout，不能当 final validation grid |
| `smoke_score_table.csv` | smoke | `1` | `4` | reliability gate context，不参与 selector quality metric |

当前 no-paid path 不缺 Selection/Holdout common grid。若后续 selector 只能因为 missing cells 无法解释结果，才触发 paid fallback；现在没有这个必要。

## 初始选择空间

本轮先使用 frozen pseudo-future replay：

- candidate pool：`frozen_split.json` 中原始 `20` 个 Selection tasks；
- later/Holdout：原始 `10` 个 Holdout tasks；
- reliability-gated top-pair later check：`doubled_timeout_top2_repeat_score_table.csv`；
- primary Agent set：四个 demo Agents；
- paid fallback top-2：`codex_gpt_5_4` 和 `kilo_gpt_5_4`。

初始预算：

- `k=20`：当前 Selection 大小，用来确认旧完整 set 是否仍是质量 tie；
- `k=10`：较小 sensitivity 和 final no-paid 候选；仍满足默认 top-pair common-valid 下限 `8`，且能形成有意义的 random baseline 分布。

## 决策指标

本轮优化和报告的指标为：

- MAE：Selection pass rate 与 later/Holdout pass rate 的平均绝对误差；
- pairwise direction agreement：非 tie Agent pair 的方向是否从 Selection 转移到 later；
- top-1 agreement：Selection top Agent 是否也是 later top Agent；
- recommendation regret：later best pass rate 减去被推荐 Agent 的 later pass rate；
- recommendation coverage：decision wrapper 给出 `recommend` 的比例；
- abstain / need-more-evidence quality：abstain 是否对应小 margin，need-more-evidence 是否对应有效样本或不确定性不足；
- random-baseline percentile：selector 相对同预算随机分布的位置。

## 泄漏控制

selector 在选 task IDs 时只能看：

- task metadata：`task_time`、source、module/path bucket、test path bucket、source cluster；
- deterministic fallback features：change-size bucket、recency bucket、quality/risk conservative defaults；
- frozen config：Agent set、budget、seed、invalid-cell policy。

selector 不能看：

- candidate Agents 在待选 Selection tasks 上的 pass/fail；
- Holdout 或 doubled-timeout repeat outcomes；
- final random-baseline distribution summary after config tuning。

实现上，selector 先产出 task IDs；evaluation 只在 task IDs 固定后 join Selection outcomes 和 later outcomes。final slice 在 selector config freeze 后只评估一次，不因结果重新调阈值。
