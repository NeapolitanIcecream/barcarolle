# Barcarolle 相关工作定位说明

状态：项目展示 deck 相关工作定位说明，2026-06-02。

用途：为 deck 中的相关工作页提供精炼定位。本文只使用已进入主报告的公开来源与声明，不扩展新的文献综述。

## Positioning principle

相关工作不应被写成 Barcarolle 的反面。更准确的叙述是：

```text
相关工作提供任务、质量、鲜度、规模或环境；Barcarolle 研究的是，在给定目标仓库、ACUT 边界、未来工作假设和评测预算时，怎样编译一个冻结的 repo-specific benchmark release，使它更可能成为未来仓库工作表现的证据。
```

因此，deck 应把 related work 放在“相邻层”中解释，而不是说这些系统没有价值。

## Positioning matrix

| 方向 | 已贡献的层 | deck 中应承认的价值 | Barcarolle 仍要回答的问题 |
| --- | --- | --- | --- |
| SWE-bench | 真实仓库 issue-resolution tasks 和 execution-based scoring | 它证明真实 GitHub issue/PR 可以组织成可执行 coding-agent 任务，是 repo-level SWE evaluation 的重要基础。 | 对一个目标仓库和一个 named ACUT，哪些任务应该进入冻结 release，并如何估计未来仓库工作表现。 |
| SWE-bench Verified | 人工验证 task quality | 它显示 feasibility、underspecification 和 task quality 会显著影响 benchmark 解释，因此质量审核是必要 gate。 | 质量审核只是 release gate；它本身不等于 target-repo prediction，也不决定 selection、split、fallback 和 future validation 规则。 |
| SWE-bench-Live | 通过较新任务缓解 freshness pressure | 它强调 benchmark 需要持续更新，避免静态任务集合与真实工作脱节。 | fresh supply 仍要被编译成 outcome-unseen、repo-specific、可冻结的 release，才能支撑未来预测声明。 |
| SWE-smith | scalable software-engineering task generation | 它扩展候选任务供应，使更大规模的 task pool 成为可能。 | 生成任务只有经过本地认证、source sufficiency、oracle、leakage 和 environment 检查后，才可能成为 release candidate；生成规模不是 compiler claim。 |
| R2E-Gym | executable environments 和 training/evaluation infrastructure | 它提供可执行环境和混合 verifier，有助于训练和评测 SWE agents。 | Barcarolle 不训练也不运行 ACUT；它围绕 ACUT 边界编译和验证 benchmark release，并记录 score、cost、latency 与 artifact hygiene。 |

## Deck implication

相关工作页应回答一个问题：为什么 Barcarolle 不是在重复 public benchmark 或 task generator？

推荐 visual object：横向矩阵或分层图。

- 左侧显示相关方向覆盖的层：real tasks、quality validation、freshness、generation scale、executable environments。
- 右侧显示 Barcarolle 的层：repo-specific release compilation、target-work profile、selection/split/weighting、ACUT boundary、verifier replay、future validation。
- 底部用一句话收束：任务供应越强，Barcarolle 的 compiler 问题越重要，因为 supply volume 不会自动回答 target-repository prediction。

## Wording guardrails

可用表述：

- “提供候选任务、质量参照、鲜度、规模或环境。”
- “回答的是相邻问题。”
- “Barcarolle 把这些输入组织成 target-repo benchmark release，并测试它能否预测未来仓库工作。”
- “生成或 live supply 可以提高 candidate pool，但 release selection 和 validation 仍需要单独研究。”

避免表述：

- “现有 benchmark 失败。”
- “public benchmark 没有用。”
- “task generator 不能解决问题。”
- “Barcarolle 取代 SWE-bench / SWE-smith / R2E-Gym。”

## Source boundary

本说明沿用主报告中的 citation labels 和公开来源：SWE-bench ICLR 2024 paper、SWE-bench Verified introduction、SWE-bench-Live project page、SWE-smith project page、R2E-Gym official repository，以及主报告中对 benchmark quality / contamination 解释风险的讨论。未新增公开浏览、未新增 citation、未扩展这些来源的原始主张。

