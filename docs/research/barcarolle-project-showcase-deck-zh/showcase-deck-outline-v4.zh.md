# Barcarolle 项目展示 Deck V4 页面大纲

状态：V4 targeted repair outline，2026-06-03。

用途：锁定 V4 PPTX 的 `11` 页结构、可见文案和视觉职责。大纲按最终读者阅读顺序组织。

## Slide 1

页眉 title label：`项目定位`

主标题：`Barcarolle 编译面向目标仓库的评测 release`

副标题：`ACUT = Agent Configuration Under Test，一次被评估的 agent 配置。`

正文：`Barcarolle 把目标仓库、候选任务、验证规则和 ACUT 边界组织成可冻结 release，用来估计这个 agent 配置在未来仓库工作中的表现。`

视觉对象：右侧为干净三段关系图：`目标仓库 -> 仓库级评测 release -> ACUT 运行与结果`。下方两条边界说明：Barcarolle 组织 release evidence；ACUT 保留 harness、prompt、tools、model 和 budget。

支撑句：`release 记录 task set、split、source/oracle metadata、ACUT boundary 和 validation rules。`

## Slide 2

页眉 title label：`问题与代价`

主标题：`通用分数还不能直接估计本仓库未来工作`

副标题：`部署、调优和治理都需要目标仓库未来证据。`

正文：`通用 benchmark 提供广泛能力信号；项目团队还要知道同一个 agent 配置在本仓库未来 issue、API、测试习惯、依赖约束和 review norms 下会怎样。`

视觉对象：上方为 `通用 benchmark score` 和 `目标仓库未来工作` 两端，中间用一条明确的桥接带标注 `预测缺口`。桥接带向下连接三类后果：`部署选择`、`配置调优`、`治理决策`。

支撑句：`如果证据不贴近目标仓库，团队可能选错配置、误读 dev set 收益，或缺少 source 质量、adapter、成本、延迟和不确定性说明。`

## Slide 3

页眉 title label：`相关工作与缺口`

主标题：`相邻工作提供任务、质量、鲜度、规模和环境`

副标题：`Barcarolle 研究这些输入怎样变成目标仓库 release 证据。`

正文：`SWE-bench、SWE-bench Verified、SWE-bench-Live、SWE-Bench++、SWE-smith 和 R2E-Gym 扩大了 coding-agent evaluation 的可用输入；Barcarolle 关注未看未来结果时的 release 选择与验证。`

视觉对象：三层矩阵：

| 层 | 来源 | Barcarolle 仍要回答 |
| --- | --- | --- |
| 真实任务 / 质量 | SWE-bench, SWE-bench Verified | 哪些目标仓库任务进入冻结 release，质量门槛怎样进入任务选择规则。 |
| 鲜度 / 规模 | SWE-bench-Live, SWE-Bench++, SWE-smith | fresh 或 generated supply 怎样认证、设来源上限，并在未看未来结果时冻结。 |
| 环境 / 验证器 | R2E-Gym | executable environment 怎样服务 release evidence，并保持 ACUT boundary 与验证材料隔离。 |

支撑句：`candidate supply 越强，任务选择、样本支撑、兜底来源和未来验证的 compiler rules 越需要单独研究。`

## Slide 4

页眉 title label：`研究目标`

主标题：`北极星是未看未来结果时的预测效度`

副标题：`评测分数要比简单替代方案更贴近未来真实表现。`

公式：

```latex
W_r(a)=\mathbb{E}[\mathrm{success}(a,\ \mathrm{future\ work\ in\ repo}\ r)]
```

正文：`W_r(a) 表示 agent 配置 a 在目标仓库 r 未来工作中的成功率。评测 release 的 score 是这个未来成功率的候选预测值。`

MAE 解释：`MAE 是平均绝对误差，表示 benchmark 预测值和未来真实表现之间平均差多少；越低，预测越贴近未来结果。`

视觉对象：上方为公式块；右侧为 MAE 解释；下方为 benchmark estimate 与 observed future performance 的距离示意，以及 claim boundary rail。

边界句：`当前证据提供 traction 和验证路线；预测效度尚未建立。`

## Slide 5

页眉 title label：`方法`

主标题：`把候选任务编译成可审计 release`

副标题：`从候选供应到冻结 release，每一层都会影响未来估计。`

正文：`候选任务先经过认证，再按目标工作画像、样本支撑、任务选择规则、split 和兜底标签组装成可冻结 release。`

视觉对象：单一 workflow：`候选供应 -> 任务认证 -> 目标画像 -> 组装规则 -> 冻结 release -> 结果与刷新`。下方用一条清晰 checklist 写认证维度：`可复现 / oracle / 泄漏 / source 质量 / 环境 / 歧义`。

支撑句：`认证、目标画像和组装规则共同决定 release 是否可审计、可复现、可用于未来验证。`

## Slide 6

页眉 title label：`执行边界`

主标题：`solver 与 verifier 分离，hidden oracle 只在验证侧出现`

副标题：`Barcarolle 控制 benchmark-side protocol；ACUT 保留自己的 harness。`

正文：`Barcarolle 建立干净 solver workspace，给出 solver-visible statement 和允许上下文，捕获 ACUT diff；随后在 verifier workspace 注入 hidden oracle，并记录 score、cost、latency、terminal status 和 sanitized artifacts。`

视觉对象：三段 sequence：`solver workspace -> captured diff -> verifier workspace`。每段保留中文说明和必要英文术语。

报告规则：`adapter 差异按 named ACUT configuration 报告，不能写成 model-only conclusion。`

## Slide 7

页眉 title label：`算法问题`

主标题：`任务选择器决定有限预算估计`

副标题：`样本支撑、兜底来源和对照基线会改变 estimate 的可信度。`

正文：`仓库级评测 release 只能观察有限数量的任务；任务选择器决定哪些观察进入估计，因此可能带来偏差、覆盖不足或切片不稳定。`

视觉对象：主流程：`有限预算 -> 任务选择器 -> 估计风险 -> selector 规则`。估计风险包括 `偏差`、`覆盖不足`、`不稳定`；selector 规则包括 `样本支撑`、`兜底来源`、`来源上限`、`切片稳定性`、`对照基线`。

历史诊断：`旧 weighted 方案在稀疏样本支撑下脆弱；它提示 selector 规则需要显式支撑检查。`

支撑句：`算法问题的核心是用有限任务得到更可信的未来估计。`

## Slide 8

页眉 title label：`当前证据`

主标题：`已有证据支持继续优化 selector，结论仍保持有限`

副标题：`协议可运行，source 可修复，MAE signal 仍然很小。`

视觉对象：四问证据板。

| 读者问题 | 证据 | 当前读法 |
| --- | --- | --- |
| 协议能跑通吗？ | `120/120` planned cells；scoreability `1.0` | workspace、diff、verifier replay 可以审计运行。 |
| source 质量能修复吗？ | click `30/30` tasks repaired | source repair 可执行；历史 paid outcomes 没有被重写。 |
| 选择器是否有初步信号？ | MAE `0.209` vs `0.2149`；edge `0.0059`；random `93.4%` | 有 traction；低于未来 `95.0%` gate。 |
| 现在还不能证明什么？ | adapter、repo/window、fallback 和 MAE margin 仍脆弱 | 预测效度未建立；tuning-loop improvement 未实证。 |

边界句：`这些结果支持继续优化 selector；还不能证明预测效度。`

## Slide 9

页眉 title label：`研究路线`

主标题：`下一步是改进任务选择器并冻结验证`

副标题：`future holdout 或 rolling-origin validation 用来检验冻结后的规则。`

正文：`研究路线从任务选择器开始：扩展候选供应，修复样本支撑，设置来源上限与兜底上限，比较随机和简单对照基线，检查切片稳定性和 practical MAE margin。`

视觉对象：左侧为对齐的算法演进 loop：`候选供应 -> 选择器候选 -> 规则检查 -> 对照基线包 -> 回到候选供应`。右侧为验证 gate stack：`freeze release`、`fix named ACUTs`、`freeze baselines`、`join future outcomes`、`state scoped result`。

支撑句：`true future holdout 是最强路线；preregistered rolling origin 需要 cutoffs、seeds、selection rule、baselines、invalid handling 和 success criteria 在 outcome 前固定。`

## Slide 10

页眉 title label：`Agent License`

主标题：`Agent License 可以使用仓库级证据状态`

副标题：`部署治理需要 evidence scope、risk status 和 uncertainty。`

正文：`Barcarolle evidence layer 连接目标仓库、任务类别、风险等级、ACUT 配置、source 质量、成本、延迟和使用范围决定，帮助团队判断某个使用范围的证据是否足够。`

视觉对象：一条主流程：`repo / task category -> risk tier -> named ACUT scorecard -> evidence status -> scoped use decision`。每个节点下方直接列出输出信息，不再单独放底部输出 strip。

支撑句：`输出包括证据状态、范围限制、source-quality note、adapter note、cost/latency note 和 uncertainty note。`

## Slide 11

页眉 title label：`Agent Tuning`

主标题：`Agent Tuning 需要受保护的 dev / eval / canary 回路`

副标题：`反馈可以帮助比较配置，同时保护正式验证材料。`

正文：`Barcarolle 可提供 dev feedback、eval release、canary release、failure taxonomy、结果卡、回归信号、成本和延迟摘要，帮助比较 prompt、retrieval、skills、tool policy、model 和 runtime budget。`

视觉对象：单一路径：`配置变更 -> dev feedback -> eval release -> canary release -> regression signal`。未来验证材料显示为独立隔离区，不作为断裂连接目标。

支撑句：`这里说明 evidence interface；调优效果仍需要后续产品验证。`

## Final Count

Target count: `11` slides.

V4 保留 V3 的高层顺序，只做局部论证、图形和术语修复。
