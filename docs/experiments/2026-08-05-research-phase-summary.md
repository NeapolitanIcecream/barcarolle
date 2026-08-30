# Barcarolle 阶段研究与工程总结

> 历史阶段文档：本文冻结记录截至 2026-08-05 的 Selection 研究，不是当前
> 路线。2026-08-30 起的三项目标、任务生成与 meta-evaluation 方法空间，
> 以及反复优化实验协议以
> [`../research-program.md`](../research-program.md) 为准。下文中的“主指标”
> 与“下一步”只描述当时的实验合同。

日期：2026-08-05。

状态：本轮工作已完成研究收口，等待代码检视与合入。本总结创建前，
分支相对 `main` 包含 148 个按计划、实现、证据和修正拆分的提交。
提交次序保留了实验的冻结点和事后修正，不宜压成一个无法审计的快照。

## 范围

本轮工作从可认证的静态 Task Pool 和付费 Agent campaign 基础设施开始，
随后使用已付费结果和公开逐 Task 结果研究 rolling-origin Selection。
范围包括：

- Task Pool 导入、认证和身份绑定；
- Agent campaign 的预算、配额、恢复、停止和证据卫生；
- rolling-origin 回放、时间和可见性 contract；
- 多个公开 Task Pool 与 Agent panel 的适用性审计；
- 多条 Selector 和理论驱动算法路线；
- 以 direct future pass-rate MAE 为主指标的方法论修正；
- 当前开发候选 `consensus_rate_match` 及其失败的迁移诊断。

本轮没有进入具体 Task Generator 开发，也没有把实验候选提升为生产
Selector。

## 阶段结论

1. Barcarolle 已具备开展下一轮无付费 rolling-origin 研究所需的主要
   基础设施，也具备在新 Agent API 可用后安全运行付费 campaign 的能力。
2. Task Pool、Agent panel、Harness、repository、horizon 和聚合方法共同
   决定可预测性。一个来源上的低 MAE 不能直接外推为系统有效。
3. 主指标仍是 future pass-rate MAE。Full eligible history 是不做
   Selection 的主 baseline；equal-budget random 是稠密的采样空间标尺；
   future-open Oracle 只表示容量，不是可部署方法。
4. 旧的低通过率 Agent panel 会奖励接近零的预测，曾使算法研究偏向错误
   目标。当前主开发 panel 已改为同一 Harness 下的现代模型。
5. `consensus_rate_match` 是目前主开发 panel 上最好的 pre-Origin、预算十
   Task 候选，但只在 repository-equal 聚合下同时改善 H5 和 H10。它在
   Origin weighting 和已打开的跨系统迁移中反向，因此尚不能作为生产
   Selector。
6. 下一问题不是继续在同一五仓库分数上调参，而是识别 reference Agent
   与 target Agent 的 population shift，并区分 cold start 与有缓存 target
   Results 的 warm start。

## 已交付的工程能力

### 静态 SWE-bench Task Pool

实现了显式的静态来源适配器和 `freeze → prepare → certify` 流程，绑定数据
集、镜像、base commit、Task 和 Check 身份。首次完整构建覆盖 75 个
SWE-bench Verified SymPy 候选，生成并认证了 75 个 Task、75 个 Check 和
54 个依赖簇。该运行证明流程可用，不作为吞吐量承诺。

用户仍可直接导入自己维护的 Task Pool；系统不要求所有 Task 都由内置
Generator 产生。来源差异由显式适配器承担，没有引入通用 Generator
注册中心或服务框架。

### 付费 Agent campaign

campaign 路径增加了：

- append-only 资源台账和调用 reservation/completion；
- 预算、配额、成本和 scoreability 停止条件；
- 有依据的 reauthorization，而非隐式扩大预算；
- management endpoint 的 rate-window 处理；
- token receipt 延迟可见时的可审计恢复和批量归因；
- 调用身份漂移、无价 usage、异常失败比例和证据缺口的 fail-closed；
- 可清理 workspace、单一 Result 写入、sanitized artifact manifest；
- 禁止自动 retry 或事后替换失败 cell 的冻结执行语义。

这些能力把“花了多少、调用了什么、为何停止、哪些结果可计分”变成可回放
证据。原始 workspace、prompt、completion、provider payload 和 verifier
材料仍位于忽略路径，不进入 Git。

### rolling-origin 和证据 contract

本轮修复和明确了以下边界：

- `strict_prospective` 与 `user_configured_counterfactual` 分开记录；
- 用户可以导入或修订影响算法的 Task/Check 时间，但必须显式标记证据模式，
  不能伪装成 source-attested 历史；
- 只有 feature 确实需要时才装载 pre-Origin Result；
- Selector 查询受 Task、Check 和 Agent 身份约束；
- frozen `FeatureSnapshot`/`SelectorInput` 可以在同一 Origin 复用；
- future Result 永远不进入可部署 Selector 输入；
- 浮点混合和相同分数 tie 使用稳定求和及确定性规则；
- counterfactual Result 可用时间不会被错误当成算法输入约束。

因此，Barcarolle 可以同时支持 source-attested 历史研究、用户迁移数据和
明确标注的反事实回放，而不要求从今天开始等待一年。

### 实验与性能基础设施

研究流程形成了可复用的 plan、amendment、execution lock、digest、独立
replay 和证据摘要模式。公开 benchmark normalizer 保存逐 Task outcome
和完整 Agent 身份；随机十 Task 的精确 PMF 在相同输入上复用，避免重复
组合计算。checkout 缓存和 Agent 并行仍保持阈值触发：只有测量表明其占比
或 campaign 规模需要时才引入。

合入收口时发现默认 CI 会因缺少 NumPy、SciPy 和 PyArrow 跳过 43 个研究
与算法测试。三项依赖现已进入锁定的 `research` extra；质量工作流保留
Python 3.11 核心门禁，并在 Python 3.14 下另跑研究套件。依赖被 Git
忽略的原始来源或中间证据的复现测试，在干净 checkout 中会显式 skip；
具备完整本地证据时，研究套件为 `1244 passed, 2 skipped`。这样无需上传
原始产物，也不需要改写绑定源码 digest 和浮点运行时的冻结实验结果。

## 已付费模型研究

完整报告见
[2026-07-25 Coding-Agent / Model Study](2026-07-25-model-agent-study.md)。

冻结主实验的 238 个 cell 全部终止，其中 237 个可计分，1 个 Terra repeat
保留为 `agent_invalid`，没有 retry 或替换。在 75 个 base Task 上：

| 结果 | Terra-high | Mini-high |
| --- | ---: | ---: |
| hidden-check pass | 53/75 (`70.67%`) | 46/75 (`61.33%`) |
| 全部调用 / 可计分 Result | 119/118 | 119/119 |
| end-to-end success | 87 (`73.11%`) | 73 (`61.34%`) |
| 精确 gateway cost | `$25.036084` | `$71.414206` |
| 每次 end-to-end success 成本 | `$0.287771` | `$0.978277` |
| workspace 中位秒数 | `99.30` | `122.92` |

Terra 的 paired advantage 为 `9.33` 个百分点；exact McNemar
`p=0.092285`，依赖簇 bootstrap 95% 区间为 `[0, 18.18]` 个百分点。
结论是：结合准确率、成本和延迟，Terra-high 可作为这个冻结的 SymPy
来源与 Codex CLI Harness 的工程默认值；证据不支持“对所有来源普遍更好”。

完整 sprint 记录了 291 次模型调用、287 个可计分 Result。精确 token-log
归因成本为 `$114.406752`，全局余额变化为 `$117.795124`，保守调用估计
合计 `$216.113623`，均未越过 `$300` 上限。观察到的 repeat flip rate 为
`13.85%`，bootstrap 区间 `[6.15%, 21.88%]`；重复运行暂留在实验层，
没有为此扩张核心 Result schema。

## Selection 研究方法的修正

### 部署和评估单位

真实部署单位是一个 target Agent、一个 repository 和一个 Task Pool。
多仓库只用于离线检验算法是否过拟合某个仓库，不在运行时把不同仓库的
Task 混成一个 benchmark。

Agent 身份包括 model、Harness 及版本、inference policy、attempt count
和其他影响结果的运行设置。只按模型名合并结果会制造不可解释的差异。

### 指标层级

每个候选首先比较 direct future pass-rate MAE：

1. Full eligible history：不做 Selection 的主 baseline；
2. uniform random budget-ten：候选在可采样空间中的位置；
3. always-zero/always-one：识别低或高 prevalence 的平凡区域；
4. target-future 和 reference-future Oracle：可选子集的上限与共享响应结构；
5. repository、Agent、Origin 和 joint-cell 方向：避免平均值掩盖反转。

Brier、AUC、surrogate loss 和 task-space loss 只能作为诊断，不能替代
pass-rate MAE。回溯审计没有发现被二级指标错误接受的候选；若二级指标
与 direct MAE 冲突，后者决定去留。

H5 和 H10 是不同需求和统计分辨率，不再合并为一个结论。repository-equal
与 Origin-weighted 也必须同时报告。

## 数据来源和失效区域

### 早期 SymPy 与 SWE-bench Verified

最初的 SymPy panel 只有 75 个 Task、2 个 Agent 和 12 个 rolling Origins，
适合验证基础设施，但不足以支持稳定算法结论。随后加入公开 Verified
逐 Task outcome，扩大 Agent 和 Origin 覆盖，并发现 response、semantic、
difficulty 和 Markov 路线的开发增益不能稳定迁移。

### Multi-SWE

Multi-SWE 固定证据包含 1,632 个 Task、39 个仓库和 36 个完整 Agent
配置，正例率仅 `4.9581%`。标准 H5 frame 的 future block 中 `83.61%`
全为零，always-zero MAE `0.059870`，优于 Full 的 `0.067348`；H10 的
方向对聚合、仓库和 Origin 定义敏感。

结论不是 Multi-SWE 数据损坏，而是这个 Task Pool 与 Agent panel 组合的
H5 主估计量被低 prevalence 支配。它可用于压力、容量和 cached-target
诊断，不应作为当前 unseen-target Selector 的主要 nomination panel。
完整边界见
[Multi-SWE Regime Assessment](2026-07-30-multi-swe-failure-region.md)。

### SWE-bench Full 旧 panel

旧 Full panel 中 6 个早期 RAG submission 的全部 repository cell 通过率
低于 `0.10`。已有候选在 RAG 组平均改善、在其他组平均恶化，说明聚合
分数曾奖励近零预测。Full 仍然比 always-zero 和 previous-block baseline
更好，但这只证明局部 prevalence 有用，不能证明 Selection 能预测未来
偏移。审计见
[SWE-bench Full estimand and reliability audit](2026-07-30-swe-bench-full-estimand-reliability-audit.md)。

### 现代开发 panel

当前主 panel 是 mini-SWE-agent v2.0.0 同一 Harness 下的 13 个模型配置，
覆盖全部 500 个 SWE-bench Verified Task：

- pooled pass rate `0.713077`，Agent 范围 `0.562–0.768`；
- 5 个满足历史门槛的仓库；
- 61 个 H5 Origin、30 个 H10 Origin；
- 151 种 response pattern，无重复 Agent vector。

辅助 panel 是 SWE-bench Full 的 3 个现代完整系统、2,294 个 Task、10 个
仓库。它用于异构系统迁移诊断，不是同 Harness 的模型比较，也已属于打开
数据，不能继续充当独立确认集。

## 算法路线结果

本轮不是只做参数搜索。研究过的机制包括时间/recency、response matching、
语义与 embedding、难度/Markov、budget-horizon adaptive、生成暴露、Git
模块压力、registry-dated dependency lag、prequential assembly、cached
finite-horizon assembly、distributional/MMD/IRT，以及 reference-Agent
consensus。

主要去留如下：

| 路线 | 结论 |
| --- | --- |
| coverage、stratified、semantic | 没有通过 direct MAE 和迁移门禁 |
| Joint Markov | 开发结果曾明显改善，独立审计和扩展 Agent transfer 失败 |
| Agent-invariant / adaptive Markov | 仓库、Agent 或 horizon 方向不稳定，退出 |
| budget `3/5/10` × horizon `5/10/15` | 没找到可稳定宣称的有效区间 |
| THY-001/001R | Git 模块变化不能直接建立 Task outcome 预测，冻结后退出或 data-gated |
| THY-002/002S | 暴露/共享 task-space 信号不能转成稳定 direct MAE，退出 |
| THY-003 | registry lag Stage A 可运行，但 outcome-free gate 未支持晋级 |
| Multi-SWE prequential/cached | cached-target 有局部结果；unseen-target 跨 H5/H10 不稳定 |
| 旧算法原样迁移到现代 panel | recency、stationary、ALG-015U、ALG-016U 均输给 Full |
| `consensus_rate_match` | 当前开发 incumbent；主 panel 改善，但迁移失败，不能部署 |

失败路线及冻结计划继续留档，是为了避免用新的术语或轻微变体重复打开
同一假设。

## 当前最佳候选

完整报告见
[Consensus-Rate Selector Sprint](2026-07-31-consensus-rate-selector.md)。

`consensus_rate_match` 在每个 Origin 排除 target Agent，用其余 reference
Agents 的 pooled pass rate 描述历史 Task；选择十个 Task，使其 reference
pass rate 尽量匹配 Full history 的 reference pass rate，再以较低 reference
disagreement 打破精确 tie。算法不读取 target column 或 future block。

| 固定 mini-SWE-agent v2 panel | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.179527` | `0.129700` |
| Candidate MAE | `0.173387` | `0.115927` |
| Candidate − Full | `-0.006140` | `-0.013774` |
| 相对降低 | `3.42%` | `10.62%` |
| favorable repositories | 3/5 | 4/5 |
| favorable Agents | 10/13 | 11/13 |
| favorable Origins | 23/61 | 13/30 |

两次完整执行 byte-identical；1,183 个正式 membership/score 与独立实现
一致；36,956 个小矩阵经穷举和动态规划检查无分歧；两个组成部分的
ablation 都输给 Full。

但以下结果阻止晋级：

| 诊断中的 Candidate − Full | H5 | H10 |
| --- | ---: | ---: |
| 主 panel 改为 Origin weighting | `+0.004284` | `+0.001864` |
| 3 个现代 Full 系统 internal LOO | `+0.014960` | `+0.024006` |
| 13 个主 reference → 3 个外部 target | `+0.017513` | `+0.007707` |

因此它是同 Harness、repository-equal、outcome-open 的开发 incumbent，
不是一般性的 cross-Harness 结论，更不是生产 Selector。

## 基础设施准备度

在不增加付费 Agent run 的情况下，当前系统可以继续：

- 导入公开逐 Task outcome 或用户提供的 Task Pool/Results；
- 在明确证据模式下修订 Task/Check 时间并重建 rolling Origins；
- 运行 cold-start reference-only 和 warm-start cached-target 研究；
- 复用随机分布、Full baseline、trivial controls 和 Oracle 容量诊断；
- 冻结新算法、重放、做独立 audit，并生成 sanitized evidence。

新服务器和 API 到位后，付费 campaign 也已有认证、预算、归因、恢复和
stop gate。当前不需要为未来可能的 Generator、trainer、scheduler 或
generic plugin registry 预建框架；新增来源时实现一个直接适配器即可。

## 后续工作

下一轮应使用现有公开 outcome，按以下顺序推进：

1. 测量 `consensus_rate_match` 对 reference panel 数量、target ability、
   model family 和 Harness shift 的敏感度；
2. 明确 cold start（没有 target outcome）与 warm start（Result Store 中
   已有 target 历史 outcome）的两个 contract；
3. 在看新分数前冻结 support/abstention 规则或 target-robust mechanism；
4. 寻找新的同 Harness target 边界，避免继续优化当前五仓库平均值；
5. 只有公开结果无法回答已冻结问题时，才设计新的付费 Agent panel；
6. 只有 Generator 研究问题明确后，才实现具体 built-in Generator。

importance weighting 或 AIPW 只是研究线索。它们会改变原始 benchmark
pass rate 的解释，不能直接成为 schema 或默认评分改动。

## 证据索引与发布卫生

短期交接见 [`PROCESS.md`](../../PROCESS.md)，当前路线和候选状态见
[Research Ledger](../research-improvement-backlog.md)。每个实验的冻结
计划、输入 digest、sanitized summary 和 reproduction 命令保存在对应的
`docs/experiments/` 与 `examples/` 子目录。

合入前的发布门禁包括：

- 完整测试、Ruff、Pyright 和 `git diff --check`；
- 当前树和本分支全部未合入提交的本地绝对路径扫描；
- 常见 secret、credential URL、private key 和 endpoint literal 扫描；
- 确认原始 prompt、completion、workspace、provider payload、cache 和
  verifier 私有材料没有进入 Git。

测试 fixture 中允许出现显式的假值、保留域名和环境变量名称；它们不是
可用凭据。任何真实本地路径或 secret 都不进入提交、PR 正文或 CI 日志。
