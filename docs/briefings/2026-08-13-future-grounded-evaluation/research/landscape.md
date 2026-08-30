# 领域版图：coding-agent 评测正在补哪几块缺口

> 本文只把论文、官方项目页和官方审计当作事实来源。共享聊天用于提出问题，不作为外部事实证据。访问日期：2026-08-13。
>
> 这是日期化 landscape。2026-08-30 新增的 paired gap、active testing、
> IRT/Generation 与 coding reward-hacking 文献综合见
> [`../../../research-program.md`](../../../research-program.md)。

## 1. 不应把整个领域压成一条“新 benchmark 比旧 benchmark 好”的线

当前工作至少在解决七个相互独立的问题：

1. **任务是否来自真实软件工程工作**：从小程序题走向 repository-level issue/PR。
2. **任务与 oracle 是否可靠**：描述是否充分，测试是否既不拒绝正确解、也不放过错误解。
3. **任务是否已暴露**：公开题目和 gold patch 是否进入训练、微调或人工调参闭环。
4. **任务供应是否持续**：能否自动采集、重建环境、认证并滚动更新。
5. **工作过程是否真实**：需求是否会逐步披露，是否需要用户纠正，评价是否超越终局 pass/fail。
6. **评测被当作优化目标后是否仍有效**：Agent 反复根据分数改变后，评测上的改进是否仍代表后来真实工作上的改进。
7. **评测如何进入工程流程**：能否保存实验、比较版本、检查 regression、接入 CI/CD 和生产监控。

前五项各有快速进展；第七项也已有成熟产品；第六项正是 Barcarolle 新故事要单独研究的对象。解决“污染”“交互”“未来方向”或“把 eval 跑起来”中的任何一项，都不能自动推出 optimization-safe evaluation。

## 2. 代表性工作对比

| 方向 | 工作 | 主要贡献 | 它没有单独闭合的问题 |
| --- | --- | --- | --- |
| 固定真实任务 | [SWE-bench](https://arxiv.org/abs/2310.06770)（2023/ICLR 2024） | 将 12 个 Python 仓库的 2,294 个真实 issue/PR、仓库快照和 F2P/P2P 可执行测试组成标准 repository-level benchmark | 固定且公开；开发者测试可能过窄、过宽或覆盖不足；不记录评测暴露，也不研究被反复优化后的有效性 |
| 人工筛选 | [SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/)（2024） | 93 名开发者审核 1,699 题，每题三人，保留 500 题 | “人工验证过”不是永久状态。OpenAI 在 [2026 复审](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)中，对 o3 在 64 次运行中未稳定解决的 138 题定向复审，至少 59.4% 有实质性问题，并观察到前沿模型可复现部分 benchmark 细节；不能把该比例外推到全部 500 题 |
| 长程/私有任务 | [SWE-Bench Pro](https://arxiv.org/abs/2509.16941)（2025） | 扩展到 1,865 题、41 个公开/私有/商业仓库和更长任务 | 私有来源缓解公开泄漏，不保证 oracle 正确。OpenAI 2026-07 [审计](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)的人工标注汇总将 249/731（34.1%）标为有问题；结合自动化分析，OpenAI 对整体问题率估计约 30%，并撤回此前推荐 |
| 滚动真实任务 | [SWE-bench-Live](https://arxiv.org/abs/2505.23419)（2025） | 初版 1,319 个 2024 年后任务、93 个仓库，并计划月度更新 | “近期”只是污染风险代理；仍继承 PR 测试质量问题；持续更新没有回答 adaptive selection validity |
| 自动持续供应 | [SWE-rebench](https://arxiv.org/abs/2505.20411)（2025） | 自动采集 PR、建环境、认证；公开池约 21,336 题；同一固定 scaffold 下多次运行并报告不确定性 | 自动质量标签和环境启发式仍有错；固定 scaffold 主要比较模型，不等于比较完整 Agent system；没有以 later real work 验证 winner selection |
| 合成训练工厂 | [SWE-smith](https://arxiv.org/abs/2504.21798)（2025） | 128 个仓库生成 50,137 个 bug task，缓解训练数据不足 | 作者明确指出当时实例不适合评测：F2P 测试对 Agent 可见、缺少 hidden tests。它是训练供应，不是 optimization-safe evaluator |
| 自动跨语言构造 | [SWE-Bench++](https://arxiv.org/abs/2512.17419)（2025） | 从真实 PR 自动构建 11,133 题、3,971 仓库、11 种语言，并使用 Base/Before/After 三态 oracle | 执行通过仍是语义正确的代理；开发者测试稀疏时可能放过错误补丁；cutoff 过滤不是无污染证明 |
| 时间一致性 | [A Time-Consistent Benchmark for Repository-Level Software Engineering Evaluation](https://arxiv.org/abs/2603.26137)（2026） | 在 T0 构造 repository knowledge，用 (T0,T1] 后续 PR 做 matched A/B，控制时间泄漏 | 目标是隔离 repository knowledge 的因果贡献，规模为两个仓库；并不构造能承受多轮 Agent 搜索的评测协议 |
| 未来导向合成 | [SWE-Future](https://arxiv.org/abs/2606.18733)（2026） | 先用 T0 前证据预测 future task families，用 T0 后 PR metadata 做回溯语义匹配，再按入选 family 从新快照合成 200 题/61 仓库 | 在论文主语义匹配判分口径下，151/260（58.1%）个 families 相对 T0 后 PR metadata 被标为 strong 或 related；这是 synthesis eligibility，不是人工确认的精确 issue 命中、Agent 解题率或最终生成题的外部有效性 |
| 用户交互（人工改写） | [SWE-INTERACT](https://arxiv.org/abs/2606.30573)（2026） | 用户模拟器从模糊需求逐步披露约束；最强模型从单轮约 50% 降至多轮约 25%，显示交互能力是独立轴 | 任务来自既有静态 benchmark；结果同时受 user simulator、persona 和 scaffold 影响；不研究未来任务分布或 adaptive optimization |
| 用户交互（真实会话来源） | [SWE-Together](https://arxiv.org/abs/2606.29957)（2026） | 从 11,260 个真实会话中筛出 109 个可重放任务，评价终局正确性和纠正轮数 | 真实来源不自动产生完整 oracle；评测时仍由状态化 simulator 代替真人，终局 correctness 由结合 repository inspection 与 executable evidence 的 agentic rubric judge 评定；不研究优化压力下的未来有效性 |
| 自我改进 Agent | [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954)（2025） | Agent 修改自身代码，并用 coding benchmark 经验性选择后代；论文报告 SWE-bench 20%→50%、Polyglot 14.2%→30.7% | 评测准则在搜索环外给定；证明“能沿 benchmark 改进”，不等于这些改进能迁移到尚未发生的真实工作 |
| evaluator 共演化 | [Red Queen Gödel Machine](https://arxiv.org/abs/2606.26294)（2026） | evaluator-dependent roles 在 epoch 内冻结 evaluator；边界处用固定 held-out ground-truth anchor 比较 incumbent 与 challenger evaluator；evaluator-independent roles 使用固定 benchmark | anchor 约束的是 evaluator promotion，不直接认证 writer/prover 等 task agent 的真实效用；无直接 ground truth 的 task agents 仍按 epoch-local evaluator 排序。论文将当前实证称为 preliminary，尚未构造 delayed、changing、repo-specific 的未来 workload anchor |
| 自适应统计 | [Preserving Statistical Validity in Adaptive Data Analysis](https://arxiv.org/abs/1411.2664)；[The Ladder](https://arxiv.org/abs/1502.04585) | 形式化“反复看同一 holdout/leaderboard 会过拟合”，并给出限制信息泄漏或稳定发布分数的方法 | 通常假设 target distribution/holdout 已定义；不能替我们定义哪个未来 repository workload 才是目标，也不能验证 Generator 的具体化是否忠于未来 |
| 内部 eval 平台 | [Braintrust experiments](https://www.braintrust.dev/docs/evaluate/compare-experiments)；[LangSmith comparison](https://docs.langchain.com/langsmith/compare-experiment-results) | 在给定 dataset/score 上运行并保存多个实验，展示逐项/汇总 improvement 与 regression，支持版本比较和工程门禁 | 解决 evaluation execution，不自动证明该 dataset 上的 A>B 会迁移到下一批真实工作；Barcarolle 研究这层 external validity |

### 2.1 机制邻接，不是 Barcarolle 问题的直接方案

| 邻接方向 | 工作与直接证据 | 对本项目的边界 |
| --- | --- | --- |
| reward/specification gaming | [Skalse 等](https://arxiv.org/abs/2209.13085)形式化 reward hacking：优化不完整 proxy 时，proxy 的期望回报上升可能伴随 true reward 下降；论文也说明 unhackability 在其奖励与策略设定下是很强的条件 | 提供 proxy 失真的定义和反例条件；没有研究 repository-level coding Agent、later-real workload 或任务刷新协议 |
| benchmark/reward-model overoptimization | [Gao 等](https://arxiv.org/abs/2210.10760)在 synthetic gold reward model 设定中，以 RL 或 best-of-n 持续优化 proxy reward model，并测量 gold score 随优化压力变化 | 说明应画 optimization-pressure curve；gold 仍是固定模型，不是后来真实工作，实验也不包含 coding-agent Harness 与 task supply |
| live refresh | [LiveBench](https://arxiv.org/abs/2406.19314)使用近期信息源、客观自动判分并按月增加或更新问题，以限制污染窗口 | 证明通用 LLM benchmark 可以持续刷新；它不是 repository-level 软件工程任务，也不测反复使用反馈后的 winner selection 或 later-work external validity |

这三类工作提供风险机制、压力曲线和刷新设计的证据。它们支持 Barcarolle 的实验选择，但不能单独证明 Barcarolle 的 Selector、Generator 或 adaptive protocol 有效。

## 3. 从 landscape 得出的六个判断

### 3.1 污染和 oracle 错配是两类不同故障

题目没见过，不代表测试就正确；测试经过人工审核，也不代表题目没进入训练。Verified 和 Pro 的后续审计说明“认证”必须可以撤销、复审并随 Agent 能力变化而重新校准。Barcarolle 的 hidden-oracle replay、证据层级和可审计 provenance 正好服务于这类长期边界，但它本身不能保证某个 Generator 的 task distribution 代表真实未来。

### 3.2 持续更新不等于未来有效

Live/rebench 把固定快照变成任务流，SWE-Future把后续工作方向引入合成条件。这些工作都减少了静态公开题的局限，但还缺一个单独问题：在一批 Agent variants 上，今天的评测差值和排序能否预测 later-real-work 差值和排序。

### 3.3 交互真实性与时间/选择有效性是正交维度

SWE-INTERACT 和 SWE-Together 证明“完整 prompt + 终局 pass/fail”遗漏真实用户协作成本。Barcarolle 可以未来接入 interaction/correction 等 outcome，但这不是第一阶段前提。先用 pass/fail 研究 adaptive selection validity，能够保留一个清楚、可证伪的主张。

### 3.4 评测一旦成为 optimizer 的 objective，问题性质改变

普通 pointwise evaluation 只问自然出现的 Agent 是否测得准；optimizer 会主动搜索评测误差。Adaptive data analysis 已形式化反复复用 holdout 产生偏差的条件与反馈控制方法，DGM/RQGM 又说明自动 Agent variant search 和 evaluator evolution 已从假设走向系统研究。Barcarolle 的特有问题不是预设“必然严重过拟合”，而是把 evaluation target 锚定在未来真实 repository work，并度量这种锚定能承受多大 optimization pressure。

但“会产生偏差”不等于“每个实践系统都必然严重退化”。[Roelofs 等人的 112 个 Kaggle 竞赛分析](https://arxiv.org/abs/1902.10811)发现 substantial overfitting 的总体证据很少。候选高度相关、private set 分布变化和反馈制度都会改变结果。因此 Barcarolle 必须把 candidate diversity、temporal shift、population shift 和 adaptive exposure 分开报告，不能把任何 public/future gap 都归因于 Goodhart。

### 3.5 公共 benchmark 和 repo-specific eval 的价值来源不同

SWE-bench 的价值不只是一项统计估计。公共任务、统一协议和排行榜给模型提供商、Agent 团队和研究者一个共同坐标系；可比性与采用规模本身会产生协调价值。它不必逐家公司证明对其下个月 workload 的局部预测准确。

Barcarolle 选择 repo-specific、rolling-origin 路线时，主动放弃了一部分公共 network effect，换取本地 external-validity 主张。因此它承担更高的证明义务：相对 Full/recent/user-curated suite，是否少选错 future winner，是否在同等 regret 下少跑任务。它不能只说“我们是更严谨的 SWE-bench-X”。

### 3.6 EvalOps 已能比较版本，缺口是这些比较是否值得相信

Braintrust 与 LangSmith 已支持在同一 dataset 上对齐多个 experiments，查看分数差值、improvement/regression 和输出 diff。这意味着 Barcarolle 的产品位置不能是“也能比较 Agent versions”。准确边界是：

> **EvalOps 平台回答 A 在当前 eval set 上是否优于 B；Barcarolle 研究这个 A>B 是否仍代表 later real work 上的 A>B。**

## 4. Barcarolle 的拟建研究位置

Barcarolle 不应定位成另一个固定榜单，也不应宣称自己是 Agent trainer/self-improver。拟建研究位置是：

> **一个 repo-specific、future-grounded、可持续刷新且可审计的 evaluation boundary；它研究评测反馈在被反复用于选择/优化 Agent 时，多久仍能代表后来真实工作。**

当前已实现的是可复现 benchmark boundary 和初步 selection evidence；continual refresh、exposure-aware adaptive selection 与 abstention 都尚待实现和验证。拟建方向连接三条此前分开的链：

- benchmark infrastructure：Task/Check、隔离执行、hidden verification、Results/provenance；
- temporal prediction：rolling origin、只用 origin 前信息、later Task outcomes；
- adaptive selection：记录 exposure，比较 benchmark gain、winner choice 与 later-real-work gain。

它不占据 Proposer：候选可由工程师、配置搜索或外部 self-improver 产生。它也不替代 Braintrust/LangSmith 的实验执行层；拟新增的研究对象是 repo-specific future external validity，以及证据不足时能否可靠 abstain。

## 5. 最需要避免的错误表述

- 不说“现有 benchmark 都没用”；它们分别成功建立了真实任务、规模、持续供应、交互等范式。
- 不说“动态 benchmark 就不会污染”；准确说法是缩短暴露窗口或污染感知。
- 不把 SWE-Future 的 58.1% 写成 Agent 准确率或精确预言率。
- 不把 SWE-smith 当成已成立的 hidden-test benchmark。
- 不把 RQGM 写成已经解决 delayed real-work ground truth。
- 不把 reward hacking、reward-model overoptimization 或 live refresh 写成 Barcarolle 的直接方案；它们只支持机制和实验设计。
- 不说 Barcarolle 已经 counter-Goodhart；这是待检验目标，而不是现有属性。
- 不说 repeated optimization 必然造成严重退化；把风险、机制与实证幅度分开。
- 不把“能比较两个 experiment”当作产品差异；差异在比较结果的 later-work external validity。
