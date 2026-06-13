# Agent 选型 Demo 完成 Closeout

生成日期：2026-06-13

## 执行状态

执行分支：`codex/agent-selection-demo-2026-06-12`。

本次完成的是 demo 收口与报告/工具卫生整理，没有启动新的付费 Agent cell。

## 已完成

- 新增最终中文包：`experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`。
- 新增 Agent tuning feedback 原型：`experiments/agent_selection_demo/reports/agent_tuning_feedback_prototype_zh.md`。
- 保留第一轮 `mahmoud/boltons` demo 的历史事实：selection lock 推荐 `Codex + GPT mainline`，fresh holdout contradicted 该推荐。
- 在最终解释中修正成本口径：top-2 selection 质量打平，Kilo usage 缺失，所以 production-value 不能用不可比估算成本给单一成本赢家。
- 将 top-2 repeatability check 定位为 Kilo adapter/CLI timeout blocker，而不是新的 ranking result。
- 更新 demo tooling：未来生成的 cost ledger 和 score table 会包含 `cost_observation_kind`、`usage_source`、`billed_cost_usd` 字段。
- 在 demo config 中显式记录 `cost_usage_observed_rate_min: 0.95`。
- 更新 `PROCESS.md`，把最终中文包列为 canonical demo artifact，并记录推荐下一步。

## 最终 demo-level claim

可以 claim：

- Barcarolle 在 `mahmoud/boltons` 上完成了一次真实 Coding Agent 选型 demo；
- 系统能运行多个完整 Agent 配置、捕获 diff、在干净验证工作区重放，并记录质量、成本口径、延迟和失败类型；
- 原 selection 推荐在 fresh holdout 上被 contradicted；
- 这个结果说明目标仓库 Agent 选型需要 holdout check、成本口径审计、repeatability 报告和 adapter reliability gate。

不能 claim：

- predictive validity 已经被证明；
- Kilo、Codex、GPT 或 Claude 在一般意义上更强；
- Kilo 的 holdout 领先稳定；
- top-2 repeatability check 得到了有效 ranking；
- 第二仓库 paid scoring 已经通过 gate；
- Agent tuning 已经改进了某个 Agent。

## 付费 cell 使用

本次完成工作没有运行新的付费 Agent cell。

没有做 Kilo smoke/debug paid cell，也没有重跑 top-2 repeat batch。

## 未推进的事项

- 没有扩展 Agent 矩阵。
- 没有调 prompt、工具、模型设置或任务。
- 没有启动第二仓库 paid scoring。
- 没有引入 learned selector。
- 没有把 Kilo timeout 修复作为本 demo 完成的前置条件。

## 剩余 blocker

- Kilo repeat 路径存在连续 900 秒 adapter/CLI timeout，尚未定位到可修复根因。
- Kilo usage coverage 仍为 0，成本字段只能继续标为 conservative estimate，不能用于 production-value 成本赢家。
- 当前 `boltons` 结果是单仓库 demo，不支持跨仓库泛化结论。

## 验证

已运行：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

结果：`8 passed in 0.04s`。

已运行：

```text
git diff --check
```

结果：通过。

已运行：

```text
git ls-files | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

结果：命中了 repo 中既有的 `workspace`/`raw` 命名文件，包括历史 workspace runner/tooling、workspace summary artifacts 和 raw candidate inventory 文件名。它们不是本次新增的缓存、完整运行会话、solver/verifier 工作区或 secret 文件。

已运行更窄的 demo 目录检查：

```text
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)'
```

结果：无命中。

## 推荐下一步

如果下一步要强化“Kilo holdout lead 是否稳定”这个窄 claim，先做无付费的 Kilo timeout/usage root-cause patch 和 adapter tests；只有 gate 重新通过后，才在已批准边界内重跑 frozen top-2 holdout repeat。

如果下一步要强化“系统能跨仓库工作”这个 claim，先做 no-paid 第二仓库 gate，只输出 go/no-go 和预算估计，不直接启动 paid matrix。
