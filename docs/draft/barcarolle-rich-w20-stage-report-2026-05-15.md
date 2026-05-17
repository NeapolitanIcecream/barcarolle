# Barcarolle 阶段性实验报告：Repository-Local Rich-W20 Reduced Primary

生成日期：2026-05-15

报告性质：阶段性实验结果报告

当前结论：reduced-scale repository-local decision-validity pilot 已完成；预注册成功门槛未通过；不支持将 0514 冻结线改写为完整 benchmark generation 成功，也不支持当前阶段给出 NFL-style ranking reversal 结论。

## 摘要

本报告汇总 Barcarolle core narrative 在 2026-05-14 至 2026-05-15 的当前阶段结果。0514 冻结的 repository-local Rich benchmark 线在 primary run 之前终止：W* 达到 20 个 primary task floor，但未达到 5 个 reserve 与 40 个 candidate pool 目标，因此不能在原协议下启动 R、W* 或 G primary attempts。随后，项目以新的预注册 revision 建立 `repository-local-rich-w20-v1` reduced protocol：保留 20 个 R primary tasks、20 个 W* primary tasks、4 个 cheap-tier ACUT，并取消 W* reserve 与 40-pool 要求，仅用于检验缩小规模下的 repository-local decision validity。

`repository-local-rich-w20-v1` primary run 已完整完成。共 160 个 normalized results，R 轴 80/80 cells 完成，W* 轴 80/80 cells 完成；无 missing cells，无 rerun/exclusion cells，无 triage-paused cells。结果显示，R 轴选择 generic baseline A0（`cheap-generic-swe`），W* 轴最佳为 inert control A1（`cheap-rich-inert-control-v1`），selection regret 为 1 个 W* task。这个近邻选择结果满足“R-selected within W* best 1 或 2 tasks”的弱门槛，但两个主要改进门槛失败：A4 localization tool 对 A0 的 W* 增益为 0，低于要求的 +4 tasks；R-selected 对 A0 的 W* 增益也为 0，低于要求的 +3 tasks。

因此，当前阶段最稳妥的读法是：Barcarolle 已证明自己能够完成一次仓库本地、固定分母、clean replay、hidden verifier 的 reduced primary run，并能在结果不利时停止和报告负结果；但当前 Rich-W20 结果没有证明 repository-calibrated 或 localization-heavy ACUT 在 held-out W* 上优于 generic baseline。

## 读者问题与判读标准

本报告回答的问题不是“哪个 ACUT 以后一定最好”，而是：在 0514 冻结线失败后，新预注册的 reduced Rich-W20 是否提供足够证据，说明 repository-local R 轴能选择出更适合 W* held-out work 的 ACUT？

判读标准有四条。第一，0514 terminal block 不能被事后改写；reduced protocol 是一个新 revision，只能支持 reduced-scale claim。第二，primary score 与 post-run audit 必须分开；本报告使用固定分母 primary score，不把失败类型解释回填为 pass。第三，R、W* 和未来 G 的分母不能混合；Rich-W20 也不能与 M5/M6 Click 结果合并统计。第四，成功门槛以 `repository-local-rich-w20-v1` 预注册 protocol 为准，而不是根据结果重新设定。

## 协议边界

0514 原协议的终止原因是 W* supply gate 未通过。已接受 W* primary candidates 为 20，达到 target primary count；但 target primary + reserve count 为 25，在当前 scan 下最大可能 W* admissions 为 23，仍差 2 个 reserve；candidate-pool gap 为 17。因此，原协议 primary runs authorized 为 false。

0515 reduced protocol 的边界是明确的。它继承 Rich 仓库任务构造与 ACUT manifest，但声明不满足原 0514 reserve gate，也不满足原 40-candidate-pool gate。它允许的 claim 只有 reduced-scale repository-local decision-validity pilot；不允许声称 full benchmark generation robustness、original 0514 protocol success，或没有完整 G/R/W 证据的 no-free-lunch support。

## 实验材料与方法

Rich-W20 使用两个 20-task primary denominator：

| Split | Primary tasks | Reserve policy | 说明 |
| --- | ---: | --- | --- |
| R | 20 | 保留 5 个 accepted reserve tasks，但只能在 primary scoring 前按规则替换 | 用于 repository-specific selection signal |
| W* | 20 | reserve_required 为 false | 用于 held-out work performance judgment |

四个 ACUT 均使用 frozen cheap route `gpt-5.4-mini`，差异主要来自上下文与工具策略：

| Slot | ACUT | 角色 |
| --- | --- | --- |
| A0 | `cheap-generic-swe` | generic baseline |
| A1 | `cheap-rich-inert-control-v1` | same-token inert control |
| A3 | `cheap-rich-c-calibrated-v1` | C-derived repository-calibrated playbook |
| A4 | `cheap-rich-localization-tool-v1` | code-understanding localization tool |

所有 primary cells 遵守一次 attempt、非 best-of-N、fresh workspace replay、hidden verifier、fixed-denominator status mapping。预检查要求所有 primary tasks 满足 no-op fail、reference pass、hidden verifier digest recorded、public statement digest recorded、leakage reviewed。route probe 显示 Barcarolle Responses transport 对 `gpt-5.4-mini` 不可用，但用户 authenticated default Codex provider 可服务同一 frozen model route；因此 primary run 使用 `--codex-provider-mode default`。

## Primary completion

Rich-W20 primary 于 2026-05-15 完成：

| 项目 | 结果 |
| --- | ---: |
| Expected primary attempts | 160 |
| Normalized results | 160 |
| R present cells | 80 / 80 |
| W* present cells | 80 / 80 |
| Missing cells | 0 |
| Rerun/exclusion cells | 0 |
| Triage-paused cells | 0 |

运行过程曾在 130/160 cells 处按 operator request 暂停，暂停时 W* 已完成 80/80，R 完成 50/80；之后按 runner skip-existing 语义恢复并补齐 R 轴剩余 30 cells。最终 `summary.json` 与 `analysis.json` 均记录 `primary_complete`。

## Primary scores

固定分母 primary score 如下：

| Slot | ACUT | R pass / 20 | R score | W* pass / 20 | W* score |
| --- | --- | ---: | ---: | ---: | ---: |
| A0 | `cheap-generic-swe` | 5 | 25.0% | 8 | 40.0% |
| A1 | `cheap-rich-inert-control-v1` | 2 | 10.0% | 9 | 45.0% |
| A3 | `cheap-rich-c-calibrated-v1` | 3 | 15.0% | 6 | 30.0% |
| A4 | `cheap-rich-localization-tool-v1` | 2 | 10.0% | 8 | 40.0% |

R 轴选择 A0，因为 A0 的 R score 最高。W* 轴最佳为 A1，9/20，领先 A0 与 A4 各 1 个 task。A3 在 R 和 W* 上均未超过 A0。A4 在 W* 上与 A0 同为 8/20，没有表现出 localization tool 带来的 held-out gain。

## Success criteria

预注册成功门槛的结果如下：

| Criterion | Required | Observed | Result |
| --- | ---: | ---: | --- |
| A4 vs A0 on W* | at least +4 tasks | 0 | failed |
| R-selected vs A0 on W* | at least +3 tasks | 0 | failed |
| R-selected within W* best | within 1 or 2 tasks | 1 | passed |
| Inert control guard | A1 not selected unless W* supports it | A0 selected | passed |

这个组合不能解释为正结果。最重要的两个 intervention-effect gates 均失败；“R-selected within W* best”只能说明 R 轴没有选到远离 W* best 的配置，不能说明 R 轴选择相对 generic baseline 产生了实质 W* 改进。

## 状态分布与任务分离度

按 split 的状态分布如下：

| Split | verified_pass | verified_fail | unsafe_or_scope_violation |
| --- | ---: | ---: | ---: |
| R | 12 | 66 | 2 |
| W* | 31 | 40 | 9 |

R 轴整体更像 hard/floor-heavy denominator。20 个 R tasks 中，15 个 task 对四个 ACUT 都没有 pass，2 个 task 对四个 ACUT 全部 pass，只有 3 个 task 产生部分区分。W* 的分离度更高一些：20 个 W* tasks 中，9 个 task 为 0 pass，4 个 task 为 4 pass，7 个 task 产生部分区分。这个结构提示，当前 reduced denominator 可完成、可评分，但仍包含较多 floor/ceiling tasks；它对精细 ACUT 差异的统计解释力有限。

Unsafe/scope-violation 在固定分母下计为 0。R 轴有 2 个 unsafe/scope cells；W* 轴有 9 个 unsafe/scope cells。当前报告不把这些结果从 denominator 中剔除，也不把它们改写为 infrastructure exclusion，因为 primary analysis 未记录 rerun/exclusion 或 triage-paused cells。

## 解释

第一，当前结果削弱了“更多 Rich-specific intervention 会自动改善 W*”的假设。A3 使用 C-derived repository-calibrated playbook，但 W* 只有 6/20，低于 A0 的 8/20。A4 使用 localization tool，但 W* 与 A0 持平，未达到 +4 tasks 门槛。

第二，R 轴在这次 reduced protocol 中没有提供可用的 winner-selection advantage。R 选择 A0，而 A0 在 W* 上不是最佳；虽然它只落后 W* best A1 一个 task，但它相对自身 baseline 没有任何增益，因为它本身就是 baseline。预注册的 `r_selected_vs_A0_w_star_min_delta_tasks` 因此必然观察为 0。

第三，A1 inert control 成为 W* best 是一个需要谨慎解释的信号。协议的 inert control guard 没有触发，因为 R 没有选择 A1；但 W* 上 A1 以 9/20 领先 1 个 task，说明 held-out denominator 对“真实 repository-useful context”和“同 token 惰性 control”的区分仍不够稳健。这个结果更适合被视为 validity warning，而不是 A1 有实质仓库能力优势。

第四，当前阶段的主要正向成果是评测管线，而不是 agent ranking。项目已经完成从 task admission、route probe、pause/resume、workspace-mode primary、normalized summary 到 success-criteria analysis 的闭环；这对 Barcarolle 的治理叙事有价值，因为它能防止在结果不符合预期时继续追求事后胜利故事。

## 不能支持的结论

本阶段不能支持以下说法：

1. 不能说 0514 原 repository-local Rich benchmark 成功。原协议已在 primary run 前因 W* reserve 与 pool gate 失败而终止。
2. 不能说 Rich-specific calibrated playbook 或 localization tool 已优于 generic baseline。A3 与 A4 均未超过 A0 的 W* score。
3. 不能说 R 轴已经证明能选择出 W* 上明显更好的 ACUT。R-selected A0 在 W* 上没有超过 A0 baseline，也不是 W* best。
4. 不能说 Barcarolle 已证明 NFL-style ranking reversal。当前 reduced protocol 没有完成 G/R/W 的完整 reversal evidence。
5. 不能把 Rich-W20 与早期 Click M5/M6 或 RGW v1 分母合并，制造跨实验 aggregate advantage。

## 有效性威胁

第一，reduced protocol 是一次有边界的 revision。取消 W* reserve 与 candidate-pool gate 让 primary run 可执行，但也降低了 benchmark-generation robustness claim 的强度。

第二，样本量仍小。每个 split 只有 20 个 tasks，每个 ACUT/task cell 只有一次 attempt，没有置信区间，也没有多 attempt 方差估计。

第三，任务分离度不足。R 轴 floor-heavy，W* 轴仍有较多 zero-pass 与 all-pass tasks；这会压低 rank-selection analysis 的分辨率。

第四，ACUT 差异主要集中在上下文与工具层面，且全部使用同一 cheap model route。结果不能推广到高预算、多轮、test-first、retrieval-heavy 或 frontier-model 配置。

第五，unsafe/scope categories 的含义需要后续审计。当前 fixed-denominator primary score 正确地把它们计为 0，但这并不回答其中哪些属于模型行为失败、政策 hold、任务表述诱导，或 verifier/scoping 设计问题。

第六，当前没有 ACUT G scoring。通用 benchmark 与 repository-local work 的排序关系仍未闭合，因此任何 no-free-lunch 或 ranking reversal 论证都只能作为未来工作目标，而不是当前结论。

## 隐私、复现与研究伦理

本报告只使用仓库内公开/可发布的 aggregate artifacts 与 digest-level evidence。报告不公开 raw commits、raw subjects、reference patch bodies、hidden verifier source、credential values、endpoint values、private raw run directories 或本地绝对路径。

AI 辅助用于整理已有实验 artifacts、核对表格数值、组织中文报告结构和生成网页版本。报告没有新增 ACUT model calls，没有修改 primary score，没有重跑 hidden verifier，也没有把 post-run interpretation 回填为 primary evidence。

## 结论

`repository-local-rich-w20-v1` 是一个完整但负向的 reduced-scale primary result。它证明 Barcarolle 当前能够执行固定分母、仓库本地、clean replay、hidden verifier 的 primary matrix，并能把结果转化为预注册 success-criteria analysis。但它没有证明 repository-calibrated intervention 或 localization intervention 在 Rich held-out W* tasks 上优于 generic baseline。

下一步应保持 0514 原协议为 terminal blocked，保持 0515 Rich-W20 为 reduced negative/mixed result。更合理的后续工作不是事后调整 Rich-W20 门槛，而是复盘任务分离度、unsafe/scope 分类、ACUT 差异设计，并在新的预注册协议下决定是否扩展到更强 ACUT、多样化工具策略或完整 G/R/W critical pair。

## 主要证据工件

- `experiments/core_narrative/configs/repository_local_rich_w20_v1.yaml`
- `experiments/core_narrative/results/repository_local_rich_w20_protocol_readiness_20260515.json`
- `experiments/core_narrative/results/repository_local_rich_w20_route_probe_20260515.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/summary.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/analysis.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/rw_table.json`
- `experiments/core_narrative/results/repository_local_rich_w20_v1/runner_execution_diagnostics.json`
- `experiments/core_narrative/reports/2026-05-15_repository_local_benchmark_final_blocked_report.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_protocol_readiness.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_route_unblocked.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_pause_checkpoint.md`
- `experiments/core_narrative/reports/2026-05-15_repository_local_rich_w20_primary_results.md`
