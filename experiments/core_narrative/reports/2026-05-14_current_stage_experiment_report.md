# Barcarolle 当前阶段实验结果报告：M5-W2 负结果冻结与 M6-W3 分母就绪

生成日期：2026-05-14  
报告性质：阶段性研究报告  
证据状态：M5-W2 primary 已完成并判定为负结果；M6-W3 denominator 已冻结并通过完整性审计；W3 primary、R3 与 ACUT G 均未运行

## 摘要

Barcarolle 的核心实验问题是：通用 coding-agent benchmark 的高排名，是否足以证明一个 agent configuration 适合特定仓库的真实维护工作。当前阶段没有得到支持 NFL-style ranking reversal 的正结果；更重要的进展是，实验流程已经能够在固定分母上产生可审计负结果，并把后续假设检验推进到新的 held-out denominator。

截至本报告撰写时，M5-W2 已完成 4 个 ACUT 乘以 10 个 Click held-out work tasks 的 primary matrix。`cheap-click-deep-specialist-v2` 与同层 `cheap-generic-swe` 均为 5/10，未达到预注册的 +2 task context-effect gate；逐任务 paired metrics 为 0 wins、0 losses、10 ties。因此，当前证据不支持“更强静态 Click context 在 W2 上优于同层 generic baseline”的假设，也不能支持 NFL-style ranking reversal。

M6 并未重解释 M5，而是作为新假设启动：RBench-calibrated repository repair guidance 是否能在新的 W3 held-out denominator 上提升 cheap-tier Click 表现。M6-W3 admission 从 40 个候选任务中接受 28 个，冻结 20 个 primary tasks 和 5 个 reserve tasks；后续 freeze integrity audit 的 17 项检查全部通过。该状态只说明 W3 已具备 primary execution 的前置条件，不说明任何 W3 模型表现。

## 研究问题与判读边界

本阶段面向的读者是 Barcarolle 项目合作者、实验评审者和可能关心仓库特异性评估的 agent 系统研究者。读者最需要区分三类证据：已经完成的 fixed-denominator primary result、用于解释失败结构的 post-run forensics，以及尚未产生模型分数的 protocol/admission readiness。

本阶段回答三个有限问题：

| 问题 | 当前回答 |
|---|---|
| 静态 Click context 是否在 W2 held-out tasks 上明显优于同层 generic baseline？ | 否。`cheap-click-deep-specialist-v2` 与 `cheap-generic-swe` 均为 5/10，margin 为 0。 |
| M5-W2 负结果能否归因于 context 没有进入 treatment prompt？ | 现有审计不支持。deep specialist 10/10 runs 通过 context delivery checks，cheap generic 10/10 negative controls 显示 context disabled。 |
| 当前是否能声称 Barcarolle 已证明 NFL-style ranking reversal？ | 不能。W2 context-effect gate 失败；W3 primary 未运行；ACUT G_score 仍未产生。 |

因此，本报告采用保守判读：M5-W2 是已完成的负结果；M6-W3 是下一轮实验的冻结分母和执行准备；二者不能混合统计，也不能用 W3 admission 代替 W3 performance。

## 材料与方法

目标仓库为 `pallets/click`，实验使用 workspace-mode runner。ACUT 在隔离工作区中自然读写、运行命令并生成代码修改；Barcarolle 从最终 workspace state 提取候选 patch，再在 fresh verification workspace 中 replay 并运行 hidden verifier。最终分数来自 fresh replay 与 hidden verifier，而不是 ACUT 自报状态、stdout、stderr 或本地测试叙述。

M5-W2 使用 10 个 admitted RWork-v2 Click tasks，覆盖 option/default/envvar/flag semantics、CliRunner/testing/input-output isolation、prompt/termui/output rendering、type conversion/parameter normalization 和 mixed integration 等任务族。四个 ACUT 为：

| ACUT | 角色 |
|---|---|
| `cheap-generic-swe` | cheap-tier generic baseline |
| `cheap-click-specialist` | Click-specific static context baseline |
| `cheap-click-deep-specialist-v2` | stronger static Click context treatment |
| `frontier-generic-swe` | higher-tier generic contrast |

M5-W2 是 one-shot fixed-denominator primary run，不使用 best-of-N。预注册 context-effect gate 为：

```text
cheap-click-deep-specialist-v2 >= cheap-generic-swe + 2 tasks
```

M6 在 M5 负结果冻结后启动，新增 `cheap-click-rbench-calibrated-v1`。该 ACUT 与 `cheap-generic-swe` 保持同模型层级、预算、工具、网络策略和 workspace-mode verifier semantics；差异在于使用 RBench-derived repair playbook。Protocol 明确禁止使用 W3 target commits、reference patches、hidden verifiers、final diffs、ACUT outputs 或 M5-W2 failed patches 进行校准。

M6-W3 admission 的任务不是运行模型，而是构造新的 held-out denominator。候选任务需要满足 no-op fails、reference patch passes、public statement 不泄漏 implementation diff、anchor 与 RBench/RWork-v1/W2 primary/W2 reserve disjoint，并且 task selection 不使用 ACUT outputs。

## M5-W2 Primary Result

M5-W2 primary matrix 的 40 个 fixed-denominator cells 全部完成；无 missing cells、无 infra reruns/exclusions、无 true unsafe、无 policy hold。总状态分布为 18 个 `verified_pass`、20 个 `verified_fail`、2 个 `no_diff`。

| ACUT | W2 score | Pass rate | Status counts |
|---|---:|---:|---|
| `cheap-generic-swe` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `cheap-click-specialist` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |
| `cheap-click-deep-specialist-v2` | 5/10 | 50.0% | 5 `verified_pass`, 5 `verified_fail` |
| `frontier-generic-swe` | 4/10 | 40.0% | 4 `verified_pass`, 5 `verified_fail`, 1 `no_diff` |

Context-effect gate 失败：deep specialist 与 cheap generic 同为 5/10，实际 margin 为 0，而预注册要求至少 +2 tasks。Deep specialist 相对 frontier generic 的 +1 task 只能作为孤立 contrast，不能绕过同层 baseline gate，也不能构成 NFL-candidate evidence。

逐任务 paired metrics 加强了这一负结论：deep specialist 相对 cheap generic 是 0 wins、0 losses、10 ties；相对 frontier generic 是 1 win、0 losses、9 ties。换言之，在 W2 的任务构造、ACUT 设计和 one-shot primary 设置下，更强静态 Click context 没有产生可观察的净优势。

## Failure Forensics

M5-W2 后续 forensics 没有新增模型调用，没有重跑 primary，也没有改变任何 score。其作用是解释失败结构，而不是补救结果。

| Classification | Count | 含义 |
|---|---:|---|
| Ceiling | 3 | 四个 ACUT 全部通过 |
| Floor | 5 | 四个 ACUT 全部失败 |
| Separator | 2 | 至少一个 ACUT 与其他 ACUT 分离 |

这个结构说明 W2 denominator 的分离度有限。10 个任务中有 8 个是 ceiling 或 floor，ACUT 间差异很难在固定分母中展开。两个 separator tasks 也没有显示 deep specialist 相对 cheap generic 的净胜：两者在两个 separator tasks 上均为通过。

Treatment delivery audit 排除了一个重要替代解释。`cheap-click-deep-specialist-v2` 的 10 次 runs 均通过 context pack id/hash marker 和 expected section presence checks；`cheap-generic-swe` 的 10 次 negative controls 均显示 context disabled。Near-miss packet 仍处于 `packet_prepared_unscored`，不能用于修改 M5-W2 primary score。

## M6-W3 Denominator Freeze

M6 的研究判断是，M5-W2 应冻结为 static Click context advantage 的负结果，不能通过事后补跑 G、改变 gate 或混合分母追求 reversal。新的可检验假设是：

```text
RBench-calibrated repository repair guidance may improve cheap-tier Click performance on a fresh held-out W3 denominator.
```

M6-W3 admission 输出状态为 `denominator_frozen_primary_not_run`。候选池与冻结结果如下：

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

Freeze controls 也已写入 manifest：deterministic run seed 为 `m6-w3-primary-20260513-denominator-v1`；ACUT run order 为 `cheap-generic-swe`、`cheap-click-deep-specialist-v2`、`cheap-click-rbench-calibrated-v1`、`frontier-generic-swe`；status mapping 规定 `verified_pass` 计 1 分，`verified_fail`、`no_diff`、`unsafe_or_scope_violation` 与非全局 infra timeout 计 0 分；`verifier_infra_error` 必须 rerun 或在 scoring 前记录为 global exclusion。

## Freeze Integrity Audit

M6-W3 freeze integrity audit 的状态为 `passed`，共 17 项检查全部通过。检查范围包括 primary/reserve manifest、admission summary counts、accepted task sheets 覆盖、no-op/reference smoke records、reference digest records、anchor records、与既有 denominator 的 disjoint anchors、public statement redaction、context hash match、W3 leakage boundary、protocol denominator synchronization、freeze controls、no W3/R3/G run boundary、cost ledger writability、workspace/source URL regression tests，以及 remote same-commit artifacts。

该审计确认了两个关键事实。第一，W3 denominator 未被审计过程改变，且 primary/reserve artifacts 与协议同步。第二，审计没有运行 W3 primary、R3 或 ACUT G，因此不会把 readiness 误写成 performance evidence。

## 当前可支持的结论

第一，Barcarolle 已能产生并保留可审计负结果。M5-W2 未被后续 forensics 改写，M6 也没有被包装成 M5 的补救胜利。

第二，当前数据证伪了一个窄假设：在 Click W2 task construction、one-shot primary、task-agnostic static context pack 和 workspace-mode runner 条件下，更强静态 Click context 没有击败同层 cheap generic baseline。

第三，W2 失败结构为下一阶段设计提供了明确约束。未来分母不能只扩大任务数量，还必须关注 separator density；同时，任务选择不能使用已观察 ACUT outputs 反向筛选。

第四，M6-W3 已达到 primary execution readiness。20-task denominator、5-task reserve、run seed、ACUT order、status mapping、infra policy、leakage boundary 和 remote artifact synchronization 均已冻结或审计通过。

## 当前不能支持的结论

当前不能说 Barcarolle 已证明 NFL-style ranking reversal。该结论至少需要同一批 ACUT 在 G/R/W 上都有可解释分数，并且 G 排名与 repository-specific R/W 排名出现不能由 leakage、infra error、policy hold、denominator mixing 或 output contract failure 解释的稳定反转。当前缺少 ACUT G_score，M5-W2 的 W gate 也失败。

当前也不能说 Click specialist 已经优于 generic SWE，或 cheap specialist 已经优于 frontier generic。M5-W2 中 deep specialist 相对 frontier generic 的 +1 task 是孤立对比；它不能绕过同层 generic baseline gate。

同样，W3 admission 与 freeze integrity audit 完成不代表 M6 已有正结果。Admission 和 audit 只说明下一轮 primary run 的分母和边界已准备好；`cheap-click-rbench-calibrated-v1` 是否有效，必须等 W3 primary 完成后才能判断。

## 局限与有效性威胁

M5-W2 样本规模较小。10 个 tasks 足以裁决预注册 gate，但不足以稳定估计细粒度 family-level effect。

W2 denominator 的分离度不足。3 个 ceiling tasks 和 5 个 floor tasks 占 8/10，使配置差异难以显现。W3 已扩展到 20 tasks，但 separator density 只有在 W3 primary 运行后才能评估。

ACUT 差异仍然有限。多数配置共享相同工具、预算、网络和运行语义；主要差异来自模型层级、静态 context 或 RBench-calibrated playbook。如果真实仓库适配能力来自 test-first workflow、高预算迭代、动态检索或维护者风格模拟，当前矩阵仍覆盖不足。

G 轴仍是关键缺口。G6 gold-patch smoke 证明 evaluator basis 可用，但不是 ACUT G_score。没有 G_score，就不能完整讨论 general benchmark ranking reversal。

公开报告必须维持隐私边界。本报告只使用 aggregate、redacted 和相对路径 artifacts；不公开 raw prompts、hidden verifier 内容、reference patch 内容、credentials、private endpoint values 或本地绝对路径。

## 下一步

下一步应严格按冻结的 W3 denominator 运行 primary matrix：4 个 ACUT 乘以 20 个 W3 tasks，一次 primary attempt，无 best-of-N，无 ACUT-specific retry。若 W3 repository-calibration gate 失败，应停止并写负结果，不运行 R3 或 ACUT G 来追求事后叙事。只有 W3 gate 通过，才应设计 R3；只有 W3 与 R3 构成可信 critical pair 后，才有理由运行 critical-pair ACUT G。

## 研究伦理与 AI 使用说明

本报告基于仓库内已存在的实验报告、配置、JSON summary、admission artifacts、forensics artifacts、context-pack audit 和 freeze integrity audit 撰写。报告没有新增模型实验调用，没有重算 hidden verifier，没有修改任何 primary score，也没有引入外部 leaderboard 或未核验资料。

AI 辅助用于整理本地 artifacts、核对数值、组织中文研究报告结构和生成网页版本。所有关键数值均来自本地实验工件；未完成事项明确标注为 negative result、denominator frozen、primary not run、R3 not run 或 ACUT G not run。

## 主要证据 artifacts

- `docs/experiments/core-narrative-experiment-plan.md`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_negative_result.md`
- `experiments/core_narrative/results/m5_w2_primary/summary.json`
- `experiments/core_narrative/results/m5_w2_primary/task_separation_matrix.json`
- `experiments/core_narrative/results/m5_w2_primary/treatment_delivery_audit.json`
- `experiments/core_narrative/reports/2026-05-13_m5_w2_m6_transition_decision.md`
- `experiments/core_narrative/configs/m6_w3_protocol.yaml`
- `experiments/core_narrative/context_packs/click_rbench_calibrated_v1/leakage_audit.json`
- `experiments/core_narrative/results/m6_context_pack_load_smoke_20260513.json`
- `experiments/core_narrative/reports/2026-05-13_m6_w3_admission_report.md`
- `experiments/core_narrative/reports/2026-05-13_m6_w3_admission_completion_audit.md`
- `experiments/core_narrative/results/m6_w3_admission_20260513.json`
- `experiments/core_narrative/results/m6_w3_admission/admission_summary_20260513.json`
- `experiments/core_narrative/reports/2026-05-13_m6_w3_freeze_integrity_audit.md`
- `experiments/core_narrative/results/m6_w3_freeze_integrity_audit_20260513.json`
- `experiments/core_narrative/configs/tasks/rwork_click_w3.yaml`
- `experiments/core_narrative/configs/tasks/rwork_click_w3_reserve.yaml`
