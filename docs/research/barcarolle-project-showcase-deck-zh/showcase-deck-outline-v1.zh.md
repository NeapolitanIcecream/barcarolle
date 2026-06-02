# Barcarolle 项目展示 Deck 大纲

状态：项目展示 deck 大纲，2026-06-02。

用途：为新的中文可编辑 PPTX 锁定逐页结构。大纲按读者问题组织，不按历史报告章节组织。

## Slide 1 - Barcarolle 编译面向目标仓库的 benchmark release

主消息：Barcarolle 研究如何把候选任务编译成 repo-specific benchmark release，用于估计某个 ACUT 在目标仓库未来工作中的表现。

画面：一句话定义 + 三段式对象图：目标仓库、被测 Agent 配置、冻结 release。

证据或例子：使用术语“面向特定仓库的 benchmark 编译器”和“ACUT”。

省略内容：资源预算、项目人员、历史阶段名称、内部写作说明。

## Slide 2 - 团队缺少对未来仓库工作的直接估计

主消息：通用 benchmark 分数很有用，但团队部署 agent 时需要回答本仓库未来 issue、API、测试和依赖约束下的表现。

画面：从“通用任务分布”到“目标仓库未来工作”的 gap diagram。

证据或例子：目标问题写成一句中文问题：一个给定 ACUT 在某个目标仓库未来真实工作中的表现会怎样？

省略内容：对 public benchmark 的贬低、泛泛的“评测不准”。

## Slide 3 - 这个缺口会影响部署、调优和治理

主消息：如果缺少 target-repo evidence，团队可能用总体可审计但对本仓库不够决策相关的证据做部署和调优选择。

画面：三列 consequence map：部署选择、配置调优、deployment governance。

证据或例子：列出仓库 API、测试习惯、依赖约束、review norms 和 failure modes。

省略内容：实验流水账、预算讨论、过长风险清单。

## Slide 4 - 相关工作已经覆盖任务、质量、鲜度、规模和环境

主消息：SWE-bench、Verified、Live、SWE-smith 和 R2E-Gym 都提供关键相邻层，但它们回答的问题与 Barcarolle 的 release compilation 问题不同。

画面：横向 positioning matrix：方向、贡献层、Barcarolle 仍要回答的问题。

证据或例子：SWE-bench 真实 issue tasks；Verified 质量验证；Live 鲜度；SWE-smith 生成规模；R2E-Gym 可执行环境。

省略内容：胜负式比较、文献综述细节、citation 堆叠。

## Slide 5 - Barcarolle 位于 target-repo release compilation 层

主消息：候选任务供应越强，越需要一个 compiler 决定哪些任务进入冻结 release、如何切分和解释。

画面：分层图：candidate supply -> certification -> selection/split -> frozen release -> future validation。

证据或例子：Barcarolle 的问题是“给定目标仓库和 ACUT，怎样编译 benchmark release 更可能预测未来工作表现”。

省略内容：把 Barcarolle 写成 task generator、ACUT harness 或 public leaderboard。

## Slide 6 - 北极星是 outcome-unseen 预测效度

主消息：长期目标是让冻结 release 比简单同仓库或通用替代方案更好地预测未来 target-repo ACUT success。

画面：north-star equation + validation gate strip：freeze、future evidence、baseline envelope、success criteria。

证据或例子：MAE 作为平均预测误差；lower MAE 表示 estimate 更接近 observed future-work performance。

省略内容：把 retrospective replay 写成已经完成的正式证明。

## Slide 7 - 方法是把候选任务编译成可审计 release

主消息：Barcarolle 的方法不是抽题，而是从候选供应、认证、目标工作画像、assembly rule 到 versioned release 的完整编译流程。

画面：主 workflow diagram：candidate supply、certification、target-work profile、assembly rule、release、score/refresh。

证据或例子：认证维度包括 replayability、oracle、leakage、source quality、environment、ambiguity。

省略内容：ACUT 内部 prompt、搜索策略、工具策略、模型选择和 trace 细节。

## Slide 8 - ACUT 边界让 benchmark 不变成 agent harness

主消息：Barcarolle 只提供 solver workspace、允许上下文、diff capture 和 verifier replay；ACUT 继续控制自己的 harness。

画面：双工作区 boundary diagram：solver workspace 与 verifier workspace，中间是 captured diff。

证据或例子：hidden oracle 只在 verifier workspace 注入；score、cost、latency 和 terminal status 被记录。

省略内容：被测 agent 的内部链路、私有 trace、model-only 归因。

## Slide 9 - Benchmark 选择不是随机抽题

主消息：朴素 weighted 构造失败说明 task selection、support 和 fallback 会显著改变估计，构造规则本身就是研究问题。

画面：negative-result callout + selector decision map。

证据或例子：attrs weighted gap `0.3148`、boltons weighted gap `0.7481`；simple same-budget baselines 为 `0.25` 和 `0.125`。

省略内容：为旧 weighted design 辩护、把失败包装成成功结果。

## Slide 10 - 算法演进环境已经成形

主消息：Barcarolle 已经具备比较 selector、baselines、random controls、support thresholds 和 adapter-stratified metrics 的实验环境。

画面：algorithm lab map：candidate features、selection policy、baseline suite、random envelope、adapter/repo/window diagnostics。

证据或例子：current selector 可描述为 coverage-constrained unweighted with labeled fallback；未来可比较 temporal、blocked、shrinkage 或其他 variants。

省略内容：过早指定唯一主线算法、隐藏 fallback 行为。

## Slide 11 - 当前效果支持继续优化，但还不支持最终有效性声明

主消息：当前 evidence 显示问题真实、执行可行、selection 有初步信号，但 edge 还太小。

画面：四个 evidence callout：weighted failure、execution feasible、source repair、MAE traction。

证据或例子：`120/120` cells、scoreability `1.0`、click `30/30` repair、candidate MAE `0.209` vs baseline `0.2149`、edge `0.0059`、random beats/ties `93.4%` of `1000`。

省略内容：把所有数字堆成证据附录、把初步证据写成正式未来预测结论。

## Slide 12 - 尚未证明的部分决定下一步

主消息：预测效度尚未建立，fallback、adapter、repo/window support 和 tuning-loop effect 都还需要更强证据。

画面：limitations-to-work bridge：current weakness -> required repair or validation action。

证据或例子：`6/18` selected slots 使用 fallback，boltons `6/6` fallback；Codex/Kilo 差异要按 named ACUT configuration 报告。

省略内容：防御性解释、把 pooled summary 当成主结论、把 tuning feedback 写成已验证效果。

## Slide 13 - 后续研究走向冻结 release 和未来验证

主消息：下一阶段应冻结 selection rule、baseline suite、invalid handling 和 success criteria，再用 true future holdout 或 preregistered rolling-origin evidence 验证。

画面：future validation roadmap：pre-outcome freeze -> release -> named ACUT configurations -> outcome-unseen score join -> baseline envelope -> scoped result。

证据或例子：simple baselines 包括 temporal recent、repo-unweighted、repo-stratified 和 many-seed random。

省略内容：开放式付费探索、事后移动 success criteria。

## Slide 14 - Agent License 需要仓库级证据层

主消息：Barcarolle 本身不是 license 产品，但可以成为 deployment governance 的证据层。

画面：governance map：仓库、任务类别、风险等级、ACUT 配置、evidence status、use decision。

证据或例子：判断某个 ACUT 在某仓库、任务类别或风险等级下是否有足够证据支持使用。

省略内容：授权流程、合规承诺、把 Barcarolle 写成最终 license issuer。

## Slide 15 - Agent Tuning 需要受保护的反馈回路

主消息：Barcarolle 不接管调优闭环，但可以提供 dev/eval/canary release、failure taxonomy、scorecard 和 regression signal。

画面：tuning feedback loop：prompt、retrieval、skills、tool policy、runtime budget -> dev feedback -> protected eval/canary -> regression monitoring。

证据或例子：可比较配置变化，同时保持正式验证材料不被过拟合。

省略内容：声称调优效果已被实证证明、把 dev-set gain 写成 future-work improvement。
