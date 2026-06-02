# Barcarolle 项目展示 Deck 页面大纲

状态：pruned project-showcase deck outline，2026-06-02。

用途：锁定 PPTX 的 14 页结构、可见文案和视觉职责。大纲按最终读者阅读顺序组织。

## Slide 1

来源页：原 Slide 1

页眉 title label：`项目定位`

独立职责：定义 Barcarolle 的项目对象和证据层边界。

可见文案草案：

- 主标题：`Barcarolle 编译面向目标仓库的 benchmark release`
- 副标题：`目标仓库、被测 Agent 配置与冻结 release 之间的证据层`
- 正文：`Barcarolle 把候选任务、ACUT 边界和验证规则组织成可冻结的 repo-specific release，用于估计某个 ACUT 在目标仓库未来工作中的表现。`
- 边界说明：`ACUT 保留自己的 harness、prompt 和工具策略；Barcarolle 负责 solver-visible 材料、diff capture 和 verifier replay 边界。`

视觉对象：三实体 evidence-layer diagram：目标仓库、被测 ACUT、冻结 release。

内容移动：删除原 Slide 5 的独立定位页后，本页保留对象定义，不展开完整 compiler workflow。

句式处理：删除二分式身份声明。

## Slide 2

来源页：原 Slide 2

页眉 title label：`问题`

独立职责：解释通用 benchmark 分数和目标仓库未来工作之间的预测缺口。

可见文案草案：

- 主标题：`团队缺少对未来仓库工作的直接估计`
- 副标题：`通用分数和目标仓库未来工作之间仍有预测缺口`
- 正文：`通用 benchmark 提供总体能力信号；部署 agent 时，团队还需要回答本仓库未来 issue、API、测试和依赖约束下的表现。`
- 目标问题：`给定一个 ACUT，它在某个目标仓库未来真实工作中的表现会怎样？`

视觉对象：从通用任务分布到目标仓库未来工作的 gap diagram。

内容移动：无。

句式处理：删除贬低通用 benchmark 的二分式表述。

## Slide 3

来源页：原 Slide 3

页眉 title label：`代价`

独立职责：说明预测缺口影响部署、调优和治理决策。

可见文案草案：

- 主标题：`这个缺口会影响部署、调优和治理`
- 副标题：`证据如果不贴近目标仓库，决策就可能偏离真实工作`
- 正文：`目标仓库证据不足时，团队可能选错配置、误读 dev set 收益，或缺少 source quality、adapter、成本、延迟和不确定性说明。`

视觉对象：三列 consequence map：部署选择、配置调优、治理判断。

内容移动：产品化方案留到 Slides 13-14；本页只讲 stakes。

句式处理：无二分式句法保留。

## Slide 4

来源页：原 Slide 4，吸收原 Slide 5 的部分定位内容。

页眉 title label：`相关工作`

独立职责：承认相关工作贡献，并说明 Barcarolle 的 release compilation 层。

可见文案草案：

- 主标题：`相关工作已经覆盖任务、质量、鲜度、规模和环境`
- 副标题：`Barcarolle 的问题位于这些贡献之后的 release compilation 层`
- 正文：`SWE-bench、Verified、Live、SWE-smith 和 R2E-Gym 提供相邻能力；Barcarolle 把这些输入编译成目标仓库 release，并测试它能否成为未来仓库工作的证据。`
- 收束句：`候选供应越强，selection、split、fallback 和 future validation 的编译规则越需要单独研究。`

视觉对象：相邻方向 / 贡献层 / Barcarolle 仍要回答的问题三列表。

内容移动：吸收原 Slide 5 的 layer-positioning 句；删除原 Slide 5 的完整流程 strip。

句式处理：避免胜负式相关工作比较。

## Slide 5

来源页：原 Slide 6

页眉 title label：`研究目标`

独立职责：定义 north-star estimand 和 MAE 解释。

可见文案草案：

- 主标题：`北极星：outcome-unseen 预测效度`
- 副标题：`冻结 release 要比简单替代方案更好地估计未来仓库表现`
- 公式：`W_r(a) = E[success(a, future target-repo work)]`
- 正文：`W_r(a) 表示 ACUT 在未来目标仓库工作中的成功率。MAE 是平均预测误差；越低，benchmark estimate 越接近 observed future-work performance。`
- 边界说明：`正式声明只属于 frozen scope；retrospective replay 用于路线发现和 debug。`

视觉对象：estimand panel + MAE interpretation block。

内容移动：validation gate strip 移出；future validation route 留到 Slide 12。

句式处理：无二分式句法保留。

## Slide 6

来源页：原 Slide 7，吸收原 Slide 5 的部分 workflow 内容。

页眉 title label：`方法`

独立职责：展示唯一完整 compiler workflow。

可见文案草案：

- 主标题：`把候选任务编译成可审计 release`
- 副标题：`从 supply 到 validation 的每一层都影响未来估计`
- 正文：`候选供应经过认证、目标画像和组装规则，形成带 task set、split、fallback、ACUT boundary 和验证规则的 release。`
- 认证维度：`replayability / oracle / leakage / source quality / environment / ambiguity`

视觉对象：单一完整 workflow：候选供应、任务认证、目标画像、组装规则、冻结 release、score/refresh。

内容移动：吸收原 Slide 5 的 candidate supply -> certification -> assembly/release 层级；其他页面不再重复完整 workflow。

句式处理：删除抽题式反衬表述。

## Slide 7

来源页：原 Slide 8

页眉 title label：`执行边界`

独立职责：界定 Barcarolle 与 ACUT harness 的执行边界。

可见文案草案：

- 主标题：`ACUT 边界让 benchmark 不变成 agent harness`
- 副标题：`solver workspace 和 verifier workspace 分离，hidden oracle 只在验证侧出现`
- 正文：`Barcarolle 给出 solver-visible task statement 和允许上下文，捕获 ACUT diff，再在 verifier workspace 注入 hidden oracle，并记录 score、cost、latency 和 terminal status。`
- 报告规则：`Adapter 差异按 named ACUT configuration 报告。`

视觉对象：solver workspace -> captured diff -> verifier workspace boundary diagram。

内容移动：无。

句式处理：删除 model-only 的二分式结论。

## Slide 8

来源页：原 Slide 9

页眉 title label：`算法问题`

独立职责：用旧 weighted design 失败说明 selection/support/fallback 是研究对象。

可见文案草案：

- 主标题：`selection、support 和 fallback 会改变估计`
- 副标题：`朴素 weighted 构造失败，构造规则本身就是研究问题`
- 正文：`旧 weighted target-profile design 在 sparse support 下失效：attrs gap 0.3148、boltons gap 0.7481，高于 simple same-budget baseline 0.25 和 0.125。`
- 结论：`后续 selector 必须显式处理 support、fallback 和 baseline comparison。`

视觉对象：negative-result metric comparison + selector decision map。

内容移动：无。

句式处理：删除“随机抽题”和“成功结果”二分式表述。

## Slide 9

来源页：原 Slide 10

页眉 title label：`算法环境`

独立职责：说明当前 algorithm lab 能比较 selector、baselines 和 diagnostics。

可见文案草案：

- 主标题：`算法演进环境已经成形`
- 副标题：`selection policy 可以用 baseline、random control 和 slice diagnostics 比较`
- 正文：`当前 candidate 是 coverage-constrained unweighted with labeled fallback。比较环境覆盖 temporal/repo baselines、many-seed random envelope、adapter/repo/window diagnostics 和 fallback accounting。`

视觉对象：algorithm lab map：candidate features、selection policy、baselines、diagnostics。

内容移动：future validation route 移到 Slide 12。

句式处理：无二分式句法保留。

## Slide 10

来源页：原 Slide 11

页眉 title label：`当前效果`

独立职责：呈现 traction evidence，不扩大为正式预测结论。

可见文案草案：

- 主标题：`当前效果支持继续优化，但还不支持最终有效性声明`
- 副标题：`问题真实、执行可行、selection 有初步信号；edge 仍然很小`
- 正文：`探索性结果支持继续优化：120/120 planned cells、scoreability 1.0、click 30/30 source repair、candidate MAE 0.209 vs baseline 0.2149、edge 0.0059、random beats/ties 93.4% of 1000 selections。`

视觉对象：four evidence callouts：执行可行、source repair、MAE traction、random control。

内容移动：weakness/action details 移到 Slide 11。

句式处理：删除 traction 与 validity 的二分式句法，改为边界清晰的直接陈述。

## Slide 11

来源页：原 Slide 12

页眉 title label：`限制`

独立职责：把 fallback、adapter 和 support weakness 转化为 repair/validation actions。

可见文案草案：

- 主标题：`尚未证明的部分决定下一步`
- 副标题：`fallback、adapter 和 support weakness 必须前置处理`
- 正文：`当前 selector 使用 6/18 fallback slots，boltons 为 6/6。Codex/Kilo 差异按 named ACUT configuration 报告；small MAE edge 需要 practical margin 和 slice stability。`
- 边界说明：`预测效度尚未建立；tuning-loop improvement 也尚未实证。`

视觉对象：weakness -> required action bridge：fallback composite、adapter fragility、small MAE edge。

内容移动：当前 traction 数字主要留在 Slide 10；本页只保留弱点和动作。

句式处理：无二分式句法保留。

## Slide 12

来源页：原 Slide 13

页眉 title label：`研究路线`

独立职责：展示未来验证协议，而非重复 compiler workflow。

可见文案草案：

- 主标题：`后续研究走向冻结 release 和未来验证`
- 副标题：`outcome-unseen evidence 才能支撑更强声明`
- 正文：`下一阶段固定 release、selection rule、baseline suite、invalid handling 和 success criteria，再用 true future holdout 或 preregistered rolling-origin evidence 验证。`
- 路线标签：`Freeze release / Run named ACUTs / Join future outcomes / Compare baseline envelope / State scoped result`

视觉对象：future validation route，使用 gate-and-evidence layout，避免复用 Slide 6 的 compiler workflow。

内容移动：无。

句式处理：无二分式句法保留。

## Slide 13

来源页：原 Slide 14

页眉 title label：`产品化方向`

独立职责：说明 Agent License / deployment governance 如何使用仓库级证据层。

可见文案草案：

- 主标题：`Agent License 需要仓库级证据层`
- 副标题：`Barcarolle 可以支持 deployment governance，但不负责发放授权`
- 正文：`证据层连接仓库/任务类别、风险等级、ACUT 配置和 scoped use decision，帮助 deployment governance 判断证据是否足够。`

视觉对象：governance decision matrix：仓库/任务类别、风险等级、ACUT 配置、evidence status、scoped use decision。

内容移动：无。

句式处理：删除 license 产品二分式声明。

## Slide 14

来源页：原 Slide 15

页眉 title label：`产品化方向`

独立职责：说明 Agent Tuning 如何使用受保护的反馈回路。

可见文案草案：

- 主标题：`Agent Tuning 需要受保护的反馈回路`
- 副标题：`Barcarolle 提供 scorecard 和 regression signal，但不接管调优闭环`
- 正文：`Barcarolle 可提供 dev/eval/canary release、failure taxonomy、scorecard 和 regression signal，帮助比较 prompt、retrieval、skills、tool policy 和 runtime budget，同时保护正式验证材料。`

视觉对象：protected feedback loop：configuration changes -> dev feedback -> protected eval/canary -> regression monitoring。

内容移动：无。

句式处理：不声称 tuning-loop improvement 已经验证。

## Deleted Or Merged Page

| 原页 | 处理 | 保留内容 |
| --- | --- | --- |
| Slide 5 `项目位置` | 删除并合并 | layer-positioning 句进入 Slide 4；candidate supply / certification / assembly / release 关系进入 Slide 6。 |

## Final Count

Target count: `14` slides.

Retained title labels remain unchanged for all retained source pages. The two
`产品化方向` pages are retained because one answers governance evidence use and
the other answers protected tuning feedback use.
