# Barcarolle：我们已经在哪里，还缺什么

> 状态：2026-08-13 截面的历史位置说明。当前研究权威见
> [`../../../research-program.md`](../../../research-program.md)。特别是，
> Generation 已进入方法空间，level/gap MAE 为共同核心目标，population
> shift 不再是唯一下一路线。

## 1. 一句话判断

Barcarolle 已经具备较完整、可审计的 repo-local benchmark compiler / evidence boundary；它能严格构造、运行、重放和报告“用历史 Task 预测后续 Task 表现”的实验。但当前科学证据只支持一个 outcome-open、same-Harness、repository-equal 的 development incumbent：还不是生产 Selector，也没有证明 adaptive optimization safety。

## 2. 已有工程基础

当前系统已经覆盖：

- 直接候选、外部 Generator prepared package、用户已有 Task Pool 三类入口；
- execution-based `Task + Check` 认证；
- fresh solver workspace、只捕获最终 diff；
- fresh verifier workspace 重放，并只在验证阶段注入 private oracle；
- 完整 Agent identity、Result availability、成本/延迟/失败标签和冲突检测；
- rolling-origin Selection、冻结 selection、Result Matrix 和 claim-safe reporting；
- paid campaign 的 reservation/completion ledger、预算 stop gate、异常 fail-closed 和 sanitized artifacts。

仓库当前仍是 alpha：内置执行共享 caller host 权限，不是 adversarial sandbox；Result Store 为 JSONL；replicate uncertainty、model-based Selector 和 interval calibration 未完成；也没有具体的新 Generator 或 trainer。

## 3. 已有实证：正结果与限制必须一起讲

### 3.1 工程闭环已经跑通

- 75 个 SymPy Verified 候选全部形成 75 Task、75 Check、54 dependency clusters。
- 冻结主 campaign 的 238 cells 全部终止，237 scoreable、1 `agent_invalid`，无 retry/replacement。
- 两次完整 selector 复现 byte-identical；独立实现重新计算 1,183 个 primary membership/score cells，未发现 mismatch。

这些结果证明边界和复现机制能工作，不证明 Selector 能泛化。

### 3.2 当前 Selector 候选在一个窄 estimand 上胜出

主开发 panel：13 个 mini-SWE-agent v2 模型、500 个 SWE-bench Verified Tasks、5 个仓库、61 个 H5 Origins、30 个 H10 Origins。

| Repository-equal MAE | H5 | H10 |
| --- | ---: | ---: |
| Full history | 0.179527 | 0.129700 |
| `consensus_rate_match` | 0.173387 | 0.115927 |
| Candidate − Full | -0.006140 | -0.013774 |
| 相对降低 | 3.42% | 10.62% |

它先让选中十题的 reference-panel pooled pass rate 匹配完整历史，再以低 reference disagreement 打破 exact ties。target column 和 future block 均不可见。

### 3.3 同一证据也明确暴露了问题

| 压力测试 | H5 Candidate − Full | H10 Candidate − Full | 结论 |
| --- | ---: | ---: | --- |
| Repository-equal development | -0.006140 | -0.013774 | 局部胜出 |
| Origin-weighted | +0.004284 | +0.001864 | 换成“典型 origin”权重即反转 |
| 3 modern Full systems internal LOO | +0.014960 | +0.024006 | 新完整系统内迁移失败 |
| 13 primary refs → 3 external targets | +0.017513 | +0.007707 | 保留 reference 数量后仍跨 system/Harness 失败 |

实际 favorable Origins 只有 23/61 和 13/30；候选还是在 outcome 已打开的多路线搜索后选出。因此现在最诚实的结论是：**我们找到了一个局部、可复现的 mechanism candidate；它在三套完整系统、不同 Harness 上未迁移。** 这使 reference-to-target population/Harness shift 成为首要待检机制，但现有实验尚未分离它与样本量、Agent–Task interaction 和任务构成的影响。

## 4. 新故事为什么是连续扩展，而不是换项目

原问题：对一个固定 Agent，十道历史题能否估计 next-H 真实任务表现。

新问题：当外部 Optimizer 根据这个评测连续产生和选择 Agent variants 后，评测增益能否预测 next-H 真实任务增益。

二者共享同一内核：

- 同样以 repository 和 evaluation origin 为单位；
- 同样只允许用 origin 前历史编译评测；
- 同样将 future outcome 隔离到 selection 之后；
- 同样需要干净 workspace、hidden checks、完整 Agent identity 和 normalized Results；
- 新问题只增加 Agent-version trajectory、benchmark exposure 和 winner/lift 指标。

更重要的是，已有 transfer failure 已经给出新问题的前置信号：即使 Optimizer 还没主动搜索，Agent population/Harness 改变就足以破坏局部 Selector。反复优化会不会进一步加速失效，仍是待实验假说，不能当作既成事实。

## 5. 当前真正的四个技术缺口

### WP1：Generator external validity

把 Generator 分成：future-demand forecast → executable-task materialization。分别验证：

- forecast validity：方向是否对应后续真实工作；
- materialization validity：同一方向的合理具体化是否不由任意出题选择决定排名；
- response validity：synthetic tasks 在 Agent panel 上形成的分数、差值与排名是否预测 later real tasks。

关键实验包括 repeated materialization、cross-materializer transfer、oracle independence、synthesis sensitivity 和按时间分块的 response calibration。Calibration 只能使用较早 rolling origins 的 development blocks；Generator 配置必须在后续 sealed block 打开前冻结，同一 later-real block 不得兼作校准和最终评估。评价用 Reality Generator 应尽量 Agent-blind；可以另设看 failure traces 的 Challenge Generator 用于训练，但其分数不能直接声称代表 future utility。

### WP2：Contrast-aware Selector

当前 Selector 主要保留单个 target Agent 的平均 pass rate。下一阶段要保留候选 Agent 之间的差异：pairwise lift error、sign accuracy、ranking fidelity、top-1 selection regret、worst-case pair distortion。先区分：

- cold start：没有 target history，只能依赖 reference support；
- warm start：已有少量 target Results，可做 target calibration。

在继续评分前冻结 support/abstention 或 target-robust rule，避免再次对同一五仓库调参。

### WP3：Adaptive exposure protocol

把 Agent version、optimizer round、已见 tasks、aggregate score、failure traces 作为 experiment state。epoch 内 evaluator 固定，epoch 边界才 refresh；old evidence 有明确 lifetime；later real work 永远不进入 optimizer loop。

### WP4：Adaptive optimization experiment

不需要先发明新的 self-improver。固定同一个初始 Agent、同一个简单 proposer、相同 K 轮预算，只替换 evaluator：static benchmark、recent tasks、Barcarolle、refreshed Barcarolle。搜索完成后一次性打开 historical future tasks，比较 benchmark gain 与 real-future gain。

## 6. 可证伪里程碑

1. **固定 candidate panel**：Barcarolle 比 full/recent/random/user-curated regression suite 更少选错 future winner。
2. **增加候选数与 exposure**：随着 optimizer query 增加，Barcarolle 的 lift error 和 selection regret 增长慢于 static eval。
3. **Generator stress test**：同一 demand family 的多次/多方法 materialization 不轻易翻转 Agent contrast；校准后的 Generator 在 later real tasks 上更接近真实 response surface。
4. **closed-loop test**：同一 optimizer、同一预算下，由 Barcarolle 选择的最终 Agent 在 sealed future tasks 上优于 static-eval 组。
5. **外部确认**：在新的 same-Harness boundary 或 prospective later source 上重复，不用当前 outcome-open 五仓库作为最终确认集。

## 7. 不能声称什么

- 已有 production Selector；
- 对典型 Origin 有效；
- 跨 Harness、Agent system、模型家族或 repository 泛化；
- 当前候选是 independent/confirmatory discovery；
- raw selected-subset mean 是 unbiased estimator；
- 已实现 Goodhart resistance 或 repeated-optimization safety；
- 生成任务已经代表未来真实工作；
- Barcarolle 是 Generator、trainer 或 self-improver；
- synthetic workload 可以替代 later real workload。

## 8. 由当前研究计划取代的旧优先级

不再继续调同一五仓库 repository-equal 分数仍然成立；但“先只做
population shift，再考虑 Generator/闭环”的顺序已经被 2026-08-30 决定
取代。当前近期工作并行推进两目标静态 replay、fixed-candidate pressure、
Generation response validity 与 adversarial attack-transfer screen，详见当前
research program 与 ledger。
