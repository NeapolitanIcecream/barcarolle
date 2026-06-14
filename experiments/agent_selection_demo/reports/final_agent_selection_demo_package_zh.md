# Agent 选型 Demo 最终报告

生成日期：2026-06-14

## 1. 这个 demo 想证明什么

这个 demo 面向一个很具体的用户问题：

> 给定一个目标仓库和几种 Coding Agent 配置，Barcarolle 能不能用冻结的 Selection 任务给出 Agent 选择建议，并用后续 Holdout 任务检查这个建议是否站得住？

本报告的主线 selector 是 `HRD v3 70/30`。它不是最终成果算法，也不是全局最佳 selector。它是当前足够支撑 demo story 的一个可解释、可运行、可审计的 selector：先覆盖目标仓库的代表性任务，再补一部分更有区分度的任务，然后输出 Agent 排名、选择建议和证据表。

## 2. 任务、Agent、Selection、Holdout 设置

目标仓库是 `mahmoud/boltons`。任务来自仓库历史改动；每个 scoreable Agent diff 都在干净验证工作区重放，并用隐藏验证检查。

候选 Agent：

| Agent | Harness | Model |
| --- | --- | --- |
| Codex + GPT mainline | codex | `gpt-5.4` |
| Kilo + GPT mainline | kilo | `gpt-5.4` |
| Kilo + GPT low-cost | kilo | `gpt-5.4-mini` |
| Kilo + Claude Sonnet | kilo | `claude-sonnet-4-6` |

任务划分：

| 部分 | 任务数 | 用途 |
| --- | ---: | --- |
| Selection candidate tasks | 20 | 供 selector 选择评估任务并形成 Agent 推荐 |
| HRD selected tasks | 10 | HRD v3 70/30 实际用于决策的 Selection 子集 |
| Holdout tasks | 10 | 推荐锁定后的后续验证 |
| Doubled-timeout top-2 repeat | 10 | 对 Codex GPT mainline 与 Kilo GPT mainline 做同批 holdout repeat |

本次最终收口没有启动新的 paid cells。报告使用已经提交的 sanitized results。

## 3. HRD selector 给出了什么选择

HRD v3 70/30 在 10 个 selected Selection tasks 上给出的 Agent 排名如下：

| Rank | Agent | Selection pass | Pass rate | Gap to top |
| ---: | --- | ---: | ---: | ---: |
| 1 | Kilo + GPT mainline | `9/10` | `0.90` | `0.00` |
| 2 | Codex + GPT mainline | `7/10` | `0.70` | `0.20` |
| 3 | Kilo + Claude Sonnet | `7/10` | `0.70` | `0.20` |
| 4 | Kilo + GPT low-cost | `7/10` | `0.70` | `0.20` |

选择建议：推荐 `Kilo + GPT mainline`。

证据表：

| Agent | Selection | Pair common vs top | Top minus agent margin | Top W/L/T |
| --- | ---: | ---: | ---: | ---: |
| Kilo + GPT mainline | `9/10` |  |  |  |
| Codex + GPT mainline | `7/10` | `10` | `0.20` | `2/0/8` |
| Kilo + Claude Sonnet | `7/10` | `10` | `0.20` | `2/0/8` |
| Kilo + GPT low-cost | `7/10` | `10` | `0.20` | `2/0/8` |

这个 wrapper 的读者口径是：先给 Agent 排名和建议。只有 scoreable cells 明显不足、缺 outcome row，或基础设施失败导致无法比较时，才输出 `insufficient_data`。如果多个 Agent 在 Selection 上接近，则输出 `top_tier`，由用户按成本、速度、稳定性做破平。paired wins/losses、bootstrap LCB 等字段是证据，不再因为单个 discordant task 或统计显著性不足直接拒绝推荐。

这也修复了一个边界问题：类似 `9/10` 对 `8/10` 的 Selection 优势不应因为浮点或阈值边界被误判为不推荐。

## 4. Holdout 是否验证了这个选择

Holdout 结果支持 HRD 给出的选择。推荐的 `Kilo + GPT mainline` 在后续 Holdout 上仍是第一：

| Agent | Holdout pass | Pass rate |
| --- | ---: | ---: |
| Kilo + GPT mainline | `9/10` | `0.90` |
| Kilo + Claude Sonnet | `8/10` | `0.80` |
| Kilo + GPT low-cost | `6/10` | `0.60` |
| Codex + GPT mainline | `5/10` | `0.50` |

对 top-2 的 doubled-timeout repeat 也支持同一方向：

| Agent | Top-2 repeat pass | Pass rate |
| --- | ---: | ---: |
| Kilo + GPT mainline | `9/10` | `0.90` |
| Codex + GPT mainline | `6/10` | `0.60` |

因此，这个 demo 支持的核心故事是：用户可以根据 Selection 结果做一次 Agent 选型；在这批后续 Holdout 任务上，Selection 推荐的 `Kilo + GPT mainline` 也处于领先位置。推荐 regret 为 `0.0`。

## 5. 和 random baseline / 其他 selector 的关系

MAE 和 random baseline 是辅助证据，不是本报告的唯一核心目标。HRD v3 70/30 在这个 boltons demo slice 上的 MAE 是 `0.100000`；同预算 stratified random k=10 的 MAE mean 是 `0.151700`。这说明 HRD 在这个 slice 上有辅助性的数值支持。

这不能写成“selector 已经严格击败强 random baseline”。原因是当前证据仍来自单仓库 demo slice 和 no-paid retrospective replay；selector family、wrapper policy 和报告口径都经历了开发收口，不能把它扩展成 full predictive-validity proof。

算法 bakeoff 仍保留为附录口径：

| Selector candidate | Development decision signal | MAE signal | 报告角色 |
| --- | ---: | ---: | --- |
| HRD v3 70/30 | validated recommendation rate `1.0` | MAE `0.122643` | 本 demo 主线 selector |
| COD-lite | validated recommendation rate `1.0` | MAE `0.142087` | 普通候选算法，保留在 bakeoff 表 |
| RSQ / FLC / RO-LSP / SAES-lite / ablations | 见 bakeoff 表 | 见 bakeoff 表 | 对比和消融 |

COD-lite 不作为最终 demo 主算法，也不和 HRD 写成双主线。

## 6. 当前边界和下一步

可以支持的 claim：

- 在 `mahmoud/boltons` 上，Barcarolle 可以运行真实 Coding Agent、捕获 diff、在干净工作区验证，并形成可审计的 Agent 选择证据。
- HRD v3 70/30 在 frozen Selection 子集上推荐 `Kilo + GPT mainline`。
- 后续 Holdout 和 doubled-timeout top-2 repeat 都显示 `Kilo + GPT mainline` 处于领先位置。
- 当前 wrapper/reporting policy 更适合用户决策：输出排名、建议和证据；接近时给 top tier；只有不可比较时才给 insufficient data。

不能支持的 claim：

- predictive validity 已经被证明；
- HRD 严格击败所有强 random baselines；
- 这个 selector 已经跨仓库、跨模型家族泛化；
- `Kilo + GPT mainline` 是全局最佳 Agent；
- COD-lite 是最终 demo 主算法。

推荐下一步：

| 目标 | 下一步 |
| --- | --- |
| 强化 demo 可信度 | 在另一个目标仓库上冻结同样的 Selection/Holdout 协议后再看结果 |
| 强化 selector 证据 | 增加 leakage-safe historical Agent-disagreement 或更多独立 rolling-origin/future slices |
| 强化生产决策 | 纳入真实账单成本、延迟稳定性、timeout/adapter 可靠性 |
| 强化产品故事 | 把失败标签和 unstable tasks 输出给 Agent tuning backlog，但不声称 tuning 已完成 |

## 7. 主要 artifact

| 内容 | Artifact |
| --- | --- |
| HRD final eval | `experiments/agent_selection_demo/reports/selector_final_eval_zh.md`；`experiments/agent_selection_demo/results/selector_final_eval.json` |
| Wrapper policy eval | `experiments/agent_selection_demo/reports/selector_decision_eval_zh.md`；`experiments/agent_selection_demo/results/selector_decision_eval.json` |
| Wrapper v2 development eval | `experiments/agent_selection_demo/reports/selector_decision_wrapper_v2_eval_zh.md`；`experiments/agent_selection_demo/results/selector_decision_wrapper_v2_eval.json` |
| Algorithm bakeoff appendix | `experiments/agent_selection_demo/reports/selector_algorithm_bakeoff_eval_zh.md`；`experiments/agent_selection_demo/results/selector_algorithm_bakeoff_eval.json` |
| Corrected validation context | `experiments/agent_selection_demo/reports/selector_corrected_validation_closeout_zh.md`；`experiments/agent_selection_demo/results/selector_corrected_validation_closeout.json` |
