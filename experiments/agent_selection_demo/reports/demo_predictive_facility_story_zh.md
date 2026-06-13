# Barcarolle 目标仓库预测式 Agent 评估 Demo

生成日期：2026-06-14

## 1. 我们建成了什么

Barcarolle 已经能做一次完整的目标仓库 Agent 评估 demo。

给定一个真实代码仓库，它可以整理一批可验证任务，把任务交给不同完整 Agent 配置运行，捕获每次运行后的代码 diff，再放到干净验证工作区里重放和检查。输出不是一个模糊印象，而是一组可审计数字：通过率、失败类型、是否可评分、延迟、成本口径和任务级结果。

这里评估的是完整 Agent 配置，不是裸模型。也就是说，模型、运行方式、工具权限、提示和超时策略一起作为被比较对象。

## 2. 为什么这件事重要

团队选择 Coding Agent 时，真正关心的是：

> 这个 Agent 以后在我的仓库里能不能继续做好新任务？

只看一批已知任务的 pass/fail 不够。一个选择集上的赢家，可能在之后的新任务上掉队。一个看起来成本更低的配置，也可能只是因为成本记录口径不一致。

所以这个 demo 的核心不是制造一个公开排名，而是把“选择哪一个 Agent”变成目标仓库里的可验证问题：先选任务、再跑完整 Agent、再用新任务和重复检查验证这个选择是否可靠。

## 3. Evidence 1：完整 Agent 执行和干净验证能跑通

`mahmoud/boltons` demo 已经完成了端到端流程：

| 部分 | 证据 |
| --- | --- |
| 候选 Agent | Codex + GPT mainline、Kilo + GPT mainline、Kilo + GPT low-cost、Kilo + Claude Sonnet |
| Selection tasks | `20` 个 frozen 目标仓库任务 |
| Holdout tasks | `10` 个未参与推荐的新任务 |
| 验证方式 | 捕获 Agent diff，在干净 verifier workspace 重放 hidden tests |
| 记录内容 | pass/fail、scoreable/non-scoreable、failure category、延迟、成本口径 |

旧结果已经暴露了一个真实问题：selection 上 Codex + GPT mainline 和 Kilo + GPT mainline 都是 `15/20`，但 holdout 上 Kilo 是 `9/10`，Codex 是 `5/10`。这说明 selection winner 不能自动等同于之后新任务 winner。

## 4. Evidence 2：任务选择明显好于随机同预算抽样

本 demo 的主量化证据是同预算随机基线。

MAE 是 `abs(benchmark pass rate - later task pass rate)` 的平均值；越低，说明选择出来的 benchmark tasks 越接近之后任务表现。

| Design | MAE | 含义 |
| --- | ---: | --- |
| Barcarolle candidate: `coverage_constrained_unweighted` | `0.209011` | 当前候选任务选择 |
| Random same-budget baseline | `0.252499` | 同预算随机抽样 |

Candidate 比随机基线低 `0.043488` MAE，相对改善 `17.22%`。这同时超过 demo 门槛：

- absolute MAE improvement 至少 `0.02`；
- relative MAE improvement 至少 `10%`。

还有一个 1000-seed 随机分布可以作为上下文：candidate 位于低误差端，优于或打平 `93.4%` 的同预算随机样本。

这不等于“预测有效性已经证明”。它说明的是：Barcarolle 已经能把任务选择的预测价值量化出来，而且当前 candidate 在 retrospective evidence 中明显好于随机同预算抽样。

## 5. Evidence 3：Agent-selection matrix 可以支持真实选型讨论

修正后的选型故事不再强行把旧成本字段当成赢家依据。旧 selection 中，Codex 有 observed token estimate，Kilo 是 missing-usage conservative estimate，成本口径不可比。因此原 Codex cost tie-break 应改为 cost-inconclusive。

核心矩阵如下：

| Evidence slice | Codex + GPT mainline | Kilo + GPT mainline | 解释 |
| --- | ---: | ---: | --- |
| Original selection | `15/20` | `15/20` | 质量打平 |
| Original holdout | `5/10` | `9/10` | 新任务检查支持 Kilo |
| Old 900s repeat | `7/10` | `0/0` scoreable from 3 timeouts | Kilo repeat 当时被 timeout 阻断 |
| New 1800s repeat | `6/10` | `9/10` | 两者都可评分，repeat 支持 Kilo |

新的 `1800s` repeat 还解决了 demo 里的关键可靠性问题：

- Kilo reliability gate：`1` 个新 smoke/debug cell，`verified_pass`；
- top-2 repeat：`20/20` scoreable；
- Codex repeat：`6/10`；
- Kilo repeat：`9/10`；
- 两者新 repeat usage 都是 `10/10` observed。

今天能给出的选型结论很窄但有用：在 `mahmoud/boltons` 的这批 top-2 evidence 中，Kilo + GPT mainline 是 reliability-gated evidence leader。这个结论不能推广成全局排名。

## 6. Caveats

这些限制必须保留：

- Best-simple-baseline 只是稳健性检查，不是主 gate。Candidate 对 best simple baseline 的 MAE 优势只有 `0.005889`，catastrophic miss rate 没改善。
- Kilo 旧 repeat 的 `900s` timeout 是真实历史问题；新 `1800s` repeat 解决了本次 top-2 path，但不代表所有 Kilo path 都稳定。
- 当前数据量仍小，主要来自一个目标仓库的 demo 和 retrospective/pseudo-future evidence。
- 这不是完整预测有效性证明，也不是模型家族排名。
- 成本比较必须看 usage coverage；旧 selection 成本不可比，新 repeat 成本才有同 slice 的 observed usage 基础。

## 7. 下一步

最自然的下一步不是扩大模型矩阵，也不是马上讲成产品级榜单。

下一步应是加强信号：冻结任务、候选 Agent、baseline、score-join 规则和 success threshold，然后做预注册的新任务验证。这样才能把现在的 demo-level evidence 推向更强的预测有效性结论。

当前 demo 已经足够说明一件事：Barcarolle 是一个可投资推进的目标仓库 Agent 评估设施。它能运行真实 Agent，能验证 diff，能把任务选择和未来表现的误差说清楚，也能在可靠性门禁后给出可审计的 Agent-selection evidence。
