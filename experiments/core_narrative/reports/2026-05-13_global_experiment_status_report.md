# Barcarolle 实验现状全局报告

日期：2026-05-13  
范围：`experiments/core_narrative/` 核心叙事实验、Click 仓库任务、G/R/W 证据链与下一阶段实验规划

## 摘要

Barcarolle 当前已经从“有核心叙事但缺少可评分结果”的阶段，推进到“能够构造固定分母任务、隔离 ACUT 可见材料、执行 clean replay、保留成本与原始证据、并用预注册 gate 停止负结果”的阶段。这个进展本身重要：项目已经能把模型层级、仓库上下文、任务构造、输出契约、验证器可靠性和政策边界拆开审计，而不是把一次 agent 成功或失败直接解释为能力差异。

但从实证结论看，当前实验尚未支持 NFL-style ranking reversal。早期 Click RBench/RWork 结果显示了“通用排名、仓库基准和 held-out work 之间可能错位”的诊断信号；RGW-full-workspace-v1 显示 RBench 能分离一部分模型层级，但 RWork 没有分离配置，G 轴不可解释；M5-W2 在新的 10 个 held-out Click work 任务上完成了 40 个固定分母 primary cells，却没有发现更强 Click static context 相对 cheap generic 的优势。因此，当前最诚实的全局结论是：Barcarolle 已经建立了能够证伪仓库级 agent 准入直觉的实验框架；当前数据反而证伪了“给 cheap agent 增强 task-agnostic Click 静态上下文就足以产生 held-out W 优势”这一具体假设。

下一阶段不应试图改写 M5-W2，也不应补跑 G 来追求事后 reversal。更合适的路线是冻结 M5 为负结果，先做 no-new-call failure forensics，再把假设从 static context specialist 改成 repository-calibrated configuration：用 RBench 作为校准集生成可审计的 Click repair playbook，并在新的 W3 held-out 任务上预注册检验。

## 研究问题与证据标准

项目的核心问题不是“哪个模型总体最强”，而是：一般 coding-agent benchmark 的高分是否足以证明某个 agent configuration 适合特定仓库的真实维护工作。实验计划把证据拆成三条轴：

| 轴 | 含义 | 当前状态 |
| --- | --- | --- |
| G_score | 通用 benchmark 表现 | 已锁定 SWE-Bench Pro G6 任务与 gold-patch smoke；ACUT G scoring 尚未得到可解释结果 |
| R_score | Click 仓库内 RBench 表现 | 已有多轮 RBench 结果，后期 workspace-mode 下可评分 |
| W_score | Click held-out work 表现 | 已有 RWork-v1 与 RWork-v2，其中 M5-W2 是当前最完整 W-only primary matrix |

支持 NFL-style reversal 至少需要：同一批 ACUT 在 G/R/W 上有可比较分数；G 排名和 R/W 排名出现稳定反转；并且反转不能由任务泄漏、输出契约失败、验证器错误、分母混合或 policy hold 解释。当前证据没有达到这个标准。

## 实验演进

### 1. 设计与目标仓库锁定

初始实验计划明确要求选择一个有确定性本地测试、足够历史任务、可接受构建时间且许可允许本地评测的目标仓库。最终锁定 `pallets/click`，依据包括本地 clone、Python 3.12/uv 环境、安装、smoke tests 和完整非 stress 测试通过。`target_repositories.yaml` 记录了 Click checkout commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`，smoke 结果为 `618 passed`，完整本地非 stress 结果为 `1435 passed, 24 skipped, 30000 deselected, 1 xfailed`。

ACUT 设计采用模型层级与上下文策略的组合：cheap generic、cheap Click specialist、frontier generic、frontier Click specialist；M5-W2 又加入更强的 `cheap-click-deep-specialist-v2`。这些 ACUT 控制了预算、turn cap、test cap、retry policy 和网络策略，把主要实验差异限定在模型层级或 Click-specific task-agnostic context。

### 2. 早期 pilots：先暴露运行与契约问题

5 月 7 日前后的 pilots 001-009 主要结论是：设计、任务包、ACUT manifests、成本 ledger 和规范化结果记录已经存在，但前八个 pilot 没有产生可评分 ACUT capability result。失败集中在 Codex CLI Responses streaming、OpenClaw/direct transport 和 patch 输出契约层面，而不是 verified task outcome。`kickoff_narrative_evidence_memo.md` 明确把这一阶段界定为“rigorous evaluation program with infrastructure blocker”，而非 ranking reversal 证据。

这个阶段建立了一个关键原则：不能把 pre-verifier transport failure 当成模型能力失败，也不能把没有 reach verifier 的结果混入 capability score。这条边界后来贯穿 M1/M2 scoreability 工作和 RGW/M5 的 fixed-denominator 语义。

### 3. 5 月 8 日：首批 Click RBench 可评分结果与诊断性 film

Codex-owned direct runner 取代脆弱控制面后，项目拿到首批 live scoreable Click RBench 结果。最早的 3 任务 x 3 ACUT 矩阵有 9 个 scoreable verifier results：6 pass、3 fail、0 infra_failed；三个 ACUT 都是 2/3。后续补齐 `frontier-click-specialist` 并做 attempt-2 后，baseline plus follow-up 为 24 个 scoreable cells：17 passed、5 failed、2 invalid_submission。

这些结果的价值主要是诊断性，而非统计性。Click 001/002 很快变成 ceiling-like tasks；Click 003 才暴露差异：generic ACUT 漏掉仓库特定 affordance，specialist ACUT 在 `show_choices` API plumbing 上不完整，frontier specialist 两次受 search/replace 输出契约影响。也就是说，box score 看起来相近，但失败原因区分了仓库知识、API plumbing、hidden-test inference 和输出契约可靠性。

同日的 G/R/W predictivity step 7 报告显示：RBench canonical 4 ACUT x 8 的 R_score 与 6 个 RWork 任务的 W_score 可以计算，但 G_score 因 dataset cache 和 evaluator checkout 缺失不可计算。R_score 排名中 `frontier-generic-swe` 最高，W_score 中 `cheap-click-specialist` 相对最好；这只是“Click-only mismatch warning signal”，不是 reversal 证明。

### 4. 5 月 9-10 日：测量稳定化与 scoreability 边界

M1/M1.1/M2 的核心贡献是把“agent 没解对题”和“agent 输出无法评分”分开。M1 发现 anchored search/replace 在选定 RWork smoke 上 invalid-submission rate 为 100%，patch-ready coverage 为 0%。改用 `structured-files-json-v1` 后，M1.1 把 invalid-submission rate 降到 66.7%，patch-ready coverage 提高到 33.3%，相对 anchored baseline 都改善 33.3 个百分点，达到预注册的 25 个百分点阈值。因此 M1.1 支持“structured submission 改善测量稳定性”这一较窄结论。

M2 进一步设置更严格 scoreability gate：patch-ready coverage 至少 70%，invalid-submission rate 不超过 25%，clean replay disagreement 为 0。结果 live `structured-files-json-v1` 和 `patch-or-files-v1` 都失败，只有 no-model synthetic control 通过。这说明 clean replay/verifier path 能评分有效 patch artifact，但 live model-output 层仍不稳定。

Scorecard v0/v1 将已有结果压成 digest-addressed diagnostic artifacts。v1 在 80 个 fixed-denominator entries 上记录：`verified_pass` 26、`verified_fail` 18、`invalid_submission` 35、`infra_failed` 1；attemptability score 为 0.6，verified correctness rate 为 0.590909，fixed-denominator pass rate 为 0.325。它没有声称 reversal，而是把 pass/fail/invalid/infra/missing/policy state 都保留下来。

### 5. workspace-mode：从输出契约转向真实工作区 diff

`workspace_mode_runner.py` 的意义在于改变 ACUT 交付物接口：ACUT 在隔离工作区中自然读写、运行命令，Barcarolle 从最终 workspace state 中提取 patch，再在 fresh verification workspace 中 replay 并注入 hidden verifier。5 月 11 日的 no-model coverage 支持多个关键 failure mode：tracked edit 不需要模型输出 JSON、no diff 独立记录、patch apply error 与 verified fail 区分、hidden verifier 不暴露给 ACUT、untracked source file 可纳入 patch、harness 文件不污染 candidate patch、非零 ACUT exit 不覆盖 fresh verification 成功。

这是后续 RGW v1 和 M5-W2 能够更可信运行的基础。它把 scoreability 瓶颈从“模型是否按 patch JSON 格式回答”转向“模型是否在真实工作区留下可 replay 的候选改动”。

### 6. M3-lite：最低可用研究证据，但故事仍未建立

M3-lite 重置为 research-grade MVE，不把 clean-room replay 作为全部研究 scoreability 的硬门槛。它在 3 ACUT、4 RBench、4 RWork 上形成 partial R/W inspection：三个 ACUT 的 R fixed pass 都为 50%，W fixed pass 都为 25%，G_score 仍不可用。报告明确结论为 `not_established`，即测量准备度推进了，但不能支持 NFL reversal、license、admission 或 G_score predictivity。

### 7. RGW-full-workspace-v1：负/中性基线

RGW-full-workspace-v1 是第一次更接近完整 G/R/W primary 的 workspace-mode 尝试，矩阵包含 4 个 ACUT、8 个 RBench、6 个 RWork 和 6 个 G tasks。结果显示：

| 证据轴 | 主要结果 | 解释 |
| --- | --- | --- |
| RBench | `cheap-generic-swe` 2/8，`cheap-click-specialist` 3/8，`frontier-generic-swe` 5/8，`frontier-click-specialist` 5/8 | RBench 主要分离模型层级，specialist context 的增益不稳定 |
| RWork | 固定分母下四个 ACUT 都是 2/6 | W 轴没有分离配置 |
| G | 24 个 G cells 均为 `verifier_infra_error` | 不能解释为模型失败，也不能当作 zero score |

RGW 的 raw reversal analysis 曾给出“ranking reversal observed”的机械排名描述，但 5 月 13 日 decision note 已将 RGW-full-workspace-v1 冻结为 negative/neutral baseline。原因是 W 分母没有真实分离，G 不可解释，且 RWork 中多项 `unsafe_or_scope_violation` 经 validity audit 后属于 source-derived URL-only policy holds，不能直接混成能力失败。该阶段的正确用途是为 M5 定义更窄问题：更强 Click task-agnostic specialist context 能否在新 held-out W2 上击败 generic SWE。

### 8. M5-W2：当前最完整的 held-out W 结果，也是负结果

M5-W2 构造了新的 RWork-v2 denominator：10 个 admitted primary Click tasks，覆盖 option/default/envvar/flag semantics、CliRunner/testing isolation、prompt/termui rendering、type conversion/parameter normalization 和 mixed integration 五类。每个 primary task 都通过 no-op fails 与 reference patch passes 的 admission smoke。

Primary matrix 是 4 ACUT x 10 tasks，共 40 个 fixed-denominator primary cells，单次 primary attempt，无 best-of-N、无事后分母混合。结果如下：

| ACUT | W2 score | 状态 |
| --- | ---: | --- |
| `cheap-generic-swe` | 5/10 | 5 `verified_pass`，5 `verified_fail` |
| `cheap-click-specialist` | 4/10 | 4 `verified_pass`，5 `verified_fail`，1 `no_diff` |
| `cheap-click-deep-specialist-v2` | 5/10 | 5 `verified_pass`，5 `verified_fail` |
| `frontier-generic-swe` | 4/10 | 4 `verified_pass`，5 `verified_fail`，1 `no_diff` |

预注册 context-effect gate 要求 `cheap-click-deep-specialist-v2` 至少比 `cheap-generic-swe` 多 2 个任务；实际 margin 为 0。deep specialist 相对 cheap generic 是 0 wins、0 losses、10 ties。deep specialist 相对 frontier generic 有 1 win、0 losses、9 ties，但这不能形成 NFL candidate，因为 context-effect gate 已先失败。

G6 gold-patch smoke 后来在 6/6 pinned tasks 上通过，证明的是 evaluator/gold-patch basis 可用；它不是 ACUT G_score，也不能补救 W2 负结果。M5-W2 的结论应保持为：当前 Click static context treatment 没有产生 held-out W 轴优势，不支持 NFL reversal。

## 当前可支持的结论

第一，Barcarolle 的实验系统已经能执行可信的负结果。它能够预注册分母、控制 ACUT 差异、保留 raw/normalized artifacts、区分 capability failure 与 output-contract/infra/policy failure，并在 gate 失败时停止。

第二，仓库级 benchmark 的价值不只在“证明某个 specialist 更强”，也在“防止直觉式准入”。没有这套框架，`cheap-click-deep-specialist-v2` 很容易因 context pack 看起来更强而被误认为更适合 Click；M5-W2 显示该直觉在 10 个 held-out tasks 上没有兑现。

第三，当前静态上下文路线的证据很弱。普通 Click specialist、deep specialist 与 generic SWE 的差异都没有稳定转化为 W2 verified pass 优势。RWork/W2 则更像 floor/ceiling 混合 denominator，缺少足够 separator tasks。

第四，G 轴已完成部分基础准备，但还没有可解释 ACUT G_score。RGW v1 的 G cells 是 verifier infra error；M5 的 G6 是 gold-patch smoke，不是 agent scoring。任何 “G > R/W reversal” 仍然缺关键证据。

## 当前不能支持的结论

当前不能说 Barcarolle 已证明 NFL-style ranking reversal。也不能说 Click specialist 已经优于 generic SWE，或 cheap specialist 已经优于 frontier generic。M5-W2 中 deep specialist 对 frontier generic 的 +1 task 只能作为孤立现象，不足以绕过同层 generic 对照失败。

也不能混合 RGW v1 与 M5-W2 分母。RGW 使用 RBench-v1/RWork-v1/G6，M5-W2 使用新的 RWork-v2，问题设定、政策修复和 ACUT 组合都不同。把它们合并只会产生事后选择偏差。

最后，不应把 invalid submission、policy hold、verifier infra error 简化为模型任务失败。早期 scorecard 已显示这些类别在 fixed denominator 中占比很高；把它们抹平会破坏 Barcarolle 最重要的证据完整性。

## 局限与风险

任务分母仍小。M5-W2 的 10 个 tasks 足以证伪当前 gate，但不足以稳定估计细粒度 ACUT 能力。逐任务模式显示许多任务是全员同过或同挂，separator density 不够。

当前 ACUT 差异仍偏窄。多数配置共享相同工具、预算、网络与运行方式，主要差异是模型层级和静态 context。若真实仓库适配度来自测试优先策略、维护者风格、检索策略或 RBench 校准经验，当前矩阵没有充分覆盖这些差异。

G 轴仍是主要缺口。G6 gold-patch smoke 已证明 evaluator basis，但 ACUT G scoring 未完成。没有 G，项目只能讨论 R/W mismatch 或 repository-specific held-out evidence，不能完整讨论 general benchmark ranking reversal。

另外，未来如果使用 RBench-derived playbook 进行校准，必须重新定义 leakage boundary。RBench 可以作为 calibration set，但 W3 必须 held-out，且不能把 W3 target commits、reference patches、hidden verifiers、final diffs 或 ACUT outputs 用于校准。

## 未来工作

下一阶段应明确从“挽救 M5”改为“启动新的预注册假设”。建议分四步。

第一，冻结 M5-W2 decision note。M5 primary scores 不修改，不补跑 ACUT G 来制造 reversal，不把 RGW v1 和 M5-W2 合并。结论写成：static Click context treatment 在当前 W2 denominator 上没有击败 cheap generic，M6 是新假设而不是 M5 salvage。

第二，做 no-new-call failure forensics。输出 `task_separation_matrix`、`treatment_delivery_audit` 和 `near_miss_blind_review`。需要回答四个问题：deep context 是否真实进入 prompt 且未被截断；W2 是否主要由 floor/ceiling tasks 构成；deep specialist 在失败任务上是否比 generic 更接近 reference；失败是否集中在 prompt/termui、Choice normalization、CliRunner isolation 等 task family。这个阶段不改变 primary score，只解释失败结构。

第三，设计 `cheap-click-rbench-calibrated-v1`。它应与 `cheap-generic-swe` 保持同模型层级、同预算、同工具、同网络策略，但允许使用 RBench-derived repair playbook。playbook 可以包含 RBench task family taxonomy、抽象修复模式、Click 常见 bug-fix locations、maintainer-style regression test patterns、常见失败原因与 debug checklist。禁止使用 W3 target commits、W3 reference patches、W3 hidden verifiers、W3 final diffs，以及任何 W3 ACUT outputs。

第四，构造 W3 held-out experiment。建议 16-20 个新 Click tasks，且与 RBench、RWork-v1、W2 anchors disjoint；no-op 必须 fail，reference patch 必须 pass；每个 family 至少 3 个任务，避免全部是大型 feature addition 或全部是单行 bugfix。预注册 gates 可设为：calibrated specialist 比 cheap generic 至少多 4/20；calibrated specialist 优于 static deep specialist；若还优于 frontier generic，才进入 NFL candidate status。

只有 W3 gate 通过后，才值得运行 R3 和 critical-pair G。critical pair 应至少包括 `frontier-generic-swe` 与 `cheap-click-rbench-calibrated-v1`。只有同时出现 frontier generic 在 G 上更强，而 calibrated specialist 在 R 和 W 上更强，才可写成 weak NFL-style support。

一个替代或并行方向是扩大 ACUT 多样性，而不是继续扩写 static context pack。更贴近 Barcarolle 产品价值的问题是：RBench 能否比 G 更好地选择适合某个仓库的 agent configuration。因此可以加入 test-first agent、patch-minimalist agent、maintainer-style agent、high-budget generic agent、retrieval-heavy repo agent 等真正不同的配置，再比较 `rank_correlation(R, W)` 与 `rank_correlation(G, W)`，以及 `selected_by_R` 的 W_score 是否优于 `selected_by_G`。

## 写作与证据说明

本报告基于仓库内已生成的实验计划、报告、配置和 JSON 结果工件撰写，并参考 2026-05-13 的未来工作备忘。报告没有重算 hidden verifier、没有新增模型调用，也没有修改任何 primary score。所有数值均来自既有工件；对未来路线的判断属于基于这些工件的研究设计建议，而非已完成实验结论。
