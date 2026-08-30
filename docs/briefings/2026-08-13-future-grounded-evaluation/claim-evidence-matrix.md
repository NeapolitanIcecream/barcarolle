# 论断—证据—边界矩阵

> 历史矩阵（2026-08-13）。其中的路线优先级不是当前指令；当前研究合同见
> [`../../research-program.md`](../../research-program.md)。

状态说明：`观察` = 已有直接材料；`推断` = 由观察与既有理论导出的解释；`假说` = 未来实验要证伪；`定义` = 项目约定，不是经验结果。

| ID | 论断 | 状态 | 主要证据 | 限制 / 允许措辞 |
| --- | --- | --- | --- | --- |
| C01 | SWE-bench 建立了真实 repository issue + executable tests 的标准化能力测量 | 观察 | [SWE-bench](https://arxiv.org/abs/2310.06770) | 说“建立范式”；不说 tests 等价于完整语义 |
| C02 | 固定公开 benchmark 同时面临污染与 oracle 错配 | 观察 | OpenAI 的 [Verified 复审](https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/)；[Pro 审计](https://openai.com/index/separating-signal-from-noise-coding-evaluations/) | 两类问题分开陈述；审计样本不能无条件外推到所有 coding benchmark |
| C03 | Verified 中 o3 在 64 次运行仍未稳定解决的 138 题定向子集，至少 59.4% 有实质性问题 | 观察 | OpenAI Verified 复审 | 该 138 题是 27.6% 的 targeted subset，不是随机抽查；不能外推成全部 500 题缺陷率 |
| C04 | SWE-Bench Pro 的人工标注汇总将 249/731（34.1%）标为有问题；OpenAI 对整体问题率估计约 30% | 观察 | OpenAI [Pro 审计](https://openai.com/index/separating-signal-from-noise-coding-evaluations/) | 区分 249/731 的人工标注汇总与约 30% 的整体估计；同时说明 OpenAI 撤回自身此前推荐 |
| C05 | Live/rebench/smith/Bench++ 分别推进滚动供应、自动构建和训练规模 | 观察 | 对应论文 [Live](https://arxiv.org/abs/2505.23419)、[rebench](https://arxiv.org/abs/2505.20411)、[smith](https://arxiv.org/abs/2504.21798)、[Bench++](https://arxiv.org/abs/2512.17419) | 不把“新/大/自动”写成无污染或 oracle 正确证明 |
| C06 | SWE-Future 的主语义匹配判分将 151/260（58.1%）个 forecast families 相对 T0 后 PR metadata 标为 strong 或 related | 观察 | [SWE-Future](https://arxiv.org/abs/2606.18733) | 该指标衡量 synthesis eligibility；不是独立人工确认、精确 issue 命中率、Agent pass rate 或最终生成题外部有效性 |
| C07 | 交互需求披露是终局 pass/fail 之外的能力轴 | 观察 | [SWE-INTERACT](https://arxiv.org/abs/2606.30573)、[SWE-Together](https://arxiv.org/abs/2606.29957) | simulator 和 judge 也需要验证；交互真实性不自动解决未来有效性 |
| C08 | 自动 Agent variant search 已从概念进入可运行系统 | 观察 | [Darwin Gödel Machine](https://arxiv.org/abs/2505.22954) | 证明可沿给定 benchmark 搜索；不证明 field transfer |
| C09 | RQGM 对 evaluator-dependent slots 采用 fixed-within-epoch evaluator，并以 held-out ground-truth anchor 决定 evaluator promotion；evaluator-independent roles 使用固定 benchmark | 观察 | [Red Queen Gödel Machine](https://arxiv.org/abs/2606.26294) | anchor 不直接认证 writer/prover 等 task-agent utility；task agents 仍按 epoch-local evaluator 排序。当前 empirical investigation 是 preliminary，也未构造 delayed repo future workload |
| C10 | 自适应查询同一 holdout 可能破坏统计有效性 | 观察 | [Dwork 等](https://arxiv.org/abs/1411.2664)、[Ladder](https://arxiv.org/abs/1502.04585) | “可能且有理论条件”；不说每个 benchmark 必然严重退化 |
| C11 | public/private gap 不能自动归因于 repeated optimization | 观察 | [Roelofs 等](https://arxiv.org/abs/1902.10811) | 需同时检查候选相似性和分布漂移 |
| C12 | Barcarolle 已有 Task/Check、干净 solver、diff capture、新 verifier + hidden oracle、Results、rolling-origin 和 reporting 边界 | 观察 | 仓库 `README.md`、`docs/design/system-design.md`、`src/barcarolle/`、`PROCESS.md` | 说“repo-local 可审计边界”；alpha host-shared execution 不是 adversarial sandbox |
| C13 | SymPy 路线生成 75 Task/Check、54 clusters；campaign 238 cells 终止，237 scoreable、1 invalid | 观察 | `examples/model_agent_study/study-results.json` 与 `PROCESS.md` | 证明执行与审计闭环；不证明科学泛化 |
| C14 | `consensus_rate_match` 在 repository-equal H5/H10 上相对 Full 降低 MAE 3.42%/10.62% | 观察 | `examples/modern_agent_panel/evidence/consensus-rate-summary.json`、`PROCESS.md` | outcome-open、13 个同 Harness 模型、5 repo development estimand |
| C15 | 换 Origin weighting 后 H5/H10 方向反转 | 观察 | 同上与 `PROCESS.md` | 说明结论依赖 estimand；不能声称 typical-Origin 改善 |
| C16 | internal LOO 和 13 refs→3 external targets 均落后 Full | 观察 | `examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json`、`PROCESS.md` | 说明跨完整 system/Harness transfer 失败；不是所有未来方法必然失败 |
| C17 | 当前最直接的下一问题是 reference-to-target population shift | 推断 | C14–C16；仓库当前 `PROCESS.md` | 作为研究优先级，不作为已证机制因果结论 |
| C18 | 低 pointwise MAE 不保证选对版本 | 推断 | selection regret 的定义；adaptive/model-selection 文献 | 逻辑上指标不同；实际严重程度仍需 candidate-panel 实验 |
| C19 | Forecaster 正确不保证 Materializer 的 Agent contrasts 正确 | 推断 | SWE-Future 的分层构造；oracle/synthesis sensitivity 机制 | 需 repeated/cross materialization + later response 实验确认 |
| C20 | Barcarolle 应把目标设为 future-grounded evaluation boundary，而不是 trainer | 定义 | `AGENTS.md` 的 benchmark boundary；现有架构职责 | 清楚声明外部 Agent/Optimizer 拥有改进 loop |
| C21 | Optimization horizon 是 evaluator 在指定协议下可承受的优化压力 | 定义/假说 | `research/adaptive-validity.md` | 不能写成已有数值或 evaluator 固有常数 |
| C22 | support/abstention 可能降低 population shift 下的错误决策 | 假说 | 当前 transfer failure；coverage–risk 方法 | 必须同时报告 coverage；低 risk + 近零 coverage 不是成功 |
| C23 | refreshed Barcarolle 的 regret 随查询次数增长可能慢于 static benchmark | 假说 | adaptive-data-analysis/RQGM 设计启发 | 需相同 proposer、预算、反馈和 sealed future 的对照实验 |
| C24 | Generator 经 response calibration 后可能更好保留 future Agent differences | 假说 | `research/adaptive-validity.md` 的 Generator validity 与 Stage D | calibration 只用较早 development origins；配置在 sealed later-real evaluation block 前冻结。同一 block 不能兼作校准与最终评估；synthetic 不替代 later-real audit |
| C25 | SWE-bench 的公共价值还包括统一坐标和行业协调 | 推断 | SWE-bench 的公开任务/协议/排行榜形态；`research/landscape.md` | 作为产品价值解释，不冒充论文测得的 network-effect 因果效应 |
| C26 | Braintrust/LangSmith 已能在给定 dataset 上比较 experiments 与 regression | 观察 | [Braintrust](https://www.braintrust.dev/docs/evaluate/compare-experiments)、[LangSmith](https://docs.langchain.com/langsmith/compare-experiment-results) 官方文档 | 说明 execution 已成熟；不贬低其线上监控能力，也不假设其 dataset 必然没有 external validity |
| C27 | Barcarolle 相对 EvalOps 的研究差异是 later-work external validity | 定义/推断 | C20、C26；Barcarolle rolling-origin 边界 | 这是拟议定位；需用 winner regret/成本实验证明用户价值 |
| C28 | 一般的自主项目优化不进入第一阶段主张 | 定义 | `discussion-synthesis.md` 的 treatment-dependent workload 与多 outcome 分析 | 不是说项目优化永远不可研究；只是当前没有保持原始闭环的通用 protocol |
| C29 | SWE-Together 的终局 correctness 由 agentic rubric judge 结合 repository inspection 与 executable evidence 评定 | 观察 | [SWE-Together](https://arxiv.org/abs/2606.29957) | rubric 在候选前冻结有助于可比性，但 LLM-based judge 与 simulator 仍需独立验证；不能把分数当作完整人工验收 |
| C30 | SWE-Bench++ 的 state-differential oracle 比较 Base、Before 和 After 三个 repository states | 观察 | [SWE-Bench++](https://arxiv.org/abs/2512.17419) | 三态执行支持区分 regression fix 与 feature request；仍受开发者测试稀疏和执行代理语义正确性的限制 |
| C31 | Reward hacking 可形式化为优化 proxy reward 时 expected proxy return 上升而 expected true return 下降 | 观察 | [Skalse 等](https://arxiv.org/abs/2209.13085) | 是 reward/policy 设定下的机制定义与理论结果；不是 coding-agent benchmark 的实证，也不提供 later-real anchor |
| C32 | Gao 等在 synthetic gold reward model 设定中测得 reward-model overoptimization，且 proxy/gold 关系随 RL 或 best-of-n 等优化方式而变 | 观察 | [Gao 等](https://arxiv.org/abs/2210.10760) | 支持测量 optimization-pressure curve；fixed synthetic gold model 不等于人类效用或后来真实 repository work |
| C33 | LiveBench 使用近期信息源、客观自动判分并按月增加或更新问题，以限制测试污染窗口 | 观察 | [LiveBench](https://arxiv.org/abs/2406.19314) | 是通用 LLM benchmark 的 live-refresh 证据；不是 repository-level coding-agent 任务，也不验证 adaptive winner selection 或 later-work external validity |

## 写作规则

- `观察`可以用陈述句，但必须保留样本、estimand 和来源限定。
- `推断`用“说明、提示、因此优先研究”，不用“证明因果机制”。
- `假说`统一用“预计、待检验、成功标准”；不得画成 observed result。
- 任何新数字先在本表登记来源和 denominator；不能只来自共享聊天。
- 原始聊天用于保留讨论脉络，不作为本表任何外部事实论断的证据。
