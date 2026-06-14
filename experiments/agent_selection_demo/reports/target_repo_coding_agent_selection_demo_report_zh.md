# 目标仓库 Coding Agent 选型 Demo 报告

生成日期：2026-06-14

本报告是 `mahmoud/boltons` Agent 选型 demo 的读者版摘要。当前 demo 主线使用 `HRD v3 70/30` selector，而不是初版 selection-lock 成本破平规则，也不是 COD-lite。

## Demo 设置

| 项目 | 设置 |
| --- | --- |
| 目标仓库 | `mahmoud/boltons` |
| 候选 Agent | Codex + GPT mainline；Kilo + GPT mainline；Kilo + GPT low-cost；Kilo + Claude Sonnet |
| Selection pool | 20 个冻结 Selection tasks |
| HRD decision subset | 10 个 selected Selection tasks |
| Holdout | 10 个后续任务 |
| Top-2 repeat | Codex GPT mainline 与 Kilo GPT mainline 各 10 个 doubled-timeout repeat cells |

所有 scoreable Agent diff 都在干净验证工作区重放。hidden verifier material 只进入 verifier workspace。

## HRD 给出的选择

| Rank | Agent | Selection pass | Pass rate |
| ---: | --- | ---: | ---: |
| 1 | Kilo + GPT mainline | `9/10` | `0.90` |
| 2 | Codex + GPT mainline | `7/10` | `0.70` |
| 3 | Kilo + Claude Sonnet | `7/10` | `0.70` |
| 4 | Kilo + GPT low-cost | `7/10` | `0.70` |

选择建议：推荐 `Kilo + GPT mainline`。

## Holdout 验证

| Agent | Holdout pass | Pass rate |
| --- | ---: | ---: |
| Kilo + GPT mainline | `9/10` | `0.90` |
| Kilo + Claude Sonnet | `8/10` | `0.80` |
| Kilo + GPT low-cost | `6/10` | `0.60` |
| Codex + GPT mainline | `5/10` | `0.50` |

Top-2 doubled-timeout repeat 也支持同一方向：Kilo + GPT mainline `9/10`，Codex + GPT mainline `6/10`。

## 怎么读这个结果

这个 demo 支持：Barcarolle 可以把目标仓库任务、真实 Agent 运行、干净验证、Selection 推荐和 Holdout 检查连成一个可审计的 Agent 选型流程。在这批任务上，HRD v3 70/30 推荐 Kilo + GPT mainline，后续 Holdout 也验证了这个选择。

这个 demo 不支持：full predictive validity、跨仓库或跨模型家族排名、HRD 严格击败所有强 random baselines，或 COD-lite 是最终 demo 主算法。

完整报告见 `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`。
