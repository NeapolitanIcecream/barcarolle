# Demo Tooling And Artifact Hygiene Audit

生成日期：2026-06-13

## 范围

本包审计并修补了以下路径：

- `experiments/agent_selection_demo/`
- `experiments/phase0_headroom/tools/`
- `experiments/phase1_compiler/tools/`

本包没有运行任何付费 Agent cell；只使用 committed sanitized artifacts 和本地测试。

## Adapter 调用路径

Demo runner 通过 `experiments/agent_selection_demo/tools/agent_selection_demo.py` 的 `adapter_config_for()` 生成 workspace adapter command：

- Codex：`experiments/phase0_headroom/tools/codex_workspace_adapter.py`
- Kilo：`experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- 外层 workspace 执行与 verifier replay：`experiments/phase0_headroom/tools/workspace_acut_run.py`

`workspace_acut_run.run_workspace_cell()` 负责：

- 构建 solver workspace；
- 写入 solver-visible statement；
- 调用 adapter；
- 捕获 `git diff`；
- 执行 out-of-scope/test-edit policy check；
- 在 fresh verifier workspace 重放 diff；
- 注入 hidden verifier material；
- 写入 sanitized submission/verifier artifacts。

## Timeout 与子进程处理

发现的问题：

- 共享 runner 和 Codex/Kilo adapters 原先都依赖 `subprocess.run(..., timeout=...)`。
- 该模式会处理直接子进程超时，但没有显式创建/清理进程组；当 CLI 自己再拉起子进程时，timeout 后可能留下 CLI grandchild 或后台进程。
- 这类残留会让 Kilo timeout 的边界变模糊，也会影响后续 smoke/repeat gate 的可信度。

已实施修补：

- `workspace_acut_run.run_command()` 改为 `subprocess.Popen(..., start_new_session=True)`，超时后用 `os.killpg(..., SIGKILL)` 清理整个进程组。
- `codex_workspace_adapter.run_child()` 和 `kilo_workspace_adapter.run_child()` 使用同样的进程组清理策略。
- 保留 stdout/stderr draining：超时后调用 `communicate()` 收集已产生输出，再记录 timeout return code `124`。
- 新增测试 `test_run_command_timeout_kills_child_process_group()`，验证 timed-out parent 的 child 不会继续写入 marker 文件。

## stdout/stderr 与 raw artifact 边界

- Adapter stdout/stderr 仍写入 ignored raw path，由 committed submissions 只保留相对路径引用。
- `workspace_acut_run.run_workspace_cell()` 仍在 sanitized submission/verifier rows 中记录 raw artifact path、patch hash、terminal status、fresh verifier replay status。
- 本包没有提交 raw stdout、stderr、patch body、完整 prompt、completion、transcript、solver workspace 或 verifier workspace。

## Usage/Cost metadata

发现的问题：

- Demo code 已经有 `cost_observation_kind`、`usage_source`、`billed_cost_usd` 字段，但早期 committed score tables 是旧表头，只包含 `usage_observed` 和 `estimated_cost_usd`。
- 旧 score tables 不足以直接区分 observed token estimate、missing usage conservative estimate、真实 billed cost。

已实施修补：

- 新增 `normalize_cost_row()`，对旧 cost ledger row 回填：
  - `cost_observation_kind`
  - `usage_source`
  - `billed_cost_usd`
- 将 observed token usage 标为 `observed_tokens_estimated_cost`。
- 将缺失 usage 的保守估算标为 `missing_usage_conservative_estimate`，`usage_source` 为 `missing_adapter_usage`。
- 将真实账单成本预留为 `billed_cost`，`usage_source` 为 `provider_billing_export`。
- 新增 CLI：`refresh-sanitized-stage-metadata`，可从 committed sanitized submissions/verifiers/cost ledgers 重写 score tables 和 metrics，不需要 raw artifacts。
- 已用该 CLI 刷新 `smoke`、`selection`、`holdout`、`top2_repeat` 的 committed sanitized ledgers、score tables 和 metrics。
- 重新生成 `top2_repeatability_check.json`，使 infrastructure rows 带上 cost metadata。

## Score table metadata

刷新后的 score table 表头包含：

```text
stage,agent_id,reviewer_name,harness,model,task_id,terminal_status,scoreable_cell,verified_pass,failure_category,latency_seconds,estimated_cost_usd,usage_observed,cost_observation_kind,usage_source,billed_cost_usd,patch_sha256
```

这足以在不读取 raw transcript 的情况下定位：

- 哪些 cell 可评分；
- 哪些 cell 是 timeout/infrastructure；
- 哪些成本是 observed token estimate；
- 哪些成本是 missing usage 下的 conservative estimate；
- 是否存在 provider billed cost。

## Artifact hygiene scan

命令：

```text
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)' || true
```

结果：无命中。

更宽扫描：

```text
git ls-files experiments/agent_selection_demo experiments/phase0_headroom/tools experiments/phase1_compiler/tools | rg '(__pycache__|\.pyc$|raw|transcript|workspace|\.DS_Store|\.pytest_cache|\.venv)' || true
```

结果命中 `workspace` 命名的工具源码和测试文件：

- `experiments/phase0_headroom/tools/codex_workspace_adapter.py`
- `experiments/phase0_headroom/tools/kilo_workspace_adapter.py`
- `experiments/phase0_headroom/tools/workspace_acut_run.py`
- 相关 `test_*workspace*` 和 `workspace_usage_import.py`

这些是 committed tooling paths，不是 raw paid-call transcripts、solver/verifier workspaces、cache 或 secret artifacts。

## Tests

已运行：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

结果：`46 passed in 3.34s`。

已运行：

```text
git diff --check
```

结果：通过。

## 结论

Package 2 完成。明确 bug 已修补：

- timeout path 现在会清理 adapter/CLI 进程组；
- committed sanitized score tables 和 cost ledgers 已回填 usage/cost metadata；
- tests 覆盖了 process-group timeout cleanup 和 cost metadata normalization。

这些修补降低了 Kilo repeat smoke 的基础设施风险，但不等于 Kilo timeout root cause 已完全证明；Kilo 的具体 timeout/usage root-cause 仍在 package 3 单独处理。
