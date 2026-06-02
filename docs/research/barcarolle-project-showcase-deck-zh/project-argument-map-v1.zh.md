# Barcarolle 项目展示论证图

状态：项目展示 deck 论证图，2026-06-02。

用途：先确定读者问题、主张、证据和反驳，再写逐页 deck。本文是内部写作依据，不作为投影片原文。

## Audience

目标读者包括技术项目评审者、coding-agent 评测研究者、agent 产品与调优负责人，以及没有跟随内部实验过程的项目决策者。

这些读者通常已经知道通用 coding benchmark、真实 issue 任务、自动化任务生成和 agent 调优工作流的价值，但不一定知道为什么“同一个 Agent 配置在某个目标仓库未来工作中的表现”需要单独建模。他们关心的是：是否值得把 Barcarolle 当成一个研究和产品化方向继续推进，而不是只把它看作又一个任务集合或评测脚本。

## Reader questions

1. Barcarolle 解决的具体问题是什么？
2. 为什么已有 public benchmark、live benchmark、生成式任务系统和可执行训练环境还不能直接回答这个问题？
3. Barcarolle 的方法是什么，边界在哪里？
4. 当前已经建成或学到了什么？
5. 哪些结论仍未证明？
6. 为什么现在可以进入 benchmark 选择算法的发现和演进？
7. 后续研究如何走向更强的预测效度证据？
8. 这个项目未来怎样服务 Agent License 和 Agent Tuning？

## Condition

Coding-agent 评测存在目标仓库预测缺口：一个团队要部署或调优某个被测 Agent 配置（ACUT）时，真正需要知道的是它在本仓库未来真实工作中的表现，而不是只知道它在通用任务分布或某个大 benchmark 上的表现。

现有方向分别贡献了重要能力：真实仓库 issue 任务、人工验证任务质量、任务鲜度、可扩展任务生成、可执行训练和评测环境。它们可以成为候选任务供应、质量参照或对照系统，但它们本身不决定：在给定目标仓库、ACUT、未来工作假设和评测预算时，哪些任务应该进入一个冻结的 repo-specific benchmark release，以及这个 release 如何解释成对未来工作的证据。

## Consequence

如果这个缺口没有被处理，团队可能会基于“总体可审计但对本仓库不够决策相关”的证据选择、部署或调优 coding agent。风险包括：

- 通用分数高，但在目标仓库的 API、测试习惯、依赖约束或 review 规范上失效；
- 同仓库抽样看似合理，但没有处理时间窗口、任务来源、source quality、leakage、fallback 和 support 问题；
- 调优反馈把 dev set 的短期收益误读成未来仓库工作改善；
- governance 决策缺少 adapter 边界、成本、延迟、source 质量、隐藏 oracle 隔离和不确定性说明。

## Response

Barcarolle 的响应是把“任务供应”和“agent harness”之间的 benchmark 构造层变成研究对象。它面向一个目标仓库和一个被定义清楚的 ACUT 边界，编译 versioned benchmark release：候选任务先经过认证，再按目标工作画像、support 约束、selection rule、split、weight 或 unweighted 策略、fallback 标签和验证协议组装成可审计 release。

Barcarolle 不接管 ACUT 的搜索、编辑、prompt、工具策略、模型、重试或 trace 内部。它建立干净 solver workspace，给出 solver-visible statement 和允许上下文，调用配置好的 ACUT harness，捕获最终 workspace diff；随后在独立 verifier workspace replay diff，只在 verifier 侧注入隐藏 oracle，并记录 score、cost、latency、terminal status 和 sanitized artifacts。

## Main claim

Barcarolle 是面向特定仓库的 benchmark 编译器项目：它研究如何把候选任务编译成可冻结、可验证、可解释的 benchmark release，使未来能够更可靠地估计某个 ACUT 在目标仓库未来工作中的表现。

当前项目已经证明的问题不是“已完成未来预测证明”，而是：目标仓库 benchmark 构造是一个真实、可度量、技术上可执行、并且有初步优化信号的研究问题。下一阶段应把重点放在 benchmark-selection algorithm 演进、source/task supply 强化、严格未来验证，以及 Agent License / Agent Tuning 的证据接口上。

## Reasons

1. 目标仓库预测是不同于通用能力测量、任务质量验证、任务鲜度和任务生成规模的评测层。
2. Barcarolle 的 ACUT 边界和 verifier replay 机制把 benchmark 编译器与 agent harness 分开，使结果可以审计而不重写被测 agent。
3. 朴素 weighted 构造失败说明任务选择和构造规则会显著改变 repo-specific estimate，不能用“随机抽题”替代。
4. 已完成的 exploratory pilots 表明 workspace 执行、diff 捕获、hidden-oracle 隔离、score accounting 和 artifact hygiene 能跑通。
5. 当前 MAE 和 random baseline 结果说明 selection policy 有优化目标，但 best-simple-baseline edge 很小，必须继续约束声明。
6. fallback、adapter、repo/window support 的弱点不是附带瑕疵，而是后续算法、source repair 和验证协议要解决的核心问题。
7. Agent License 和 Agent Tuning 都需要 repo-specific evidence layer，但 Barcarolle 应提供证据、scorecard、failure taxonomy 和 regression signal，而不是变成 license 产品或调优闭环本身。

## Evidence

- 朴素 weighted target-profile design 的差距为 attrs `0.3148`、boltons `0.7481`，对应 simple same-budget baseline 为 `0.25` 和 `0.125`。这支持“构造问题真实存在”，但不是成功 compiler 结果。
- 三仓库 exploratory pilot 完成 `120/120` planned cells，scoreability 为 `1.0`。这支持“benchmark-side execution feasible”，但不证明未来预测。
- click source context repair 完成 `30/30` frozen tasks，说明 source-quality repair 可执行；历史 paid outcomes 没有因此被重写。
- 当前 candidate aggregate MAE 为 `0.209`，best simple aggregate baseline 为 `0.2149`，edge 为 `0.0059`。这支持“有牵引性”，但 margin 太小，不能承载正式预测效度声明。
- `1000` seed same-budget random comparison 中，candidate 在 MAE 上 beats or ties `93.4%` random selections。这说明 selection 不只是噪声。
- 当前 selector 有 `6/18` selected slots 使用 fallback，boltons 为 `6/6` fallback。这说明当前结果是 composite/support-limited，未来必须修复 support 或缩小声明。
- Adapter metrics 显示 Codex 与 Kilo 的表现差异应作为 named ACUT configuration evidence 报告，不能被 pooled summary 掩盖，也不能解释成模型-only 结论。

## Warrants

- 如果一个 benchmark release 的目标是估计未来目标仓库工作表现，那么任务选择、source 质量、split、fallback、adapter 边界和验证协议都会影响估计值；因此这些不是工程细节，而是研究对象。
- 如果 ACUT harness 拥有自己的策略和 runtime，benchmark 编译器必须只控制 workspace、task statement、allowed context、diff capture、verifier replay 和 accounting；否则 benchmark 会混入 agent 实现。
- 如果 retrospective evidence 已经接触过 outcome、feature 或 policy choices，它可以用于路线发现和 baseline stress testing，但不能替代 true future holdout 或 preregistered rolling-origin evidence。
- 如果调优工作会反复看到 dev tasks，那么 eval、canary 和 future validation material 必须隔离；否则 tuning feedback 会削弱正式评测证据。

## Strongest objections

1. 现有 public benchmark 与 live benchmark 已经能提供真实、可执行和新鲜的任务，Barcarolle 可能只是重复工作。
2. 朴素 weighted design 失败，可能说明 benchmark compiler 思路本身不可行。
3. 当前 MAE edge 只有 `0.0059`，不足以支持继续投入。
4. fallback share 和 adapter fragility 说明当前 selector 太脆弱。
5. Agent Tuning 很容易过拟合 benchmark，反而会降低未来评测可信度。
6. Agent License 听起来像产品授权系统，可能偏离研究边界。

## Responses

1. 相关工作提供任务、质量、鲜度、规模或环境；Barcarolle 研究 release compilation 和 future target-repo estimation。二者是相邻层，不是互相替代。
2. 失败的 weighted design 应作为负面诊断保留：它证明 sparse support 下高维 metadata weighting 不安全，也证明 construction choices materially affect estimates。
3. 小 MAE edge 不能支持预测效度声明，但足以证明 metric、baseline envelope 和 random control 可以作为算法搜索目标。
4. fallback 与 adapter fragility 应被前置为 future algorithm/support requirements：修复 feature support、增加 source supply、narrow unsupported claims、按 named ACUT configuration 报告。
5. 调优路径必须区分 dev feedback、eval release、canary release 和 future holdout；Barcarolle 输出 scorecard 和 regression signal，但不把当前结果写成调优闭环已改善。
6. Barcarolle 不是 license 产品；它可以成为 license / deployment governance 的证据层，帮助判断某个 ACUT 在某仓库、任务类别或风险等级下是否有足够证据支持使用。

## Future work

后续研究应沿六条线推进：

- benchmark-selection algorithm evolution：以 simple baselines、random controls、support thresholds、fallback caps、adapter-stratified metrics 和 MAE margin 为约束，探索 coverage-constrained、temporal、blocked、shrinkage 或其他 selector。
- source/task supply strengthening：扩展候选任务来源，提升 source sufficiency、oracle validity、environment replayability、leakage checks 和 feature support。
- outcome-unseen validation：冻结 release、selection rule、baseline suite、invalid-cell rule、success criteria 和 score-join procedure，再用 true future holdout 或 preregistered rolling-origin evidence 验证。
- multi-configuration extension：在需要比较 prompts、retrieval、skills、tool policy、model 和 runtime budget 时，按 named ACUT configuration 报告，避免 pooled rescue。
- Agent License path：把 Barcarolle 作为 deployment governance 的 evidence layer，而不是授权产品本身。
- Agent Tuning path：输出 dev/eval/canary release、failure taxonomy、scorecard 和 regression signal，帮助团队比较配置变化，同时保护正式验证材料不被过拟合。
