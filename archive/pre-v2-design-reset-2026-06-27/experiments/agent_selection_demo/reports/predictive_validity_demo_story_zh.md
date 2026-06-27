# Barcarolle Predictive-validity Demo Story

生成日期：2026-06-13

## 1. 一页摘要

软件团队真正关心的问题不是“某个 Agent 在公开榜单上高不高”，而是：

> 这个完整 Agent 配置，之后在我的仓库里会不会稳定做好真实工作？

Barcarolle 的目标是把这个问题变成可测量的问题：给定一个目标仓库，在某个历史时间点只看当时能看到的任务，选出一组 benchmark tasks，然后检查这组任务能不能预测之后的同仓库任务表现。

已经完成的 `mahmoud/boltons` Agent 选型 demo 给出了一个清楚的动机：选择集推荐是 `Codex + GPT mainline`，但 fresh holdout 上 `Kilo + GPT mainline` 是 `9/10`，Codex 是 `5/10`。也就是说，一个看起来合理的仓库内推荐，到了新任务上会被反转。

这次补全的 predictive-validity layer 给 demo 加上了测量框架和 no-paid retrospective 结果。结果是：best Barcarolle candidate `coverage_constrained_unweighted` 的 MAE 是 `0.209011`，best simple baseline `temporal_recent_baseline` 的 MAE 是 `0.214900`。候选方法小幅领先 `0.005889` MAE，但 catastrophic miss rate 都是 `0.555556`。

这不是 predictive validity proof。它是 directional retrospective traction：Barcarolle 已经能把“选出来的任务是否预测未来表现”量化，并且在现有数据上看到一点点优于简单 baseline 的信号；但要证明预测有效性，还需要事先冻结的新任务验证。

## 2. 问题：用户关心未来表现

一个仓库负责人评估 Coding Agent 时，核心问题通常是：

- 这个 Agent 会不会在我的仓库后续任务上通过验证；
- 选择哪一个 Agent 配置风险更低；
- 如果要调 prompt、工具或运行策略，哪些失败最值得修。

一次普通 pass/fail dashboard 不能回答这些问题。它只说明一批已知任务上的表现，不说明这批任务是否代表后续工作。

因此，Barcarolle 把 predictive validity 放在中心：benchmark task 的价值不只在于能评分，还在于能不能预测之后的同仓库工作。

## 3. 已有 demo 结果：推荐被 fresh holdout 反转

`boltons` demo 先在 20 个选择集任务上比较 4 个完整 Agent 配置，再锁定推荐，最后用 10 个未参与选择的 holdout tasks 检查推荐。

选择集上：

- `Codex + GPT mainline`：`15/20`
- `Kilo + GPT mainline`：`15/20`
- `Kilo + Claude Sonnet`：`14/18` scoreable
- `Kilo + GPT low-cost`：`13/18` scoreable

原推荐锁到 Codex，主要是成本破平。但后续发现 Codex 有 observed token usage，Kilo 是 conservative estimate，成本不可比。

Holdout 上：

- `Kilo + GPT mainline`：`9/10`
- `Kilo + Claude Sonnet`：`8/10`
- `Kilo + GPT low-cost`：`6/10`
- `Codex + GPT mainline`：`5/10`

这说明 selection-set winner 不能自动等同于 future-work winner。这个反转是 demo 的关键价值：它把 predictive validity 的必要性暴露出来。

## 4. 方法：rolling-origin 怎么问问题

Rolling-origin 的问法很简单：

1. 选一个历史时间点 `T`。
2. 只使用 `T` 时能看到的仓库任务和元数据。
3. 用某个策略选出 benchmark tasks。
4. 用这些任务预测 Agent 在 `T` 之后任务上的 verified pass rate。
5. 把预测误差和简单替代方法比较。

这样做的重点不是让任务更多，而是让任务选择更有预测意义。

## 5. 指标：用简单数字解释预测准不准

主指标是 MAE：

```text
abs(benchmark pass rate - later task pass rate)
```

越低越好。

辅助指标：

- Signed error：看系统性高估还是低估。
- RMSE：对大错更敏感。
- Rank agreement：选择集上的 top Agent 是否仍是之后任务的 top Agent。
- Recommendation regret：如果按选择集推荐选 Agent，比之后真实最优 Agent 损失多少 pass rate。
- Catastrophic miss rate：误差大于 `0.15` 的比例。

## 6. Baselines：必须打过简单方法

一个复杂选择器只有打过简单 baseline 才有意义。本 demo 使用这些 baseline：

- 最近任务 baseline：选最近的同预算任务；
- 随机同预算 baseline：多个 seed 的随机选择；
- 同仓库不加权 baseline；
- 简单仓库分层 baseline；
- best simple baseline envelope：简单 baseline 里表现最好的那个。

Barcarolle candidate 不能只和 random 比，也不能只报告最好的一次结果。

## 7. Data：no-paid retrospective result

这次补全没有运行新的 paid cells。它读取的是已提交的 sanitized outcomes 和 score tables。

可用窗口：

- 三仓库 retrospective pseudo-future windows：`attrs`、`boltons`、`click`；
- 一个 sparse true rolling-origin diagnostic；
- `boltons` demo selection-to-holdout window；
- top-2 repeatability blocker 只作为基础设施 caveat。

核心 numeric result：

| Method | MAE | RMSE | Signed error | Catastrophic miss | Slices |
| --- | ---: | ---: | ---: | ---: | ---: |
| best simple baseline: `temporal_recent_baseline` | `0.214900` | `0.257954` | `-0.061789` | `0.555556` | `18` |
| best Barcarolle candidate: `coverage_constrained_unweighted` | `0.209011` | `0.258881` | `-0.043267` | `0.555556` | `18` |

Candidate 比 best simple baseline 低 `0.005889` MAE。这个差距很小，但方向上支持“任务选择可能有优化空间”。

Rank/regret diagnostics：

- rank groups evaluated：`64`
- top-rank agreement rate：`0.8125`
- mean recommendation regret：`0.041552`
- max recommendation regret：`0.4`

`boltons` demo-only selection-to-holdout MAE 是 `0.136111`，但没有同预算 simple baselines，所以它主要说明推荐反转和 regret，不单独证明预测有效性。

## 8. Claim boundary

可以讲：

- Barcarolle 现在能把目标仓库 Agent 评估表达成“benchmark tasks 是否预测之后任务表现”的问题；
- 已有工具能生成 window inventory、计算 MAE/RMSE/rank/regret，并和 simple baselines 比较；
- no-paid retrospective data 给出小幅 directional traction；
- `boltons` fresh holdout contradiction 说明这个问题真实存在。

不能讲：

- predictive validity 已经被证明；
- 当前 selector 已经稳定优于 simple baselines；
- Kilo、Codex、GPT 或 Claude 有一般性排名；
- Kilo 的 holdout 领先稳定；
- 新 paid predictive-validity pilot 已经完成。

## 9. Product relevance

Agent selection 需要 predictive feedback，因为团队要选的是未来会工作的 Agent，而不是在一批已知任务上看起来最好的 Agent。

Agent tuning 也需要 predictive feedback。调 prompt、工具或运行策略之后，真正的问题是新配置能否提升之后任务的 verified pass rate，而不只是修好旧任务。

因此，Barcarolle 的产品价值不是一个 pass/fail 表格，而是一个面向目标仓库的预测评估循环：选择任务、运行完整 Agent、验证 diff、报告误差、和简单 baseline 比较，再把失败类型反馈给选型和调优。
