# 11 轮讨论如何收敛成当前项目故事

> 本文不是原始聊天的替代品。它记录问题怎样被提出、哪些方向被质疑后放弃、最终保留了什么。逐字原件见 `raw/chatgpt-share-transcript.md`，结构化原件见 `raw/chatgpt-share-messages.json`。
>
> 这是 2026-08-13 的讨论史，不是当前路线。特别是其 population-shift-first
> 顺序与旧指标层级已由
> [`../../research-program.md`](../../research-program.md) 取代。

## 1. 起点：技术闭环存在，但“so what”没有闭环

最初命题是：用历史真实 Tasks 编译动态 benchmark，使固定 Agent 在 benchmark 上的 pass rate 接近它在后来真实 Tasks 上的 pass rate；Generator、Selector 和误差分解都可分别评价。这是讨论的研究设定，不代表仓库已完成 Generator 或已获得 prospective validity。

用户提出的质疑有两层：

1. 即使分数预测得更准，为什么团队需要接入？
2. 用户要的是 benchmark “指导项目优化”，而现有任务只测 Agent 能否完成外部给定工作。

第一轮回答先把价值从绝对分数移动到工程决策：一个 benchmark 即使把两个版本的绝对分数都估得很准，仍可能把 improvement/regression 的方向排反。由此形成三级目标：level fidelity、contrast fidelity、decision fidelity；top-1 decision regret 比单一 MAE 更接近用户损失。

但这还没有回答“优化项目本身”。后续讨论的价值正是在这里连续纠错，而不是把第一次回答包装成最终答案。

## 2. 为什么 SWE-bench 不需要同样的购买证明

第二轮识别出公共 benchmark 和 repo-specific predictive eval 的社会功能不同。

讨论提出一个产品定位上的推断：SWE-bench 的核心价值不只来自测量精度，还来自一个公开、标准、可比较的坐标系。研究者和供应商愿意在同一榜单上投入，本身产生协调和 network effect。因此，公共 benchmark 的采用逻辑不完全依赖逐家公司证明“这个分数能预测你下个月的真实 workload”。这项解释是对采用机制的分析，不是本次调研直接测得的因果结论。

Barcarolle 的原始叙事却更像内部决策产品：它主动针对某个 repository 和未来工作，并承诺 predictive validity。它没有公共 benchmark 自动获得的协调资产，因此必须回答本地决策是否更好、错误选择是否更少、评测成本是否更低。

讨论由此排除了一个混合叙事：不能一边用“SWE-bench-X”的公共 benchmark 语言，一边要求用户为 repo-specific decision tool 付费，却不提供相应决策证据。

## 3. 第一次错误扩张：从 Agent 版本选择跳到“项目该怎么改”

第三、四轮尝试把被优化变量从 Agent 改成 Project：固定 Agent，通过 diagnostic interventions 修改 repository 的文档、测试、接口或结构，测哪些改动能恢复失败；再进一步想象一个 Project Optimizer Agent，自主决定 what to change 和 how to change。

用户指出这仍混淆了两件事：让 benchmark 帮工程师优化 Agent/repo，与让 Agent 自主优化项目，不是同一个接口。普通 SWE-bench 的输入已经包含外部给定 Task；项目优化 Agent 则必须自己发现机会和定义优先级。

这个方向一度给出一个有吸引力的类比：SWE-bench 给 Agent 一张 todo list；项目优化 benchmark 不给 todo list，而看 Agent 能否提前把项目改到让未来 todo list 更容易完成。但讨论没有找到在一般情形下同时可观测的反事实测试集和统一 outcome。

## 4. 决定性反驳：一般的项目优化没有保持原始闭环

第五轮把问题推到可行性层面：未来 workload 在项目改动后会变成 treatment-dependent。

一次架构改动可能消灭一类未来 bug，又产生另一类工作；真实世界只能观察“做了改动”或“没做改动”其中一条路径。与此同时，“项目改善多少”可能是时延、成本、维护性、安全性或 agentability 的多维结果，不再天然对应原始 Task 的 pass/fail。这不等于所有项目优化都不可评测：在外生 workload、明确 outcome 或可随机化干预成立的窄场景中仍可研究；它只是不能作为当前的一般性主张。

如果让 Generator 同时生成需求、验收标准和“项目提升”标签，系统就自己定义了目标，再自己证明目标达成。这破坏了原始 Barcarolle 最重要的外部锚：历史真实工作与后来真实工作语义一致，并可做 rolling-origin 验证。

因此讨论明确撤回一般化的“project optimizer benchmark”主张。最多保留狭窄的 future changeability/agentability 作为可能扩展；它不进入第一阶段承诺。

对最初质疑的最终答复是：

- benchmark 不能仅凭 observational failures 告诉你具体该改什么；
- 它可以研究“改完以后，依据什么判断该不该 ship”；
- Barcarolle 解决可信 objective/evaluator，不同时承担 open-ended optimizer。

## 5. 第二次收敛：Proposer 和 Evaluator 必须分工

第六、七轮把“像 gradient descent”修正成 black-box/evolutionary search：

- Proposer 持续产生 Agent candidates；
- Evaluator 对 candidates 给出反馈；
- Selection 决定下一版本或拒绝判断。

Barcarolle 的拟建位置是 Evaluator/evidence boundary，不是 Proposer。Diagnostic interventions 只是检查 evaluator 能否识别已知对照的校准砝码，不是连续、处处存在的 gradient。如果只存在几项已知 intervention，直接 ablation 即可；开放式候选生成可由工程师、简单搜索或外部 DGM/ADAS 类 self-improver 完成。当前仓库已有 evidence boundary，不等于完整的 adaptive Evaluator 已实现。

这一步让 RSI 进入故事，但不是项目成立的前提。今天团队已经会根据 benchmark 选择 prompt、模型、工具和 Harness；self-improvement 只是让候选产生更便宜、优化压力更大。项目的稀缺能力是 selection signal，而不是同时造 proposer、trainer 和 self-modifying Agent。

## 6. 从 pointwise prediction 升级到 adaptive selection validity

原问题是：固定一个 Agent，今天的 benchmark score 能否预测 later real-work score。

升级后的问题是：Agent candidates 正是根据此前 evaluator 反馈产生的；在这种条件下，benchmark 上的 lift、排序和 winner 是否仍迁移到 later real work。

由此提出核心对照实验：同一个初始 Agent、同一个 proposer、同样 K 轮或候选预算，只替换 evaluator；搜索结束后一次性打开此前密封的 future workload。报告 benchmark gain、future gain、pairwise lift error、sign accuracy、top-1 regret 和虚涨率。该实验尚未执行，密封性、随机种子、预算等价和泄漏检查都需要机器可验证。

“Optimization Horizon”由此产生：在明确的 proposer、反馈粒度、预算和误差阈值下，一套 evaluator 能承受多少候选/轮次，benchmark gain 才开始持续不再转化为 real-future gain。它是待测 protocol-level 指标，不是 Barcarolle 已有属性。

## 7. 可行性审查：已有的是地基，不是新命题的完成品

第八轮的判断是：现有 Generator/Selector、rolling origin、Task/Check、Result provenance 和 hidden verification 足以支撑第一块工程地基，但远未证明 adaptive safety。

特别是仓库当前 evidence 暴露了前置问题：一个在同 Harness、repository-equal 口径下有改善的 Selector，换 weighting 后反转，在已测的完整 Agent system/Harness 场景也没有保持优势。这与 Agent population shift 假说相符，但也可能受样本量、任务构成或 Agent–Task interaction 影响；它不是 adaptive Goodhart 的证据。研究顺序应先处理 reference-to-target support、cold/warm start 和 abstention，再增加真正闭环压力。

最便宜的实验不需要 self-improver：在已有候选池上逐步允许 evaluator 从 2、5、10、20、50 个候选中挑 winner，观察 historical sealed-future regret 是否扩大。这先检验 selection validity；随后才让 candidates 根据 evaluator 自适应产生。

## 8. Generator 是最大研究风险：有效性必须拆成三层

第九轮接受了对 SWE-Future 的关键批评：验证未来 task family 的相关性与生成题的可执行性，不等于验证 family 被具体化成哪个 requirement、acceptance criteria、test 和 gold patch 是真实的。

因此拟建 Generator 不应以“看起来像真实任务”自证，而要拆成：

1. forecast validity：需求方向后来是否真实出现；
2. materialization validity：同一方向的合理具体化是否不随任意出题选择翻转 Agent contrast；
3. response validity：synthetic workload 上的分数、lift 和 ranking 是否预测 later-real workload。

方法包括 repeated independent materialization、cross-materializer、synthesis sensitivity、solution/oracle independence 和按时间分块的 response calibration。校准只用较早 rolling origins 的 development blocks，所有配置在后续 sealed block 打开前冻结；同一 later-real block 不能同时校准和评估。用于评价的 Reality Generator 尽量 Agent-blind；查看 failure traces、专门找弱点的 Challenge Generator 可以服务训练，但其分数不能声称代表 future utility。

“counter-Goodhart”也不应被写成 Generator 的单独属性。最多是 Generator、contrast-aware Selector、exposure/refresh protocol 和 real-future audit 整体在特定实验中的表现。

## 9. 最终项目故事

面向管理评委的完整逻辑是：

1. 现有 benchmark 成功回答“Agent 能否完成一批真实任务”；公共榜单还提供行业协调价值。
2. Agent 团队已经用 benchmark 选择下一版本；如果候选生成进一步自动化，评测会从尺子进一步变成 optimization objective。
3. 绝对分数准确不保证 lift、排序和 ship decision 正确；退化是否随压力增加必须实测。
4. later real repository work 是不能由系统自行定义的外部锚。
5. Barcarolle 已有可审计的 repo-specific rolling-origin evidence boundary，但当前 Selector 只是一项窄 development candidate；其跨 system/Harness 结果没有保持优势，population shift 是待分离的优先假说。
6. 下一步依次验证固定候选选择、support/abstention、Generator 三层有效性、自适应压力和 prospective external confirmation。
7. 长期价值是为外部 self-improver 提供更可信的 selection pressure；近期价值是少跑任务、少做错误 ship decision。

一句话版本：

> **我们不预测未来本身，也不替 Agent 产生所有改进方向；我们研究怎样让“今天评测上更好的下一版本”更大概率在后来真实工作上也确实更好。**

这里的 workload 与 outcome 必须继续分开：workload 是外部需求流；outcome 是 Agent 执行需求后测得的结果。第一阶段仍用 pass/fail；time、cost、interaction 和 correction 只作为后续可测扩展。Generator 可以预测并具体化需求，但不能自行生成“项目价值已经提高”的结论。

## 10. 证据口径：事实、推断和假说

- **已核对事实**：原始聊天共有 11 轮可见问答；仓库已有 Task/Check、Workspace、Verification、Result Store、Selection、Reporting 和 Runner 边界；当前 selector 结果来自 retrospective、outcome-open development；换 weighting 反转，在已测的跨 system/Harness 场景没有保持优势。
- **由事实支持的解释**：参考 Agent 与目标 Agent 的适用范围是当前优先故障假说；公共 benchmark 与 repo-specific eval 的采用逻辑不同；Generator 的 materialization 是独立有效性环节。
- **待验证假说**：候选数、反馈暴露或搜索轮数增加会使 static evaluator 的 future regret 上升；contrast-aware、refreshed 或 abstaining Barcarolle 会让这种退化更慢；response-calibrated materialization 会更好迁移到 later real work。
- **愿景**：在外部 self-improver 中长期提供可信 selection pressure。愿景不应被写成当前产品能力或现有实验结果。

## 11. 原讨论中被明确排除的表述

- “Barcarolle 能自动指导 Agent 怎样优化整个项目。”
- “Diagnostic interventions 就是 Agent 优化的 gradient。”
- “预测到 future family，就已经有真实 future benchmark。”
- “合成题可替代后来真实 workload。”
- “当前 MAE 正结果已经证明版本选择或 adaptive safety。”
- “反复优化一定造成严重 benchmark overfitting。”
- “RSI 必须先实现，项目才有近期价值。”
- “当前跨 system/Harness 结果已经识别出唯一因果机制。”
- “Optimization Horizon 已经测得，或 Barcarolle 已经能延长它。”

这些排除项不是弱化项目，而是保住了可观测对象、外部锚和可证伪实验。
