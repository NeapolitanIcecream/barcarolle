# Agent 选型 Demo 剩余 Gap Audit

生成日期：2026-06-13

## 范围与状态

本 audit 只做状态确认和后续工作定位；本包未运行任何付费 Agent cell。

- 当前分支：`codex/agent-selection-demo-2026-06-12`。
- 当前 HEAD：`63fb2e72 docs: require strict agent selection demo completion`。
- 近邻相关提交：
  - `c3a0230c demo: add final agent selection package`
  - `35d3502d demo: clarify cost usage metadata`
  - `ffbea96a Record top-2 repeatability blocker`
  - `9a454579 Add top-2 repeatability gate`
  - `9be3ba40 Guard selection recommendation cost tie-breaker`
  - `33b38ed1 Add agent selection post-demo diagnostics`
  - `d19ffbed docs: record agent selection demo outcome`
- 本次严格 runbook 的源文件：`docs/research/agent-selection-demo-strict-completion-runbook-2026-06-13.md`。

## 已完成 demo artifact

第一轮 `mahmoud/boltons` demo 已经完成，并有以下 committed sanitized artifacts：

- 最终中文包：`experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`。
- 原始 demo 报告：`experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`。
- post-demo 诊断：`experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md`。
- top-2 repeatability blocker：`experiments/agent_selection_demo/reports/top2_repeatability_check_zh.md`。
- repository gate、smoke、selection、holdout、recommendation、top-2 repeat 的 sanitized result files：`experiments/agent_selection_demo/results/`。
- closeout 草案：`experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`。

重要边界：最终中文包已经存在，但它不是本 strict runbook 的结束条件。runbook 还要求完成工程诊断、artifact hygiene audit、Kilo root-cause work、必要 gate 后的 repeat 尝试、no-paid 第二仓库 gate、可运行 feedback summary generator、最终 closeout 和 `PROCESS.md` 更新。

## Gap 到 mandatory package 的映射

| Package | 当前状态 | 剩余 gap |
| --- | --- | --- |
| 1. state audit and gap list | 本文件新增 | 需要提交本 audit；无付费调用。 |
| 2. tooling/artifact hygiene audit | 部分已有 cost metadata patch | 仍需系统审计 `experiments/agent_selection_demo/`、`experiments/phase0_headroom/tools/`、`experiments/phase1_compiler/tools/`，确认 timeout、stdout/stderr、usage/cost、score table metadata、tracked artifact hygiene；如发现 bug 则补测试和 patch。 |
| 3. Kilo timeout and usage root-cause work | 旧 closeout 只记录 blocker | 仍需检查两个 900 秒 Kilo timeout 的代码路径、ignored raw artifacts、Kilo adapter process handling、usage parser；需要输出 `kilo_timeout_usage_root_cause_zh.md`。 |
| 4. Kilo smoke/gate and frozen top-2 repeat attempt | 旧 top-2 repeat stopped at 12/20 cells | 只有在 package 3 判定 Kilo paid smoke 安全且 endpoint/secret/model/tests/raw-path gate 通过后，才能在批准边界内运行最多 4 个 Kilo smoke/debug cells；若 smoke 通过，再尝试同一 frozen top-2 repeat。 |
| 5. no-paid second-repo gate | 尚未为本 demo 完成 | 默认检查 `python-attrs/attrs`，不运行 paid cells；需要报告 checkout/setup、可见测试、任务 supply、hidden verifier replay 可行性和未来矩阵成本。 |
| 6. runnable Agent tuning feedback summary generator | 只有静态 prototype report | 需要实现或完善可运行 CLI，从 sanitized results 生成 `agent_tuning_feedback_summary_zh.md`，并用测试覆盖核心聚合或输出。 |
| 7. final package and closeout update | 旧 closeout 是提前收口 | 需要把 package 2-6 的实际结果写入最终中文包、closeout 和 `PROCESS.md`；最终回答 runbook checklist。 |

## 计划使用的命令与文件

Kilo timeout/usage 诊断：

```text
sed -n '1,260p' experiments/phase0_headroom/tools/kilo_workspace_adapter.py
sed -n '454,570p' experiments/phase0_headroom/tools/workspace_acut_run.py
cat experiments/agent_selection_demo/results/top2_repeatability_check.json
cat experiments/agent_selection_demo/results/top2_repeat_cost_ledger.jsonl
cat experiments/agent_selection_demo/results/top2_repeat_score_table.csv
cat experiments/agent_selection_demo/results/top2_repeat_submissions.jsonl
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests experiments/phase0_headroom/tools/test_cli_workspace_adapters.py -q
```

如 sanitized artifacts 不足，将只读取 ignored raw paths 里的 stdout/stderr/patch metadata 用于诊断，不提交 raw prompts、raw completions、raw transcripts、solver/verifier workspaces 或 secrets。

第二仓库 no-paid gate：

```text
find experiments -path '*attrs*' -type f
sed -n '1,260p' experiments/phase1_compiler/tools/phase1_attrs_source_repair.py
sed -n '1,260p' experiments/phase1_compiler/tools/phase1_two_repo_certified_supply_expansion.py
cat experiments/phase1_compiler/results/phase1_attrs_source_repair_paid_readiness_gate.json
wc -l experiments/phase0_headroom/certified_tasks/attrs_*_certified_tasks.jsonl
git clone --filter=blob:none https://github.com/python-attrs/attrs.git experiments/phase0_headroom/external_repos/attrs
```

clone 只用于本地 checkout/setup gate；不得启动第二仓库 paid scoring。

Feedback summary generator：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py tuning-feedback-summary --output experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
```

该 CLI 目前还不存在，是 package 6 的实现目标。输入必须限制在 committed sanitized score tables、metrics、repeatability summary 和 cost ledgers 下；输出不得声称 tuning 已经改进任何 Agent。

## Artifact hygiene 初始观察

- `git status --short` 当前无 tracked dirty files。
- 本地存在 ignored `__pycache__/` 目录：`experiments/agent_selection_demo/tests/__pycache__/`、`experiments/agent_selection_demo/tools/__pycache__/`、`experiments/phase0_headroom/tools/__pycache__/`、`experiments/phase1_compiler/tools/__pycache__/`。
- 这些 cache 目录不是 tracked artifacts；package 2 仍需用 `git ls-files` 扫描 committed hygiene。

## 付费调用状态

本 package 付费 Agent cells 使用数：`0`。
