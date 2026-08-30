# PPT 逐页材料索引（建议 15 页）

> 本文件是 2026-08-13 第一版技术提纲，保留供追溯；同批汇报优先使用
> [`strategic-slide-outline.md`](strategic-slide-outline.md)。当前项目研究合同见
> [`../../research-program.md`](../../research-program.md)。

> 目标读者：非原生 AI 背景、技术转管理的评委。建议先讲问题与决策价值，再讲领域位置和已有证据，最后讲拟建方案、实验、效果假说、风险与立项决策。
>
> 证据标记统一使用：`OBSERVED` = 已有直接材料；`INFERENCE` = 基于观察的解释；`HYPOTHETICAL` = 待验证假说。Python 图中的前两张是 observed development evidence，第三张是假设机制图。

## 第 1 页｜封面：评测将从“尺子”变成“选择压力”

**一句主结论：** Barcarolle 研究怎样让 Agent 的连续优化仍和后来真实工作对账。

**建议内容：**

- 标题：`Barcarolle：面向未来真实工作的持续可信评测`
- 副标题：`As proposing improvements becomes cheap, selecting real improvements becomes the bottleneck.`
- 只放项目名、日期和一句话，不在封面堆术语。

**可用文件/图：**

- 旧 ImageGen 封面图已按 artifact-hygiene 规则从公开归档移除；使用纯文字
  封面，或从 `figures/story/` 选择不承载证据结论的示意图。

**口头边界 / 不要说：**

- 说“研究目标”，不说“已实现 counter-Goodhart”。
- 不把主视觉解释成当前 Generator、adaptive protocol 或系统架构已经实现；它只表达概念分工。

## 第 2 页｜问题：涨分不一定等于真实进步

**一句主结论：** 当候选数和反馈增加，评测中的小偏差有更多机会被选中。

**建议内容：**

- 用 A/B/C/D 四个版本讲数字例子：benchmark 为 60/70/80/90，后来真实任务为 60/67/70/68。
- 指出 D 的 benchmark 最高，但真实表现低于 C。
- 收束成问题：评测还能否选对下一版本？

**可用文件/图：**

- `briefing.md` §1 的表格，可直接重绘成两条简单折线。
- 若不重绘，仅用四列数字卡片即可。

**口头边界 / 不要说：**

- 必须标注 `HYPOTHETICAL — NOT MEASURED`；这些数字不是 Barcarolle 实验结果。
- 不说“优化次数越多必然退化”；说“风险是否以及多快上升，需要压力曲线实测”。

## 第 3 页｜价值：从测分数转向少选错版本

**一句主结论：** 用户购买的不是更精确的分数，而是更少的错误 ship decision 和更低的评测成本。

**建议内容：**

- 两行表达式即可：`Benchmark performance ≈ Future performance`；`Benchmark improvement ≈ Future improvement`。
- 从 level fidelity 依次落到版本差值、排序和 top-1 decision regret。
- 产品化表达：`Run fewer tasks. Make fewer wrong ship decisions.`

**可用文件/图：**

- `briefing.md` §§4–5。
- `research/adaptive-validity.md` 的指标定义作为讲者备份，不建议全放正文。

**口头边界 / 不要说：**

- `INFERENCE / RESEARCH TARGET`：低 pointwise MAE 不保证选对版本，但实际损失多大尚未测。
- 不把“少选错”说成当前产品 KPI；它是待验证的价值指标。

## 第 4 页｜先回答质疑：“指导项目优化”有三种含义

**一句主结论：** Barcarolle 不负责告诉 Agent 该改什么；它研究改完以后依据什么判断该不该选。

**建议内容：**

- 三栏呈现：
  1. 直接建议改 retrieval、prompt 或架构：当前不能承诺，已知有限选项应做 ablation。
  2. 在多个 Agent/system 版本中选值得 ship 的版本：这是拟验证核心。
  3. Agent 自主修改整个项目并评价项目整体价值：一般情形下 future workload 随干预改变，第一阶段不承诺。
- 页尾一句：`Barcarolle provides selection pressure, not gradients.`

**可用文件/图：**

- `briefing.md` §2。
- `discussion-synthesis.md` §§3–5。

**口头边界 / 不要说：**

- 不说项目优化永远不可评测；外生 workload、明确 outcome 或可随机化的窄场景仍可研究。
- 不把 failure attribution 当成 intervention 的因果效果。

## 第 5 页｜Landscape：领域分别补了哪些缺口

**一句主结论：** 真实性、认证、持续供应、未来方向和交互都在进步，但任何一项都不自动保证反复选择后仍选对未来 winner。

**建议内容：**

- 用五到六条短横带，不做论文名堆墙：
  - SWE-bench / Verified / Pro：真实任务、标准化、认证；
  - Live / rebench / Bench++：持续供应与自动构造；
  - SWE-Future：预测未来需求方向；
  - INTERACT / Together：任务怎样展开、用户如何纠正；
  - DGM / RQGM：自动候选搜索与 evaluator evolution；
  - adaptive data analysis：反复查询 holdout 的统计风险。
- 右侧统一写“仍未单独回答”：评测被持续用于选 Agent 后，later-real-work ranking 是否保持。

**可用文件/图：**

- `research/landscape.md` §2 的对比表。
- `claim-evidence-matrix.md` C01–C11、C29–C33。

**口头边界 / 不要说：**

- `OBSERVED + SYNTHESIS`：说“本次调研覆盖的代表性工作中尚未看到单项闭环”，不说“整个领域无人做”。
- 不把 SWE-Future 的 58.1% 说成精确未来 issue 命中率或 Agent pass rate。
- 不贬低现有 benchmark；它们已经解决重要且不同的问题。

## 第 6 页｜我们的位置：公共榜单、EvalOps 与 Barcarolle

**一句主结论：** 公共 benchmark 提供共同坐标，EvalOps 执行版本比较，Barcarolle 拟研究这些比较能否迁移到下一批真实工作。

**建议内容：**

- 三列对比：
  - 公共 benchmark：standardization、comparability、coordination；
  - Braintrust/LangSmith 类 EvalOps：在给定 dataset 上运行、比较、看 regression；
  - Barcarolle：repo-specific、rolling-origin、later-work external validity。
- 突出：不是另一个 leaderboard，也不是 trainer。

**可用文件/图：**

- `briefing.md` §5。
- `research/landscape.md` §§4–5。
- `claim-evidence-matrix.md` C25–C27。

**口头边界 / 不要说：**

- coordination/network effect 是 `INFERENCE`，不是本次实验证明的采用因果。
- 不暗示现有 EvalOps 没有线上监控或其 dataset 必然缺乏 external validity。

## 第 7 页｜职责边界：Proposer、Evaluator、Selection

**一句主结论：** 外部系统提出候选，Barcarolle 提供证据，Selection 选择或拒绝判断。

**建议内容：**

- 简单三段流程：`Proposer → Candidate Agents → Barcarolle Evaluator → Select / Abstain`。
- 下方放 later real workload，强调它在选择冻结后才打开。
- 说明 workload 是外部需求；outcome 是执行后测得的 pass/fail，后续才扩展 time/cost/correction。

**可用文件/图：**

- `briefing.md` §§2、5。
- `discussion-synthesis.md` §§5、9。
- 可裁切使用 hero 中的概念元素，但建议重新画简洁流程；hero 仍标 `CONCEPT ART`。

**口头边界 / 不要说：**

- 当前已有 evidence boundary，但完整 adaptive Evaluator 尚未实现。
- Generator 不能生成“项目价值提高”的标签；later real workload 不能由系统自行定义。

## 第 8 页｜已有工程地基：边界可运行、可重放、可审计

**一句主结论：** Barcarolle 已经跑通 benchmark 边界，但这只证明工程证据链，不证明科学泛化。

**建议内容：**

- 展示当前模块链：Task Pool / certification → clean Workspace → diff capture → fresh Verification + hidden oracle → Result Store → Selection / Reporting。
- 放三个工程数字：75 Task/Check、54 clusters；238 cells 全部终止；237 scoreable、1 invalid、无 retry/replacement。
- 可补一句：两次 selector 运行 byte-identical，独立复算未发现 mismatch。

**可用文件/图：**

- `research/barcarolle-position.md` §§2–3.1。
- `briefing.md` §6.1。
- `claim-evidence-matrix.md` C12–C13。

**口头边界 / 不要说：**

- `OBSERVED`，但只证明执行与审计闭环。
- 不说 adversarial sandbox；当前内置执行仍共享 caller host 权限。
- 不用装饰性概念图证明系统组件已经存在。

## 第 9 页｜已有正证据：一个窄 development estimand 上改善

**一句主结论：** 在同 Harness、五仓库、repository-equal 的 outcome-open development 口径上，候选 Selector 降低了预测误差。

**建议内容：**

- 用一张图配一句数字：H5/H10 相对 Full 的 MAE 分别降低 3.42%/10.62%。
- 简释 H5/H10：历史时间切点后的 5/10 个真实任务。
- 简释负值：Candidate MAE 低于 Full，越负越好。

**可用文件/图：**

- `figures/observed-selector-boundaries.png` 或可编辑 `figures/observed-selector-boundaries.svg`；本页只聚焦最左侧 repository-equal 分组，也可下一页继续使用完整图。
- `briefing.md` §6.2；`claim-evidence-matrix.md` C14。

**口头边界 / 不要说：**

- 显著标 `OBSERVED — RETROSPECTIVE, OUTCOME-OPEN DEVELOPMENT`。
- 不说独立确认、production Selector、典型 origin 改善或跨 Agent 泛化。

## 第 10 页｜已有反证据：换口径、换完整系统后没有保持优势

**一句主结论：** 当前最重要的结果不是“Selector 已成功”，而是局部优势对 weighting 和受测 Agent 群体敏感。

**建议内容：**

- 完整展示四个口径的 H5/H10 `Candidate − Full MAE`：repository-equal、Origin-weighted、modern Full internal LOO、13 refs→external targets。
- 旁边写：Origin weighting 方向反转；跨完整 system/Harness 诊断均落后 Full。
- 下方列可能原因：population shift、样本量、任务构成、Agent–Task interaction，尚未分离。

**可用文件/图：**

- `figures/observed-selector-boundaries.png` / `.svg`，状态 `OBSERVED`。
- `research/barcarolle-position.md` §3.3；`claim-evidence-matrix.md` C15–C17。

**口头边界 / 不要说：**

- 图中 transfer 是 opened post-freeze diagnostic，不是独立确认。
- 不说已经证明 population shift 是唯一因果机制；它只是当前优先假说。
- 不把负面结果包装成 adaptive Goodhart 的观察证据。

## 第 11 页｜异质性：一个平均数掩盖了 repository 差异

**一句主结论：** Selector 的方向和幅度随 repository、horizon 变化，因此需要 support diagnostics 和 abstention。

**建议内容：**

- 放 repository × H5/H10 热图。
- 指出同一方法并非在每个 repository 都改善；总体平均不等于可安全迁移。
- 引出 cold start、warm start、support 和“证据不足时不排名”。

**可用文件/图：**

- `figures/observed-repository-heterogeneity.png` / `.svg`，状态 `OBSERVED`。
- `briefing.md` §§6.3、7 WP2。
- `claim-evidence-matrix.md` C17、C22。

**口头边界 / 不要说：**

- 热图是相同 outcome-open development evidence。
- 不从五个 repository 外推到所有 repository。
- abstention 降低风险只是 `HYPOTHETICAL`；必须同时报告 coverage，不能用几乎不答换低风险。

## 第 12 页｜拟建方案：四个工作包共同承担有效性

**一句主结论：** “counter-Goodhart”不是 Generator 的单项属性，而是四层协议需要共同接受 later-real-work 审计。

**建议内容：**

- 四块并列：
  1. Generator：forecast → materialization → response validity；
  2. Contrast-aware Selector：lift、sign、ranking、regret；
  3. Exposure / refresh：记录看过什么，epoch 内冻结、边界刷新；
  4. Adaptive experiment：同 proposer、同预算，只换 evaluator。
- Reality Generator 与 Challenge Generator 分流：前者尽量 Agent-blind，后者可找弱点但不能证明 future utility。

**可用文件/图：**

- `briefing.md` §7。
- `research/adaptive-validity.md` §§3–7。
- `research/notation.md` 仅供技术 Q&A，不建议把整套符号放主页面。

**口头边界 / 不要说：**

- 全页标 `PROPOSED — NOT YET VALIDATED`。
- 不说 Generator 已完成、synthetic workload 可替代真实未来，或四层协议保证无法被利用。

## 第 13 页｜核心实验：同一 proposer，只换 evaluator

**一句主结论：** 最短证据链是控制候选生成与预算，只看不同 evaluator 最后把同一优化过程带到哪里。

**建议内容：**

- 第一阶段便宜实验：从现有 candidate pool 中允许搜索 K=2/5/10/20/50，比较 Full、recent、random、Barcarolle 选中的 future regret。
- 第二阶段闭环实验：同初始 Agent、同 proposer、同 K 轮/预算，只换 static、recent、current Barcarolle、refreshed/abstaining Barcarolle。
- 所有选择冻结后，一次性打开 historical sealed future；prospective 阶段再等待新的真实 window。

**可用文件/图：**

- `briefing.md` §§7 WP4、9 Milestones 0/3/4。
- `research/adaptive-validity.md` 的 Stage A–D。
- `research/research-audit.md` Gate B–F 作为执行检查表。

**口头边界 / 不要说：**

- 标 `EXPERIMENT DESIGN — NOT RUN`。
- 现有 candidate-pool 压力测试不是 adaptive closed loop；候选并未根据 evaluator feedback 生成。
- 同一 future block 不得同时用于 calibration 和最终评估。

## 第 14 页｜待验证效果：Optimization Horizon

**一句主结论：** 我们要测的不是“永不失效”，而是在明确协议下评测能可靠承受多大优化压力。

**建议内容：**

- 展示两种机制轨迹：固定 benchmark 可能更快出现 benchmark gain 与 future gain 脱钩；future-grounded protocol 的目标是让 regret/lift error 增长更慢。
- 定义 Optimization Horizon：给定 proposer、候选/轮数预算、反馈粒度和误差阈值，评测还能可靠指导到哪里。
- 成功从弱到强：固定候选少选错 → 压力增加时退化更慢 → 闭环最终 future gain 更大。

**可用文件/图：**

- `figures/hypothetical-optimization-pressure.png` / `.svg`。
- `figures/data/hypothetical-optimization-pressure.csv` 仅为布局坐标。
- `briefing.md` §8；`claim-evidence-matrix.md` C21、C23–C24。

**口头边界 / 不要说：**

- 图上与口头都必须说 `HYPOTHETICAL — NOT MEASURED`；隐藏刻度不代表已有数量级。
- 不把两条曲线说成预期收益、预测值、真实 optimization round 或 Barcarolle 已能延长 horizon。
- 视觉只解释假说，不提供证据。

## 第 15 页｜风险、Stop Gates 与建议决策

**一句主结论：** 建议批准分阶段、可停止的研究，不承诺完整 RSI 平台。

**建议内容：**

- 左侧列四个主要风险：population shift、Materializer 决定结论、oracle 错配、outcome-open 调参偏差。
- 中间列对应 gate：新 same-Harness sealed boundary；repeated/cross materialization；独立 oracle/solution diversity；冻结计划与 prospective audit。
- 右侧给决策顺序：
  1. 现有候选池 pressure test；
  2. support/abstention 与 contrast-aware selection；
  3. Generator 三层 validity；
  4. closed-loop adaptive pressure；
  5. prospective confirmation。
- 最后一行：每阶段可独立失败、定位和停止。

**可用文件/图：**

- `briefing.md` §§9–13。
- `research/research-audit.md` Gate A–F。
- `claim-evidence-matrix.md` C20–C24、C28。

**口头边界 / 不要说：**

- 明确当前 evidence 是 `RETROSPECTIVE + OUTCOME-OPEN DEVELOPMENT`。
- 不声称 production Selector、field validity、跨 Harness/模型家族/仓库泛化、已测 Optimization Horizon 或 strict-prospective evidence。
- 不承诺 Barcarolle 自动提出改进、定义通用项目价值或解决通用 RSI。

## 附录建议（不计入 15 页）

- A1：完整 landscape 表——`research/landscape.md`。
- A2：符号与 estimand——`research/notation.md`。
- A3：论断证据矩阵——`claim-evidence-matrix.md`。
- A4：仓库数字与文件位置——`research/barcarolle-position.md`。
- A5：11 轮讨论如何收敛——`discussion-synthesis.md`；原始可见问答仍保存在 `raw/`，不得以整理稿替换。
- A6：研究审计和机器 gate——`research/research-audit.md`。

## 全局编辑规则

- 每页右上角保留状态标签：`OBSERVED`、`INFERENCE`、`HYPOTHETICAL` 或 `CONCEPT ART`。
- observed 图只配它实际支持的 claim；不要把三张 Python 图拼成同一种证据。
- 所有数字保留 denominator、样本范围、weighting 和是否 outcome-open。
- 主线只用两个表达式；完整数学定义放附录。
- 第一次出现英文术语时给中文解释；后续统一用同一个词。
- ImageGen 与示意图只用于理解，不进入论断证据链。
