# Barcarolle 当前阶段性实验结果报告：Rich-W20 与 External Calibrated SymPy Checkpoint

生成日期：2026-05-17

报告性质：阶段性实验结果报告

当前结论：Barcarolle 已完成两类互补的阶段性证据闭环。其一，`repository-local-rich-w20-v1` 已完成一次固定分母、clean replay、hidden verifier 的 reduced primary run，但预注册主要成功门槛失败；它是完整的 negative/mixed repository-local result，而不是 ranking reversal 证据。其二，`external-calibrated-repo-benchmark-v1` 已冻结 SymPy 外部 E 与仓库本地 B 分母，并在用户修改计划下完成 E30/B10 checkpoint；该 checkpoint 运行与隐私校验干净，但实验仍暂停在中间点，不能替代 full E spread gate，也不能证明 E 排名能预测 B 表现。

## 摘要

本报告汇总 Barcarolle core narrative 在 2026-05-15 至 2026-05-16 的当前阶段结果。阶段内有两条主线。

第一条主线是 repository-local Rich-W20 reduced primary。0514 原 repository-local Rich benchmark 因 W* reserve 与 candidate-pool gate 失败而在 primary run 前终止；后续以新的预注册 revision `repository-local-rich-w20-v1` 执行 reduced-scale decision-validity pilot。该 pilot 共 160 个 normalized results，R 轴 80/80 cells 完成，W* 轴 80/80 cells 完成，没有 missing cells、rerun/exclusion cells 或 triage-paused cells。固定分母结果显示，R 轴选择 generic baseline A0；W* 轴最佳为 inert control A1，selection regret 为 1 个 W* task。两个核心 intervention-effect gates 均失败：A4 localization tool 相对 A0 在 W* 上增益为 0，低于 +4 tasks 要求；R-selected 相对 A0 在 W* 上增益也为 0，低于 +3 tasks 要求。

第二条主线是 external calibrated SymPy benchmark。协议 `external-calibrated-repo-benchmark-v1` 冻结了 SWE-bench Verified SymPy E slice 与 repository-local SymPy B tasks：E 为 48 tasks / 288 cells，B primary 为 20 tasks / 120 cells，B reserve 为 20 tasks。E/B freeze integrity audit 与 ACUT freeze 均通过。随后在用户授权的修改计划下，E 运行至前 30 个 task ordinals，共 180 cells；B pilot 运行至前 10 个 task ordinals，共 60 cells；之后按 checkpoint 暂停。E30 resolved 101/180，B10 resolved 14/60，external verifier infra errors 均为 0，公开工件隐私扫描通过。

当前最稳妥的总体读法是：Barcarolle 的实验治理与执行管线继续变强，已经能冻结分母、执行 primary matrix、在结果不利时保留负结果，并对公开报告做隐私边界检查。但当前结果仍不支持 NFL-style ranking reversal，也不支持“更 rich 的仓库上下文、localization tool、或外部 E 高分会自然转化为 repository-local B/W 优势”的强结论。

## 读者问题与判断标准

本报告回答三个问题。

第一，Rich-W20 是否证明 repository-local R 轴能够选择出在 held-out W* 上明显更好的 ACUT？答案是否定的。R 轴没有选出 W* best，也没有产生相对 generic baseline 的 W* 增益。

第二，external calibrated SymPy checkpoint 是否已经支持从外部 E 到仓库本地 B 的预测性结论？答案也是否定的。E30 与 B10 只是修改计划下的中间 checkpoint；E full spread gate 未完成，B10 样本小且 floor-heavy，不能被解释成 final predictivity result。

第三，当前阶段是否仍有研究价值？有。价值主要在评测系统、协议边界、负结果报告和隐私治理，而不是在 agent 排名胜利故事。

判断标准如下：不混合不同实验分母；不把 terminal blocked 的原协议改写为成功；不把 checkpoint 当作 full protocol；不把 post-run audit 回填为 primary score；不公开 raw statements、raw commits、reference/gold patches、candidate patches、hidden verifier material、verifier outputs、credentials、endpoint values 或本地绝对路径。

## 协议边界

0514 原 repository-local Rich 线的终止仍然成立。W* 达到 20 个 primary task floor，但未达到 5 个 reserve 与 40 个 candidate pool 目标；primary runs 在该原协议下未获授权。`repository-local-rich-w20-v1` 是新的 reduced protocol，只能支持 reduced-scale repository-local decision-validity claim，不能支持 original 0514 protocol success 或 full benchmark generation robustness claim。

External calibrated SymPy 线同样有明确边界。协议配置中，B runs 原本不应在 full E spread gate 前启动；2026-05-16 的 B10 是用户授权修改计划下的 pilot override。该修改计划完成 E30 与 B10 后暂停，且 checkpoint JSON 记录 no additional experiment cells started after B10。因此，B10 只能作为中间诊断，不是完整 B primary result。

## 实验一：Repository-Local Rich-W20

Rich-W20 使用两个 20-task primary denominator：R 用于 repository-specific selection signal，W* 用于 held-out work performance judgment。四个 ACUT 均使用 frozen cheap route `gpt-5.4-mini`，差异集中在上下文与工具策略。

| Slot | ACUT | 角色 |
| --- | --- | --- |
| A0 | `cheap-generic-swe` | generic baseline |
| A1 | `cheap-rich-inert-control-v1` | same-token inert control |
| A3 | `cheap-rich-c-calibrated-v1` | C-derived repository-calibrated playbook |
| A4 | `cheap-rich-localization-tool-v1` | code-understanding localization tool |

Primary completion 如下：

| 项目 | 结果 |
| --- | ---: |
| Expected primary attempts | 160 |
| Normalized results | 160 |
| R present cells | 80 / 80 |
| W* present cells | 80 / 80 |
| Missing cells | 0 |
| Rerun/exclusion cells | 0 |
| Triage-paused cells | 0 |

固定分母 primary score 如下：

| Slot | ACUT | R pass / 20 | R score | W* pass / 20 | W* score |
| --- | --- | ---: | ---: | ---: | ---: |
| A0 | `cheap-generic-swe` | 5 | 25.0% | 8 | 40.0% |
| A1 | `cheap-rich-inert-control-v1` | 2 | 10.0% | 9 | 45.0% |
| A3 | `cheap-rich-c-calibrated-v1` | 3 | 15.0% | 6 | 30.0% |
| A4 | `cheap-rich-localization-tool-v1` | 2 | 10.0% | 8 | 40.0% |

R 轴选择 A0，W* 轴最佳为 A1，selection regret 为 1 个 W* task。预注册成功门槛结果如下：

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| A4 vs A0 on W* | at least +4 tasks | 0 | failed |
| R-selected vs A0 on W* | at least +3 tasks | 0 | failed |
| R-selected within W* best | within 1 or 2 tasks | 1 | passed |
| Inert control guard | A1 not selected unless W* supports it | A0 selected | passed |

状态分布如下：

| Split | verified_pass | verified_fail | unsafe_or_scope_violation |
| --- | ---: | ---: | ---: |
| R | 12 | 66 | 2 |
| W* | 31 | 40 | 9 |

任务分离度限制了可解释性。R 轴 20 个 tasks 中，15 个对四个 ACUT 都没有 pass，2 个对四个 ACUT 全部 pass，仅 3 个产生部分区分。W* 轴 20 个 tasks 中，9 个为 zero-pass，4 个为 all-pass，7 个产生部分区分。这个结构足以执行 reduced negative result，但不足以稳定估计细粒度 ACUT 排名差异。

Rich-W20 的结论是：pipeline 已完成，主要 intervention hypotheses 未通过。A3 与 A4 没有在 W* 上超过 A0；A1 成为 W* best 更像 validity warning，而不是 inert control 具有实质仓库能力优势的证据。

## 实验二：External Calibrated SymPy Checkpoint

`external-calibrated-repo-benchmark-v1` 的目标是用 SWE-bench Verified SymPy 作为外部 E 轴，并构造同仓库 repository-local B tasks 作为校准/控制基底。协议冻结状态如下：

| 组件 | 冻结结果 |
| --- | --- |
| E denominator | SWE-bench Verified / test / `sympy/sympy`，48 tasks，288 ACUT-task cells |
| B denominator | 40 accepted generated candidates，20 primary tasks，20 reserve tasks |
| B admission quality | generated-candidate reference patch pass rate 1.0，no-op fail rate 1.0 |
| ACUT profiles | 6 个 profiles 冻结，覆盖 `gpt-5.4`、`gpt-5.5`、`gpt-5.4-mini`、不同 reasoning effort 与 AGENTS context |
| Freeze integrity | passed |
| Raw public boundary | 不公开 raw problem statements、raw commits、patches、hidden verifier material 或 verifier outputs |

ACUT 矩阵如下：

| Slot | ACUT | 模型/配置 |
| --- | --- | --- |
| A0 | `external-sympy-a0-gpt54-medium-concise` | `gpt-5.4` medium, concise |
| A1 | `external-sympy-a1-gpt54-low-concise` | `gpt-5.4` low, concise |
| A2 | `external-sympy-a2-gpt54-high-concise` | `gpt-5.4` high, concise |
| A3 | `external-sympy-a3-gpt55-high-concise` | `gpt-5.5` high, concise |
| A4 | `external-sympy-a4-gpt54mini-high-concise` | `gpt-5.4-mini` high, concise |
| A5 | `external-sympy-a5-gpt54-high-rich-agents` | `gpt-5.4` high, rich AGENTS |

在用户修改计划下，E 完成前 30 个 task ordinals，B 完成前 10 个 task ordinals，并在 checkpoint 后暂停。

### E30 结果

E30 共 180 cells，resolved 101/180，resolved rate 56.11%，empty patches 9，external verifier infra errors 0。原 full-E spread gate 仍未完成，原因是只评分了 180/288 Phase 2 cells。

| Slot | Resolved / 30 | Rate | Empty patches | Infra errors |
| --- | ---: | ---: | ---: | ---: |
| A0 | 16 | 53.33% | 1 | 0 |
| A1 | 15 | 50.00% | 2 | 0 |
| A2 | 16 | 53.33% | 2 | 0 |
| A3 | 19 | 63.33% | 0 | 0 |
| A4 | 18 | 60.00% | 1 | 0 |
| A5 | 17 | 56.67% | 3 | 0 |

E30 的任务分离度为 13 个 all-pass tasks、9 个 all-fail tasks、8 个 partial-separator tasks。A3 在 E30 上最高，A4 次之，但这个排序仍是 first-30 checkpoint 排序，不是 full E ranking。

### B10 结果

B10 共 60 cells，resolved 14/60，score rate 23.33%，external verifier infra errors 0。状态计数为 verified_pass 14、verified_fail 46。

| Slot | Resolved / 10 | Rate | Infra errors |
| --- | ---: | ---: | ---: |
| A0 | 2 | 20.00% | 0 |
| A1 | 3 | 30.00% | 0 |
| A2 | 3 | 30.00% | 0 |
| A3 | 2 | 20.00% | 0 |
| A4 | 2 | 20.00% | 0 |
| A5 | 2 | 20.00% | 0 |

B10 的任务分离度更弱：10 个 tasks 中，2 个 all-pass，7 个 all-fail，只有 1 个 partial-separator task。这个结构说明 B10 更像 hard/floor-heavy pilot，暂时不能提供稳定 ranking signal。它还提示一个风险：E30 上较强的 A3/A4 并没有在 B10 中形成对应优势，但由于 B10 样本量和分离度都不足，这只能作为 predictivity warning，不能写成 ranking reversal 结论。

### Validation

External checkpoint 的工程与隐私验证是当前阶段的正向结果：

| 检查 | 结果 |
| --- | --- |
| Public marker scan | passed，0 raw path/private filename hits |
| Private content scan | passed，0 hits across statement snippets、raw commits、private patch/log snippets |
| Focused pytest | 52 passed，1 LibreSSL/urllib3 warning |
| Process cleanup | passed，0 residual experiment processes |
| Public artifact boundary | 仅记录 status、counts、scores、digests 与 redacted paths |

## 跨实验解释

两个实验共同支持一个谨慎结论：Barcarolle 的评测系统已经比早期 Click pilots 更能承受负结果。Rich-W20 没有让 localization 或 calibrated context 获胜；External SymPy checkpoint 没有把 first-30 E 排名自然转化为 B10 排名；但两条线都保留了固定分母、attempt 边界、hidden verifier、公开/私有工件分离和 checkpoint 状态。

当前阶段最重要的研究含义不是“某个 ACUT 最强”，而是“仓库级 agent 准入需要可证伪协议”。没有这些分母和 gate，A4 localization tool、A5 rich AGENTS、A3 stronger model 或 R-selected strategy 都容易被事前直觉高估。当前数据迫使这些直觉接受固定分母检验。

## 不能支持的结论

本阶段不能支持以下说法。

1. 不能说 0514 原 repository-local Rich benchmark 成功。该协议已在 primary runs 前 terminal blocked。
2. 不能说 Rich-specific calibrated playbook 或 localization tool 已优于 generic baseline。A3 与 A4 均未超过 A0 的 W* score。
3. 不能说 R 轴已证明能选择出 W* 上显著更好的 ACUT。R-selected A0 相对 A0 baseline 的 W* 增益为 0。
4. 不能说 external calibrated SymPy 已完成 full protocol。E 只完成 180/288 cells；B10 是用户修改计划下的 pilot override。
5. 不能说 E30 排名能预测 B10 表现，或 E/B 已出现可靠 ranking reversal。B10 样本小、分离度弱，且 full E spread gate 未完成。
6. 不能把 Rich-W20、External E30/B10、早期 Click M5/M6 或 RGW v1 分母合并成 aggregate advantage。

## 有效性威胁

第一，Rich-W20 是 reduced protocol。它取消了 0514 原协议的 W* reserve 与 40-pool 要求，因此只能支持 reduced-scale conclusion。

第二，样本量仍小。Rich-W20 每个 split 20 tasks；External checkpoint 只覆盖 E30 与 B10。单次 attempt、无 best-of-N、无多 attempt 方差估计。

第三，任务分离度不足。Rich R、External B10 均 floor-heavy；E30 也有大量 all-pass/all-fail tasks。separator density 不足会削弱 rank-selection 与 predictivity analysis。

第四，ACUT 差异仍有限。Rich-W20 的差异主要是 cheap-route context/tool intervention；External SymPy 的差异主要是模型、reasoning effort 与 AGENTS context。结果不能推广到 test-first、retrieval-heavy、高预算、多轮或人工维护者式 agents。

第五，checkpoint semantics 容易被误读。E30/B10 的价值是诊断与暂停点，不是完整 primary endpoint。任何对 E/B predictivity 的强断言都需要 full protocol 或新的预注册 reduced protocol。

第六，unsafe/scope 与 empty patch 类别需要后续审计。当前报告按 fixed denominator 保留其结果，但不把这些类别解释成单一原因。

## 隐私、复现与研究伦理

本报告只使用仓库内公开/可发布的 aggregate artifacts、score summaries、protocol reports 与 digest-level evidence。报告不公开 raw SWE-bench problem statements、raw commits、reference/gold patches、candidate patches、hidden verifier material、verifier outputs、credential values、endpoint values、private raw run directories 或本地绝对路径。

AI 辅助用于整理已有实验 artifacts、核对表格数值、组织中文报告结构和生成网页版本。报告没有新增 ACUT model calls，没有修改 primary score，没有重跑 hidden verifier，也没有把 post-run interpretation 回填为 primary evidence。

## 结论

当前阶段应被记录为“治理与执行能力增强，但主要科学假设仍未通过”。Rich-W20 是完整但负向/混合的 reduced primary result；External calibrated SymPy 是干净但暂停中的 E30/B10 checkpoint。两者共同说明，Barcarolle 已经能把仓库级 agent 评测从直觉判断推进到可证伪协议，但目前还没有得到足以支持 NFL-style ranking reversal 或 E-to-B predictivity 的结果。

下一步应保持 Rich-W20 的负结果边界，保持 External checkpoint 的暂停边界，并在新的 owner decision 下选择其一：完成 full E spread gate 后继续 B primary，或预注册一个 reduced E30/B10 follow-up，明确它只回答缩小范围内的 predictivity/diagnostic 问题。

## 主要证据工件

- `docs/draft/barcarolle-rich-w20-stage-report-2026-05-15.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_benchmark_final_blocked_report.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_primary_results.md`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/summary.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/analysis.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/rw_table.json`
- `experiments/core_narrative/configs/external_calibrated_benchmark_20260515.yaml`
- `experiments/core_narrative/reports/external_e_task_freeze_report.md`
- `experiments/core_narrative/reports/external_calibrated_freeze_integrity_audit.md`
- `experiments/core_narrative/reports/external_acut_freeze_report.md`
- `experiments/core_narrative/reports/external_e_phase2_first30_score_summary_report.md`
- `experiments/core_narrative/reports/external_b_pilot_first10_summary_report.md`
- `experiments/core_narrative/reports/external_calibrated_checkpoint_e30_b10_report.md`
- `experiments/core_narrative/results/external_e_primary/external_calibrated_e_phase2_first30_score_summary_20260516.json`
- `experiments/core_narrative/results/external_b_pilot/external_calibrated_b_pilot_first10_summary_20260516.json`
- `experiments/core_narrative/results/external_checkpoint/external_calibrated_checkpoint_e30_b10_20260516.json`
