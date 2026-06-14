# Agent Tuning Phase 1 behavior-change smoke test

生成日期：2026-06-14

## 结论

Package 5 证明了一个受限但有用的 behavior-change signal：同一个真实 Codex workspace Agent，在同一个 task statement 下，注入不同 `AGENTS.md` artifact 后，发往 real CLI request path 的上下文发生了可观察差异。

- Variant A artifact：指示不要运行测试；
- Variant B artifact：指示运行指定 public check：`python -m pytest tests/test_public_smoke.py -q`；
- 两个 variant 都使用 `codex_workspace`、`repo_AGENTS_md` surface、同一个 task statement、同一个 no-paid fake endpoint；
- `paid_calls_used = 0`；
- Variant B 的 public-test 指令只在 Variant B 的 sanitized request observation 中出现。

这不是完整 action-level 行为证明。由于 fake endpoint 只返回最终文本，没有驱动 Agent 工具调用，本 smoke 没有证明真实 command trace、file reads、file edits、diff 或 public-test execution 发生差异。Phase 2 因此应标记为 `ready_for_phase2_with_restrictions`，并在优化前加一个最小 action-level preflight：要么用更完整的 fake endpoint 模拟 tool calls，要么用 `LLM_BASE_URL`/`LLM_API_KEY` 做一两个 harmless paid smoke cells。

## 运行命令

```text
uv run --project experiments/phase1_compiler python experiments/agent_tuning_demo/tools/agent_injection_smoke.py --suite behavior --out experiments/agent_tuning_demo/results/behavior_change_smoke_test.json
```

配套测试：

```text
uv run --project experiments/phase1_compiler pytest experiments/agent_tuning_demo/tests -q
```

## 结果

| field | Variant A | Variant B |
| --- | --- | --- |
| agent | `codex_workspace` | `codex_workspace` |
| surface | `repo_AGENTS_md` | `repo_AGENTS_md` |
| artifact path | `AGENTS.md` | `AGENTS.md` |
| loaded observed | yes | yes |
| paid call used | no | no |
| command exit | 0 | 0 |
| adapter timeout status | no | no |
| request path | `/v1/responses` | `/v1/responses` |
| behavior instruction | do not run tests | run `python -m pytest tests/test_public_smoke.py -q` |
| public-test instruction observed | no | yes |

Comparison summary:

- `variant_a_loaded = true`
- `variant_b_loaded = true`
- `public_test_instruction_observed_only_in_variant_b = true`
- `terminal_status_changed = false`
- `adapter_timeout_status_changed = false`
- `behavior_change_level = request_context_and_mocked_final_output`

## Barcarolle 可观察字段

本 no-paid smoke 可记录：

- injection record；
- artifact hash；
- request path；
- fixed-phrase observation booleans；
- command exit code；
- adapter timeout status；
- latency；
- stdout/stderr line counts；
- paid-call count。

本 no-paid smoke 不能记录为已证明：

- command trace 差异；
- file read 差异；
- file edit 差异；
- final workspace diff 差异；
- public test execution 差异；
- verifier status 差异。

## Phase 2 影响

这个结果足以说明 artifact injection 可以改变 real Agent 收到的可观察上下文，因此 Barcarolle 可以记录 artifact-driven context behavior。它还不足以声明 tuned artifact 会改变真实工具使用或解题结果。

Phase 2 推荐前置限制：

1. 第一轮优化只使用一个 soft instruction surface；
2. 优先选择 Package 4 中 fake endpoint 下 exit 0 的 Kilo `AGENTS.md` 或 Kilo `.kilo/rules`，或者先修 Codex fake endpoint action smoke；
3. 在任何 GEPA/Phoenix optimization 前，先跑最小 action-level smoke，证明 Variant B 真的触发 public-test command 或产生可区分 diff；
4. 不把本结果写成 tuned Agent improvement。
