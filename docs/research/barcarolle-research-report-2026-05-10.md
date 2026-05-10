# Barcarolle 仓库级 Agent 准入研究报告

日期：2026-05-10
状态：研究报告草案
对象：Barcarolle 项目决策者、评测系统开发者、代码智能体平台团队、仓库维护者

## 摘要

Barcarolle 面向一个正在变得实际而尖锐的问题：当代码智能体已经能够在真实仓库里读代码、改代码、跑测试、开分支和提交 PR 时，通用排行榜并不能回答仓库所有者真正关心的问题：**这个具体 agent 配置，是否适合在这个具体仓库、这个权限范围和这个风险偏好下工作？**

本项目的核心判断是，代码智能体的可用性不是单个模型的属性，而是 `ACUT`（Agent Configuration Under Test）的属性：模型、提示词、工具、权限、检索/记忆策略、运行预算、控制循环、运行环境和适配器边界共同决定结果。现有公开 benchmark 已经证明了仓库级、执行式评测的重要性，但它们大多仍服务于跨模型比较或公开排行榜，尚未形成“给定一个仓库，生成可回放、可审计、可分级的准入证据”的完整系统。

Barcarolle 的解决方案是把仓库历史、Issue/PR、测试、CI、工程规范和风险偏好转化为仓库级 benchmark release，再用干净的 canonical verification、scorecard、风险策略和授权语义生成仓库范围的 admission/license 记录。它不是运行时拦截器，也不是通用模型认证；它是一套证据化的仓库准入与治理机制。

实验进展必须诚实表述：截至 2026-05-10，项目已经形成清晰的系统设计、核心叙事实验方案、ACUT 矩阵、任务/结果/成本记录、若干 runner/verifier/scoreability 工具和可审计报告；但核心实证主张，即 `R_score` 比 `G_score` 更能预测 `W_score`，以及 NFL 式排名反转，尚未被证明。近期 M1.1 只支持“提交契约使测量稳定性提升”的有限结论；M2 在固定网格补齐后仍未通过 live scoreability gate。当前阻塞不应被包装成 agent 能力结果，而应被视为输出契约、适配器和可计分路径尚不稳定的测量基础设施问题。

## 1. 研究问题与主张

本报告研究的问题是：

> 我们正在研究仓库级代码智能体准入机制，因为通用代码 benchmark 和模型榜单不足以说明某个完整 agent 配置能否在某个真实仓库中可信协作，所以仓库所有者需要一种可回放、可审计、可分级的证据链来决定 agent 的可用范围与权限等级。

报告的主张可以拆成四个层次：

1. **问题背景**：AI 编码工具已经从补全和聊天进入异步 agent、PR、CI、权限和审计流，评测问题因此从“模型会不会写代码”转向“系统能否在工程流程中可信工作”。
2. **业界洞察**：公开 benchmark 正在向仓库级、执行式、长任务、抗污染、动态更新发展，但静态公开榜单仍存在污染、弱 oracle、运行环境和 agent scaffold 不可比的问题。
3. **解决方案**：Barcarolle 将评测对象定义为 ACUT，并把任务生成、环境回放、benchmark admission、canonical verification、scorecard、风险策略、授权语义和当前运行状态分离，形成可追责的仓库准入系统。
4. **实验现状**：目前已有实验框架和若干测量稳定性证据，但没有足够 live scoreable 结果支持排名反转、能力提升、G/R/W predictivity、G0-G5 admission 或 license claim。

## 2. 问题背景

### 2.1 代码智能体正在进入真实研发流程

2025 年以后，代码智能体的使用场景明显从 IDE 内的同步辅助扩展到异步协作。GitHub 在 2025 年 5 月发布 Copilot coding agent，强调它可以在 GitHub/VS Code 中接收 issue、启动开发环境、提交 draft PR、留下 session logs，并在 PR review 中迭代；GitHub 也把 branch protection、受控网络访问、CI 触发审批等机制纳入 agent 工作流。GitHub 后续的 Agent HQ 叙事进一步把第三方 coding agents 纳入同一个 GitHub flow，使 agent 不再只是编辑器里的助手，而是 issue、branch、PR、CI 和权限体系中的参与者。

这带来一个治理问题：当 agent 只补全一行代码时，用户可以把责任放在人的局部审查上；当 agent 可以独立工作数十分钟、改动多文件、触发测试并开 PR 时，组织需要知道它是否适合当前仓库、当前模块、当前任务类型和当前权限范围。GitHub 对 Copilot cloud agent 的官方文档也把任务能力描述为研究仓库、制定实现计划、修 bug、实现增量功能、改进测试覆盖、更新文档和处理技术债。这些能力都不是单点代码生成问题，而是工作流问题。

开发者使用 AI 工具的规模也在扩大。Stack Overflow 2025 Developer Survey 收到 49,000 多份回复，并加入 AI agent tools、LLM 和社区平台相关问题；GitHub Octoverse 2024 报告显示开源受访者中已有大量用户把 AI 工具用于编码或文档工作。无论具体比例如何解释，行业方向已经明确：AI 编码工具正在成为开发栈的一部分，而不是偶发实验。

### 2.2 通用 benchmark 与仓库准入之间存在缺口

SWE-bench 一类 benchmark 的贡献很大：它把真实 GitHub issue、PR、仓库状态和隐藏测试结合起来，使“在仓库里解决真实问题”成为可执行评测对象。后续 SWE-bench Verified、SWE-Bench Pro、SWE-PolyBench、多语言和长任务 benchmark 继续推动这个方向。

但 Barcarolle 关心的问题比排行榜更窄也更难。公开 benchmark 能回答“某系统在这组公共任务上的平均表现如何”，却很难回答：

- 这个 agent 配置在我这个仓库的历史任务、测试结构、模块边界和工程规范下表现如何？
- 它适合读、提 patch、开分支、广泛改动，还是只适合某个模块/任务族？
- 它的结果是否来自真实能力，而不是 benchmark 记忆、未来提交泄漏、弱测试或 runner 偶然性？
- 当模型、提示、工具、权限、检索策略、预算或适配器变了，原来的评测证据还能否沿用？

OpenAI 2026 年对 SWE-bench Verified 的公开分析说明，静态公开 benchmark 会在前沿能力阶段快速暴露局限：被训练数据污染、测试过窄或过宽、任务描述不足、环境差异导致误判等。SWE-Bench Pro 也把抗污染、长任务和企业级问题作为设计重点。这些趋势支持 Barcarolle 的基本判断：仓库级 agent 准入不能只依赖通用排行榜。

### 2.3 评测对象是完整配置，不只是模型

项目内部研究材料已经把这一点作为底层事实：一旦评测允许仓库导航、文件编辑、测试执行、检索、迭代修复或长程规划，结果就是完整 agent 配置的结果，而不是单个模型的结果。SWE-agent 论文也把 Agent-Computer Interface 作为核心研究对象，其配置包含 prompt templates、command files、control flow 和 environment variables 等组件。GitHub Copilot coding agent、OpenHands、Aider、Claude Code、Cursor 等工程系统也都把工具、权限、运行环境、日志和工作流作为产品能力的一部分。

因此，一个仓库所有者真正需要评估的是：

```text
ACUT = 模型 + 提示/规则 + 工具接口 + 权限 + 检索/记忆 + 预算 + 控制循环 + 运行环境 + 适配器边界
```

同一个模型在不同 scaffold 下可能表现不同；同一个 agent 在不同仓库、语言、测试质量、依赖环境和任务族中也可能表现不同。Barcarolle 将 ACUT 作为不可变 tested-agent snapshot 记录，是为了避免把一个历史 benchmark 事实错误地推广到已经变化的 agent。

## 3. 业界洞察

### 3.1 行业正在从“AI 编码助手”转向“受治理的 agent 工作流”

GitHub 的官方材料显示，agent 工作流正被嵌入现有工程协作原语：issue、branch、commit、draft PR、review、Actions、branch protection、网络访问控制和 agent session logs。Agent HQ 进一步把多家供应商的 coding agents 纳入统一入口。这个方向说明企业采用 agent 的关键不只是生成质量，而是可控性、可追踪性、权限边界和可审计证据。

Barcarolle 对应的产品机会在这里：主流平台提供 agent 运行和协作入口，但仓库所有者仍需要一种独立证据来判断“哪个 agent 配置可以在哪个仓库范围内做到什么程度”。这不是替代 GitHub/Codex/CI 的 runtime guard，而是为它们提供可消费的准入证据。

### 3.2 Benchmark 正在变难、变新、变执行化，但仍不足以承担仓库准入

SWE-Bench Pro 包含来自 41 个活跃维护仓库的 1,865 个问题，并强调长程任务、小时到天级别的人类工作量、多文件修改和抗污染测试床。SWE-PolyBench 扩展到 Java、JavaScript、TypeScript 和 Python，显示不同语言、任务类型和复杂度会造成表现差异。类似趋势说明，行业已经意识到 Python-only、短任务、静态公共集不足以反映真实软件工程。

但这些 benchmark 的目标仍主要是建立共享评测基准，不是为任意单仓库生成 admission artifact。Barcarolle 与它们的关系应当是“吸收方法论，而不是直接替代问题”：历史任务、执行环境、hidden oracle、任务质量门禁、动态更新和抗污染设计都应借鉴；但最终输出要从 leaderboard score 转向 repository-scoped scorecard 与 admission decision。

### 3.3 静态公开 benchmark 的信号会退化

OpenAI 对 SWE-bench Verified 的分析指出，该 benchmark 曾是行业标准，但在前沿模型阶段已经受到测试缺陷和训练暴露影响。其核心启示不是“不要做 benchmark”，而是：高价值 benchmark 必须维护时间边界、污染扫描、oracle 质量、任务退休和动态更新。对于从真实仓库历史中生成任务的 Barcarolle，这个问题更明显：仓库历史既是任务来源，也是泄漏来源。未来提交、PR 描述、review 讨论、CI 日志、外部链接和 issue 文本都可能把答案暴露给 ACUT。

因此，Barcarolle 的 benchmark admission rubric 必须保守：固定 `T_task`，划分 agent-visible 与 verifier-only 材料，扫描 future/answer leakage，验证 canonical solution、no-op 和 known-bad patch，记录 oracle grade，并在发现污染后 quarantine/retire 任务。

### 3.4 “更多上下文”不是单调收益

业界常见直觉是给 agent 更多仓库上下文、更多规则、更多历史就会更好。但现有研究和项目材料都提示这不是单调关系。上下文选择、检索质量、任务相关性、规则长度和工具接口都会改变结果；错误或过多上下文可能增加成本、干扰定位，甚至降低成功率。因此 Barcarolle 不应把 repository context 视为免费的增强项，而应把检索/记忆策略作为 ACUT 的组成部分，并在同一仓库、同一 task release 上比较。

这也是核心实验设计中 “generic SWE” 与 “Click-specialist context” 的意义：它试图验证 repository-specialist context 是否在仓库工作上比通用配置更有预测力或更有效。不过截至目前，实验尚未产生足够可计分 live evidence 来证明这一点。

## 4. Barcarolle 的解决方案

### 4.1 系统定位

Barcarolle 是一个仓库特定、验证优先、证据感知的代码 agent 准入系统。它的对象不是训练模型，也不是替代 CI、agent runner 或代码平台，而是把一个仓库及其历史转化为可回放 benchmark 证据，并把这些证据解释成仓库范围的 admission/license 记录。

项目 README 和系统设计已经明确边界：

- Barcarolle 评估完整 ACUT，而不是只评估 base model。
- Barcarolle 不是 runtime enforcement plane；License 是证据支持的仓库准入记录，不是每一步行动的守卫。
- 默认 operating assumption 是 trusted internal collaboration：仓库所有者和 ACUT 所有者目标一致，系统先服务内部治理与比较，不声称具备对抗式认证能力。
- `G5` 是 fully trusted YOLO tier，但仍只在记录的仓库范围、target condition、能力 envelope、时间窗口和风险策略内有效。

### 4.2 核心证据链

Barcarolle 的主流程可以概括为：

```text
仓库历史与风险画像
  -> 信号抽取
  -> candidate task mining
  -> replay planning / environment reconstruction
  -> validation + benchmark admission
  -> immutable benchmark release
  -> runner integration
  -> run submission
  -> evidence ingestion
  -> clean-room canonical verification
  -> per-run scoring / Judge assessment
  -> benchmark scorecard
  -> policy calibration under risk profile
  -> authorization decision
  -> repository-agent admission / operating state
```

这个拆分的关键不是架构复杂度，而是避免把不同性质的事实混在一起：

- **benchmark fact**：在某个 benchmark release 上，某个 tested-agent snapshot 发生了什么。
- **score fact**：canonical verification、score bundle 和 scorecard 如何计算。
- **policy fact**：在某个 authorization policy 和 risk profile 下，scorecard 被如何解释。
- **admission fact**：仓库侧授予了什么准入或 License。
- **operating state**：当前仓库实际运行的是哪个 snapshot，是否仍被有效 admission 覆盖。

一旦这些对象被合并，系统就无法解释“结果差是 agent 差、任务 oracle 差、环境坏、证据不足、还是授权策略太宽”。

### 4.3 Benchmark admission：先保证任务可信，再讨论 agent 强弱

Barcarolle 的 benchmark admission rubric 把候选任务进入 release 前的质量门槛写成可执行规则。合格任务至少需要：

- 有可审计的 provenance 和固定 `T_task`；
- agent-visible 输入不含未来信息或直接答案；
- replay environment 能 faithful materialize；
- 任务边界、允许/禁止输入、期望产物和权限需求明确；
- oracle 至少为 A/B 级，且通过 canonical solution、no-op、known-bad、flakiness、runtime 和 oracle-log leakage probes；
- 重复/相似任务不会在 release 中过度加权；
- 高风险路径、权限类别和组件覆盖在 release coverage profile 中显式可见。

这套机制的意义是：Barcarolle 不把“从历史里挖到一个任务”直接等同于“这个任务能支持准入决策”。任务本身也要被评测。

### 4.4 Scoring：正确性根植于干净验证，agent 提交的轨迹只能辅助解释

Scoring semantics 把 per-run outcome 分成 `verified_pass`、`verified_fail`、`agent_timeout`、`malformed_or_empty_submission`、`infra_failed`、`verifier_flaky_unresolved` 等类别。正向 correctness 必须来自 `canonical_verification_record` 和可信 Barcarolle evidence；agent 自己提交的 trace、self-run tests、native logs 可以帮助解释过程、风险和置信度，但不能独自生成正向 correctness。

这与近期实验中的教训一致：许多 run 失败在 pre-verifier、patch application、invalid submission 或 unsafe generated text 阶段。把这些结果粗暴算作“agent 不会做任务”会污染能力结论；把它们忽略又会高估可用性。Barcarolle 的 scorecard 需要同时保留 scoreable zero、missing coverage、infra failure 和 invalid submission。

### 4.5 Authorization：从分数到权限必须经过风险与适用性门禁

Authorization semantics 定义了 `G0` 到 `G5` 的准入层级，并规定分数只是输入之一。授权还要检查：

- correctness evidence 是否足够；
- evaluated subject 是否与要准入的 subject 相同或等价；
- ACUT binding/attestation 是否可信；
- License consumption contract 是否能让下游消费者判断适用范围；
- repository risk profile 是否允许该 tier、scope 和权限类别。

因此，即使某个 ACUT 在 benchmark release 上得分高，也不能自动获得广泛权限。相反，授权范围必须是 release 支持范围、scorecard 覆盖范围、target condition 和风险偏好的交集。

### 4.6 Golden/Judge 的角色：增强证据，不替代确定性门禁

系统设计中包含 Golden Agent 与 Judge Agent，但它们不是最终权威：

- Golden 在 candidate discovery、参考 artifact、oracle 分析和验证支持中提供帮助。
- Judge 在 sealed run evidence、风险解释、过程质量和语义疑点上提供辅助。
- deterministic validation、canonical verification、scoring policy 和 authorization policy 仍是最终门禁。

这避免了“用一个 LLM 来给另一个 LLM 发驾照”的循环论证。LLM 可以帮助发现和解释，但核心 correctness 与准入决策必须落在可审计证据链上。

## 5. 实验进展

### 5.1 核心实验假设

`docs/experiments/core-narrative-experiment-plan.md` 给出的核心叙事是：

> 通用 coding-agent benchmark rank 不足以证明 agent configuration 在特定仓库中的工作质量。仓库特定 benchmark 应该更好预测该仓库中的实际工作质量。

实验计划把每个 ACUT 的结果拆成三类：

- `G_score`：通用 benchmark 表现；
- `R_score`：仓库特定 benchmark 表现；
- `W_score`：同仓库 held-out actual work 表现。

理想证据是 NFL 式排名反转：A 在通用 benchmark 高于 B，但在 repository-specific benchmark 和 held-out work 上低于 B。这个设计是合理的，因为它把“通用能力”和“仓库适配能力”拆开了。

### 5.2 已经完成的工程和证据基础

截至 2026-05-10，实验线已经产出：

- 核心叙事实验方案、预算契约、ACUT manifest、目标仓库配置和任务配置；
- Click 相关 RBench/RWork 任务切片与若干 canonical matrix；
- runner/verifier/adapter 脚本、output contract、成本 ledger 和 normalized result；
- scoreability summary、fixed-grid gate assessment、unsafe artifact triage、nonpersistent verifier channel 等可审计报告；
- 成本记录 164 条，累计 estimated cost 为 USD `38.217436`，低于 USD `240` soft stop 和 USD `300` hard cap。

这些产物说明项目已经从纯概念进入可运行的测量基础设施阶段。

### 5.3 已支持的有限结论

M1.1 measurement stabilization 支持一个有限结论：在固定 2 ACUT x 3 RWork smoke 上，`structured-files-json-v1` 相比 anchored baseline 改善了测量稳定性。具体表现为：

- invalid-submission rate 从 `1.000000` 降到 `0.666667`，改善 33.3333 个百分点；
- patch-ready coverage 从 `0.000000` 升到 `0.333333`，改善 33.3333 个百分点；
- 6/6 canonical scoreable coverage，0 个 infra_failed；
- 但没有任何 cell 通过任务 verifier，两个 patch-ready cell 只是到达 clean replay 和 verifier execution 后失败。

这只能说明提交契约和适配器路径在小样本上更可测，不能说明任务解决能力提升。

### 5.4 未支持的核心结论

M2 scoreability stabilization 没有通过 live gate。固定 2 x 3 smoke 上：

- `patch_or_files_v1_live`：6 个 live cells 中 5 个 `invalid_submission`，1 个 `infra_failed`，patch-ready 为 0；
- `structured_files_json_v1_live`：patch-ready 为 0.333333，invalid rate 为 0.666667；
- no-model `patch_or_files_v1` control 通过 gate，说明 replay/verifier 管道在模型输出层移除后可处理 patch-ready artifact。

2026-05-10 的 fixed-grid gate assessment 在 raw input gaps 关闭后仍判定：

- coverage/raw-input/no-raw policy gate：passed；
- M2 scoreability gate：failed；
- `patch_or_files_v1_live_after_gap_closure`：attemptability 0.0%，model invalid 100.0%；
- `anchored_search_replace_fixed_grid`：attemptability 33.3%，model invalid 66.7%；
- hard blocker：`live_model_output_scoreability_thresholds_not_met_after_fixed_grid_gap_closure`；
- 未识别出单个安全、代码可直接修复、且无需新批准模型调用的下一实验。

因此，当前不能声称：

- 已证明 ranking reversal；
- `R_score` 比 `G_score` 更能预测 `W_score`；
- Click-specialist ACUT 优于或劣于 generic ACUT；
- frontier/cheap 模型在仓库任务上有可靠排序；
- 已产生 G0-G5 admission、license 或 authorization outcome；
- agent 能力已经被 Barcarolle 可靠评估。

### 5.5 实验教训

现阶段最重要的实验证据不是“谁更会写代码”，而是“可计分路径本身很难”。主要教训包括：

1. **输出契约是评测系统的一部分**。统一 diff、structured files、anchored search/replace 等 contract 的微小差异会决定结果能否进入 verifier。
2. **pre-verifier 失败不能当作任务能力失败**。invalid submission、unsafe generated text、context mismatch 和 unsupported response 需要单独归因。
3. **no-model control 很有价值**。它说明 replay/verifier 路径可以工作，从而把 blocker 定位到 live model output/provider/contract 层。
4. **成本纪律已经生效**。ledger 和 budget gate 防止在不可计分路径上继续扩大 live spend。
5. **声称边界写得正确**。各报告持续声明不支持 ranking reversal、capability uplift、G_score predictivity 或 authorization，这是研究诚信的一部分。

## 6. 未来工作

### 6.1 先解决 scoreability，再恢复 predictivity 实验

下一步不应直接扩大 G/R/W 矩阵。必须先让 live model submissions 在固定 smoke 上通过 scoreability gate，至少满足：

- patch-ready / verifier-attemptable coverage 达到预设阈值；
- invalid submission rate 降到阈值以下；
- clean replay disagreement 为 0；
- output contract 与 parser/applicator 的行为在 no-model 和 live artifact 上一致；
- unsafe text、source mismatch、unsupported response 等 failure classes 能稳定归因。

只有当 live path 可计分，才有资格讨论 `R_score`、`W_score` 和 ranking reversal。

### 6.2 明确下一条 live output contract 路线

目前证据显示 `patch-or-files-v1` live path 未能提升 scoreability，anchored fixed-grid 也没有达标。未来可以选择两条路线之一：

- 回到结构化 full-file contract，但进一步降低 unsafe generated text 和 incomplete content 风险；
- 继续 anchored search/replace，但强化 source snapshot、anchor 生成、重复 old text 处理和 redaction 策略。

无论选择哪条路线，都应保留同一固定 denominator 和 no-model control，避免每次修 contract 都换任务、换 denominator、换解释口径。

### 6.3 建立最小可接受的 scorecard v1

Scorecard v0 已能消费既有矩阵，但未来需要向系统设计中的 scoring semantics 靠拢：

- 区分 scoreable zero、missing coverage、infra failure、policy invalid 和 malformed submission；
- 记录 release weight、score weight、oracle grade、duplicate cluster、risk/high-impact tags；
- 记录 score input set digest，避免后续补跑悄悄改变历史分数；
- 对 repeated runs 使用显式 trial policy，避免 best-of-N 掩盖不稳定性。

### 6.4 从 Click smoke 过渡到真正的仓库级 release

当前 Click slice 是实验烟测，不等同于 Barcarolle benchmark release。未来需要完成：

- 明确 task family、component/path、risk/permission/high-impact tags；
- 对每个 task 做 A/B oracle grading、leakage scan、flakiness/runtime probe；
- 发布 immutable release membership；
- 在 release coverage profile 中声明 supported 和 unsupported authorization scopes；
- 把 RBench 与 RWork 的 source anchors、时间边界和污染风险记录完整。

### 6.5 验证核心叙事，而不是只优化管道

一旦 scoreability gate 通过，实验应回到原始研究问题：

- 冻结至少 2-4 个 ACUT；
- 在同一 fixed RBench/RWork task set 上运行；
- 确保 G_score 的 basis 明确，最好直接运行小型 frozen general benchmark slice；如果使用公开分数，必须标注 evidence weakness；
- 检查 `R_score` 与 `W_score` 的相关性是否强于 `G_score`；
- 只有在同一任务 schedule、同一 attempt policy、无隐藏 retry 和可解释 scorecard 的前提下，才报告 ranking reversal。

### 6.6 产品化优先级

如果后续实验证据支持核心叙事，产品化应优先实现以下闭环：

1. task candidate -> replay plan -> validation -> benchmark admission；
2. immutable benchmark definition/release；
3. tested-agent snapshot 与 ACUT identity；
4. runner integration 与 clean-room canonical verification；
5. scorecard 与 denominator/missing-run semantics；
6. repository risk profile 与 authorization decision；
7. repository-agent admission 与 operating-state projection。

Operator console、完整自动 policy calibration、多仓库 federation、强对抗 attestation 和 runtime enforcement integrations 都可以后置。

## 7. 局限与伦理/治理注意事项

本报告的局限包括：

- 实验数据仍集中于 Click 小切片和 scoreability smoke，不能代表通用仓库。
- 当前 live output contract 不稳定，尚未形成可靠能力测量。
- 成本统计是 provider response usage 或本地估算，不是 invoice-verified billing。
- 外部 benchmark 和行业材料来自公开资料，部分 vendor 报告可能带有产品叙事偏差。
- Barcarolle 当前设计假设 trusted internal collaboration，不应被误用为对抗式第三方认证。

治理上需要避免三类过度宣传：

- 把 no-model control 的成功说成 agent 能力成功；
- 把 pre-verifier invalid submission 直接说成 task-solving failure；
- 把设计上的 G0-G5 语义说成已经由实验验证的 admission outcome。

## 8. 结论

Barcarolle 抓住了一个真实研究和工程缺口：代码智能体已经进入仓库工作流，但现有通用 benchmark 不能直接回答仓库级准入问题。项目的设计方向是合理的：把 ACUT 作为评测对象，把仓库历史变成可回放任务，把 task admission、canonical verification、scoring、risk profile、authorization 和 operating state 分开，并把最终输出定义为仓库范围的证据化 admission，而不是通用榜单或运行时 guard。

但项目当前的实证状态仍处在测量基础设施阶段。已有证据支持“仓库级评测需要严肃处理输出契约、可回放验证、无模型控制、成本纪律和失败归因”；尚未支持“Barcarolle 已证明 repository-specific benchmark 比 general benchmark 更能预测真实工作质量”。下一阶段的关键不是扩大宣传，而是先修复 live scoreability，再在冻结 ACUT、冻结任务集、冻结 attempt policy 和可解释 scorecard 的前提下验证核心叙事。

## 参考材料

### 项目内材料

- [README.md](../../README.md)
- [docs/draft/abstract.md](../draft/abstract.md)
- [docs/analysis/requirements.md](../analysis/requirements.md)
- [docs/architecture/system-design.md](../architecture/system-design.md)
- [docs/architecture/benchmark-admission-rubric.md](../architecture/benchmark-admission-rubric.md)
- [docs/architecture/scoring-semantics.md](../architecture/scoring-semantics.md)
- [docs/architecture/authorization-semantics.md](../architecture/authorization-semantics.md)
- [docs/architecture/workflow-runtime.md](../architecture/workflow-runtime.md)
- [docs/research/agent-configuration-evaluation.md](./agent-configuration-evaluation.md)
- [docs/research/repository-evaluation-infrastructure-landscape.md](./repository-evaluation-infrastructure-landscape.md)
- [docs/research/benchmark-trustworthiness-risks.md](./benchmark-trustworthiness-risks.md)
- [docs/research/repository-specific-benchmark-generation-related-work.md](./repository-specific-benchmark-generation-related-work.md)
- [docs/experiments/core-narrative-experiment-plan.md](../experiments/core-narrative-experiment-plan.md)
- [experiments/core_narrative/reports/kickoff_narrative_evidence_memo.md](../../experiments/core_narrative/reports/kickoff_narrative_evidence_memo.md)
- [experiments/core_narrative/reports/2026-05-09_measurement_stabilization_m1_1_report.md](../../experiments/core_narrative/reports/2026-05-09_measurement_stabilization_m1_1_report.md)
- [experiments/core_narrative/reports/2026-05-09_m2_scoreability_stabilization_report.md](../../experiments/core_narrative/reports/2026-05-09_m2_scoreability_stabilization_report.md)
- [experiments/core_narrative/reports/2026-05-10_m2_fixed_grid_gate_assessment.md](../../experiments/core_narrative/reports/2026-05-10_m2_fixed_grid_gate_assessment.md)

### 外部材料

- [GitHub Introduces Coding Agent For GitHub Copilot](https://github.com/newsroom/press-releases/coding-agent-for-github-copilot)
- [GitHub Copilot: Meet the new coding agent](https://github.blog/news-insights/product-news/github-copilot-meet-the-new-coding-agent/)
- [About GitHub Copilot cloud agent](https://docs.github.com/en/copilot/concepts/agents/cloud-agent/about-cloud-agent)
- [Introducing Agent HQ: Any agent, any way you work](https://github.blog/news-insights/company-news/welcome-home-agents/)
- [Stack Overflow Developer Survey 2025](https://survey.stackoverflow.co/2025)
- [GitHub Octoverse 2024](https://github.blog/news-insights/octoverse/octoverse-2024/)
- [DORA Accelerate State of DevOps Report 2024](https://dora.dev/research/2024/dora-report/)
- [OpenAI: Why SWE-bench Verified no longer measures frontier coding capabilities](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)
- [SWE-Bench Pro: Can AI Agents Solve Long-Horizon Software Engineering Tasks?](https://arxiv.org/abs/2509.16941)
- [SWE-PolyBench: A multi-language benchmark for repository level evaluation of coding agents](https://arxiv.org/abs/2504.08703)
- [SWE-agent: Agent-Computer Interfaces Enable Automated Software Engineering](https://papers.nips.cc/paper_files/paper/2024/file/5a7c947568c1b1328ccc5230172e1e7c-Paper-Conference.pdf)
- [METR: Measuring AI Ability to Complete Long Tasks](https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)
