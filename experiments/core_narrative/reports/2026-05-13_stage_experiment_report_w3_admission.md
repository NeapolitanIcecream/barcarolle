# Barcarolle 阶段性实验报告：M5-W2 负结果、M6 准备与 W3 分母冻结

生成日期：2026-05-13
报告性质：阶段性研究报告
当前结论：M5-W2 是完成的负结果；M6 rescue-prep 已完成；W3 held-out 分母已冻结但 primary、R3 与 ACUT G 均未运行

## 摘要

Barcarolle 当前阶段的主要进展不是得到一个正向 reversal 结果，而是建立了一个能够承认负结果、冻结分母并继续提出新假设的实验流程。到 2026-05-13 晚间，项目已经完成三个连续步骤：第一，M5-W2 在 10 个新的 held-out Click work tasks 上完成 4 个 ACUT x 10 个任务的 primary matrix，并按预注册 gate 判定为负结果；第二，M6 rescue-prep 在不修改 M5 primary scores、不新增模型调用的前提下完成 failure forensics、RBench-calibrated ACUT scaffold、leakage audit 和 W3 protocol；第三，M6-W3 admission 从 40 个候选任务中接受 28 个，冻结 20 个 primary tasks 和 5 个 reserve tasks。

实证结论必须保持保守。M5-W2 中，`cheap-click-deep-specialist-v2` 与 `cheap-generic-swe` 同为 5/10，未达到“至少多 2 个任务”的 context-effect gate；逐任务 paired metrics 显示 deep specialist 相对 cheap generic 为 0 wins、0 losses、10 ties。因此，本阶段不支持 repository-specific static context advantage，也不支持 NFL-style ranking reversal。

M6-W3 admission 只是把下一轮实验推进到可执行前状态。W3 primary denominator 已冻结，五个任务族各 4 个 primary tasks；确定性 run seed、ACUT run order、status mapping 和 infra rerun policy 也已写入 manifest。与此同时，报告边界同样清楚：W3 primary 没有运行，R3 没有运行，ACUT G 没有运行，所以 M6 仍不是正结果。

## 研究问题与判读标准

Barcarolle 的核心问题不是“哪个 agent 在通用 benchmark 上最强”，而是：通用 coding-agent benchmark 排名能否充分证明某个 agent configuration 适合特定仓库的真实维护工作。当前阶段把这个大问题拆成三个更窄的可判读问题。

| 问题 | 当前回答 |
|---|---|
| 更强的静态 Click context 是否能在 W2 held-out tasks 上显著击败同层 generic baseline？ | 不能。`cheap-click-deep-specialist-v2` 与 `cheap-generic-swe` 均为 5/10，margin 为 0。 |
| M5-W2 负结果是否可以归因于 context 没有进入 prompt？ | 现有审计不支持。deep specialist 10/10 runs 通过 context delivery checks；cheap generic 10/10 negative controls 也通过。 |
| 当前是否已经能声称 NFL-style ranking reversal？ | 不能。W2 context-effect gate 失败；G 轴仍没有可解释 ACUT G_score；W3 primary 尚未运行。 |

判读标准有四条。第一，primary score 与 post-run forensics 分开：forensics 可以解释失败结构，但不能修改固定分母得分。第二，不同 denominator 分开：RGW v1、M5-W2 与 W3 不能混合统计。第三，协议准备、分母冻结和模型结果分开：W3 admission 完成不等于 W3 primary 有结果。第四，gold-patch smoke 与 ACUT scoring 分开：G6 gold-patch smoke 通过只能说明 evaluator basis 可用，不能替代任何 agent 的 G_score。

## 材料与方法

目标仓库为 `pallets/click`，锁定 commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`。实验框架使用 workspace-mode runner：ACUT 在隔离工作区自然读写并运行命令；Barcarolle 从最终 workspace state 提取候选 patch；随后在 fresh verification workspace 中 replay 并运行 hidden verifier。候选任务的 no-op 与 reference patch admission smoke 用于确认任务可评分。

M5-W2 使用 10 个 admitted RWork-v2 Click tasks，覆盖五类行为问题：option/default/envvar/flag semantics、CliRunner/testing/input-output isolation、prompt/termui/output rendering、type conversion/parameter normalization 和 mixed integration。四个 ACUT 分别是 `cheap-generic-swe`、`cheap-click-specialist`、`cheap-click-deep-specialist-v2` 和 `frontier-generic-swe`。Primary run 为 one-shot fixed denominator，不使用 best-of-N。

M6 rescue-prep 新增 `cheap-click-rbench-calibrated-v1`，其意图不是补救 M5，而是把假设从 task-agnostic static context 转向 RBench-calibrated repository repair guidance。该 ACUT 与 `cheap-generic-swe` 保持同模型层级、预算、工具、网络策略和 workspace-mode verifier semantics；差异在于使用 RBench-derived repair playbook。Protocol 明确禁止使用 W3 target commits、reference patches、hidden verifiers、final diffs、ACUT outputs 以及 M5-W2 failed patches 进行校准。

M6-W3 admission 的目标是先冻结新的 held-out denominator，而不是运行模型。候选池包含 40 个 W3 candidates；admission 要求 no-op fails、reference patch passes、public statement 不泄漏实现 diff，并与 RBench、RWork-v1、W2 primary 和 W2 reserve anchors 保持 disjoint。Admission 结果接受 28 个候选，从中冻结 20 个 primary tasks 和 5 个 reserve tasks。

## M5-W2 primary results

M5-W2 primary matrix 共 40 个 fixed-denominator cells，全部完成；无 missing cells、无 infra reruns/exclusions、无 true unsafe、无 policy hold。总状态分布为 18 个 `verified_pass`、20 个 `verified_fail`、2 个 `no_diff`。

| ACUT | W2 score | Pass rate | Status counts |
|---|---:|---:|---|
| `cheap-generic-swe` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `cheap-click-specialist` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |
| `cheap-click-deep-specialist-v2` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `frontier-generic-swe` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |

预注册 context-effect gate 如下：

```text
cheap-click-deep-specialist-v2 >= cheap-generic-swe + 2 tasks
```

实际结果为 failed：deep specialist 为 5/10，cheap generic 为 5/10，margin 为 0。NFL-candidate contrast 在孤立意义上为 passed，因为 deep specialist 比 frontier generic 多 1 个任务；但 context-effect gate 先失败，因此不能形成 candidate status。

逐任务 paired metrics 进一步支持负结果：deep specialist 相对 cheap generic 为 0 wins、0 losses、10 ties；相对 frontier generic 为 1 win、0 losses、9 ties。换言之，M5-W2 没有发现 static Click context 对同层 generic baseline 的净优势。

## Failure forensics

M5-W2 后续 forensics 没有新增模型调用，没有重跑 primary，也没有改变任何得分。它的作用是解释负结果结构。

| Classification | Count | 含义 |
|---|---:|---|
| Ceiling | 3 | 四个 ACUT 全部通过 |
| Floor | 5 | 四个 ACUT 全部失败 |
| Separator | 2 | 至少一个 ACUT 与其他 ACUT 分离 |

这个结构说明 W2 denominator 的判别力有限。10 个任务中有 8 个是 ceiling 或 floor，使 ACUT 间差异难以显现。两个 separator tasks 中，deep specialist 没有相对 cheap generic 获得净胜：一个 separator 上二者都通过，另一个 separator 上二者也都通过。

Treatment delivery audit 排除了一个重要替代解释：`cheap-click-deep-specialist-v2` 的 10 次 runs 均通过 context pack id/hash marker 与 expected section presence checks；`cheap-generic-swe` 的 10 次 negative controls 均显示 context disabled。Patch/reference overlap audit 和 near-miss review packet 已生成，但 near-miss packet 仍是 `packet_prepared_unscored`，不能用于修改 primary score。

## M6 rescue-prep

M6 rescue-prep 的研究判断是：M5-W2 应冻结为 static context advantage 的负结果，而不是通过补跑 G 或改变分母来追求事后 reversal。M6 因此被定义为新假设：

```text
RBench-calibrated repository repair guidance may improve cheap-tier Click performance on a fresh held-out W3 denominator.
```

截至 2026-05-13，M6 rescue-prep 已完成以下材料：

| Artifact | 状态 |
|---|---|
| `cheap-click-rbench-calibrated-v1` ACUT manifest | validated: 1 valid, 0 invalid |
| RBench-calibrated context pack | generated with pack id `click_rbench_calibrated_context_pack_v1` |
| Leakage audit | `passed_for_protocol_prep` |
| Context pack load smoke | `passed`; expected sections all present; 0 model calls |
| W3 protocol | preregistered before primary run |
| M5 to M6 decision note | frozen; M5 scores unchanged |

M6 的关键伦理和方法边界是 held-out integrity。RBench 可以作为校准集；W3 必须作为新的 evaluation set。任何使用 W3 target commits、reference patches、hidden verifiers、final diffs 或 ACUT outputs 的做法都会破坏 W3 的证据价值。

## W3 admission 与冻结状态

M6-W3 admission 已经把下一轮 held-out experiment 推进到分母冻结状态。工具输出状态为 `denominator_frozen_primary_not_run`。候选池与冻结结果如下：

| 项目 | 数值或状态 |
|---|---|
| Candidate pool | 40 |
| Accepted candidates | 28 |
| Rejected candidates | 12 |
| Frozen primary tasks | 20 |
| Frozen reserve tasks | 5 |
| Model calls during admission | 0 |
| Selection used ACUT outputs | false |
| W3 primary run | false |
| R3 run | false |
| ACUT G run | false |

20 个 primary tasks 按五个任务族均衡冻结：

| Family | Primary tasks |
|---|---:|
| option/default/envvar/flag semantics | 4 |
| CliRunner/testing/input-output isolation | 4 |
| prompt/termui/output rendering | 4 |
| type conversion/parameter normalization | 4 |
| parser/mixed integration | 4 |

W3 的固定运行设置也已冻结：deterministic run seed 为 `m6-w3-primary-20260513-denominator-v1`；ACUT run order 为 `cheap-generic-swe`、`cheap-click-deep-specialist-v2`、`cheap-click-rbench-calibrated-v1`、`frontier-generic-swe`。Status mapping 规定 `verified_pass` 记 1 分；`verified_fail`、`no_diff`、`unsafe_or_scope_violation` 和非全局 infra 的 timeout 记 0 分；`verifier_infra_error` 必须 rerun 或在 scoring 前记录为 global exclusion。Infra policy 不允许 ACUT-specific retry 或 best-of-N。

W3 admission completion audit 已检查 40 个 admission sheets 的字段完整性、accepted candidates 的 no-op/reference oracle、public statement 无 implementation diff、与既有 anchors 的 disjointness、20 个 primary task packs 的 materialization、reserve ordering、run seed、ACUT order、status mapping 和 infra policy。审计还确认没有运行 W3 primary、R3 或 ACUT G。

## 当前不能支持的结论

当前不能说 Barcarolle 已经证明 NFL-style ranking reversal。这个结论至少需要同一批 ACUT 在 G/R/W 上都有可解释分数，并且 G 排名与 repository-specific R/W 排名出现不能由泄漏、infra error、policy hold、分母混合或输出契约失败解释的稳定反转。当前缺少可解释 ACUT G_score，M5-W2 的 W gate 也失败。

当前也不能说 Click specialist 已经优于 generic SWE，或 cheap specialist 已经优于 frontier generic。M5-W2 中 deep specialist 相对 frontier generic 的 +1 task 是孤立对比，不能绕过同层 generic baseline gate 的失败。

同样，W3 admission 完成不代表 M6 有正结果。Admission 只说明任务分母、reserve、运行顺序和评分政策已经冻结；模型尚未在 W3 上执行。任何“calibrated specialist 更强”的说法都必须等 W3 primary 完成后才有证据。

## 当前可支持的结论

第一，Barcarolle 已能产生可审计的负结果。M5-W2 没有被事后改写，failure forensics 没有改变 primary scores，M6 也没有被包装成 M5 的补救胜利。

第二，当前数据证伪了一个窄假设：在当前 Click W2 task construction、one-shot primary、task-agnostic static context pack 和 workspace-mode runner 条件下，更强静态 Click context 没有击败同层 cheap generic baseline。

第三，项目已经具备执行下一轮更强假设检验的前置条件。M6-W3 的 20-task denominator 已冻结，任务族分布均衡，admission oracle 与 disjointness checks 已通过，primary 前的 claim boundary 已清楚记录。

第四，W2 的失败结构为 W3 设计提供了直接约束：未来不能只扩大任务数量，还必须提高 separator density，同时避免使用已观察到的 ACUT outputs 反向筛选任务。

## 局限与有效性威胁

M5-W2 样本规模小。10 个 tasks 足以裁决预注册 gate，但不足以稳定估计细粒度 ACUT 能力或 family-level effect。

W2 denominator 的分离度不足。3 个 ceiling tasks 和 5 个 floor tasks 占 8/10，使配置差异难以在固定分母下显现。W3 虽然扩大到 20 tasks，但 separator density 只有在 primary 运行后才能评估。

当前 ACUT 差异仍然有限。多数配置共享相同工具、预算、网络和运行语义；主要差异来自模型层级、静态 context 或 RBench-calibrated playbook。若真实仓库适配度来自 test-first workflow、检索策略、高预算迭代或维护者风格模拟，当前矩阵仍覆盖不足。

G 轴仍是关键缺口。G6 gold-patch smoke 证明 evaluator basis 可用，但不是 ACUT G_score。没有 G_score，就不能完整讨论 general benchmark ranking reversal。

公开报告还必须保留隐私边界。本报告只使用 aggregate、redacted 和相对路径 artifacts；不公开 raw prompts、hidden verifier 内容、reference patch 内容、credentials、private endpoint values 或本地绝对路径。

## 结论与下一步

本阶段最稳妥的结论是：Barcarolle 的实验流程已经足以拒绝一个看似合理的 repository-specific context 直觉，但尚未支持 NFL-style reversal。M5-W2 应作为 static Click context advantage 的负结果冻结。M6-W3 已完成分母冻结，下一步可以在不改变 denominator 的前提下运行 W3 primary。

W3 primary 应严格使用已冻结的 20 个 tasks、deterministic run seed、ACUT run order、status mapping 和 infra policy。若 W3 repository-calibration gate 失败，应停止并写负结果，不运行 R3 或 ACUT G 来追求事后叙事。只有 W3 gate 通过，才应设计 R3；只有 W3 与 R3 构成可信 critical pair 后，才有理由运行 critical-pair ACUT G。

## 研究伦理与 AI 使用说明

本报告基于仓库内已存在的实验报告、配置、JSON summary、admission artifacts、forensics artifacts 和 protocol files 撰写。报告没有新增模型实验调用，没有重算 hidden verifier，没有修改任何 primary score，也没有引入外部 leaderboard 或未核验资料。

AI 辅助用于整理本地 artifacts、核对数值、组织中文研究报告结构和生成网页版本。所有关键数值均来自本地实验工件；不确定或未完成事项已明确标注为 negative result、protocol prep、denominator frozen、primary not run 或 not authorized。

## 主要证据 artifacts

- `experiments/core_narrative/reports/2026-05-13_global_experiment_status_report.md`
- `experiments/core_narrative/reports/2026-05-13_stage_experiment_report.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_negative_result.md`
- `experiments/core_narrative/results/m5_w2_primary/summary.json`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_failure_forensics.md`
- `experiments/core_narrative/results/m5_w2_primary/task_separation_matrix.json`
- `experiments/core_narrative/results/m5_w2_primary/treatment_delivery_audit.json`
- `experiments/core_narrative/results/m5_w2_primary/patch_reference_overlap_audit.json`
- `experiments/core_narrative/results/m5_w2_primary/near_miss_blind_review.json`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_m6_transition_decision.md`
- `experiments/core_narrative/reports/2026-05-13_m6_rescue_prep_completion_audit.md`
- `experiments/core_narrative/configs/acuts/cheap-click-rbench-calibrated-v1.yaml`
- `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/manifest.json`
- `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/leakage_audit.json`
- `experiments/core_narrative/results/m6_context_pack_load_smoke_20260513.json`
- `experiments/core_narrative/configs/m6_w3_protocol.yaml`
- `experiments/core_narrative/reports/2026-05-13_m6_w3_admission_report.md`
- `experiments/core_narrative/reports/2026-05-13_m6_w3_admission_completion_audit.md`
- `experiments/core_narrative/results/m6_w3_admission_20260513.json`
- `experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json`
- `experiments/core_narrative/configs/tasks/rwork_click_w3.yaml`
- `experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml`
