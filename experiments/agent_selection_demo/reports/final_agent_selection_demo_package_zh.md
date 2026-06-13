# Agent 选型 Demo 最终包

生成日期：2026-06-13

## 一页摘要

2026-06-14 random-baseline evidence run 更新了本最终包的 reader-facing 主线：demo 的核心 claim 现在是“Barcarolle 已经是一个实用的目标仓库预测式 Agent 评估设施”，主量化依据是 candidate benchmark selection 明显低于同预算随机抽样的未来 pass-rate MAE，并配合真实 Agent-selection matrix。

新主结果：

- timeout policy 已加倍：adapter `1800s`，cleanup grace `60s`，outer workspace `1860s`，verifier `360s`，endpoint/proxy upstream `3600s`。
- random same-budget baseline：candidate `coverage_constrained_unweighted` MAE `0.209011`，random baseline MAE `0.252499`，absolute improvement `0.043488`，relative improvement `17.22%`；1000-seed distribution 中 candidate 优于或打平 `93.4%` 随机样本。
- Kilo doubled-timeout reliability gate：`1` 个新 smoke/debug paid cell，`verified_pass`，无 timeout。
- doubled-timeout top-2 repeat：`20/20` scoreable；Codex + GPT mainline `6/10`，Kilo + GPT mainline `9/10`。
- 新 paid cells：`21`，未超过 runbook `42` cell cap。

因此，旧 `900s` Kilo repeat timeout 不再阻断 demo story。它仍是历史 caveat，但当前 `boltons` top-2 reliability-gated evidence leader 是 `Kilo + GPT mainline`。这不是全局 Agent 排名，也不是 predictive validity proof。

新的 reader-facing 入口：

- `experiments/agent_selection_demo/reports/demo_predictive_facility_story_zh.md`
- `experiments/agent_selection_demo/reports/random_baseline_predictive_signal_zh.md`
- `experiments/agent_selection_demo/reports/demo_agent_selection_evidence_zh.md`
- `experiments/agent_selection_demo/reports/doubled_timeout_policy_zh.md`
- `experiments/agent_selection_demo/reports/doubled_timeout_agent_reliability_gate_zh.md`

这个 demo 在 `mahmoud/boltons` 上完成了一次端到端的目标仓库 Agent 选型流程：同一批仓库历史任务交给 4 个真实 Coding Agent 配置，系统捕获每次运行产生的代码 diff，再在干净验证工作区重放并运行隐藏验证。

选择集的冻结推荐是 `Codex + GPT mainline`。但这个推荐不是质量单独领先：`Codex + GPT mainline` 和 `Kilo + GPT mainline` 在 20 个选择集任务上同为 `15/20` verified pass。推荐锁定到 Codex，主要来自成本破平；后续诊断发现 Codex 有 observed token usage，Kilo 只有保守单次估算，所以这不是可比的真实成本证据。

留出检查给出了 demo 的关键结果：原推荐在新任务上被反转。`Kilo + GPT mainline` 在 10 个留出任务上是 `9/10`，`Codex + GPT mainline` 是 `5/10`。因此，本 demo 支持的结论不是“谁全局更强”，而是：目标仓库 Agent 选型必须有冻结推荐后的新任务检查、成本口径审计和适配器可靠性门禁。

后续 top-2 repeatability check 没有变成新的排名结果。Codex 在同一批留出任务 repeat 为 `7/10`；Kilo 的 repeat 路径累计 3 个 900 秒 timeout。strict completion pass 在修补 timeout hygiene 和 usage parser 后尝试了 1 个新的 Kilo repeat cell，仍然 timeout，并按 stop-on-unscoreable guard 停止。当前 repeat 是 `13/20` completed cells、`10/20` scoreable cells。这说明 Kilo repeat 路径仍是 infrastructure blocker，不能说明 Kilo 的 holdout 领先稳定，也不能推翻第一轮 demo 的端到端价值。

Predictive-validity completion pass 补上了原来缺失的 north-star layer。现在 demo 有冻结 estimand、rolling-origin/pseudo-future window inventory、evaluation CLI、no-paid retrospective metrics、bounded paid-pilot decision 和 reader-facing story。核心 no-paid 结果是：best Barcarolle candidate `coverage_constrained_unweighted` MAE `0.209011`，best simple baseline `temporal_recent_baseline` MAE `0.214900`，candidate 小幅领先 `0.005889` MAE；两者 catastrophic miss rate 都是 `0.555556`。这只能 claim directional retrospective traction，不能 claim predictive validity 已经证明。

## Demo 问题

本 demo 回答一个很窄的问题：

> 对一个目标仓库和一组候选 Coding Agent 配置，Barcarolle 能否用同一批仓库任务比较它们，锁定一个选择集推荐，并用新留出任务检查这个推荐是否仍然合理？

它不回答这些问题：

- 哪个 Agent 在一般意义上更强；
- 哪个模型家族更适合所有代码任务；
- 任务选择方法是否已经具备长期预测有效性；
- Kilo 在 `boltons` holdout 上的领先是否稳定。

## 测试了什么

目标仓库：`mahmoud/boltons`。

任务来源：仓库历史中的真实改动。每个任务都有实现文件和测试文件变化；系统从测试变化构造隐藏验证，并在干净工作区检查 reference patch、no-op 和 Agent diff。

冻结任务划分：

| 部分 | 任务数 | 用途 |
| --- | ---: | --- |
| smoke tasks | 1 | 先检查候选 Agent 和验证链路能跑通 |
| selection tasks | 20 | 产生并锁定选择集推荐 |
| holdout tasks | 10 | 推荐锁定后的一次新任务检查 |

候选 Agent：

| Agent | 运行方式 | 模型 |
| --- | --- | --- |
| Codex + GPT mainline | codex | `gpt-5.4` |
| Kilo + GPT mainline | kilo | `gpt-5.4` |
| Kilo + GPT low-cost | kilo | `gpt-5.4-mini` |
| Kilo + Claude Sonnet | kilo | `claude-sonnet-4-6` |

## 系统实际做了什么

```mermaid
flowchart LR
    A["certified boltons task pool"] --> B["freeze selection / holdout split"]
    B --> C["run 4 Agents on selection tasks"]
    C --> D["capture each final diff"]
    D --> E["replay diff in clean verifier workspace"]
    E --> F["lock selection recommendation"]
    F --> G["run holdout tasks"]
    G --> H["compare recommendation with fresh outcomes"]
    H --> I["post-demo diagnostics and top-2 repeat blocker"]
```

关键约束：

- 每个 scoreable diff 都在干净验证工作区重放；
- hidden verifier material 只进入验证工作区；
- selection 和 holdout 之间不调 prompt、工具、模型或任务；
- 成本字段区分 observed token estimate 和 conservative per-cell estimate；
- 未提交的完整日志、工作区和 provider 会话明细不是读者理解报告所需材料。

## 核心结果

选择集：

| Agent | verified pass | scoreable | 成本口径 | 中位延迟秒 |
| --- | ---: | ---: | --- | ---: |
| Codex + GPT mainline | 15/20 | 20/20 | observed token estimate | 101.048 |
| Kilo + GPT mainline | 15/20 | 20/20 | conservative estimate | 48.297 |
| Kilo + Claude Sonnet | 14/20 | 18/20 | conservative estimate | 79.561 |
| Kilo + GPT low-cost | 13/20 | 18/20 | conservative estimate | 50.696 |

原始 selection lock 推荐：`Codex + GPT mainline`。

修正后的解释：质量视图应把 `Codex + GPT mainline` 和 `Kilo + GPT mainline` 视为 tied top；production-value 视图应标为 cost-inconclusive，而不是用不可比估算成本强行给单一成本赢家。

留出检查：

| Agent | verified pass | scoreable | 中位延迟秒 |
| --- | ---: | ---: | ---: |
| Kilo + GPT mainline | 9/10 | 10/10 | 47.921 |
| Kilo + Claude Sonnet | 8/10 | 10/10 | 275.456 |
| Kilo + GPT low-cost | 6/10 | 10/10 | 52.400 |
| Codex + GPT mainline | 5/10 | 10/10 | 110.617 |

留出结论：`contradicts`。这说明冻结推荐没有在 fresh holdout 上保持合理，而不是说明 Kilo 已经被证明为稳定赢家。

## 诊断结果

选择集推荐的脆弱点：

- top-2 质量打平：Codex GPT mainline 和 Kilo GPT mainline 都是 `15/20`；
- top-2 scoreable cell 都是 `20/20`；
- top-2 hidden verifier failure 都是 `5`；
- 原推荐依赖成本破平；
- Codex usage 覆盖为 `20/20`，Kilo usage 覆盖为 `0/20`，所以成本字段跨运行方式不可比。

selection/holdout 反转的最可解释原因是任务 split 差异：

| 维度 | selection | holdout | 含义 |
| --- | ---: | ---: | --- |
| 任务数 | 20 | 10 | 满足最小 demo split |
| `canonical_history` 任务 | 6 | 9 | holdout 明显更偏后期 history 任务 |
| 年份中位数 | 2018.5 | 2023 | holdout 更新 |
| Kilo GPT 在 holdout history 上 |  | 8/9 | later history 上明显领先 |
| Codex GPT 在 holdout history 上 |  | 4/9 | 原推荐在该子集上较弱 |

top-2 repeatability check 的结果：

| 项目 | 结果 |
| --- | --- |
| frozen repeat 计划 | Codex GPT mainline 与 Kilo GPT mainline 各跑同一批 10 个 holdout tasks |
| 已完成 cells | 13/20 |
| 可评分 cells | 10/20 |
| Codex repeat | 7/10 scoreable |
| Kilo repeat | 0/0 scoreable，3 个 adapter/CLI timeout |
| 解释 | infrastructure blocker，不是 ranking result |

Strict completion pass 进一步完成了这些 mandatory outputs：

- `kilo_timeout_usage_root_cause_zh.md`：旧 Kilo timeout rows 由 endpoint/proxy 500 retry path 与 timeout hygiene 缺口共同暴露；新修补让 adapter timeout 能更干净地记录。
- `top2_repeat_completion_zh.md`：preflight 和 smoke gate 通过后，1 个新增 Kilo repeat cell 仍 timeout，repeat 仍 blocked。
- `second_repo_gate_zh.md`：`python-attrs/attrs` supply 在 overlay 后达到 31 release-eligible，但当前 demo CLI 仍需 attrs target profile、repo_id/statement 泛化和 verifier pinning，不能立即启动 paid second-repo matrix。
- `agent_tuning_feedback_summary_zh.md`：现在可由 CLI 从 sanitized artifacts 生成 tuning feedback summary；它是反馈输入，不是 tuning 效果证明。

## 可以直接放进 slide 的表

| 读者问题 | Demo 证据 | 一句话结论 |
| --- | --- | --- |
| 系统能比较完整 Agent 吗？ | 4 个 Agent、80 个 selection cells、40 个 holdout cells | 能，且每个 scoreable diff 都做了干净验证重放 |
| 冻结推荐有用吗？ | selection lock 先于 holdout | 有用，因为它让 holdout contradiction 可审计 |
| 推荐稳定吗？ | holdout 中 Kilo 9/10、Codex 5/10 | 这次不稳定，fresh holdout 暴露了反转 |
| 成本能破平吗？ | Codex usage observed，Kilo usage missing | 当前不能，production-value 应标为 cost-inconclusive |
| repeat 给出新排名了吗？ | Kilo repeat timeout，scoreable gate 失败 | 没有，Kilo repeat 是工程 blocker |

## 产品相关性

这个 demo 对 Agent 选型的价值在于：它把“某个 Agent 看起来更好”拆成了可审计证据，包括任务来源、选择集表现、留出表现、失败类型、成本口径和延迟。工程团队可以用这种包判断一次选型是否足够可信，或者是否需要更多 repeat、更多仓库、真实账单成本或 adapter 修复。

这个 demo 对 Agent tuning 的价值在于：它产生了可验证失败标签和 per-task pass/fail delta。例如，Codex 在若干后期 `canonical_history` holdout 任务上失败，而 Kilo GPT mainline 在第一轮通过；Kilo repeat 又暴露 adapter timeout。这些信号可以进入配置改进 backlog，但不能被表述为 tuning 已经改善了 Agent。

## Predictive-validity layer

本次 completion 新增的测量目标是：

> benchmark selection 在历史 origin 处对完整 Agent 未来目标仓库 verified pass rate 的预测准确度。

可运行命令：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py predictive-validity-feasibility --output experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md
```

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py rolling-origin-eval --protocol experiments/agent_selection_demo/results/predictive_validity_protocol.json --window-inventory experiments/agent_selection_demo/results/predictive_validity_window_inventory.json --output experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
```

No-paid retrospective summary:

| Metric | Value |
| --- | ---: |
| metric slices | `208` |
| best simple baseline MAE | `0.214900` |
| best Barcarolle candidate MAE | `0.209011` |
| candidate minus best simple MAE | `-0.005889` |
| rank top-agreement rate | `0.8125` |
| mean recommendation regret | `0.041552` |
| new paid cells for predictive completion | `0` |

Paid pilot decision: no new paid cells were needed for the demo story. A future pilot plan is capped at `40` cells, but it was not executed.

## 最终 claim boundary

可以 claim：

- 在 `mahmoud/boltons` 上，Barcarolle 完成了一次真实 Coding Agent 选型 demo；
- 系统能运行候选 Agent、捕获 diff、在干净工作区验证、记录质量/成本/延迟/失败类型；
- 原 selection 推荐被 fresh holdout contradicted；
- rolling-origin/pseudo-future tooling 现在能计算 MAE、RMSE、rank agreement 和 recommendation regret，并与 simple baselines 比较；
- no-paid retrospective result 对 `coverage_constrained_unweighted` 给出小幅 directional traction；
- 这说明目标仓库 Agent 选型需要 holdout check、成本口径审计、uncertainty/repeatability 报告、adapter 可靠性门禁和 predictive-validity validation。

不能 claim：

- predictive validity 已经被证明；
- Kilo、Codex、GPT 或 Claude 在一般意义上更强；
- Kilo 的 holdout 领先稳定；
- top-2 repeatability check 得到了有效排名；
- 第二仓库 paid scoring 已经通过 gate；
- no-paid retrospective result 等同于 future proof；
- bounded paid predictive-validity pilot 已经执行；
- learned selector 或 Agent tuning 已经产生效果。

## 推荐下一步

最合适的下一步不是扩大矩阵，也不是马上做第二仓库 paid scoring，而是把后续问题分清：

| 要强化的 claim | 下一步 |
| --- | --- |
| presentation-ready demo story | 使用本最终包作为主材料，top-2 timeout 放在 caveat/appendix |
| Kilo holdout lead 是否稳定 | 修复 Kilo adapter timeout 和 usage normalization 后，重复同一 frozen top-2 holdout batch |
| 系统是否能跨仓库工作 | no-paid attrs gate 已完成；先修 attrs target profile、repo_id 泛化和 verifier pinning，再讨论 paid second-repo matrix |
| Agent tuning 产品故事 | 使用 runnable feedback generator 输出 per-Agent failures、unstable tasks、infra blockers 和 usage coverage；不声称 tuning 已完成 |
| predictive validity proof | 执行真正 future 或 strict preregistered rolling-origin validation，冻结任务、Agent、baselines、score-join 规则和 success threshold 后再看 outcomes |

## Claim 到 artifact 的映射

| Claim | Artifact |
| --- | --- |
| repository gate 和任务池可用 | `experiments/agent_selection_demo/reports/repository_gate.md`；`experiments/agent_selection_demo/results/repository_gate.json` |
| frozen split | `experiments/agent_selection_demo/results/frozen_split.json` |
| selection 运行结果 | `experiments/agent_selection_demo/results/selection_metrics.json`；`experiments/agent_selection_demo/results/selection_score_table.csv` |
| 原始 recommendation lock | `experiments/agent_selection_demo/results/recommendation_lock.json`；`experiments/agent_selection_demo/reports/recommendation_lock.md` |
| holdout contradiction | `experiments/agent_selection_demo/results/holdout_check.json`；`experiments/agent_selection_demo/results/holdout_metrics.json` |
| 成本/usage 口径诊断 | `experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md` |
| top-2 repeat blocker | `experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`；`experiments/agent_selection_demo/results/top2_repeatability_check.json` |
| Kilo timeout root cause | `experiments/agent_selection_demo/reports/kilo_timeout_usage_root_cause_zh.md` |
| strict repeat completion/blocker | `experiments/agent_selection_demo/reports/top2_repeat_completion_zh.md` |
| second-repo no-paid gate | `experiments/agent_selection_demo/reports/second_repo_gate_zh.md` |
| runnable tuning feedback | `experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md`；`experiments/agent_selection_demo/results/agent_tuning_feedback_summary.json` |
| predictive-validity state audit | `experiments/agent_selection_demo/reports/predictive_validity_state_audit_zh.md`；`experiments/agent_selection_demo/results/predictive_validity_evidence_ledger.json` |
| frozen predictive-validity protocol | `experiments/agent_selection_demo/reports/predictive_validity_protocol_zh.md`；`experiments/agent_selection_demo/results/predictive_validity_protocol.json` |
| rolling-origin feasibility | `experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md`；`experiments/agent_selection_demo/results/predictive_validity_window_inventory.json` |
| rolling-origin evaluation | `experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md`；`experiments/agent_selection_demo/results/rolling_origin_eval.json`；`experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv` |
| no-paid retrospective result | `experiments/agent_selection_demo/reports/predictive_validity_retrospective_result_zh.md` |
| paid-pilot decision | `experiments/agent_selection_demo/reports/predictive_validity_paid_pilot_decision_zh.md`；`experiments/agent_selection_demo/results/predictive_validity_paid_pilot_plan.json` |
| predictive-validity reader story | `experiments/agent_selection_demo/reports/predictive_validity_demo_story_zh.md` |
| 当前最终解释 | `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md` |
