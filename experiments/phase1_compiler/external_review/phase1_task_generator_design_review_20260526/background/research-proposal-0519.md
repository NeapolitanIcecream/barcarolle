# Barcarolle 重启版项目提案

## 0. 核心定位

**Barcarolle 是一个 repo-specific benchmark compiler，而不是又一个 SWE task generator。**

更精确地说：

> Barcarolle 把仓库历史、候选任务池、真实工作分布、agent family、评估预算和调优目标，编译成一套经过选择、加权、切分、校准和版本化的 repo-specific benchmark release，用于预测和提升 agent 在目标仓库上的后续工作表现。

这个定位抛弃旧叙事里的三个包袱：

第一，不再把项目核心放在 **agent admission / license**。那可以作为下游应用，但不是项目核心。

第二，不再试图证明 **ranking reversal**。排名只是多 agent 场景下的派生指标。

第三，不再把核心新意放在“我们能从 repo 生成任务”。SWE-Bench++、SWE-smith、SWE-bench-Live、R2E-Gym 这类工作已经把 task production 层做得很强。Barcarolle 的新意应该是：

> **从候选任务池中构造一个对目标仓库未来工作表现具有预测效度的 benchmark。**

一句话 thesis：

> Public SWE benchmarks and scalable task generators produce tasks; Barcarolle decides which tasks should become the benchmark for this repository, this agent family, this evaluation budget, and this tuning objective.

---

## 1. 背景与问题

过去两年，coding agent evaluation 已经从 HumanEval 式函数生成，转向 repository-level issue resolution。SWE-bench 是这个转向的代表：它从 12 个 Python 仓库的 issue/PR 中收集 2,294 个任务，并用 Docker 环境和 fail-to-pass tests 作为主要评估信号。([SWE-bench][1])

之后的工作沿着三个方向扩展：

一是让 benchmark 更可信、更抗污染。OpenAI 在 2026 年指出 SWE-bench Verified 已经越来越受污染，并且在其审计的 27.6% 常失败任务中，至少 59.4% 存在会拒绝功能正确解法的测试问题，因此建议转向 SWE-Bench Pro 等新评估。([OpenAI][2]) SWE-Bench Pro 则进一步引入 public、held-out 和 commercial 三个 split，包含 41 个活跃维护仓库的 1,865 个更长时程任务，其中 held-out 和 commercial set 不公开，以增强抗污染能力。([arXiv][3])

二是让 benchmark 更新、更大、更多语言。SWE-bench-Live 提出持续更新的 repository-level issue-resolution benchmark，初始版本包含 2024 年以来的 1,319 个任务，覆盖 93 个仓库，并用自动化 pipeline 构造可复现 Docker 环境。([arXiv][4]) Multi-SWE-bench 则把 issue resolving 扩展到 Java、TypeScript、JavaScript、Go、Rust、C、C++ 等语言，包含 1,632 个高质量实例。([arXiv][5])

三是把任务生成变成训练数据和环境生产。SWE-smith 能从任意 Python codebase 构造执行环境，并合成会破坏现有测试的任务实例；其数据用于训练 SWE-agent-LM-32B，在 SWE-bench Verified 上达到 40.2% Pass@1。([arXiv][6]) SWE-Gym、R2E-Gym 也把 executable SWE environments 用于训练 agent、verifier 或 test-time scaling。([arXiv][7]) SWE-Bench++ 更进一步：它从开源 GitHub PR 自动生成 repository-level coding tasks，覆盖 bug fixes 和 feature requests，经过 sourcing、environment synthesis、test oracle extraction、quality assurance 四阶段，初始数据集有 11,133 个实例、3,971 个仓库、11 种语言。([arXiv][8])

这些工作说明：**底层 task production 正在变成 commodity layer**。

但这也暴露出新的瓶颈：

> 给定一个具体目标仓库、一个具体 agent family、一个有限评估预算和一个实际调优目标，我们应该如何从大量候选任务中构造一套“小而准”的 repo-specific benchmark，使它能更好预测 agent 在这个仓库后续真实任务上的表现？

现有工作大多回答的是：

> 我们能不能生成更多、更真实、更难、更新、更可复现的 SWE tasks？

Barcarolle 要回答的是：

> 在这些 tasks 已经可以由多种来源产生的情况下，哪些 tasks 应该被选入这个 repo 的 benchmark？如何加权？如何切分 dev/eval/holdout？如何估计不确定性？如何用它指导 agent tuning？如何证明它比通用 benchmark 更能预测目标 repo 的后续表现？

---

## 2. 项目目标

Barcarolle 的目标不是成为新的 public leaderboard，也不是替代 SWE-Bench++ 这类 task factory。

Barcarolle 的目标是成为：

> **面向目标仓库的 benchmark construction、calibration 和 tuning feedback layer。**

输入：

```text
target repository r
time cutoff τ
candidate task sources S
agent family A
evaluation budget C
target work distribution assumptions T_r
tuning / evaluation objective O
```

输出：

```text
Barcarolle benchmark release B_{r,τ}
```

这个 release 不只是 task list，而是包含：

```text
task set
task weights
task strata / taxonomy
dev / eval / canary / holdout split
execution environments
oracle quality metadata
leakage / ambiguity / flakiness reports
score aggregation rule
uncertainty estimates
failure taxonomy
optimizer-readable reward schema
refresh policy
```

核心成功标准：

> Barcarolle-generated benchmark score 能在 held-out future repo work 上，比通用 benchmark score 或未校准任务池更低误差地预测 agent 表现；或者在已知通用 benchmark score 后，提供额外预测信号。

形式化地，目标仓库 `r` 的未来真实任务分布是 `T_r`，agent configuration 是 `a`。我们真正关心：

[
W_r(a) = \mathbb{E}_{x \sim T_r}[\mathrm{success}(a, x)]
]

通用 benchmark 给出：

[
G(a)
]

Barcarolle benchmark 给出：

[
B_r(a)
]

项目主张不是：

[
B_r \text{ 永远替代 } G
]

而是：

[
\mathrm{Err}(G(a), W_r(a)) > \mathrm{Err}(G(a), B_r(a), W_r(a))
]

也就是：

> Barcarolle 的 repo-specific benchmark 至少应当解释通用 benchmark 无法解释的 target-repo residual。

---

## 3. 为什么这是独立项目，而不是 SWE-Bench++ 包装

SWE-Bench++ 的贡献非常接近“自动生成 repository-level coding tasks”。它的论文明确说，SWE-Bench++ 是一个从开源 GitHub 项目自动生成 repository-level coding tasks 的框架，pipeline 覆盖 programmatic sourcing、environment synthesis、test oracle extraction 和 quality assurance，并且还把强模型解不出的实例转成 hint-guided training trajectories。([arXiv][8])

所以 Barcarolle 不能把新意放在：

> 我们也能自动从 repo 生成 benchmark tasks。

这个说法会和 SWE-Bench++ 正面重合。

Barcarolle 的独立性来自一个不同的问题定义：

| 层次               | SWE-Bench++ / SWE-smith 等                                  | Barcarolle                                               |
| ---------------- | ---------------------------------------------------------- | -------------------------------------------------------- |
| 核心对象             | task instances / training trajectories                     | calibrated benchmark release                             |
| 主要问题             | 如何大规模生产可执行 SWE tasks                                       | 如何为目标 repo 选择、加权、切分、校准 tasks                             |
| 优化目标             | yield、determinism、coverage、模型 baseline、fine-tuning utility | held-out target-repo predictive validity                 |
| 用户               | benchmark / training-data researchers                      | agent developers、repo owners、agent optimizer builders    |
| 输出形态             | dataset / task pool / trajectories                         | versioned benchmark pack + score model + tuning feedback |
| 是否依赖某个 generator | 是自己的 generation pipeline                                   | source-agnostic，可接 SWE-Bench++、SWE-smith、历史 PR、人工任务、私有任务 |
| 主要统计问题           | 任务能否被复现、验证、用于训练或评测                                         | benchmark score 是否能预测目标 repo 后续任务表现                      |

SWE-Bench++ 自己的 empirical validation 主要沿四个轴展开：pipeline yield and dataset properties、agent performance baselines、fine-tuning experiments、qualitative failure analysis。([arXiv][8]) 这非常合理，但它没有把“某个目标 repo 的 benchmark 应如何构造以预测该 repo 后续表现”作为中心问题。

Barcarolle 的研究问题可以定义为：

> **Benchmark assembly under target-repository covariate shift.**

也就是：当候选任务池很大、任务来源很多、目标仓库未来工作分布未知但可从历史估计、评估预算有限时，如何编译一套最有预测价值的 repo-specific benchmark？

---

## 4. 相关工作调研与对比

### 4.1 SWE-bench / SWE-bench Verified

SWE-bench 奠定了 repository-level issue resolution 的标准任务形式：给定 issue 描述和修复前代码库，agent 生成 patch，最终由隐藏测试判断是否解决。它的优势是任务真实、执行式验证、协议清晰。([SWE-bench][1])

限制在于：它是固定公共 benchmark，任务来自有限仓库集合；它衡量的是公共混合分布上的通用能力，而不是某个目标 repo 的未来工作表现。OpenAI 对 SWE-bench Verified 的 2026 年分析还说明，公共静态 benchmark 会面临污染、测试过窄/过宽和 gold patch 暴露等问题。([OpenAI][2])

Barcarolle 的关系：
SWE-bench 是 general prior；Barcarolle 是 target-repo estimator。Barcarolle 可以把 SWE-bench score 作为 baseline 或 covariate，但不把它当作目标仓库表现的充分统计量。

---

### 4.2 SWE-Bench Pro

SWE-Bench Pro 的目标是更真实、更长时程、更企业级、更抗污染。它包含 1,865 个问题，来自 41 个活跃维护仓库，并把任务分为 public、held-out、commercial 三个 split；商业集来自 18 个私有 startup repositories，问题和代码不公开。([arXiv][9])

它和 Barcarolle 的区别是：SWE-Bench Pro 仍然是统一 benchmark；Barcarolle 让每个目标 repo 自己生成和校准 benchmark。SWE-Bench Pro 适合回答“哪个 agent 在更真实的统一 SWE benchmark 上更强”；Barcarolle 适合回答“这个 agent 在我的 repo 后续工作上预计表现如何，应该如何调优”。

---

### 4.3 SWE-bench-Live

SWE-bench-Live 解决的是 static benchmark 的 freshness 和 contamination 问题。它持续从真实 GitHub issues 产生任务，初始发布包含 1,319 个 2024 年以来的任务，覆盖 93 个仓库，并通过 RepoLaunch 自动化环境构造和验证。([arXiv][4])

Barcarolle 可以借鉴它的时间切分、持续更新和自动环境构造思想。但 Barcarolle 不是再做一个 live global benchmark，而是把 freshness 用于每个目标 repo 的 release refresh 和 predictive validation。

---

### 4.4 SWE-smith

SWE-smith 的核心是 scalable training data。它能从任意 Python codebase 构造执行环境，合成大量会破坏现有测试的任务，并用这些任务训练 SWE-agent-LM-32B。([arXiv][6]) 它还做了 repository-specialized fine-tuning：在 SymPy-specific 生成数据上训练 specialist，并在 2022 年后的 SymPy SWE-bench Verified 子集上评估，发现单仓库 specialization 能显著提升目标仓库表现且只有轻微 generalization loss。([arXiv][6])

这对 Barcarolle 很重要，因为它提供了一个强旁证：

> repo-specific data 对目标 repo 行为确实可能有额外价值。

但 SWE-smith 的主要验证链是：

```text
repo-derived tasks -> training trajectories -> model improves on SWE-bench / same-repo eval
```

Barcarolle 的验证链是：

```text
repo-derived candidate tasks -> calibrated benchmark release -> predicts held-out same-repo work
```

前者是 training data utility，后者是 benchmark predictive validity。

---

### 4.5 SWE-Bench++

SWE-Bench++ 是最接近 Barcarolle 的相关工作。它已经大规模解决“从开源 PR 生成可执行 repository-level tasks”的问题：11,133 个实例，3,971 个仓库，11 种语言；它还报告了从 137,048 个 candidate PR 到 28,513 个环境/日志处理成功实例，再到 11,133 个 deterministic instances 的 yield funnel。([arXiv][8])

因此，Barcarolle 必须避免和 SWE-Bench++ 争夺底层 task factory 叙事。SWE-Bench++ 可以成为 Barcarolle 的一个上游 source adapter：

```text
SWE-Bench++ task pool
        ↓
Barcarolle compiler
        ↓
target-repo benchmark release
```

Barcarolle 的差异点不是“能不能生成 task”，而是：

```text
which tasks
for which repo
with what weights
for which agent family
under what budget
validated against which future-work target
used for which tuning objective
```

---

### 4.6 SWE-Gym / R2E-Gym / Multi-SWE-bench

SWE-Gym 把真实 SWE tasks 和 executable environments 用于训练 agent 和 verifier，并在 SWE-bench Verified / Lite 上取得 open-weight agent 提升。([arXiv][7]) R2E-Gym 也强调大规模 procedural executable environments 和 hybrid verifier，用于训练 open-weight SWE agents 和 test-time scaling。([arXiv][10]) Multi-SWE-bench 则解决多语言 issue resolving 的覆盖问题。([arXiv][5])

它们都说明 repository-level task environments 已经成为训练和评估 SWE agents 的关键基础设施。Barcarolle 的机会在于：这些环境和任务池生产出来之后，仍然需要一个 target-repo benchmark compiler 来服务具体 repo 的评估和调优。

---

### 4.7 DSPy、SkVM 和 agent tuning 框架

DSPy 的定位是从 prompt tinkering 转向 structured / declarative natural-language modules，并通过 optimizers 改进 prompts、weights、RAG pipelines 和 agent loops。([DSPy][11]) SkVM 则把 skills 放进可编译、可优化的 language VM，支持 profiling、AOT compilation、JIT optimization 和 benchmark；其论文在多个模型和 agent harness 上评估 skills，报告任务完成率提升和 token / latency 下降。([GitHub][12])

这类系统需要的不是一个单一 leaderboard 分数，而是：

```text
repo-specific dev set
repo-specific eval set
failure labels
reward / metric schema
cost-performance feedback
regression holdout
```

Barcarolle 可以成为这类 optimizer 的 target-repo feedback substrate。

---

## 5. Barcarolle 的核心方法

### 5.1 总体架构

Barcarolle 分为六个层次：

```text
Layer 1: Task Source Adapters
Layer 2: Task Certification
Layer 3: Target Work Distribution Modeling
Layer 4: Benchmark Assembly & Weighting
Layer 5: Score Calibration & Uncertainty
Layer 6: Tuning / Evaluation Interfaces
```

这六层共同完成从“候选任务”到“可用 benchmark release”的编译。

---

### 5.2 Layer 1：Task Source Adapters

Barcarolle 不绑定某一个 task generator。它应该支持多源候选任务：

```text
historical issue/PR tasks
SWE-Bench++ tasks
SWE-smith-style synthetic tasks
SWE-Gym / R2E-Gym-like tasks
manual or expert-authored tasks
customer-provided regression tasks
mutation / procedural tasks
future canary tasks
```

每个 source adapter 输出统一格式：

```yaml
task_id:
source_type:
repo:
base_commit:
task_time:
problem_statement:
patch_reference_optional:
test_oracle:
environment:
changed_files:
candidate_labels:
source_confidence:
known_leakage_risks:
```

这样做的意义是：Barcarolle 的核心价值不被 task factory 技术锁死。SWE-Bench++ 越强，Barcarolle 的上游候选池越丰富。

---

### 5.3 Layer 2：Task Certification

候选任务不能直接进入 benchmark release。Barcarolle 需要自己的 task certification protocol，重点不是提高 yield，而是保证 task 对预测和调优有用。

Certification gates 包括：

```text
replayability: base commit 可 checkout，环境可构建
oracle validity: no-op fail、reference pass、known-bad fail
flakiness: 多次运行稳定
ambiguity: 问题描述不过度欠定
solution leakage: issue / comments / docs 不直接泄露解法
scope clarity: task 边界明确，不混入无关变更
cost boundedness: 运行时间和资源消耗可控
feature taxonomy: 可标注模块、任务类型、难度和 failure category
```

这里可以吸收 SWE-Bench++、SWE-Bench+、OpenAI 对 SWE-bench Verified 的经验：仅有“测试能跑”不等于 benchmark task 可信，测试可能过窄、过宽、弱验证或泄露解法。SWE-Bench+ 曾指出 SWE-bench 中存在 solution leakage 和 weak tests 问题，OpenAI 后续也指出 SWE-bench Verified 的剩余任务中存在测试设计和污染问题。([arXiv][13])

Barcarolle 的 task certification 目标不是做最大规模 dataset，而是做 target-repo benchmark 的可信输入。

---

### 5.4 Layer 3：Target Work Distribution Modeling

这是 Barcarolle 和 task factories 的核心分界线。

Barcarolle 需要估计目标仓库未来工作分布 `T_r`。这个分布无法直接观察，但可以从历史数据、近期 PR、issue taxonomy、maintainer workflow 和用户指定目标中估计。

可建模特征包括：

```text
module / package / directory
task type: bug fix, feature, refactor, dependency, test, docs
change size: files changed, lines changed, functions touched
test type: unit, integration, snapshot, property, e2e
code locality: single-file vs cross-module
dependency graph radius
issue text style
API surface
runtime / platform constraints
review convention
frequency over time
risk / business relevance, optional
```

目标不是完美恢复真实分布，而是产生一个明确的、可审计的 `target profile`：

```yaml
target_profile:
  repo: target/repo
  cutoff: 2026-05-01
  horizon: next_90_days
  strata:
    parser_bugfix: 0.18
    cli_behavior: 0.12
    docs_tests: 0.10
    dependency_compat: 0.08
    ...
  confidence:
    parser_bugfix: high
    dependency_compat: low
```

这个 profile 之后用于 benchmark assembly 和 score weighting。

---

### 5.5 Layer 4：Benchmark Assembly & Weighting

给定候选任务池 `S`、目标分布 `T_r` 和预算 `C`，Barcarolle 要选择一个 benchmark release：

[
B_{r,\tau} = \operatorname{Compile}(S, T_r, A, C, O)
]

其中 `A` 是目标 agent family，`O` 是评价或调优目标。

Assembly 策略可以从简单到复杂：

#### Baseline 0：random same-budget

从候选任务池随机抽 `n` 个任务。

#### Baseline 1：stratified sampling

按目标分布 `T_r` 的 strata 抽样。

#### Baseline 2：coverage-constrained selection

在预算内最大化模块、任务类型、难度、测试类型覆盖。

#### Barcarolle v1：weighted benchmark

允许 benchmark task distribution 和 target distribution 不完全一致，但给每个 task 分配权重，使最终 score 是目标分布下的估计：

[
\hat{W}*r(a) = \sum_s \pi_s \hat{p}*{a,s}
]

其中 `s` 是 task stratum，`\pi_s` 是目标仓库未来任务分布权重，`\hat{p}_{a,s}` 是 agent 在该 stratum 上的表现估计。

#### Barcarolle v2：information-aware selection

当已知 agent family 时，选择最能降低预测不确定性的任务。例如，如果两个 candidate tasks 都覆盖 parser bugfix，但一个任务对 agent 失败模式更有区分力，就优先选后者。

#### Barcarolle v3：active benchmark refinement

先用小 benchmark 跑 agent，观察 failure modes，再补充任务以减少不确定性或覆盖残差最大的 strata。

---

### 5.6 Layer 5：Score Calibration & Uncertainty

Barcarolle 的输出不能只是：

```text
Agent A: 63%
Agent B: 58%
```

更应该输出：

```text
Agent A estimated target-repo pass rate:
  0.63 ± 0.08
  parser_bugfix: 0.52 ± 0.13
  cli_behavior: 0.71 ± 0.10
  dependency_compat: insufficient evidence
```

可用的统计层包括：

```text
binomial confidence intervals
Bayesian beta-binomial estimates
hierarchical model across strata
bootstrap over tasks
calibration curves
Brier score / negative log likelihood on held-out windows
```

这会让 Barcarolle 的 benchmark 更像一个 estimator，而不是一个排行榜。

---

### 5.7 Layer 6：Tuning / Evaluation Interfaces

Barcarolle 输出要能被 agent tuning 系统消费。

对 DSPy-style optimizer，输出：

```text
train/dev examples
metric function
failure labels
per-task reward
trace evaluator
compiled prompt comparison report
```

对 SkVM-style skill compiler，输出：

```text
skill effectiveness benchmark
before/after compiled skill comparison
token/cost/latency metrics
failure taxonomy
cross-harness comparison
```

对一般 agent framework，输出：

```text
agent run manifest
patch application result
test result
cost and latency
tool-use trace
localization quality
regression status
```

这使 Barcarolle 不只是“评测一次”，而是成为 repo-specific optimization loop 的反馈基建。

---

## 6. Barcarolle 的输出物

一个 Barcarolle release 应该长这样：

```text
barcarolle-release/
  manifest.yaml
  target_profile.yaml
  task_index.jsonl
  tasks/
    TASK-001/
      problem.md
      base.patch
      reference.patch.optional
      oracle.yaml
      env.lock
      metadata.yaml
    ...
  splits/
    dev.json
    eval.json
    canary.json
    holdout.json
  weights/
    target_weights.yaml
    score_aggregation.py
  certification/
    replay_report.json
    flakiness_report.json
    leakage_report.json
    oracle_quality_report.json
  results/
    agent_runs/
    scorecards/
  tuning/
    dspy_metric.py
    skvm_benchmark.yaml
    reward_schema.json
```

核心 manifest 示例：

```yaml
release_id: barcarolle-click-2026q2-v0.1
target_repo: pallets/click
cutoff_time: 2026-04-01
target_horizon: 2026-Q2
task_sources:
  - github_pr_history
  - swebenchpp_adapter
  - manual_canary
benchmark_budget:
  eval_tasks: 40
  dev_tasks: 20
  canary_tasks: 10
target_objective:
  primary: predict_heldout_pass_rate
  secondary:
    - tune_repo_skill
    - identify_failure_modes
score_model:
  type: weighted_stratified_beta_binomial
quality_gates:
  replayability: required
  no_op_fail: required
  reference_pass: required
  flakiness_max: 0.02
  leakage_check: required
```

---

## 7. 研究验证计划

Barcarolle 的验证应该分阶段，不要求项目一开始就证明最终 claim。

### Phase 0：立项前 headroom evidence

目标：证明 repo-specific benchmark signal 值得生成。

#### 实验 0.1：distribution mismatch audit

比较通用 benchmark 分布 `Q` 和目标 repo 后续 work 分布 `T_r`：

```text
module distribution divergence
change-type divergence
diff-size divergence
test-type divergence
issue-text embedding distance
dependency locality
```

输出：

> 目标 repo 的真实工作分布与公共 benchmark 混合分布存在可测差异。

#### 实验 0.2：oracle repo-specific headroom

使用已有历史任务，不依赖 Barcarolle 自动生成：

```text
early same-repo tasks -> B_real
late same-repo tasks  -> W_real
general benchmark     -> G
```

比较：

```text
G -> W_real
G + B_real -> W_real
```

如果 early same-repo tasks 能解释 general benchmark score 的 residual，就说明“repo-specific signal 本身有价值”。

#### 实验 0.3：task supply funnel

对若干 repo 的 historical PR / issue anchors 做候选任务 funnel：

```text
candidate anchors
↓
replayable checkouts
↓
environment build success
↓
oracle extractable
↓
no-op fail / reference pass
↓
low-flakiness tasks
↓
benchmark-grade tasks
```

输出：

> 目标 repo 历史中存在足够可转换为 benchmark 的材料；同时也说明需要 compiler / certification，而不是随便拿 PR。

---

### Phase 1：MVP benchmark compiler

目标：在不从零实现 task factory 的情况下，做出 Barcarolle 的核心 release。

做法：

```text
input: historical tasks + external generated tasks + manual canaries
process: certification + target profile + selection + weighting
output: benchmark release v0.1
```

最小目标：

```text
3 repos
每个 repo 20–50 个 eval tasks
至少 2 个 task sources
dev/eval/canary split
weighted scoring
basic uncertainty interval
```

评估：

```text
single ACUT pass-rate prediction
multiple time windows
MAE / RMSE / binomial NLL
calibration interval coverage
```

单个 ACUT 也可以做，因为目标不是 ranking，而是 pass-rate forecast：

[
|\hat{W}_{B_r}(a) - W_r(a)|
]

---

### Phase 2：multi-ACUT residual predictive validity

目标：证明 Barcarolle score 在已知通用 benchmark score 后仍有增量预测价值。

ACUT 选择要避免“强模型 vs 弱模型”的 obvious gradient，应该使用 paired configurations：

```text
same model + generic prompt
same model + repo docs skill
same model + repo history retriever
same model + local test runner enabled
same model + output contract repair
same model + constrained budget
same model + wrong-version repo skill
```

指标：

```text
MAE / RMSE for pass-rate prediction
negative log likelihood
Brier score
pairwise ordering accuracy
top-1 selection regret
ΔR² or ΔMAE after adding B_r to G
```

主结果：

```text
G-only predictor
B-only predictor
G+B predictor
unweighted repo-pool predictor
Barcarolle weighted predictor
```

最重要的 claim：

> Barcarolle weighted predictor lowers held-out prediction error relative to G-only and unweighted repo task pools.

---

### Phase 3：agent tuning validation

目标：证明 Barcarolle 不只是评测，还能帮助 tuning。

#### DSPy-style experiment

```text
optimizer input A: generic dev set
optimizer input B: Barcarolle repo-specific dev set
held-out eval: target repo future tasks
```

比较：

```text
held-out pass rate
cost
failure modes
regression on canary tasks
```

#### SkVM-style experiment

```text
skill original
skill compiled
skill JIT-optimized
```

在 Barcarolle dev/eval split 上比较：

```text
completion rate
token consumption
latency
task-family-specific gains
cross-harness robustness
```

SkVM 本身就强调 profiling、compilation、JIT optimization 和 benchmark across tasks/conditions/models，因此 Barcarolle 可以为它提供 target-repo-specific task substrate。([GitHub][12])

---

## 8. 产品价值

### 8.1 对 agent developers

Agent developers 不只需要知道：

```text
我的 agent 在 SWE-bench Pro 上多少分？
```

他们还需要知道：

```text
我的 file localization skill 在这个 repo 是否有用？
我的 repo-docs retriever 是否减少错误修改？
我的 test-running policy 是否值得成本？
我的 prompt optimizer 是否过拟合 dev tasks？
我的 agent 在 parser bugs 上好，还是在 dependency compatibility 上好？
```

Barcarolle 提供 repo-specific dev/eval/canary feedback loop。

---

### 8.2 对 repo owners / 企业用户

即使不讲 admission，repo owners 也有实际需求：

```text
我们是否应该用 agent A 还是 agent B？
这个 agent 在我们的 monorepo 上预计能解决多少任务？
它在哪些模块上不可靠？
调 prompt / skill / retriever 后是否真的改善？
模型升级后是否 regress？
```

SWE-Bench Pro 的商业集说明企业级、私有代码库评估已经成为真实需求。([arXiv][3]) Barcarolle 的差异是：不是让所有企业拿同一个 private benchmark，而是让每个企业为自己的 repo 编译 benchmark。

---

### 8.3 对 SWE benchmark 生态

SWE-Bench++、SWE-smith、SWE-Gym、R2E-Gym 负责产生越来越多任务。Barcarolle 提供消费层：

```text
task pool -> benchmark release
```

这会让上游 generator 的价值更容易落地：

```text
大量候选任务
↓
按目标 repo 选择
↓
按目标工作分布加权
↓
按调优目标切分
↓
输出可预测、可调优、可复现的 benchmark
```

---

## 9. 技术路线图

### Milestone 1：schema and runner

交付：

```text
task manifest schema
release manifest schema
agent run manifest
basic runner interface
scorecard format
```

目标：

```text
能导入历史 SWE-style task
能运行一个 ACUT
能输出 pass/fail/cost/trace
```

---

### Milestone 2：certification pipeline

交付：

```text
replay checker
no-op / reference / known-bad checks
flakiness checker
leakage scanner
oracle quality report
```

目标：

```text
候选任务可以被系统性接受/拒绝
输出 task-yield funnel
```

---

### Milestone 3：target profile and compiler

交付：

```text
repo history profiler
task taxonomy
target profile estimator
stratified task selector
weighted scoring
```

目标：

```text
从候选任务池生成第一个 benchmark release
```

---

### Milestone 4：predictive validation

交付：

```text
time-split validation harness
held-out future task evaluator
prediction metrics
baseline comparison
```

目标：

```text
证明 Barcarolle release 比 unweighted repo pool / general benchmark 更好预测 held-out tasks，或至少提供 residual signal
```

---

### Milestone 5：tuning integrations

交付：

```text
DSPy metric adapter
SkVM benchmark adapter
optimizer feedback schema
dev/eval/canary split manager
```

目标：

```text
把 Barcarolle release 用于 agent config optimization
```

---

### Milestone 6：private repo productization

交付：

```text
self-hosted mode
secret-safe task manifests
data retention controls
benchmark refresh workflow
report UI / markdown report
```

目标：

```text
支持企业或团队在私有 repo 上运行
```

---

## 10. 关键评估指标

### 10.1 Benchmark construction metrics

```text
candidate yield
certification yield
environment build success
oracle determinism
flakiness rate
leakage rejection rate
coverage by module / task type / test type
manual review minutes per accepted task
```

### 10.2 Predictive validity metrics

```text
MAE / RMSE of pass-rate prediction
binomial negative log likelihood
Brier score
confidence interval coverage
calibration error
pairwise ordering accuracy
top-1 selection regret
ΔMAE after adding Barcarolle score to general benchmark score
```

### 10.3 Tuning utility metrics

```text
held-out improvement after optimization
dev-to-eval generalization gap
cost per resolved task
token consumption
latency
regression on canary tasks
failure-mode reduction
```

---

## 11. Baselines

Barcarolle 至少要和这些 baseline 比较：

```text
G_all:
  通用 benchmark score

G_same_size_random:
  从通用 benchmark 随机抽同等数量任务

G_nearest:
  从通用 benchmark 中选择 taxonomy 最近的任务

Repo_unweighted:
  目标 repo 候选任务池中随机抽样，不加权

Repo_stratified:
  简单按目标 profile 分层抽样

External_generator_default:
  直接使用 SWE-Bench++ / SWE-smith 等上游生成任务，不做 Barcarolle 编译

Barcarolle_weighted:
  经过 certification、target profile、selection、weighting、calibration 的 release
```

Barcarolle 成功不要求每次都赢所有 baseline。最低可接受 claim 是：

> 在某些 repo / agent family / target horizon 下，Barcarolle 能比通用 benchmark 或 unweighted repo pool 提供更低预测误差，并清楚报告何时证据不足。

---

## 12. 风险与应对

### 风险 1：repo-specific signal 没有增量价值

可能出现：

```text
G + B_r 并不比 G 更好预测 W_r
```

应对：

先做 oracle headroom experiment。如果真实 same-repo historical tasks 都没有 residual predictive value，就不要强行推进 predictive validity 主线，转向 tuning feedback / regression testing / coverage benchmark。

---

### 风险 2：候选任务太少

应对：

Barcarolle 保持 source-agnostic：

```text
historical PR
SWE-Bench++ adapter
SWE-smith-style synthetic tasks
manual canary
mutation tasks
customer-provided tasks
```

如果仍然不足，release 应输出：

```text
insufficient evidence for strata X
```

这比伪造完整覆盖更可信。

---

### 风险 3：oracle 不可靠

应对：

```text
no-op fail
reference pass
known-bad fail
multiple-run flakiness check
test narrowness / wideness audit
optional human review for high-impact tasks
```

OpenAI 对 SWE-bench Verified 的分析说明，test oracle quality 本身就是 benchmark 成败关键。([OpenAI][2])

---

### 风险 4：tuning 过拟合 benchmark

应对：

```text
dev / eval / canary / future holdout split
periodic refresh
task-level leakage detection
score uncertainty reporting
no public release of private canary tasks
```

---

### 风险 5：和 SWE-Bench++ 差异不清

应对：

项目文档第一屏就写清楚：

```text
Barcarolle is not a task generation framework.
Barcarolle is a benchmark compiler and calibration layer.
It can consume SWE-Bench++, SWE-smith, historical PRs, manual tasks, and private canaries.
```

---

## 13. 推荐项目命名与 tagline

项目名可以保留 Barcarolle，但 tagline 建议改掉。

旧 tagline：

> repository-specific Agent License and evaluation system

新 tagline：

> **A target-repository benchmark compiler for coding-agent evaluation and tuning.**

更短：

> **Compile task pools into predictive repo-specific benchmarks.**

中文：

> **把候选 SWE 任务池编译成能预测目标仓库表现的 repo-specific benchmark。**

---

## 14. Proposal 摘要版

可以直接放到 README / grant proposal 开头：

> Barcarolle is a target-repository benchmark compiler for coding agents. Recent systems such as SWE-Bench++, SWE-smith, SWE-Gym, and SWE-bench-Live have made scalable production of executable repository-level tasks increasingly feasible. This shifts the bottleneck from task production to benchmark construction: given a target repository, an agent family, a fixed evaluation budget, and a tuning objective, which candidate tasks should be selected, weighted, split, refreshed, and interpreted?
>
> Barcarolle addresses this problem by compiling candidate task pools from repository history, task generators, and private canaries into calibrated benchmark releases. Each release includes certified tasks, target-work distribution profiles, task weights, dev/eval/canary splits, score uncertainty, failure taxonomy, and optimizer-readable feedback. Barcarolle is evaluated not by task count or leaderboard difficulty, but by predictive validity: whether its repo-specific benchmark scores better predict held-out future work in the target repository, or add predictive signal beyond general benchmark scores.
>
> The project serves two primary users: agent developers who need target-repo feedback for tuning prompts, tools, skills, retrieval, and harness policies; and repository teams who need realistic estimates of how different agent configurations will perform on their own codebases. Barcarolle is source-agnostic: SWE-Bench++ and SWE-smith can serve as upstream task factories, while Barcarolle provides the compiler, calibration, and tuning layer that turns raw tasks into useful repo-specific benchmarks.

中文版本：

> Barcarolle 是一个面向 coding agents 的目标仓库 benchmark compiler。SWE-Bench++、SWE-smith、SWE-Gym、SWE-bench-Live 等系统已经证明，大规模生成可执行 repository-level tasks 越来越可行。因此，新的瓶颈不再只是 task production，而是 benchmark construction：给定一个目标仓库、一个 agent family、固定评估预算和调优目标，应该选择哪些候选任务、如何加权、如何切分、如何刷新、如何解释分数？
>
> Barcarolle 把来自仓库历史、task generators 和私有 canary 的候选任务池，编译成经过校准的 benchmark release。每个 release 包含 certified tasks、目标工作分布 profile、任务权重、dev/eval/canary split、score uncertainty、failure taxonomy 和 optimizer-readable feedback。Barcarolle 的成功标准不是任务数量或 leaderboard 难度，而是 predictive validity：它的 repo-specific benchmark score 是否能更好预测目标仓库 held-out future work，或者是否能在通用 benchmark score 之外提供额外预测信号。
>
> 这个项目服务两类用户：一类是需要调优 prompt、tools、skills、retrieval 和 harness policy 的 agent developers；另一类是需要评估不同 agent configurations 在自己代码库上实际表现的 repo teams。Barcarolle 不绑定某个 task generator；SWE-Bench++ 和 SWE-smith 可以作为上游 task factories，而 Barcarolle 提供 compiler、calibration 和 tuning layer，把原始任务转化成有用的 repo-specific benchmark。

---

## 15. 最终项目主张

Barcarolle 的独立主张应该是：

> **The next bottleneck is not generating more SWE tasks. It is compiling the right tasks into a benchmark that predicts and improves performance on a specific repository.**

中文：

> **下一个瓶颈不是生成更多 SWE 任务，而是把正确的任务编译成能预测并提升目标仓库表现的 benchmark。**

这条线能把 SWE-Bench++ 从竞争者变成上游基础设施，把 admission 从核心叙事降为可选应用，把 ranking reversal 降为派生指标，并把 Barcarolle 的核心 idea——生成 repo-specific benchmark——重新定义成一个更强、更独立、也更可验证的问题。

[1]: https://www.swebench.com/original.html "SWE-bench"
[2]: https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/ "Why SWE-bench Verified no longer measures frontier coding capabilities | OpenAI"
[3]: https://arxiv.org/html/2509.16941v1 "SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?"
[4]: https://arxiv.org/html/2505.23419v2 "SWE-bench Goes Live!"
[5]: https://arxiv.org/abs/2504.02605?utm_source=chatgpt.com "Multi-SWE-bench: A Multilingual Benchmark for Issue Resolving"
[6]: https://arxiv.org/html/2504.21798v1 "\bugs: Scaling Data for Software Engineering Agents"
[7]: https://arxiv.org/abs/2412.21139?utm_source=chatgpt.com "Training Software Engineering Agents and Verifiers with SWE-Gym"
[8]: https://arxiv.org/html/2512.17419v1 "SWE-Bench++: A Framework for the Scalable Generation of Software Engineering Benchmarks from Open-Source Repositories"
[9]: https://arxiv.org/abs/2509.16941?utm_source=chatgpt.com "SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?"
[10]: https://arxiv.org/abs/2504.07164?utm_source=chatgpt.com "R2E-Gym: Procedural Environments and Hybrid Verifiers for Scaling Open-Weights SWE Agents"
[11]: https://dspy.ai/ "DSPy"
[12]: https://github.com/SJTU-IPADS/SkVM "GitHub - SJTU-IPADS/SkVM: The Language Virtual Machine for Agent Skills · GitHub"
[13]: https://arxiv.org/abs/2410.06992?utm_source=chatgpt.com "SWE-Bench+: Enhanced Coding Benchmark for LLMs"
