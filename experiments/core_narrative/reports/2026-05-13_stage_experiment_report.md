# Barcarolle 阶段性实验报告：M5-W2 负结果与 M6 协议准备

生成日期：2026-05-13  
报告性质：阶段性研究报告  
当前结论：M5-W2 为完成的负结果；M6 已完成协议准备，但尚未执行 W3 primary

## 摘要

Barcarolle 当前阶段已经从“证明评测流程能产生可评分结果”推进到“能够在预注册 gate 下接受负结果，并把下一轮假设与上一轮失败严格隔离”。这一点比单次 agent 胜负更重要：项目现在可以区分模型能力失败、输出契约失败、验证器基础设施失败、policy hold、任务分母混合和事后选择偏差。

本阶段的实证结论仍然是保守的。`M5-W2` 在 10 个新的 held-out Click work tasks 上完成了 4 个 ACUT x 10 个任务的 40-cell primary matrix。更强的静态 Click context treatment `cheap-click-deep-specialist-v2` 得分为 5/10，与同层 `cheap-generic-swe` 的 5/10 持平，未达到预注册的 +2 tasks context-effect gate。因此，M5-W2 不支持 repository-specific advantage，也不支持 NFL-style ranking reversal。

后续 no-new-model-call failure forensics 解释了负结果结构，但没有修改 primary scores。10 个 W2 任务中有 3 个 ceiling tasks、5 个 floor tasks、2 个 separator tasks；deep specialist 的上下文投递审计通过，cheap generic 的负控也通过。这说明失败不能简单归因于 context 未进入 prompt，而更可能与 W2 分母的分离度、静态上下文 treatment 强度和任务族难度有关。

M6 不是 M5 的补救实验，而是一项新假设的协议准备：用 RBench-derived、可审计的 repository repair playbook 构造 `cheap-click-rbench-calibrated-v1`，并在未来新的 W3 held-out denominator 上检验 repository-calibrated guidance 是否优于 generic 与 static-context baselines。截至本报告，M6 已完成 ACUT manifest、context pack、leakage audit、context loader smoke 和 W3 protocol；没有执行 W3 primary、R3 或 ACUT G。

## 研究问题与判读标准

Barcarolle 的核心问题不是“哪个模型总体最强”，而是：通用 coding-agent benchmark 的高分是否足以证明某个 agent configuration 适合特定仓库的真实维护工作。当前阶段回答三个较窄的问题：

| 问题 | 当前回答 |
|---|---|
| 更强的静态 Click context 是否能在新的 W2 held-out tasks 上击败 cheap generic baseline？ | 不能。`cheap-click-deep-specialist-v2` 与 `cheap-generic-swe` 均为 5/10。 |
| M5-W2 的负结果是否可能由 context 没有进入 prompt 造成？ | 现有审计不支持。deep specialist 10/10 runs 通过 context delivery checks，cheap generic 10/10 negative controls 也通过。 |
| 当前是否可以推进 NFL-style reversal claim？ | 不能。W2 context-effect gate 失败，ACUT G score 也尚未形成可解释结果。 |

判读标准有三条。第一，primary scores 与 post-run diagnostics 分开：forensics 可以解释失败结构，但不能事后改写固定分母得分。第二，不同 denominator 分开：RGW v1、M5-W2 与未来 W3 不能混合统计。第三，G 轴准备与 ACUT G scoring 分开：gold-patch smoke 通过只说明 evaluator basis 可用，不代表任何 ACUT 的 G_score。

## 材料与方法

目标仓库为 `pallets/click`，锁定 commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`。实验框架使用 workspace-mode runner：ACUT 在隔离工作区自然读写并运行命令，系统从最终 workspace state 提取候选 patch，再在 fresh verification workspace 中 replay 并注入 hidden verifier。

M5-W2 的 primary denominator 是 10 个 admitted RWork-v2 Click tasks，覆盖五类行为问题：option/default/envvar/flag semantics、CliRunner/testing isolation、prompt/termui rendering、type conversion/parameter normalization 和 mixed integration。每个 primary task 都通过 admission smoke：no-op 必须失败，reference patch 必须通过。Primary run 不使用 best-of-N；每个 ACUT/task cell 只有一次 attempt。

M5-W2 使用四个 ACUT：

| ACUT | 角色 |
|---|---|
| `cheap-generic-swe` | cheap generic baseline |
| `cheap-click-specialist` | 既有 Click specialist baseline |
| `cheap-click-deep-specialist-v2` | 更强静态 Click context treatment |
| `frontier-generic-swe` | 高能力 generic contrast |

M5-W2 的预注册 context-effect gate 是：

```text
cheap-click-deep-specialist-v2 >= cheap-generic-swe + 2 tasks
```

若该 gate 失败，协议要求停止并报告负结果，不运行 R2 或 ACUT G 来追求事后 reversal。

## M5-W2 primary results

M5-W2 primary matrix 共 40 个 fixed-denominator cells，全部完成；无 missing cells、无 infra reruns/exclusions、无 true unsafe、无 policy hold。总状态分布为 18 个 `verified_pass`、20 个 `verified_fail`、2 个 `no_diff`。

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
| NFL-candidate contrast | passed in isolation | deep specialist 为 5/10，frontier generic 为 4/10，margin 为 +1；但 context-effect gate 先失败，因此不能形成 candidate status |

逐任务 paired metrics 也支持负结果：`cheap-click-deep-specialist-v2` 相对 `cheap-generic-swe` 为 0 wins、0 losses、10 ties；相对 `frontier-generic-swe` 为 1 win、0 losses、9 ties。也就是说，deep specialist 与 cheap generic 在 W2 上没有任何逐任务净优势。

## Failure forensics

M5-W2 之后执行了 no-new-model-call failure forensics。该步骤没有新增 ACUT 调用，没有重跑 primary，也没有改变固定分母得分。它只分析已存在的 artifacts。

W2 任务分离度如下：

| Classification | Count | 含义 |
|---|---:|---|
| Ceiling | 3 | 四个 ACUT 全部通过 |
| Floor | 5 | 四个 ACUT 全部失败 |
| Separator | 2 | 至少一个 ACUT 与其他 ACUT 分离 |

这个结构解释了为什么 W2 对 context treatment 的判别力有限。3 个 ceiling tasks 和 5 个 floor tasks 占 8/10，使得任何 ACUT 都很难在一次 attempt 的固定分母口径下拉开差距。两个 separator tasks 中，deep specialist 没有相对 cheap generic 获得净胜。

Treatment delivery audit 显示：`cheap-click-deep-specialist-v2` 的 10 次 runs 均通过 context pack id/hash marker 与 expected section presence checks；`cheap-generic-swe` 的 10 次 negative controls 均显示 context disabled。审计使用 redacted prompt metadata，而不是公开 raw prompt content。

Patch/reference overlap audit 生成 20 行 deep-vs-generic 诊断记录，但没有把 candidate 或 reference patch 内容复制到公开 artifacts。Near-miss blind review packet 已准备但未评分，状态为 `packet_prepared_unscored`；它被明确限制为后续解释材料，不改变 primary scores。

## 与 RGW v1 的关系

RGW-full-workspace-v1 是上一阶段负/中性基线。它显示 RBench 能区分部分模型层级：`frontier-generic-swe` 与 `frontier-click-specialist` 均为 5/8，高于 cheap 层级；但 RWork 固定分母下四个 ACUT 均为 2/6，没有 configuration-level separation。G 轴 24 个 cells 均为 `verifier_infra_error`，不能解释为模型失败，也不能按零分填入。

M5-W2 的意义在于把问题收窄到一个可裁决的 W-only 压力测试：如果更强静态 Click context 真能带来 repository-specific advantage，它至少应相对同层 cheap generic baseline 增加 2 个任务。结果没有发生。因此，RGW v1 与 M5-W2 应作为连续的负结果链条理解，但不能合并成一个统计 denominator。

## M6 protocol prep

M6 的目标不是修改 M5-W2，而是检验一个新的、可预注册的假设：

```text
RBench-calibrated repository repair guidance may improve cheap-tier Click performance on a fresh held-out W3 denominator.
```

M6 新增 ACUT 为 `cheap-click-rbench-calibrated-v1`。它与 `cheap-generic-swe` 保持同模型层级、同预算、同工具、同网络策略和同 workspace-mode verifier semantics；唯一差异是使用 RBench-derived repair playbook。该 playbook 可以使用 RBench task family taxonomy、抽象修复模式、Click 常见 bug-fix locations、maintainer-style regression test patterns 与常见失败原因 checklist，但禁止使用 W3 target commits、W3 reference patches、W3 hidden verifiers、W3 final diffs、W3 ACUT outputs，也禁止用 M5-W2 ACUT failed patches 作为校准材料。

截至本报告，M6 已完成以下准备：

| Artifact | 状态 |
|---|---|
| `cheap-click-rbench-calibrated-v1` ACUT manifest | validated: 1 valid, 0 invalid |
| RBench-calibrated context pack | generated with pack id `click_rbench_calibrated_context_pack_v1` |
| Leakage audit | `passed_for_protocol_prep` |
| Context pack load smoke | `passed`; expected sections all present; 0 model calls |
| W3 protocol | preregistered; primary not run |

W3 protocol 计划构造 20 个新的 held-out Click behavior tasks，五个任务族各 4 个。所有 concrete W3 tasks 仍未 materialize，必须在 primary 前完成 disjointness 与 leakage checks。

M6 预注册 gates 为：

| Gate | 表达式 |
|---|---|
| Repository-calibration gate | `cheap-click-rbench-calibrated-v1 >= cheap-generic-swe + 4 tasks` |
| Static-context comparison | `cheap-click-rbench-calibrated-v1 > cheap-click-deep-specialist-v2` |
| NFL-candidate gate | `cheap-click-rbench-calibrated-v1 > frontier-generic-swe` |

若 W3 失败，协议要求停止，不运行 R3 或 ACUT G。只有 W3 gate 通过后，才设计 R3；只有 W3 与 R3 形成可信 critical pair 后，才有理由运行 critical-pair ACUT G。

## 当前不能支持的结论

当前不能说 Barcarolle 已经证明 NFL-style ranking reversal。也不能说 Click specialist 已经优于 generic SWE，或 cheap specialist 已经优于 frontier generic。M5-W2 中 deep specialist 相对 frontier generic 的 +1 task 只能作为孤立对比，不能绕过同层 generic baseline gate 的失败。

当前也不能说 W2 负结果证明“repository-specific context 永远无效”。M5-W2 只证伪一个较窄假设：在当前 Click task construction、ACUT design、静态 task-agnostic context pack 和 one-shot primary attempt 条件下，更强静态 Click context 没有击败 cheap generic baseline。

最后，M6 目前只能被描述为协议准备完成，不能被描述为 positive result。W3 primary 尚未执行，R3 与 ACUT G 也未授权。

## 局限与有效性威胁

第一，W2 样本规模小。10 个 tasks 足以裁决预注册 gate，但不足以稳定估计细粒度 ACUT 能力或 family-level effect。

第二，任务分离度不足。8/10 W2 tasks 是 ceiling 或 floor，使 ACUT 间差异难以显现。下一阶段必须提高 separator density，同时避免用已观察到的 ACUT outputs 反向选择任务。

第三，当前 ACUT 差异仍偏窄。多数配置共享相同工具、预算、网络与运行方式，主要差异是模型层级和上下文策略。若真实仓库适配度来自 test-first 策略、检索策略、维护者风格或高预算迭代，当前矩阵覆盖不足。

第四，G 轴仍缺少 ACUT scoring。G6 gold-patch smoke 已证明 evaluator basis，但不是模型生成 patch 的 G_score。没有可解释 G_score，就不能完整讨论 general benchmark ranking reversal。

第五，公开报告必须保留隐私边界。涉及 raw prompts、URL-bearing patches、hidden verifier paths、credentials、secrets、private endpoint values 的材料不应公开；本报告只使用 aggregate 与 redacted artifacts。

## 结论与下一步

当前阶段的最稳妥结论是：Barcarolle 已经能产生可信负结果，并据此推进研究设计；但现有数据不支持 NFL-style reversal。M5-W2 应被冻结为 static Click context advantage 的负结果。M6 应作为新的 repository-calibrated hypothesis 继续，但必须在 W3 task admission、disjointness audit 和 leakage checks 完成后，才可执行 W3 primary。

下一步建议是按 M6 protocol materialize 20 个 W3 held-out tasks，保持五个任务族配额，确保 no-op fails 与 reference patch passes，并在执行前再次确认没有使用 W3 target commits、reference patches、hidden verifiers、final diffs 或 ACUT outputs 进行校准。只有 W3 gate 通过，才进入 R3 与 critical-pair G 设计。

## 研究伦理与 AI 使用说明

本报告基于仓库内已存在的实验报告、配置、JSON summary、forensics artifacts 与 protocol files 撰写。报告没有新增模型实验调用，没有重算 hidden verifier，没有修改任何 primary score，也没有引入外部 leaderboard 或未核验资料。

AI 辅助用于整理本地 artifacts、核对数值、组织中文研究报告结构和生成网页版本。所有关键数值均来自本地实验工件；不确定或未完成事项已明确标注为 protocol prep、not authorized 或 not run。

## 主要证据 artifacts

- `experiments/core_narrative/reports/2026-05-13_global_experiment_status_report.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_negative_result.md`
- `experiments/core_narrative/results/m5_w2_primary/summary.json`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md`
- `experiments/core_narrative/results/m5_w2_primary/task_separation_matrix.json`
- `experiments/core_narrative/results/m5_w2_primary/treatment_delivery_audit.json`
- `experiments/core_narrative/results/m5_w2_primary/patch_reference_overlap_audit.json`
- `experiments/core_narrative/results/m5_w2_primary/near_miss_blind_review.json`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_m6_transition_decision.md`
- `experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml`
- `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json`
- `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/leakage_audit.json`
- `experiments/core_narrative/results/m6_context_pack_load_smoke_20260513.json`
- `experiments/core_narrative/results/m6_validate_acut_20260513.json`
- `experiments/core_narrative/configs/m6_w3_protocol.yaml`
- `experiments/core_narrative/reports/2026-05-13_m6_rescue_prep_completion_audit.md`
