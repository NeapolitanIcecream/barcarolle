# Barcarolle 核心叙事阶段性实验报告：RGW v1 与 M5-W2

生成日期：2026-05-13
报告性质：阶段性研究报告
当前结论：负结果；不支持 NFL reversal claim

## 摘要

本报告汇总 Barcarolle core narrative 当前阶段的两组关键实验：先前冻结的 `RGW-full-workspace-v1`，以及随后为检验 repository-specific advantage 而设计的 `M5-W2`。两组实验共同指向一个保守结论：当前证据不支持“更强 Click-specific context 足以产生稳定 W 轴优势”，也不支持将结果推进为 NFL reversal claim。

`RGW-full-workspace-v1` 显示，RBench 能区分 frontier 与 cheap 模型层级，但 RWork 在固定分母口径下四个 ACUT 全部为 2/6，不能形成配置层面的可解释差异。后续 validity audit 将 9 个 RWork `unsafe_or_scope_violation` 中的 7 个归为 source-derived URL-only policy hold，使 W 轴 measured verified pass rate 从 8/24（33.3%）调整为 8/17（47.1%）；但这一审计只改善测量解释，不把 replay pass 回填为 primary result。

`M5-W2` 进一步收窄问题：在 10 个新的 held-out Click RWork-v2 任务上，测试更强的 `cheap-click-deep-specialist-v2` 是否能相对 `cheap-generic-swe` 拉开至少 2 个任务的 W2 优势。40 个 primary cells 已全部完成。`cheap-click-deep-specialist-v2` 得分为 5/10，与 `cheap-generic-swe` 的 5/10 持平；预注册的 context-effect gate 失败。因此，按协议应停止并报告负结果，不运行 R2，也不运行 ACUT G 作为结论性评分。

## 读者问题与判读标准

本阶段报告回答的核心问题不是“哪个 ACUT 总体最好”，而是：当前实验结果是否足以支持继续构造跨任务、跨轴的 NFL reversal 叙事？

判读标准有三条。第一，primary result 与 post-run audit 必须分开，审计可以解释失败类型，但不能事后改写 primary score。第二，不同分母不能混合：RGW v1 的 6 个旧 RWork 任务与 M5-W2 的 10 个新 RWork-v2 任务属于不同 primary denominator。第三，G 轴的 no-model readiness 与 ACUT G scoring 必须分开：gold-patch smoke 通过只说明 evaluator basis 可用，不说明任何 ACUT 在 G 上得分。

## 实验一：RGW-full-workspace-v1

RGW v1 是早期冻结矩阵，包含四个 ACUT：`cheap-generic-swe`、`cheap-click-specialist`、`frontier-generic-swe`、`frontier-click-specialist`。完整设计包含 RBench、RWork 与 G 三个轴，共 80 个 cells；当前可解释的 primary scoring 覆盖 RBench 与 RWork 共 56 个 cells。G 轴 24 个 cells 在该阶段均为 `verifier_infra_error`，不能按零分填入，也不能用于 ranking。

### RGW v1 primary results

| ACUT | RBench pass / denom | RBench pass rate | RWork fixed pass / denom | RWork fixed pass rate | G 状态 |
|---|---:|---:|---:|---:|---|
| `cheap-generic-swe` | 2/8 | 25.0% | 2/6 | 33.3% | 6 个 `verifier_infra_error` |
| `cheap-click-specialist` | 3/8 | 37.5% | 2/6 | 33.3% | 6 个 `verifier_infra_error` |
| `frontier-generic-swe` | 5/8 | 62.5% | 2/6 | 33.3% | 6 个 `verifier_infra_error` |
| `frontier-click-specialist` | 5/8 | 62.5% | 2/6 | 33.3% | 6 个 `verifier_infra_error` |

RBench 的信号主要是模型层级信号：两个 frontier 配置均为 5/8，高于两个 cheap 配置。RWork 则没有给出 configuration-level separation：四个 ACUT 均为 2/6。这个结果不能支持 specialist 优势，也不能支持稳定排序反转。

### RGW v1 validity audit

RGW v1 的主要测量风险来自 RWork 中 9 个 `unsafe_or_scope_violation` cells。审计结果显示，其中 7 个应归为 source-derived URL-only policy hold，2 个是真正的 model-generated unsafe。排除 7 个 policy hold 后，W 轴 measured denominator 从 24 变为 17，verified pass rate 从 8/24（33.3%）变为 8/17（47.1%）。

按 ACUT 的审计派生口径为：`cheap-generic-swe` 2/4，`cheap-click-specialist` 2/4，`frontier-generic-swe` 2/4，`frontier-click-specialist` 2/5。这个结果说明，清理 policy attribution 后 W 轴并非完全无信号；但它仍没有形成足够大的 Click specialist 优势。

RGW v1 因此应被冻结为负/中性基线，而不是与后续 M5-W2 分母混合。

## 实验二：M5-W2 repository-specific advantage stress test

M5-W2 的目标是检验一个更窄、更可裁决的问题：更强的 Click-specific task-agnostic context 是否能在新的 held-out Click work tasks 上显著优于 cheap generic baseline。

M5-W2 使用四个 ACUT：

| ACUT | 角色 |
|---|---|
| `cheap-generic-swe` | cheap generic baseline |
| `cheap-click-specialist` | 既有 Click specialist baseline |
| `cheap-click-deep-specialist-v2` | 新的强 Click context treatment |
| `frontier-generic-swe` | 高能力 generic contrast |

任务分母为 RWork-v2 的 10 个新 admitted Click tasks（`click__rwork__101` 至 `click__rwork__110`），另有 4 个 reserve tasks 预注册但未进入 primary denominator。10 个 primary tasks 的 admission smoke 全部通过：no-op base verifier 失败，reference patch verifier 通过。M5-W2 不使用 best-of-N；每个 ACUT/task cell 只有一次 primary attempt。

预注册 gates 为：

| Gate | 表达式 | 判读 |
|---|---|---|
| Context-effect gate | `cheap-click-deep-specialist-v2 >= cheap-generic-swe + 2 tasks` | 若失败，停止并报告 stronger Click context 未产生 W separation |
| NFL-candidate gate | `cheap-click-deep-specialist-v2 > frontier-generic-swe` | 只有在 context-effect gate 先通过时才有解释价值 |

## M5-W2 primary results

M5-W2 primary matrix 共 40 个 cells，全部完成；无 missing cells，无 infra reruns/exclusions，无 true unsafe，无 policy hold。总状态分布为 18 个 `verified_pass`、20 个 `verified_fail`、2 个 `no_diff`。

| ACUT | W2 score | Pass rate | Status counts |
|---|---:|---:|---|
| `cheap-generic-swe` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `cheap-click-specialist` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |
| `cheap-click-deep-specialist-v2` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `frontier-generic-swe` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |

Gate 结果如下：

| Gate | Result | 解释 |
|---|---|---|
| Context-effect gate | failed | deep specialist 为 5/10，cheap generic 为 5/10，margin 为 0，低于要求的 +2 tasks |
| NFL-candidate gate | passed in isolation | deep specialist 为 5/10，frontier generic 为 4/10，margin 为 +1；但由于 context-effect gate 先失败，这不足以形成 candidate status |

Pairwise secondary metrics 也支持负结果：`cheap-click-deep-specialist-v2` 相对 `cheap-generic-swe` 为 0 wins、0 losses、10 ties；相对 `frontier-generic-swe` 为 1 win、0 losses、9 ties。也就是说，deep specialist 与 cheap generic 的逐任务表现完全同分，不能被解释为有效 context treatment。

## G 轴状态

M5-W2 之后执行了 G6 gold-patch no-model smoke。该 smoke 在 pinned six-task SWE-Bench Pro basis 上通过，resolved count 为 6/6，证明 dataset cache、evaluator checkout、Docker/backend、gold-patch input path、artifact layout 与 score parser 可在 no-model 条件下跑通。

这不是 ACUT G scoring。没有 ACUT patch generation，没有 G_score，也没有 public leaderboard proxy。它只能说明 G 轴基础设施从“不可解释阻塞”推进到“gold-patch basis 已证明”的状态。由于 M5-W2 的 W gate 已失败，当前阶段没有根据继续运行 R2 或 ACUT G。

## 解释与论证

第一，RGW v1 的 RBench 结果说明矩阵能够观察到模型层级差异，但这一差异没有迁移到 RWork。RWork fixed denominator 上四个 ACUT 全部 2/6，意味着旧 W pack 无法支持 specialist 或 frontier 的稳定排序。

第二，RGW v1 的 validity audit 修复了一个重要测量问题：source-derived URL-only policy hold 不应与 model-generated unsafe 混为一类。但该修复不会改变 primary score，也不会制造配置优势。审计后的 W 轴更可解释，但仍不足以支持 reversal。

第三，M5-W2 是对“是否只是 context treatment 不够强”的直接压力测试。若更强 Click context 真能带来 repository-specific advantage，它至少应相对 cheap generic baseline 增加 2 个任务。实际结果为 5/10 对 5/10，context-effect gate 明确失败。

第四，`cheap-click-deep-specialist-v2` 以 5/10 略高于 `frontier-generic-swe` 的 4/10，不能单独构成 NFL-candidate 证据。因为预注册逻辑要求先证明 context treatment 相对同层 cheap generic baseline 有效；否则 +1 任务 margin 可能只是任务噪声、tie/no_diff 分布或小样本波动。

因此，当前最稳妥的解释是：在现有 Click task construction、ACUT design 与 one-shot primary attempt 条件下，未观察到可用于推进 NFL reversal 叙事的 repository-specific advantage。

## 威胁到有效性的因素

1. 样本规模仍小。M5-W2 只有 10 个 held-out Click tasks，每个 cell 只有一次 attempt，没有方差估计或 confidence interval。
2. 任务域单一。当前结果主要覆盖 Click work tasks，不能直接推广到所有 Python CLI 库、所有 repository-specific repair tasks 或其他语言生态。
3. Verifier score 是行为门槛，不等同于完整人工质量评估。`verified_fail` 可能包含局部正确但未满足测试的解法，`verified_pass` 也不代表全局最优实现。
4. Context pack 的构造已排除目标 commits、reference patches、hidden verifiers、future history 与 final diffs；这提升了实验洁净度，但也限制了 treatment 强度。
5. RGW v1 与 M5-W2 不能合并统计。它们使用不同 task denominator 与不同问题设定，只能作为阶段叙事的前后证据。
6. G6 gold-patch smoke 通过不等于 ACUT G 可用结论。它只证明 known-good patches 可由 evaluator basis 评分。

## 隐私、复现与研究伦理

本报告只发布 aggregate evidence 与 redacted interpretation，不公开 full URLs、secrets、credentials、raw unsafe content、raw URL-bearing patches 或绝对本地文件路径。涉及 source-derived URL-only 的 replay artifacts 仅作为私有审计材料保留，不能被提升为公开 primary evidence。

AI 辅助用于整理本地实验 artifacts、核对数值并撰写本报告；报告中的关键数值来自已生成的 primary summaries、decision notes、task admission smoke、W2 summary 与 G6 gold-patch smoke artifacts。没有引入外部文献、外部 leaderboard 分数或未核验的模型声称。

## 结论

当前阶段的结论是负结果。RGW v1 应作为负/中性基线冻结；M5-W2 已完成 40-cell W2 primary matrix，并且 preregistered context-effect gate 失败。`cheap-click-deep-specialist-v2` 没有超过 `cheap-generic-swe`，因此 stronger Click-specific context 未在当前 held-out Click work tasks 上产生可解释的 W separation。

下一步不应继续运行 R2 或 ACUT G 来追求结论性 reversal；更合理的方向是记录负结果，复盘 task construction 与 context treatment 假设，并在新的预注册问题下重新设计更有统计解释力的实验。

## 主要证据 artifacts

- `experiments/core_narrative/reports/2026-05-13_rgw_v1_decision.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_negative_result.md`
- `experiments/core_narrative/reports/m5_w2_protocol.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_task_admission.md`
- `experiments/core_narrative/results/m5_w2_primary/summary.json`
- `experiments/core_narrative/results/m5_w2_primary/reports/w2_primary_summary.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_g6_gold_patch_smoke_executed_abs_python.md`
