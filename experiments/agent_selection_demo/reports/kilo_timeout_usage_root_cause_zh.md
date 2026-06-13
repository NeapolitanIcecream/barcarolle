# Kilo Timeout And Usage Root-Cause Report

生成日期：2026-06-13

## Scope

本报告完成 strict runbook package 3：Kilo timeout 与 usage root-cause work。

本 package 没有运行任何付费 Agent cell。诊断只使用 committed sanitized artifacts、本地源码、测试、以及 ignored raw artifacts 的元数据和错误模式计数；未提交 raw prompt、raw completion、raw transcript、solver workspace、verifier workspace 或 secret。

## Sanitized row evidence

`top2_repeat_score_table.csv` 中 Kilo frozen top-2 repeat 只有两个已记录 row：

| run_id | task_id | status | exit | latency | scoreable | usage | patch |
| --- | --- | ---: | ---: | ---: | --- | --- | --- |
| `top2_repeat__kilo_gpt_5_4__boltons__clean_ext__017` | `boltons__clean_ext__017` | `acut_harness_error` | `124` | `900.009s` | `False` | missing | empty patch hash |
| `top2_repeat__kilo_gpt_5_4__boltons__hist__019` | `boltons__hist__019` | `acut_harness_error` | `124` | `900.009s` | `False` | missing | empty patch hash |

对应 verifier rows 为：

- `status=acut_harness_error`
- `harness_error=acut_command_failed`
- `acut_exit_code=124`
- `fresh_workspace=false`

这说明 hidden verifier 未执行，失败发生在 ACUT harness / adapter 调用期，不是 verifier replay 或 hidden tests 卡住。

## Ignored raw artifact evidence

两个 persisted Kilo timeout rows 的 ignored raw 文件大小：

| run_id | stdout | stderr | patch |
| --- | ---: | ---: | ---: |
| `top2_repeat__kilo_gpt_5_4__boltons__clean_ext__017` | `0` bytes | `18456` bytes | `0` bytes |
| `top2_repeat__kilo_gpt_5_4__boltons__hist__019` | `0` bytes | `14817` bytes | `0` bytes |

stderr pattern counts：

| run_id | HTTP 500 | BrokenPipeError | Traceback |
| --- | ---: | ---: | ---: |
| `top2_repeat__kilo_gpt_5_4__boltons__clean_ext__017` | `5` | `5` | `10` |
| `top2_repeat__kilo_gpt_5_4__boltons__hist__019` | `4` | `4` | `8` |

结论：

- Kilo CLI 已启动并进入 OpenAI-compatible provider path。
- 配置端点返回了重复 HTTP 500；本地 endpoint proxy 在向已断开的 client 写错误响应时记录 `BrokenPipeError`。
- Kilo 没有产生 stdout usage event，也没有产生 workspace diff。
- solver workspaces 中只有 `.barcarolle/` 类运行目录，没有可评分实现改动。

## Timeout path classification

Kilo timeout 是两层问题叠加：

1. 直接根因是上游 `/v1/chat/completions` 在 Kilo paid call 过程中重复返回 HTTP 500，Kilo 保持在 retry/error path，直到 900 秒预算耗尽。
2. Barcarolle runner/adapters 原先也有 timeout hygiene 缺口：外层 workspace runner 与 adapter child 使用相同 900 秒 timeout，且没有显式进程组清理。外层有可能先杀 adapter，使 adapter 来不及完成自己的 timeout 记录和临时目录清理。

它不是 hidden verifier、fresh verifier workspace、任务可见测试、或 patch replay 导致的 hang；verifier 未执行，patch 为空。

## Implemented mitigations

Package 2 已先修补共享 process cleanup：

- `workspace_acut_run.run_command()` 改为创建独立进程组，timeout 后杀进程组并 drain stdout/stderr。
- `codex_workspace_adapter.run_child()` 和 `kilo_workspace_adapter.run_child()` 使用同样的进程组清理策略。

本 package 继续修补 Kilo-specific repeat 风险：

- `agent_selection_demo.adapter_config_for()` 现在把 candidate 的 timeout 作为 adapter 内部 `--timeout`，并给外层 workspace runner 增加 `adapter_cleanup_grace_seconds`，默认 30 秒。
- `workspace_acut_run.run_workspace_cell()` 在 sanitized submission/verifier rows 记录 `adapter_timed_out`，后续 timeout 能区分 adapter 自己超时与其他 nonzero exit。
- `agent_selection_demo.extract_usage_from_text()` 新增 Kilo JSONL event stream fallback：从 `step_finish.part.tokens` 归一化 `input_tokens`、`cached_input_tokens`、`output_tokens`，并标记 `usage_source_schema=kilo_step_finish_tokens`。

## Usage root cause

Kilo successful stdout 不是标准 OpenAI usage JSON，而是 Kilo event stream。旧 parser 只找 nested usage object，因此会把成功 Kilo row 错判为 missing usage。

修补后，本地 sanity check 对一个既有 Kilo successful stdout 提取出：

```text
input_tokens=381185
cached_input_tokens=0
output_tokens=5413
usage_source_schema=kilo_step_finish_tokens
```

注意：这只证明 parser 能恢复成功 Kilo event stream 的 token usage。两个 top-2 timeout rows 的 stdout 仍为 0 bytes，因此它们仍然没有可观测 usage，score table 中保留：

- `usage_observed=False`
- `cost_observation_kind=missing_usage_conservative_estimate`
- `usage_source=missing_adapter_usage`

## Test evidence

已运行：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_cli_workspace_adapters.py -q
```

结果：`39 passed in 4.84s`。

已运行：

```text
uv run --project experiments/phase1_compiler python -m py_compile experiments/agent_selection_demo/tools/agent_selection_demo.py experiments/phase0_headroom/tools/workspace_acut_run.py
```

结果：通过。

新增或更新的覆盖：

- adapter command 保留 Kilo/Codex CLI 内部 timeout，并给外层 runner 加 cleanup grace；
- workspace adapter timeout 会在 sanitized row 中记录 `adapter_timed_out=True`；
- Kilo `step_finish` token event stream 会被归一化为 cost/usage input。

## Safe-to-smoke decision

Kilo smoke/repeat 可以进入 package 4 gate，但必须先通过以下 no-paid preflight：

- `LLM_BASE_URL` 和 `LLM_API_KEY` 存在；
- endpoint/model proof 只通过 required endpoint，不回退到 provider-specific env；
- adapter unit tests 通过；
- raw artifact paths 仍为 ignored；
- Kilo CLI 可执行；
- smoke/debug paid cells 数量不超过 strict runbook 边界。

若 preflight 通过，package 4 可运行最多 4 个 Kilo smoke/debug cells；若 smoke 成功并没有再次出现 endpoint/adapter timeout，再尝试同一 frozen top-2 repeat。若重复 HTTP 500 或 timeout 再现，则记录 blocker，不继续扩大 paid calls。

本 package 付费 Agent cells 使用数：`0`。
