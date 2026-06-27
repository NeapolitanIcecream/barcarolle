# Agent Tuning Demo paid pause checkpoint

生成时间：`2026-06-18`。

## 当前状态

Agent Tuning Demo 已完成一次端到端 before/after future holdout 验证，但结果不是正向收益：

- Terminal state: `agent_tuning_demo_complete`。
- Result label: `agent_tuning_demo_complete_regressed`。
- Target repo: `mypy`。
- Window: `origin_40`。
- Agent: `Kilo + gpt-5.4-mini`。
- Tuning surface: repo-local `AGENTS.md` appendix。
- Chosen artifact: `agent-tuning-demo-mypy-family-triage-loop`。
- Future holdout: baseline `12/20` scoreable pass，tuned `11/19` scoreable pass，paired net wins `-1`。
- Task-level flips: `4` improved tasks，`5` regressed tasks，`1` tuned invalid output。
- Estimated/observed cost: `$29.39064915` across `76` paid solver Agent cells。

## 核实结论

当前没有证据表明本轮误用了非 mini 模型：

- preregistration、runner、Kilo adapter、ledger 均记录 `gpt-5.4-mini`；
- raw Kilo event metadata 抽样显示 `modelID: gpt-5.4-mini`；
- 成本高主要来自 Coding Agent 的工具调用轨迹：`76` 个 solver cells 合计约 `95.66M` input tokens、`69.53M` cached input tokens、`1.02M` output tokens。

当前也没有证据表明 future holdout 的 task-level flips 是网络错误造成：

- future baseline `20/20` scoreable；
- future tuned `19/20` scoreable；
- future rows 均有 observed usage 和 endpoint proof；
- 唯一非 scoreable 是 tuned 条件下一个 `invalid_output` / no meaningful change。

## 解释边界

本轮支持的说法：

- Barcarolle 可以生成 repo-specific certified tasks；
- 可以冻结 corrected rolling-origin window，避免 future holdout 进入 tuning input；
- 可以把 train-only feedback 转成可部署的 repo-local Agent artifact；
- 可以在 future holdout 上做 before/after 验证并记录成本；
- 这个 artifact 足以改变 Agent 的任务级行为，带来新增通过，也带来新增失败。

本轮不支持的说法：

- 不支持 Agent tuning 有稳定正向收益；
- 不支持 predictive validity；
- 不支持统计显著结论；
- 不支持 GEPA/DSPy/LLM tuner 有效，因为最终 artifact 是 local rule proposer 生成；
- 不支持跨 repo 泛化；
- 不支持 opaque Agent 可以被当前方法稳定调优。

## 暂停决策

短期暂停继续推进 paid Agent Tuning Demo。原因不是基础设施无法运行，而是经济性不合适：

- baseline 结果可以复用；
- 同一 artifact hash 的 tuned 结果可以复用；
- task supply、verifier、rolling-origin windows 可以复用；
- 但每个新 artifact 都会改变 Agent 行为轨迹，必须重新付费跑 tuned cells，不能像 Agent Selection Demo 那样一次付费、多次复用。

后续没有预算时，不应继续用 paid cells 追正向 tuning result。当前结果应定位为 Agent tuning feedback loop 的 feasibility pilot。

## 有预算后的下一步

恢复 paid work 前，先补这几个低成本或预算受控的机制：

- outcome cache：按 `(repo, task, Agent config, artifact hash, timeout, harness version)` 复用 paid cell；
- cost smoke gate：每个新 repo / Agent 先跑 2-3 个 cells，估算平均成本；
- funnel protocol：先在 baseline-failed tasks 上筛新增 pass，再用少量 baseline-passed tasks 做 regression guard，最后才跑完整 future holdout；
- neutral `AGENTS.md` control：区分“存在 AGENTS.md 文件”与“具体 tuning 内容”的影响；
- repeat check：对 flipped tasks 做 1-2 次重复，估计随机性；
- parent `AGENTS.md` leakage preflight：证明 solver workspace 不会读取 Barcarolle repo 根目录的 `AGENTS.md`。

## Canonical artifacts

- Final report: `experiments/agent_tuning_demo/reports/agent_tuning_demo_final_report_zh.md`
- Final closeout: `experiments/agent_tuning_demo/results/agent_tuning_demo_final_closeout.json`
- Future holdout summary: `experiments/agent_tuning_demo/results/agent_tuning_demo_future_holdout_summary.json`
- Cost summary: `experiments/agent_tuning_demo/results/agent_tuning_demo_cost_summary.json`
- Cost ledger: `experiments/agent_tuning_demo/results/agent_tuning_demo_cost_ledger.jsonl`
