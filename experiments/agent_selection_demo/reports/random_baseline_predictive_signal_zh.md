# Random-baseline Predictive Signal

生成日期：2026-06-14

## 摘要

本 package 把 demo 的主量化证据重新放在同预算随机抽样比较上。所有数字都读取已提交的 sanitized artifacts；没有运行 paid Agent cells，也没有读取 raw prompts、raw completions、transcripts 或 solver/verifier workspaces。

主结论：

> `coverage_constrained_unweighted` 的未来 pass-rate 预测 MAE 是 `0.209011`，同预算随机基线 MAE 是 `0.252499`。Candidate 降低 `0.043488` MAE，相对改善 `17.22%`，通过 demo success gate。

MAE 是 `abs(benchmark pass rate - later task pass rate)` 的平均值；越低，说明 benchmark selection 对之后任务表现的预测越接近。

## 主比较：candidate vs random same-budget

| 指标 | Candidate | Random same-budget |
| --- | ---: | ---: |
| Design | `coverage_constrained_unweighted` | `seeded_random_same_budget` |
| MAE | `0.209011` | `0.252499` |
| RMSE | `0.258881` | `0.299514` |
| Signed error | `-0.043267` | `-0.035303` |
| Catastrophic miss rate | `0.555556` | `0.733333` |
| Slice count | `18` | `90` |
| Selection scoreable cells | `94` | `445` |
| Future scoreable cells | `249` | `1245` |

Improvement:

| 项目 | 数值 |
| --- | ---: |
| Absolute MAE improvement | `0.043488` |
| Relative MAE improvement | `17.22%` |
| Demo absolute threshold | `0.02` |
| Demo relative threshold | `10%` |
| Success gate | `pass` |

解释：candidate 比同预算随机抽样低 `0.043488` MAE，超过 runbook 要求的 `0.02` absolute improvement；相对降低 `17.22%`，也超过 `10%` relative improvement。因此这个 demo-level predictive-signal gate 通过。

## 随机分布和 percentile

当前 `rolling_origin_eval.json` 中的 random same-budget 指标是聚合 summary，包含 `90` 个 random slices。完整 seed 分布来自已提交的 phase1 proposal evidence package：

| 项目 | 数值 |
| --- | ---: |
| Seed count | `1000` |
| Random MAE mean | `0.2469` |
| Random MAE median | `0.2464` |
| Random MAE p05 | `0.2056` |
| Random MAE p25 | `0.2291` |
| Random MAE p75 | `0.2640` |
| Random MAE p95 | `0.2899` |
| Candidate MAE in that artifact | `0.2090` |
| Candidate beats/random-ties share | `93.4%` |
| Lower-is-better percentile | `6.6` |

这个 percentile 说明 candidate 位于 1000 个同预算随机样本的低误差端。它仍然是 retrospective traction，不是未来 predictive-validity proof。

## Best-simple-baseline robustness note

Best-simple-baseline 不是本 demo 的主 gate，但需要保留为 robustness check：

| 指标 | Candidate | Best simple baseline |
| --- | ---: | ---: |
| Design | `coverage_constrained_unweighted` | `temporal_recent_baseline` |
| MAE | `0.209011` | `0.214900` |
| RMSE | `0.258881` | `0.257954` |
| Catastrophic miss rate | `0.555556` | `0.555556` |
| Candidate minus best-simple MAE | `-0.005889` |  |

这个比较只能说明 candidate 对最强简单 baseline 有小幅 MAE 优势，且 catastrophic miss rate 没改善。它是限制和稳健性信息，不应压过随机基线主结果。

## Reproducibility inputs

| Artifact | SHA-256 | 用途 |
| --- | --- | --- |
| `experiments/agent_selection_demo/results/rolling_origin_eval.json` | `1dfc33c3e9b21717bd12dbc273e3ef00d23b39449f433c5164001e92056d98ad` | 当前 rolling-origin summary |
| `experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv` | `c39c1f1cca5aaba02d2bea490557f5c9f08c3e9282f2ee17c6d3e8039a562e1b` | slice-level audit |
| `experiments/phase1_compiler/results/phase1_proposal_evidence_package_random_baseline_distribution.json` | `ded7433d2662bfc608abc56b63ca609fd731900917d3ebbafe76d51ed98353c7` | 1000-seed random distribution |

## Claim boundary

可以 claim：

- Barcarolle candidate 在当前 retrospective/pseudo-future evidence 中明显打过同预算随机抽样；
- improvement 同时通过 `0.02` absolute MAE 和 `10%` relative MAE demo gate；
- 随机 seed 分布可用，candidate 位于低误差端。

不能 claim：

- predictive validity 已经证明；
- selector 稳定打过所有简单 baseline；
- 这个结果可直接推广到所有仓库、所有 Agent 或所有模型；
- old paid result rows 是在 `1800s` timeout 下产生的。
