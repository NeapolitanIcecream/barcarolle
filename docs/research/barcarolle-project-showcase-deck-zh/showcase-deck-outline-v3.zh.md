# Barcarolle 项目展示 Deck V3 页面大纲

状态：reader-centered project-showcase deck outline，2026-06-02。

用途：锁定 V3 PPTX 的 `11` 页结构、可见文案和视觉职责。大纲按最终读者
阅读顺序组织。

## Slide 1

页眉 title label：`项目定位`

主标题：`Barcarolle 编译面向目标仓库的 benchmark release`

副标题：`ACUT = Agent Configuration Under Test，一次被评估的 agent 配置。`

正文：`Barcarolle 把目标仓库、候选任务、验证规则和 ACUT 边界组织成可冻结的 repo-specific release，用于估计这个 agent 配置在未来仓库工作中的表现。`

视觉对象：三方关系图：目标仓库 -> benchmark release -> ACUT。旁注说明 ACUT 保留自己的 harness、prompt、工具策略、模型选择和 runtime budget。

支撑句：`release 记录 task set、split、source/oracle metadata、ACUT boundary 和 validation rules。`

## Slide 2

页眉 title label：`问题与代价`

主标题：`通用分数还不能直接估计本仓库未来工作`

副标题：`部署、调优和治理都需要 target-repo future-work evidence。`

正文：`通用 benchmark 提供广泛能力信号；项目团队还要知道同一个 agent 配置在本仓库未来 issue、API、测试习惯、依赖约束和 review norms 下会怎样。`

视觉对象：左侧为通用 benchmark score，右侧为 target-repo future work，中间显示 prediction gap；下方用三段 consequence rail 标注 deployment choice、configuration tuning、governance decision。

支撑句：`如果证据不贴近目标仓库，团队可能选错配置、误读 dev set 收益，或缺少 source quality、adapter、成本、延迟和不确定性说明。`

## Slide 3

页眉 title label：`相关工作与缺口`

主标题：`相邻工作提供任务、质量、鲜度、规模和环境`

副标题：`Barcarolle 研究这些输入怎样变成目标仓库 release 证据。`

正文：`SWE-bench、SWE-bench Verified、SWE-bench-Live、SWE-Bench++、SWE-smith 和 R2E-Gym 都扩大了 coding-agent evaluation 的可用输入；Barcarolle 的问题是 outcome-unseen release selection 与验证。`

视觉对象：三层矩阵：

| 层 | 来源 | Barcarolle 仍要回答 |
| --- | --- | --- |
| Real tasks / quality | SWE-bench, SWE-bench Verified | 哪些目标仓库任务进入冻结 release，quality gate 怎样进入 selection 规则。 |
| Freshness / scale | SWE-bench-Live, SWE-Bench++, SWE-smith | fresh 或 generated supply 怎样认证、设 source caps，并在 outcome-unseen 条件下冻结。 |
| Environments / verifiers | R2E-Gym | executable environment 怎样服务 release evidence，并保持 ACUT boundary 与 verifier material 隔离。 |

支撑句：`candidate supply 越强，selection、support、fallback 和 future validation 的 compiler rules 越需要单独研究。`

## Slide 4

页眉 title label：`研究目标`

主标题：`北极星是 outcome-unseen predictive validity`

副标题：`benchmark score 要比简单替代方案更贴近未来真实表现。`

公式：

```latex
W_r(a)=\mathbb{E}[\mathrm{success}(a,\ \mathrm{future\ work\ in\ repo}\ r)]
```

正文：`W_r(a) 表示 agent 配置 a 在目标仓库 r 未来工作中的成功率。benchmark release 的 score 是这个未来成功率的候选预测值。`

MAE 解释：`MAE 表示 benchmark 预测值和未来真实表现之间平均差多少；越低，预测越贴近未来结果。`

视觉对象：上方为 typeset formula block；右侧为 benchmark estimate 与 observed future performance 的距离示意；下方为 claim boundary rail。

边界句：`当前证据提供 traction 和验证路线；预测效度尚未建立。`

## Slide 5

页眉 title label：`方法`

主标题：`把候选任务编译成可审计 release`

副标题：`从 supply 到 assembly 的每一层都会影响未来估计。`

正文：`候选任务先经过认证，再按目标工作画像、support 约束、selection rule、split 和 fallback labels 组装成可冻结 release。`

视觉对象：单一 workflow：候选供应 -> 任务认证 -> 目标画像 -> 组装规则 -> 冻结 release -> score / refresh。

认证维度：`replayability / oracle / leakage / source quality / environment / ambiguity`

支撑句：`这个流程只画一次；研究目标、执行边界和未来验证在后续页面分别展开。`

## Slide 6

页眉 title label：`执行边界`

主标题：`solver 与 verifier 分离，hidden oracle 只在验证侧出现`

副标题：`Barcarolle 控制 benchmark-side protocol；ACUT 保留自己的 harness。`

正文：`Barcarolle 建立干净 solver workspace，给出 solver-visible statement 和允许上下文，捕获 ACUT diff；随后在 verifier workspace 注入 hidden oracle，并记录 score、cost、latency、terminal status 和 sanitized artifacts。`

视觉对象：三段 sequence：solver workspace -> captured diff -> verifier workspace。每段只保留中文说明和必要英文术语。

报告规则：`adapter 差异按 named ACUT configuration 报告，不能写成 model-only conclusion。`

## Slide 7

页眉 title label：`算法问题`

主标题：`task selection 会改变 target-repo estimate`

副标题：`support、fallback 和 baseline comparison 是 compiler algorithm 的核心变量。`

正文：`旧 weighted target-profile design 在 sparse support 下失效：attrs weighted gap 为 0.3148，boltons weighted gap 为 0.7481，高于 simple same-budget baselines 0.25 和 0.125。`

视觉对象：左侧为 negative-result mini chart；右侧为 algorithm lab map：candidate features、selection policy、baselines、diagnostics、fallback accounting。

支撑句：`后续 selector 需要显式处理 support thresholds、fallback caps、source caps、slice stability 和 random/simple-baseline comparison。`

## Slide 8

页眉 title label：`当前证据`

主标题：`已有证据支持继续优化，结论仍保持有限`

副标题：`问题真实、执行可行、source repair 可做，MAE signal 还很小。`

视觉对象：evidence-by-question board。

| Reader question | Evidence | Current reading |
| --- | --- | --- |
| 问题是否真实？ | weighted gaps attrs `0.3148`、boltons `0.7481` | 构造规则会改变估计，旧 weighted design 是负面诊断。 |
| 协议能否执行？ | `120/120` planned cells；scoreability `1.0` | workspace / diff / verifier replay machinery 可审计运行。 |
| source 质量能否修复？ | click `30/30` frozen tasks repaired | source repair 可执行；历史 paid outcomes 没有被重写。 |
| selection 是否有信号？ | MAE `0.209` vs `0.2149`；edge `0.0059`；random beats/ties `93.4%` | 有 traction；edge 太小，不能支撑 validity claim。 |

边界句：`预测效度尚未建立；tuning-loop improvement 也尚未实证。`

## Slide 9

页眉 title label：`研究路线`

主标题：`下一阶段重点是 task-selection algorithm evolution`

副标题：`future holdout 或 rolling-origin validation 用来检验冻结后的 algorithm。`

正文：`研究路线从 selector 开始：扩展 candidate supply，修复 feature support，设置 source caps 与 fallback caps，比较 random/simple baselines，检查 slice stability 和 practical MAE margin。`

视觉对象：中心为 algorithm evolution loop；右侧为 validation gate stack。

算法演进：`coverage-constrained / temporal / blocked / shrinkage candidates -> support checks -> fallback policy -> baseline envelope -> slice stability`

验证 gate：`freeze release、fix named ACUT configurations、freeze baselines and seeds、join future outcomes、state scoped result`

支撑句：`true future holdout 是最强路线；preregistered rolling origin 需要 cutoffs、seeds、selection rule、baselines、invalid handling 和 success criteria 在 outcome 前固定。`

## Slide 10

页眉 title label：`Agent License`

主标题：`Agent License 可以使用仓库级证据状态`

副标题：`deployment governance 需要 scoped evidence、risk status 和 uncertainty。`

正文：`Barcarolle evidence layer 连接目标仓库、任务类别、风险等级、ACUT 配置、source quality、成本、延迟和 scoped use decision，帮助团队判断某个使用范围的证据是否足够。`

视觉对象：governance flow：repo/task category -> risk tier -> named ACUT scorecard -> evidence status -> scoped use decision。

支撑句：`输出是 evidence status、limits、source-quality note、adapter note、cost/latency note 和 uncertainty note。`

## Slide 11

页眉 title label：`Agent Tuning`

主标题：`Agent Tuning 需要受保护的 dev / eval / canary 回路`

副标题：`反馈可以帮助比较配置，同时保护正式验证材料。`

正文：`Barcarolle 可提供 dev feedback、eval release、canary release、failure taxonomy、scorecard、regression signal、cost 和 latency summaries，帮助比较 prompt、retrieval、skills、tool policy、model 和 runtime budget。`

视觉对象：protected feedback loop：configuration change -> dev feedback -> eval release -> canary release -> regression signal；future validation material 显示为隔离层。

支撑句：`当前 deck 只说明 evidence interface；调优效果仍需要后续产品验证。`

## Final Count

Target count: `11` slides.

V2 Slide 11 `限制` 不再作为独立页面保留；其有用内容吸收到 V3 Slide 8
的 evidence boundary 和 V3 Slide 9 的 algorithm / validation route 中。
