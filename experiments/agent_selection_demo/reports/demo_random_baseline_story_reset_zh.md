# Demo 随机基线故事重置

生成日期：2026-06-14

## 当前 demo claim

Barcarolle 现在可以作为一个目标仓库 Agent 评估 demo：它能在同一目标仓库里选 benchmark tasks、运行完整 Agent、捕获 diff、在干净验证工作区重放验证，并用这些任务对之后任务的 pass rate 做预测检查。

这次故事的主证据不是“predictive validity 已经证明”，也不是“当前 selector 稳定打过所有简单方法”。更合适的 demo claim 是：

> Barcarolle 已经具备实用的目标仓库预测式 Agent 评估能力；当前可提交的数字证据显示，Barcarolle candidate 对未来 pass rate 的预测 MAE 明显低于同预算随机抽样。

## 随机基线主比较

主比较读取已提交 sanitized artifact：

- `experiments/agent_selection_demo/results/rolling_origin_eval.json`
- `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv`

| 项目 | 数值 |
| --- | ---: |
| Candidate design | `coverage_constrained_unweighted` |
| Candidate MAE | `0.209011` |
| Random same-budget baseline MAE | `0.252499` |
| Absolute MAE improvement | `0.043488` |
| Relative MAE improvement | `17.22%` |
| Candidate slices | `18` |
| Random baseline slices | `90` |

MAE 是 `abs(benchmark pass rate - later task pass rate)` 的平均值，越低说明选择集越接近之后任务表现。

按 runbook 的 demo 成功门槛，candidate 相比随机基线降低 `0.043488` MAE，超过 `0.02` absolute improvement；相对降低 `17.22%`，超过 `10%` relative improvement。因此当前随机基线比较通过 demo gate。

## 随机 seed 分布

随机 seed 分布可用，但来自较早的 proposal evidence package：

- `experiments/phase1_compiler/reports/phase1_proposal_evidence_package_random_baseline_distribution.md`
- `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json`

总体分布：

| 项目 | 数值 |
| --- | ---: |
| Seed count | `1000` |
| Random median MAE | `0.2464` |
| Random p05 MAE | `0.2056` |
| Random p95 MAE | `0.2899` |
| Candidate MAE in distribution artifact | `0.2090` |
| Candidate beats/random-ties share | `93.4%` |
| Lower-is-better percentile | `6.6` |

这说明 candidate 不只是好于五个随机 seed 的聚合均值；在 1000 个同预算随机样本中，它处在低误差端。但这个分布是 retrospective traction，不是未来验证证明。

## 可支撑故事的现有 artifact

| Artifact | 用途 |
| --- | --- |
| `rolling_origin_eval.json` | 读取 candidate、random baseline、best simple baseline 的主 MAE/RMSE/miss-rate 指标 |
| `rolling_origin_eval_slices.csv` | 审计每个 repo/window/Agent/design slice 的 selection/future pass rate 与误差 |
| `rolling_origin_eval_zh.md` | 已有人读 summary，可作为附录 |
| `phase1_proposal_evidence_package_random_baseline_distribution.json` | 1000-seed 随机分布、candidate percentile、seed count |
| `final_agent_selection_demo_package_zh.md` | 完整 Agent 执行、selection/holdout matrix、验证链路和 caveats |
| `demo_completion_closeout_zh.md` | 上一轮 closeout、Kilo timeout blocker、测试和 hygiene 记录 |

## 仍需补齐的证据 gap

- timeout policy 仍需从旧 `900s` demo policy 升级并验证生成命令实际使用 `1800s`；
- 随机基线比较需要独立产出一份 reader-facing evidence packet，而不是埋在 predictive-validity story 里；
- Kilo 在 doubled timeout 下是否可评分需要重新做 reliability gate；
- Agent-selection matrix 需要用 reliability-gated 口径重新包装，不能隐藏 timeout/non-scoreable cells；
- final story 需要把随机基线放到主线，把 best-simple-baseline 和 catastrophic miss 放到 robustness/limitations。

## Claim boundary

Best-simple-baseline 结果是 robustness check，不是本次 demo 的主 gate。当前 best simple baseline `temporal_recent_baseline` MAE 是 `0.214900`，candidate 只小幅领先 `0.005889`；这个事实应保留在限制和附录里，避免把 demo 主线变成“勉强打过最强简单基线”。

不能 claim：

- predictive validity 已经被证明；
- 当前 selector 已经稳定优于所有简单 baseline；
- Kilo、Codex、GPT 或 Claude 有全局排名；
- 第二仓库或扩大模型矩阵已经完成。

本 package 未运行 paid calls。
