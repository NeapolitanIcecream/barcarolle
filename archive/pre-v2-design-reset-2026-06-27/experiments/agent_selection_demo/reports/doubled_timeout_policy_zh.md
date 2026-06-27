# Doubled-timeout Policy

生成日期：2026-06-14

## 结论

本 package 已把 demo 新运行使用的 Agent/adapter timeout 从 `900s` 加倍到 `1800s`，并让外层 workspace runner 多给 adapter `60s` 清理窗口。因此 demo 配置生成的 workspace outer timeout 是：

```text
1800s adapter timeout + 60s cleanup grace = 1860s outer timeout
```

这只影响后续新运行。已经提交的旧 selection、holdout、repeat 结果仍按当时的 `900s` policy 解释，不能被重写成 `1800s` 结果。

## Active timeout settings

| 层级 | 当前设置 | 实现位置 |
| --- | ---: | --- |
| Agent/adapter solving timeout | `1800s` | `experiments/agent_selection_demo/config/demo_config.json` 的所有 candidate 和 fallback `timeout_seconds` |
| Adapter cleanup grace | `60s` | `run_policy.adapter_cleanup_grace_seconds` |
| Outer workspace timeout | `1860s` | `agent_selection_demo.adapter_config_for()` 使用 `timeout_seconds + cleanup_grace` |
| Codex adapter CLI default | `1800s` | `codex_workspace_adapter.DEFAULT_TIMEOUT_SECONDS` |
| Kilo adapter CLI default | `1800s` | `kilo_workspace_adapter.DEFAULT_TIMEOUT_SECONDS` |
| LLM endpoint proxy upstream timeout | `3600s` | `llm_endpoint_proxy.DEFAULT_UPSTREAM_TIMEOUT_SECONDS` |
| Kilo provider request timeout | `3600000ms` | `kilo_workspace_adapter.write_kilo_config()` |
| Verifier timeout | `360s` | `run_policy.verifier_timeout_seconds` |

Verifier timeout 原来在 demo package builder 中是 `180s`。本次按 runbook 加倍到 `360s`，原因是新 Agent-side timeout 加倍后，hidden verifier 也应减少偶发慢测试误判，但 verifier 仍明显小于 Agent budget，不会掩盖 adapter timeout。

## Generated command verification

使用当前 committed config 生成 adapter configs，结果如下：

| Agent | Candidate timeout | Generated adapter command | Outer timeout |
| --- | ---: | --- | ---: |
| `codex_gpt_5_4` | `1800` | contains `--timeout 1800` | `1860` |
| `kilo_gpt_5_4` | `1800` | contains `--timeout 1800` | `1860` |
| `kilo_gpt_5_4_mini` | `1800` | contains `--timeout 1800` | `1860` |
| `kilo_claude_sonnet_4_6` | `1800` | contains `--timeout 1800` | `1860` |
| fallback `codex_gpt_5_4_mini` | `1800` | contains `--timeout 1800` | `1860` |

检查命令：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler python - <<'PY'
import agent_selection_demo as demo
config = demo.load_config(demo.ROOT / demo.DEFAULT_CONFIG)
for candidate in [*config['agent_candidates'], config['fallback_candidate']]:
    adapter = demo.adapter_config_for(config, candidate)
    print(candidate['agent_id'], candidate['timeout_seconds'], adapter.timeout_seconds, '--timeout 1800' in adapter.command_template)
print('cleanup', config['run_policy']['adapter_cleanup_grace_seconds'])
print('verifier', demo.run_policy_int(config, 'verifier_timeout_seconds', demo.DEFAULT_VERIFIER_TIMEOUT_SECONDS))
print('proxy', config['run_policy']['endpoint_proxy_upstream_timeout_seconds'])
PY
```

输出摘要：

```text
codex_gpt_5_4 1800 1860 True
kilo_gpt_5_4 1800 1860 True
kilo_gpt_5_4_mini 1800 1860 True
kilo_claude_sonnet_4_6 1800 1860 True
codex_gpt_5_4_mini 1800 1860 True
cleanup 60
verifier 360
proxy 3600
```

## Tests

新增和更新的测试覆盖两个稳定 contract：

- demo config 生成的 adapter command 必须包含 `--timeout 1800`；
- adapter outer timeout 必须是 `1860s`；
- adapter/proxy defaults 必须匹配 doubled timeout policy；
- Kilo provider config 的 upstream request timeout 必须是 `3600000ms`。

已运行：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests/test_agent_selection_demo.py -q
```

结果：`18 passed in 0.05s`。

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py -q
```

结果：`9 passed in 0.04s`。

因为本 package 触及 phase0 shared adapter/proxy code，也运行了 workspace 相关测试：

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
```

结果：`21 passed in 4.47s`。

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

结果：`9 passed in 0.01s`。

## Claim boundary

- 新 `1800s` policy 只适用于本次 patch 后生成的新 commands 和新 paid/no-paid runs。
- 旧 `900s` timeout rows 保持历史解释；例如旧 Kilo repeat timeout 仍是 `900s` policy 下的 infrastructure blocker。
- 本 package 未运行 paid Agent cells。
