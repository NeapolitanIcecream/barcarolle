# Barcarolle：研究如何让 Agent 优化持续和未来真实工作对账

> 本文件是 2026-08-13 第一版技术证据底稿，保留供追溯；同批管理层材料见
> [`strategic-briefing.md`](strategic-briefing.md)。当前项目研究合同见
> [`../../research-program.md`](../../research-program.md)。

## 执行摘要

今天，coding Agent 团队已经会围绕 benchmark 做大量工程选择：换模型、改 prompt、增加工具、调整上下文、检索和重试策略。如果 Agent 进一步自动产生自己的下一版本，候选改动可能从每周几十个增加到每小时几百个。届时瓶颈可能从“提出改进”转向**判断哪个改进在未来真实工作上确实更好**。

固定 benchmark 很适合做统一能力测量；但当它从“尺子”变成“优化目标”，optimizer 可能找到并利用其中的偏差，且风险会随候选数、反馈粒度和搜索轮数变化。公开题目还可能因持续暴露而污染，任务测试也可能过严、过宽或遗漏正确解。本次调研覆盖的代表性工作正在分别补任务真实性、质量认证、持续供应、未来导向和用户交互；我们尚未看到其中任何一项单独闭合这个问题：

> **当 Agent 被反复针对评测选择和优化后，评测上的改进还能否预测后来真实软件工程工作上的改进？**

Barcarolle 的现有地基是一个按 repository 定制、按历史时间切点回放的评测编译器和证据边界：只使用切点当时可见的信息编译评测，让完整 Agent 在干净 workspace 中工作，捕获最终 diff，在新的 verifier workspace 中注入 private oracle（隐藏验收材料）并重放，然后才打开后续真实 Task outcomes。新方向不是把它改造成 trainer，而是从“固定一个 Agent 时预测准不准”升级到“Agent 根据评测持续变化后还能不能选对”：记录每一轮 Agent version 和 benchmark exposure，比较评测增益、winner choice 与 later-real-work 增益。

当前证据证明了工程回放与审计链可以工作，但没有证明新的科学主张。一项 13 个同运行框架模型、500 题、5 仓库的回溯式开发实验中，`consensus_rate_match` 在“每个仓库等权”的口径上，把后续 5/10 个真实任务的平均预测误差相对降低 3.42%/10.62%；但改成“每个历史时间切点等权”后方向反转，换成不同完整 Agent system/运行框架也没有保持优势。这项方法是在后续结果已经打开的多路线搜索中选出的，属于 outcome-open development evidence，不是独立确认。下一步应先研究参考 Agent 与目标 Agent 的适用范围、没有/已有目标 Agent 历史结果的两种情形、证据不足时拒绝强行排序，以及版本差值能否保留；然后再做同初始 Agent、同 proposer、同预算、只换 evaluator，且真实未来在选择冻结前保持密封的对照实验。

我们不声称能预测未来本身，也不声称 Generator 可以替代真实工作。项目的有限主张是：

> **构造一种评价方式，使今天看起来更好的 Agent，更大概率在明天真实到来的工作上也确实更好；并测出这种评价能可靠指导多大的连续优化压力。**

## 1. 先看一个可能发生的失败

假设团队有一个基线 Agent A，并连续产生三个版本：B、C、D。下表只是说明失效机制的假设数字，不是 Barcarolle 的实验结果。

| 版本 | 固定 benchmark | 后来真实任务 |
| --- | ---: | ---: |
| A | 60 | 60 |
| B | 70 | 67 |
| C | 80 | 70 |
| D | 90 | 68 |

从 A 到 C，分数和真实能力都上升；到 D，benchmark 继续大涨，真实效果却下降。benchmark 没有在某一刻突然“坏掉”。问题是：当搜索越来越积极，系统可能同时找到真正能力增益和测量误差，并逐渐偏向后者。

今天人肉尝试 20 个版本时，这可能只是工程噪声；如果 self-improver 一小时产生 500 个候选，它会有更多机会找到可利用的偏差。于是“最会做考试”的版本可能被选中，而不是“最能完成下个月真实工作”的版本。这里的退化幅度不是既成事实，必须由候选数与反馈暴露的压力曲线来测量。

这就是项目的实际价值入口：**Barcarolle 不是再出一套更难的试卷；它要让试卷持续和后来真实发生的工作对账。**

## 2. 先直接回答“能不能指导项目优化”

这句质疑在 11 轮讨论中有三种不同含义，答案不能混在一起。

第一，如果问题是“benchmark 能否直接告诉人或 Agent 下一步该改 retrieval、prompt、工具还是 repository 架构”，目前不能承诺。失败归因不等于某个改动的因果效果；一组已知改动如果可以直接做 ablation，就应直接做 ablation。

第二，如果问题是“已有若干 Agent/system 版本时，benchmark 能否判断哪个值得继续或 ship”，这正是 Barcarolle 要升级验证的命题：从预测一个版本的绝对分数，走向保留版本之间的改进差值、排序和最终选择。它尚未被当前证据证明，但有清楚的历史回放和密封未来实验路径。

第三，如果问题是“让 Agent 自己修改项目，并判断项目整体变好了多少”，一般情形下没有形成可执行闭环。项目改动会改变后来可能出现的 workload；不做改动时的反事实任务无法同时观察；“项目变好”也没有一个天然统一的二元标签。为回答这项需求而临时生成时延、维护性或架构分数，会改变原项目的 workload 和 outcome 语义，并让 Generator 自己定义目标。

因此当前故事主动收缩范围：

> **Barcarolle 不产生优化方向；它研究当外部优化者提出下一批 Agent 版本时，怎样判断哪些改进更可能迁移到未来真实工作。**

这里 workload 仍是外部后来发生的软件工程需求；Generator 预测并具体化需求，不生成“项目提升了多少”的标签。第一阶段 outcome 仍是可执行的 pass/fail，time、cost、interaction 和 correction 作为后续向量扩展。Diagnostic interventions 只是校准 evaluator 的“砝码”，不是处处存在的 gradient；开放候选由人、人机工程流程或外部 self-improver 提出。

## 3. 为什么现有 benchmark 的成功仍然不够

### 3.1 SWE-bench 成功解决了标准化能力测量

[SWE-bench](https://arxiv.org/abs/2310.06770) 把真实 GitHub issue、repository snapshot、patch 和可执行 tests 组合成标准任务。它回答的是：

> 给定同一批固定任务，哪个 Agent 更能解决真实 repository-level issue？

这创造了 realism、comparability 和一个共同进步目标。Barcarolle 不应通过贬低这项贡献来证明自己。

### 3.2 公开固定题会同时遇到污染和 oracle 错配

这两类问题相互独立：

- **污染**：模型训练、微调、合成数据或人工开发过程见过题目、gold patch 或 benchmark 特征；
- **oracle 错配**：测试拒绝功能正确的替代解，或测试太弱而放过错误实现。

[SWE-bench Verified](https://openai.com/index/introducing-swe-bench-verified/) 经 93 名工程师筛选后，OpenAI 在 [2026 年复审](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)中又针对 o3 在 64 次运行中未稳定解决的 138 个难题做分析；这个定向子集里至少 59.4% 有实质性问题，同时受测前沿模型能复现部分 benchmark 细节。该比例不能外推到全部 500 题。[SWE-Bench Pro](https://arxiv.org/abs/2509.16941) 试图以更长任务和私有来源改进；OpenAI 后续 [人工标注汇总](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)将 249/731（34.1%）标为有问题，并结合自动化分析把整体问题率估计为约 30%，因而撤回此前推荐。这里的教训不是“benchmark 无法做”，而是：**任务认证必须可复审、可撤销；任务来源、oracle、Agent exposure 和 claim boundary 必须分开记录。**

### 3.3 滚动更新、自动供应、交互化分别补了一块

- [SWE-bench-Live](https://arxiv.org/abs/2505.23419)、[SWE-rebench](https://arxiv.org/abs/2505.20411) 把固定 snapshot 变成滚动任务供应；
- [SWE-smith](https://arxiv.org/abs/2504.21798)、[SWE-Bench++](https://arxiv.org/abs/2512.17419) 等推进自动/合成任务规模化；
- [SWE-INTERACT](https://arxiv.org/abs/2606.30573)、[SWE-Together](https://arxiv.org/abs/2606.29957) 证明逐步披露需求和用户纠正是不同于终局 pass/fail 的能力轴；
- 时间一致性工作用 T0 之前的 knowledge、T0 之后的 PR 做严格 A/B；
- [SWE-Future](https://arxiv.org/abs/2606.18733) 先预测未来 task families，再按 validated family 合成任务。

这些进展都重要，但它们主要回答“测什么、题从哪里来、如何重放、如何降低污染”。它们没有自动推出：**拿这套评测反复筛 Agent variants 后，最后选中的 winner 仍是 later real work 上的 winner。**

### 3.4 自我改进系统让这件事从理论风险变成现实需求

[Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) 已经展示 Agent 修改自身代码、用 coding benchmark 选择后代的闭环；[Red Queen Gödel Machine](https://arxiv.org/abs/2606.26294) 又把 evaluator evolution 纳入 epoch，并在 epoch 内固定 objective、边界处更新。更早的 [adaptive data analysis](https://arxiv.org/abs/1411.2664) 和 [leaderboard](https://arxiv.org/abs/1502.04585) 理论则形式化了反复查询同一 holdout 何时会产生自适应偏差，以及限制反馈能提供什么保护。

这些工作说明“optimizer 可以搜索 evaluator”已是可研究的系统问题，但不能直接推出每个 coding benchmark 都会严重过拟合。coding-agent 场景还有一个未解决层：**held-out ground truth 不是天然给定的静态数据集；我们真正关心的是特定 repository 后来才发生、不断变化的真实工作。**

## 4. 研究问题：从“测一个 Agent”升级到“选对下一版本”

主材料只需要两个表达式：

```text
Benchmark performance ≈ Future real-work performance
Benchmark improvement ≈ Future real-work improvement
```

第一行是现有 Barcarolle 的 pointwise predictive validity：固定一个 Agent，今天的 benchmark 分数能否预测 next-H Task 的真实表现。

第二行是升级后的 adaptive / selection validity：Agent 会根据左边的反馈持续变化，我们仍希望评测上的增益、排序和 winner choice 能迁移到右边。

这个升级带来三种不同误差：

1. **时间分布误差**：历史 Task 不代表接下来的 repository work；
2. **Agent population shift（受测 Agent 群体变化）**：参考模型上有用的 Task subset，不代表由新运行框架、工具或策略构成的完整 Agent；
3. **自适应暴露误差**：optimizer 看过任务、分数和运行轨迹后，可能利用 evaluator 的盲区。

新项目要分别测量这三种误差，不能把它们压成一个 MAE。

## 5. Barcarolle 的位置：不是榜单，也不是 trainer

Barcarolle 的研究定位可以压成一句英文：

> **Barcarolle studies how to keep agent optimization grounded in future real work.**

拟建目标是一个按 repository 定制、以后来真实工作为锚、持续刷新且可审计的 evaluation substrate；当前已实现的是可复现 benchmark boundary 和初步 selection evidence。外部 Agent/Optimizer 仍拥有模型、prompt、skills、tools、retrieval、edit loop 和改进策略；Barcarolle 只拥有 benchmark boundary：

1. 在 origin 冻结当时可见历史、repository state、Task Pool 和 Selector 输入；
2. 给 solver 只暴露任务材料，在干净 worktree 运行完整 Agent；
3. 只捕获最终 workspace diff；
4. 在新的 verifier workspace 重放 diff，只在那里注入 private oracle；
5. 记录 terminal status、cost、latency、failure label 和 sanitized artifacts；
6. selection 完成后才打开 later real Task outcomes；
7. 报告评测分数与 later-real-work 分数之间的 level、lift、ranking 和 regret。

这条边界让 Generator、Selector、exposure protocol 和 future audit 能被独立替换和检验，而不让任何一个组件自证正确。

在拟建的优化闭环中，三种职责要分开：

- **Proposer（候选提出者）** 产生候选 Agent 状态，可以是工程师、简单配置搜索或 DGM/ADAS 一类外部 self-improver；
- **Evaluator** 给出在当前评测边界下的证据，Barcarolle 主要位于这里；
- **Selection** 根据证据选择下一版本或 abstain（证据不足时拒绝强行排序）。

Barcarolle 提供 selection pressure，不提供 gradient，也不负责保证 Proposer 持续找到好方向。如果候选只有几项已知 intervention，直接 ablation 就够了；Barcarolle 的新增价值出现在候选持续增加、workload 漂移、完整评测昂贵且错误 ship 的代价较高时。

[Braintrust](https://www.braintrust.dev/docs/evaluate/compare-experiments)、[LangSmith](https://docs.langchain.com/langsmith/compare-experiment-results) 一类平台已经能在给定 dataset 上运行和比较多个实验、显示 improvement/regression。Barcarolle 不重复这层 execution；它要验证的是：**这些离线比较是否仍能代表下一批真实工作。** 其最短用户价值可以写成：`Run fewer tasks. Make fewer wrong ship decisions.`

拟验证的接入流程是：团队提交若干冻结 Agent versions；Barcarolle 在 repository 的历史时间切点编译同一评测并输出 winner 或“证据不足”；所有选择冻结后，才用后来真实任务复核。当前仓库还没有证据支持把这段流程作为已验证产品能力。目标指标不是“多一个榜单分数”，而是错误 ship 次数、top-1 decision regret（按评测选择的版本与未来最佳版本之间的真实差距），以及达到同等 regret 所需的评测成本。

## 6. 已有工程地基：工程闭环与初步统计候选

### 6.1 可审计运行闭环已存在

仓库已有 Task supply/certification、Workspace、Verification、Result Store、Selection、Reporting 和 Runner。工程 campaign 中，75 个 SymPy Verified 候选的冻结→准备→认证路径跑通；238 cells 全部终止，237 scoreable、1 `agent_invalid`，且没有 retry/replacement，见 [`study-results.json`](../../../examples/model_agent_study/study-results.json)。另一次 selector 复现得到 byte-identical 输出，见 [`consensus-rate-summary.json`](../../../examples/modern_agent_panel/evidence/consensus-rate-summary.json)；独立实现重新计算 1,183 个 primary membership/score cells，未发现 mismatch，见 [`consensus-rate-transfer-diagnostic.json`](../../../examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json)。

这证明系统可以产生审计证据，不证明科学主张已经成立。

### 6.2 一个窄但真实的 development result

在 13 个 mini-SWE-agent v2 模型、500 个任务、5 个仓库、61/30 个 H5/H10 origins（历史时间切点；每个切点后取 5/10 个真实任务）上，`consensus_rate_match` 的 repository-equal（每个仓库等权）结果为：

| MAE（平均绝对预测误差） | H5 | H10 |
| --- | ---: | ---: |
| Full history | 0.179527 | 0.129700 |
| Candidate | 0.173387 | 0.115927 |
| Candidate − Full | -0.006140 | -0.013774 |

这相当于相对降低 3.42% 和 10.62%。候选保持 raw benchmark semantics：目标 Agent 在十个选中 Task 上的未加权 pass rate。

主结果见 [`consensus-rate-summary.json`](../../../examples/modern_agent_panel/evidence/consensus-rate-summary.json)；跨 system/Harness 诊断见 [`consensus-rate-transfer-diagnostic.json`](../../../examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json)。

### 6.3 最重要的发现其实是它在哪里失败

- 换成 Origin-weighted：H5/H10 变为 +0.004284/+0.001864，方向反转；
- 三个 modern complete systems 做 internal LOO：+0.014960/+0.024006；
- 用 13 primary references 预测三个 external systems：+0.017513/+0.007707；
- favorable Origins 只有 23/61 和 13/30；
- 候选来自 outcome-open 的多路线搜索，不是独立确认。

因此当前最强结论不是“我们已有好 Selector”，而是：

> **在预先定义的 repository-equal development estimand 上，一个同 Harness、有限 reference panel 的 Task coreset 表现更好；但它在被测的完整 system/Harness 迁移实验中没有保持优势。具体原因仍需分离 population shift、样本量、Agent–Task interaction 与任务构成。**

这把下一步指向受测 Agent 群体变化下的 selection，以及随后才施加的 adaptive pressure，而不是继续优化同一汇总分数。当前材料不能把后者写成已经观察到的故障。

## 7. 新增科学问题：四个 work packages

### WP1 — Generator external validity

拟建 Generator 不能只是“LLM 生成更像真的题”。它至少分两步：

1. Forecaster：从 origin 前历史预测未来需求方向；
2. Materializer：把一个需求方向具体化为 requirement、environment、hidden checks 和 executable task。

[SWE-Future](https://arxiv.org/abs/2606.18733) 已显著推进第一步：冻结 task-family forecast，再用后续 PR 回溯验证。但正确方向不自动产生正确题。比如我们预测 repository 未来需要“支持新的 serialization 类型”，Materializer 仍要决定具体类型、API、edge cases 和 tests。如果这些决定全由同一个 pipeline 控制，Agent 最后可能只是在适应该 pipeline 的口味。

因此要分别验证三层：

- **forecast validity**：方向是否对应后来真实工作；
- **materialization validity**：同一方向的合理具体化是否给出稳定、非任意的 Agent contrasts；
- **response validity**：synthetic workload 上的 score/ranking/lift surface 是否预测 later real workload。

决定性实验：同一 demand family 多次独立 materialize；比较 Agent A/B 的差值是否频繁翻转；再让不同 Materializer 交叉生成。Response calibration 只能使用较早 rolling origins 的 development blocks；Materializer、阈值和超参数必须在后续 sealed evaluation block 打开前冻结。同一个 later-real block 不得同时用于校准和最终评估；数据不足时按时间做 cross-fitting，不能随机拆分。如果一个 improvement 只在某个 Materializer 上成立，就不能用它声称 future utility。

Reality Generator 应尽量 Agent-blind。另设查看 failure traces 的 Challenge Generator 可以帮助训练，但 challenge score 不应冒充真实未来工作的无偏代理。

### WP2 — Contrast-aware Selector

现有 Selector 主要保留一个 Agent 的平均 pass rate；拟建的自我改进场景需要保留候选 Agent 之间的相对差异。目标函数应从 level MAE 扩到：

- pairwise lift error；
- improvement/regression sign accuracy；
- ranking correlation；
- top-1 selection regret；
- worst-case candidate-pair distortion。

同时分开 cold start（没有目标 Agent 的历史结果）和 warm start（已有少量目标 Agent 的历史结果）。先冻结参考样本的适用范围、abstention 或对目标 Agent 更稳健的规则，再查看 future outcomes。现有 transfer failure 提示适用范围可能不足；“强行排序比保留 Full 更差”仍需在预注册边界上验证。

### WP3 — Adaptive exposure / refresh protocol

拟把 evaluator exposure 变成显式状态：optimizer 看过哪些 tasks、aggregate scores、failure traces 和 checks。一个候选协议是：

- epoch 内 evaluator 完全冻结；
- optimizer 可以在明确预算内搜索；
- epoch 边界才 refresh Task material / Selection；
- old evidence 有 validity lifetime；
- later real workload 永远不进入 optimization loop；
- development eval 和最终 assurance audit 分开。

这与现有 immutable Origin、Selection、Result identity 和 provenance 直接兼容，初期只需在 experiment layer 表示 trajectory，无需立即扩大 core schema。

### WP4 — Adaptive optimization experiment

不必先发明 RSI system。拟用一个简单、可复现 proposer：它可以在 prompt、tool policy、context、retrieval、retry 或 harness configuration 上产生候选 Agent。

固定：同一个初始 Agent、同一个 proposer、同样 K 轮/候选预算。只改变 fitness evaluator：

- static historical benchmark；
- recent-N tasks；
- current Barcarolle；
- refreshed/abstaining Barcarolle。

搜索全部结束后，一次性打开历史上当时不可见的 next-H real tasks。报告每一轮 benchmark gain 和最终/逐轮 real-future gain，并计算 winner ranking、selection regret、虚涨比例与 optimization horizon。

## 8. 待验证指标：Optimization Horizon

一个易懂的产品化指标是：

> **一套 evaluator 能可靠承受多少候选、多少轮或多强的 optimization pressure，benchmark gain 才开始不再转化为 real-future gain？**

这不是当前已测结果，而是待验证的新指标。它应该和具体 protocol 绑定：例如最多 100 个候选、20 轮、固定反馈粒度。不能抽象地说“counter-Goodhart”。

预先声明的目标结果按强度分三层，均尚未获得：

1. 固定 candidate panel：比 Full/recent/random/regression suite 更少选错 future winner；
2. 随候选数和 exposure 增加：lift error 和 regret 增长慢于 static eval；
3. 同一 self-improver/预算：Barcarolle 组最终在 sealed future workload 上产生更大真实增益。

项目价值应该以决策结果表达，而不主要以 “MAE 小了 0.01” 表达。

## 9. 可行性、阶段目标与 stop gates

### Milestone 0：先用现有候选池测 selection pressure

不先造新 Generator，也不需要真正 self-improver。从现有 candidate pool 中把可搜索候选数依次设为 2、5、10、20、50；对 Full、recent、random 和 Barcarolle 分别选择 winner，再用历史上当时密封的 next-H outcomes 计算 regret。候选池顺序、抽样和主指标要先冻结。

这个实验最便宜地回答：pointwise prediction 与 selection validity 是否确实不同，以及错误选择是否随可搜索候选数增加。它仍不是 adaptive closed loop，因为候选不是根据 evaluator 反馈生成的。

### Milestone 1：先解决 population shift

用现有公开 outcomes 分析 reference-panel size、target ability、model family、Harness shift；分开 cold/warm start；冻结 support/abstention rule。禁止继续调同一五仓库 repository-equal 分数。

成功标准：在未参与规则选择的新 same-Harness target boundary 上，contrast-aware rule 对 H5/H10 至少不劣于 Full，并改善预先声明的 winner/lift metric。若 support 不足，正确动作是 abstain，不是制造精确排名。

### Milestone 2：Generator synthesis sensitivity

对多个 demand families 做 repeated/cross materialization，以 Agent panel 形成 response vectors；检验同 family 内 contrast variance 和跨 Materializer transfer。

成功标准：response-calibrated materialization 相对 semantic-only baseline 更好预测 later-real-work contrasts，且结果不由一个 oracle/pipeline 决定。

### Milestone 3：受控 adaptive pressure

让简单 proposer 在不同 evaluator 上做同预算搜索，future block 在搜索结束前密封。

成功标准：Barcarolle 的 selection regret/lift error 曲线随 exposure 上升得更慢；若没有优势，应定位失败来自 demand forecast、materialization、selection support 还是 exposure protocol。

### Milestone 4：prospective audit

冻结 pipeline 后，在新 repository/time window 上等待真实工作到来。这个阶段才支持 strict-prospective claim。

## 10. 风险与对应验证

| 风险 | 为什么危险 | 检查/应对 |
| --- | --- | --- |
| 未来 workload 不可完美预测 | 可能把“预言未来”当不可能目标 | 只要求相对 Full/recent 更好，并允许 uncertainty/abstention |
| Materializer 决定结论 | 同一方向的具体题可能翻转排名 | repeated synthesis、cross-materializer、response calibration |
| reference panel 与新 Agent 不同 | 当前 development 诊断中，候选在跨 system/Harness 场景没有保持优势 | support diagnostics、cold/warm split、新 same-Harness boundary |
| oracle/test 错配 | hidden 不代表正确 | solution diversity、independent audit、later task invalid rate、可撤销认证 |
| optimizer 通过 traces 反推 evaluator | failure feedback 本身泄漏 | exposure ledger、feedback budget、epoch refresh、separate assurance set |
| 同一数据上调参和证明 | outcome-open search 产生乐观偏差 | frozen plan、external boundary、prospective audit |
| 指标太多导致目标漂移 | time/cost/interaction 混成万能 utility | 第一阶段保留 pass/fail，其他 outcome 先作为 vector/Pareto 报告 |

## 11. 明确不 claim 什么

Barcarolle 不负责：

- 自动提出好的 Agent intervention；
- 解决通用 RSI；
- 定义所有软件项目的价值函数；
- 保证 Generator 绝对无法被利用；
- 用 synthetic workload 取代真实 future workload；
- 从当前 development result 推出跨 Harness/模型家族/仓库泛化；
- 声称已经有 production Selector 或已经获得 field validity。
- 把 outcome-open retrospective development 结果写成 independent、confirmatory 或 strict-prospective evidence；
- 声称反复优化已经在 Barcarolle 上造成可测的 Goodhart 退化。

它研究的是一个更有限、可证伪、但基础的命题：

> **Can we construct an evaluator whose feedback stays aligned with later real work under increasing adaptive optimization pressure?**

## 12. 评委应该记住的三句话

1. 现有 benchmark 很适合测 Agent；当 Agent 开始反过来针对 benchmark 自动优化时，评测承担了新的选择责任。
2. 候选和反馈越多，benchmark 里的小偏差越有机会被放大；是否以及多快发生，必须用密封未来实验测量。
3. Barcarolle 研究怎样让评测持续和后来真实发生的软件工程任务对账，目标是更可靠地选出“未来工作上真正更好”的下一版本。

## 13. 建议的决策

批准一个分阶段、证据驱动的研究方向，而不是承诺一个完整 RSI 平台：

- 先复用现有 Barcarolle 边界，解决 Agent population shift 和 contrast-aware selection；
- 再验证 forecast→materialization→response 三层 Generator validity；
- 最后施加 adaptive optimization pressure，并用 sealed/prospective future workload 外部审计；
- 每一阶段均可独立失败、定位和停止，不以愿景替代结果。

---

详细来源与逐项缺口见 `research/landscape.md`；仓库证据与数字见 `research/barcarolle-position.md`；严格定义与实验协议见 `research/adaptive-validity.md`；讨论如何从“项目优化”收敛到当前故事见 `discussion-synthesis.md`。原始 11 轮可见问答在 `raw/chatgpt-share-transcript.md` 和 `raw/chatgpt-share-messages.json` 中完整保留，不被这些整理稿替换。
