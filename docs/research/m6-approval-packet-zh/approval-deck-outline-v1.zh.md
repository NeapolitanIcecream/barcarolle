# Barcarolle 中文立项 PPTX 大纲 V1

状态：中文 approval deck claim spine，2026-06-01。

主参考文本：`docs/research/barcarolle-proposal-report-v5.md`。

Deck contract:

- 主要交付物：可编辑 PowerPoint deck；
- 目的：帮助评审者决定是否批准 Barcarolle 作为面向特定仓库的 benchmark 编译器项目；
- 证据标准：当前证据提供有边界的牵引性证据和可信的验证路径，但预测效度仍未建立；
- 产品路径：调优与回归反馈是计划交付能力，不是已经完成验证的效果声明；
- 用户自有值保持占位符，直到项目 owner 提供。

## Slide 1: 审批请求

Claim: 在有边界的验证声明下，批准 Barcarolle 作为面向特定仓库的 benchmark 编译器项目。

Proof object: 一句话审批请求，加紧凑 north-star statement。

Source evidence: V5 executive summary 和当前声明边界。

Claim limit: 审批是为了建设和验证项目，不是接受预测效度已经完成验证。

Placeholder notes:

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`
- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`

## Slide 2: 评测缺口

Claim: 团队需要关于自己仓库未来工作的证据，而不只是通用 benchmark 分数。

Proof object: 对比 public benchmark、generated task supply，以及 target-repository prediction gap。

Source evidence: V5 关于问题、stakes 和 public benchmark 定位的章节。

Claim limit: public benchmark 和任务生成系统仍是有价值输入；deck 不应把它们描述成整体失败的竞争品。

Placeholder notes: 无。

## Slide 3: Barcarolle 构建什么

Claim: Barcarolle 编译 benchmark release；ACUT 继续控制自己的 agent harness。

Proof object: boundary diagram，区分 candidate supply、certification、release assembly、ACUT execution、verifier replay 和 score accounting。

Source evidence: V5 thesis、boundary 和 proposed compiler design。

Claim limit: Barcarolle 不重写文件搜索、编辑策略、prompt、工具使用、模型选择、重试策略或 trace 内部细节。

Placeholder notes: 无。

## Slide 4: 为什么它对调优有用

Claim: 面向特定仓库的 release 只有在支持配置比较、调优反馈和回归监控，同时避免过拟合验证证据时才真正有用。

Proof object: 从 release outputs 到 dev、eval、canary 和 future-validation feedback 的 workflow diagram。

Source evidence: V5 executive summary、thesis boundary、validation strategy、project work packages 和 expected deliverables。

Claim limit: 调优接口是计划产出；当前没有实证结果支持 Barcarolle 已改善 agent 调优闭环。

Placeholder notes: 无。

## Slide 5: 当前已经学到什么

Claim: 当前证据显示问题真实、可度量、技术上可执行，足以支持批准项目。

Proof object: 四行 evidence table，覆盖朴素加权失败、干净 workspace 执行、source-quality repair 和 retrospective traction。

Source evidence: V5 preliminary evidence section 和 evidence index。

Claim limit: 证据仍是初步证据；当前 selector 优势很小，不能承载正式有效性声明。

Placeholder notes: 无。

Key numbers to preserve on slide: `0.3148`, `0.7481`, `0.25`, `0.125`, `120/120`, `1.0`, `30/30`, `0.209`, `0.2149`, `0.0059`, `93.4%`, `1000`, `6/18`, `6/6` where layout permits.

## Slide 6: 我们不做哪些声明

Claim: 本交付包保留严格非声明边界：预测效度、调优效果、pooled rescue 和任务生成范围都不能被扩大。

Proof object: claim-boundary callout，包含当前可支持声明和明确 non-claims。

Source evidence: V5 current claim boundary 和 appendix current non-claims。

Claim limit: 这一页必须显眼直接，不能被处理成脚注。

Placeholder notes: 无。

## Slide 7: 验证路径

Claim: 更强声明需要冻结 release，并用未来证据或预注册 rolling-origin 证据，与简单 baseline 比较。

Proof object: validation roadmap，展示 pre-outcome freeze、named ACUT configuration、future evidence mode、score join、baseline envelope 和 success criteria。

Source evidence: V5 validation strategy。

Claim limit: retrospective replay 只支持牵引性证据和 debugging。

Placeholder notes: 无。

## Slide 8: 项目 work package

Claim: 获批项目建设 release machinery、selection algorithms、certification、validation、reporting 和 tuning-facing interfaces。

Proof object: work-package map，包含六类产出及其审批作用。

Source evidence: V5 project plan、decision gates 和 expected deliverables。

Claim limit: 这张图展示项目范围，不预先承诺最终科学结论。

Placeholder notes:

- 人员配置和对外材料中的 owner 类别仍是用户自有占位符。
- `[待用户决定：对外材料中的交付负责人类别]`

## Slide 9: 闸门与预算纪律

Claim: 评测支出由冻结协议和审批闸门约束，不是开放式探索。

Proof object: gate table，覆盖 release freeze、source support、baseline margin、fallback handling、endpoint/accounting 和 artifact hygiene。

Source evidence: V5 validation strategy 和 decision gates。

Claim limit: 本交付包不设定最终预算、周期、人员配置或审批 owner。

Placeholder notes:

- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`

## Slide 10: 风险与缓解

Claim: 主要风险是可见、有边界的，并且已绑定到更强声明前必须执行的实际缓解措施。

Proof object: risk matrix，覆盖初步证据泛化、selection-vs-baseline 失败、fallback support、adapter interpretation、source quality、tuning overfit 和 evaluation-budget timing。

Source evidence: V5 risks、objections 和 mitigations。

Claim limit: 风险缓解是控制计划，不是风险已经消失的证据。

Placeholder notes: 无。

## Slide 11: 交付物

Claim: 评审者可以期待具体 release、protocol、report 和 tuning-facing interfaces。

Proof object: deliverable list，按 release、validation、reporting、tuning 和 governance 归组。

Source evidence: V5 expected deliverables 和 project work packages。

Claim limit: 交付物必须保持在 benchmark 编译器边界内，不变成 ACUT harness 或公共排行榜承诺。

Placeholder notes:

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`

## Slide 12: 决策

Claim: 在声明边界和评测闸门下批准 Barcarolle，并在对评审者流通前处理用户自有资源值。

Proof object: final ask、approval conditions、placeholder list 和 next actions。

Source evidence: V5 executive summary、resource ask 和 current claim boundary。

Claim limit: 批准不授权无闸门评测支出，也不表示正式预测效度已经完成验证。

Placeholder notes:

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`
- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`
