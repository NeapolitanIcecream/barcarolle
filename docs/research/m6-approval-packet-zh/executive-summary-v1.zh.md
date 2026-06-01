# Barcarolle 立项交付包中文一页摘要 V1

状态：面向决策的一页摘要，2026-06-01。

## 审批请求

批准 Barcarolle 作为面向特定仓库的 benchmark 编译器项目推进。批准范围包括 benchmark 选择算法、任务认证、版本化 release、验证协议、报告体系，以及面向调优的接口建设。批准必须带有明确声明边界：当前证据提供有边界的牵引性证据和可信的验证路径，但预测效度仍未建立。

## 为什么值得做

团队把 coding agent 用在自己的仓库里。未来 issue、API、测试、依赖、review 规范和失败模式，都可能不同于公共 benchmark 的分布。一个 benchmark 可以可执行、可复核、也相对公平，但仍然不能很好回答某个被测 Agent 配置（ACUT）在目标仓库未来任务上的表现。

## Barcarolle 是什么

Barcarolle 位于 benchmark 构建层。它选择、认证、切分、刷新、加权或保持不加权，并解释面向特定仓库的 benchmark release。ACUT 保留自己的 harness：文件搜索、编辑策略、prompt、工具、模型选择、重试策略、运行预算和 trace 内部细节都不由 Barcarolle 重写。

## 当前证据

当前证据足以支持项目审批，但不足以支持完成后的有效性声明。

- 朴素加权设计出现实质性失败：attrs 加权 gap 为 `0.3148`，boltons 加权 gap 为 `0.7481`，而同预算简单 baseline 分别是 `0.25` 和 `0.125`。
- benchmark 侧执行可行：三仓库 pilot 完成 `120/120` 个探索性 cell，scoreability 为 `1.0`。
- source quality 修复可行：click 的 `30/30` 个冻结任务已补齐公开 issue 和 pull request 语境。
- 当前 candidate 有方向性牵引：aggregate MAE 为 `0.209`，best simple aggregate baseline 为 `0.2149`；在 `1000` 个同预算随机选择中，它胜过或打平 `93.4%`。

## 仍未证明什么

预测效度仍未建立。当前 best-simple-baseline 优势只有 `0.0059` MAE，adapter 和仓库切片都较脆弱；`6/18` 个被选 slot 使用 fallback，其中 boltons 为 `6/6` fallback。Barcarolle 也尚未提供实证结果来支持其反馈能改善 agent 调优闭环。这些是获批项目的验证目标，不是当前声明。

## 获批项目要做什么

获批项目将建设更好的选择规则、认证 gate、release manifest、baseline suite、未来或预注册 rolling-origin 验证协议、adapter 分层 scorecard、不确定性与 fallback 报告，以及 optimizer 可读的调优与回归接口。产出是版本化 benchmark release 和证据模型，不是替代 ACUT harness、通用任务工厂或公共排行榜。

## 预算与验证闸门

付费评测只应在这些内容冻结后开始：benchmark release、任务选择规则、baseline suite、score join 程序、命名 ACUT 配置、invalid-cell 规则和成功标准。付费评测是有闸门的项目资源，不是开放式探索。

仍由用户决定的值：

- `[待用户决定：项目人员配置]`
- `[待用户决定：项目周期]`
- `[待用户决定：有闸门 ACUT 评测的预算上限]`
- `[待用户决定：审批路径或审批负责人]`

## 预期决策结果

在上述声明边界和评测闸门下批准项目；在对评审者流通前，填入或明确保留用户自有资源占位符；以 V5 作为本交付包背后的长文论证基准。
