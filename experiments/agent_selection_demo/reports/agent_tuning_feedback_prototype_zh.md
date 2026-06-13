# Agent Tuning Feedback Prototype

生成日期：2026-06-13

本报告只使用 `experiments/agent_selection_demo/results/` 下已提交的 sanitized score tables、metrics 和 repeatability summary。它展示这些 verifier-backed 信号如何变成 Agent tuning 或配置改进输入；它不声称任何 Agent 已经被 tuning，也不声称 tuning 后效果已提升。

## 可消费的反馈信号

| 信号 | 当前来源 | tuning/配置含义 |
| --- | --- | --- |
| verified pass/fail | `selection_score_table.csv`、`holdout_score_table.csv` | 判断配置是否真的修复任务，而不是只通过可见检查 |
| failure category | score table 和 metrics | 区分 hidden verifier failure、timeout、no meaningful change 等不同修复方向 |
| task-level flip | `top2_repeatability_stability_table.csv` | 找出不稳定任务，避免把单次 pass/fail 当成确定能力 |
| usage coverage | `*_cost_ledger.jsonl`、post-demo diagnostics | 成本优化前先确认 usage 是否可比 |
| latency | score table 和 metrics | 识别慢但可解、快但失败、或 adapter timeout 问题 |

## 当前失败画像

| Agent | selection 主要失败 | holdout 主要失败 | tuning 含义 |
| --- | --- | --- | --- |
| Codex + GPT mainline | 5 个 hidden verifier failure | 5 个 hidden verifier failure | later `canonical_history` holdout 上需要更细的任务理解和验证反馈 |
| Kilo + GPT mainline | 5 个 hidden verifier failure | 1 个 hidden verifier failure | 第一轮质量强，但 repeat 被 adapter timeout 阻断，先修运行可靠性 |
| Kilo + GPT low-cost | 5 个 hidden verifier failure，2 个 timeout | 4 个 hidden verifier failure | 低成本模型的质量和超时风险都需要单独门禁 |
| Kilo + Claude Sonnet | 4 个 hidden verifier failure，2 个 no meaningful change | 2 个 hidden verifier failure | 需要减少空 diff/无意义改动，并继续观察长延迟任务 |

## 可进入 backlog 的任务例子

| 任务 | 现象 | 可用反馈 |
| --- | --- | --- |
| `boltons__supply_expansion_20260526__001` | selection 中 4 个 Agent 全部 failed | 可能是高难或 statement/verifier 需要人工复核的任务 |
| `boltons__supply_expansion_20260526__107` | selection 中 4 个 Agent 全部 failed | 适合作为 shared failure case，不适合用来区分 top-2 |
| `boltons__hist__022` | holdout 中 Codex failed，Kilo GPT passed；Codex repeat 仍 failed | 可作为 Codex later-history failure exemplar |
| `boltons__hist__023` | holdout 中 Codex failed，Kilo GPT passed；Codex repeat 仍 failed | 可作为稳定失败候选，但 Kilo repeat 缺失，不能确认 top-2 稳定差距 |
| `boltons__hist__027` | Codex holdout failed，repeat passed | 标记为 stochastic/unstable，不应用作单次 tuning 胜负证据 |
| `boltons__clean_ext__017`、`boltons__hist__019` | Kilo repeat 连续 900 秒 timeout | adapter/CLI reliability blocker，不应归因到模型解题能力 |

## 反馈到 tuning 系统时应保留的字段

| 字段 | 原因 |
| --- | --- |
| `agent_id`、运行方式、`model` | tuning 目标是完整 Agent 配置，不是裸模型 |
| `task_id`、`source`、`task_time`、`module` | 分析是否集中在某类任务或时间段 |
| `terminal_status`、`failure_category` | 区分 verifier fail、timeout、policy failure、empty diff |
| `scoreable_cell`、`verified_pass` | 防止把 infra failure 当作质量失败 |
| `latency_seconds` | 识别 timeout 风险和效率问题 |
| `usage_observed`、`cost_observation_kind`、`usage_source`、`billed_cost_usd` | 成本反馈只在口径可比时使用 |
| `patch_sha256` | 允许稳定引用 diff，而不提交完整运行会话明细 |

## 当前能支持的 tuning claim

可以 claim：

- 已有结果能生成 verifier-backed failure labels；
- task-level pass/fail delta 能指出值得复核或重复运行的任务；
- Kilo repeat timeout 是 Agent 配置评估前必须解决的 adapter reliability 问题；
- 成本优化前必须修复 usage coverage 不对称。

不能 claim：

- tuning 已经提升某个 Agent；
- 某个 prompt、工具策略或模型设置一定能修复这些失败；
- Codex 或 Kilo 在一般意义上更适合 tuning；
- 单次 holdout 反转足够定义长期 Agent 配置策略。

## 推荐的最小下一步

先把这个反馈原型接成一个只读 summary generator：输入 sanitized score tables 和 metrics，输出每个 Agent 的 failure taxonomy、unstable tasks、infra blockers 和 cost-usage coverage。只有当 Kilo adapter timeout 与 usage normalization 修复后，再把这些信号用于下一轮 repeat 或配置改进评估。
