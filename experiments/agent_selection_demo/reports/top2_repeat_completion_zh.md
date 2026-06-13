# Top-2 Repeat Completion Attempt

生成日期：2026-06-13

## 结论

本 package 结论：`infrastructure blocker still unresolved`。

Kilo gate 已通过到可以尝试 repeat 的程度，但 frozen top-2 completion attempt 在第一个新增 Kilo repeat cell 再次超时，因此按 strict runbook 停止后续付费 repeat cells。不要把当前结果解释为全局 Agent 排名；它只说明本轮 `mahmoud/boltons` top-2 repeat 仍被 Kilo infrastructure timeout 阻断。

## Preflight gates

已完成 no-paid preflight：

- `LLM_BASE_URL` 和 `LLM_API_KEY`：sourcing `~/.zshrc` 后存在。
- `/models` gate：`repository_gate.json` 为 `status=ready`，`present_models` 包含 `gpt-5.4`、`gpt-5.4-mini`、`claude-sonnet-4-6`，无 missing model。
- secret isolation：`secret_isolation_gate.status=ready`，solver-visible child 不可见真实 endpoint secrets，dummy proxy key 存在。
- raw artifact paths：`experiments/phase0_headroom/results/raw/workspace_acut/...` 和 `experiments/phase0_headroom/external_repos/...` 均为 ignored path。
- adapter tests：`29 passed in 4.37s`。
- Kilo CLI：`7.3.1`。

本 package 还新增了一个 repeat-safety guard：

- top-2 repeat 默认 agent set 固定为 `codex_gpt_5_4` 与 `kilo_gpt_5_4`，避免无参数调用扩大 Agent matrix；
- `--stop-on-unscoreable` 会在新增 cell 出现 timeout、harness error、policy error 或 empty diff 后停止后续 paid cells。

对应测试：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py -q
```

结果：`41 passed in 4.32s`。

## Smoke/gate result

未新增付费 Kilo smoke/debug cell。原因：既有 smoke row 已经是 scoreable pass；package 3 修补 usage parser 后，本 package 用 no-paid `recover-stage smoke` 从 ignored raw stdout 恢复 usage/cost metadata。

恢复后 smoke stage：

- scheduled cells：`4`
- completed cells：`4`
- scoreable-cell rate：`1.0`
- verified solve rate：`1.0`
- usage observed rate：`1.0`
- Kilo GPT mainline smoke：`verified_pass`，latency `41.792s`，observed estimated cost `$0.1137155`

这说明 Kilo successful event stream usage 已经可解析，但不保证 Kilo repeat timeout 已修复。

## Frozen repeat attempt

命令：

```text
source ~/.zshrc >/dev/null 2>&1 || true
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools \
  uv run --project experiments/phase1_compiler \
  python experiments/agent_selection_demo/tools/agent_selection_demo.py top2_repeat --stop-on-unscoreable
```

命令返回的 stage threshold code：`2`。这不是脚本崩溃；含义是完整 stage 仍低于 configured scoreable-cell gate。

本次新增 paid repeat cell 数：`1`。

新增 row：

| run_id | status | exit | latency | usage | patch | verifier |
| --- | --- | ---: | ---: | --- | --- | --- |
| `top2_repeat__kilo_gpt_5_4__boltons__hist__020` | `acut_harness_error` | `124` | `900.692s` | missing | empty | not run |

该 row 的 ignored raw artifact 元数据：

- stdout：`0` bytes
- stderr：`442` bytes
- patch：`0` bytes
- stderr pattern：`timed out=1`，`HTTP Error 500=0`，`BrokenPipeError=0`，`Traceback=0`

`adapter_timed_out=False` 表示外层 workspace runner 没有先杀 adapter；adapter 自己返回了 `124`。这符合 package 3 的 cleanup-grace 修补目标，但 Kilo child 仍然无法在 budget 内产出 diff/usage。

## Updated repeat accounting

当前 `top2_repeat` stage：

- scheduled cells：`20`
- completed cells：`13`
- scoreable cells：`10`
- scoreable-cell rate：`0.5`
- verified pass count：`7`
- usage observed count：`10`

Agent-level：

| Agent | completed | scoreable | pass | timeout/infra | usage observed |
| --- | ---: | ---: | ---: | ---: | ---: |
| Codex + GPT mainline | 10 | 10 | 7 | 0 | 10 |
| Kilo + GPT mainline | 3 | 0 | 0 | 3 | 0 |

All scored diffs are Codex rows and replayed in clean verifier workspaces. Kilo has no scored repeat diff in the current repeat stage.

## Task-level comparison

Legend：`P=verified pass`，`F=verified fail`，`I=infrastructure/timeout`，`M=missing/not run`。

| Task | Original holdout C/K | Previous repeat C/K | Package 4 new attempt | Current repeat C/K |
| --- | --- | --- | --- | --- |
| `boltons__clean_ext__017` | P/P | P/I | not rerun | P/I |
| `boltons__hist__019` | F/F | P/I | not rerun | P/I |
| `boltons__hist__020` | P/P | P/M | Kilo I | P/I |
| `boltons__hist__022` | F/P | F/M | stopped before cell | F/M |
| `boltons__hist__023` | F/P | F/M | stopped before cell | F/M |
| `boltons__hist__024` | P/P | P/M | stopped before cell | P/M |
| `boltons__hist__025` | P/P | P/M | stopped before cell | P/M |
| `boltons__hist__026` | P/P | P/M | stopped before cell | P/M |
| `boltons__hist__027` | F/P | P/M | stopped before cell | P/M |
| `boltons__hist__028` | F/P | F/M | stopped before cell | F/M |

## Acceptance status

- All reachable cells are accounted for: yes. The attempt reached one new Kilo cell and stopped at the first fresh non-scoreable timeout as required.
- Scoreable rate reported: yes, current repeat scoreable-cell rate is `0.5`.
- Every scored diff replayed in a clean verifier workspace: yes, all scored rows are Codex repeat rows; Kilo rows are infrastructure rows with no diff.
- Task-level comparison included: yes.
- Required conclusion: `infrastructure blocker still unresolved`.

Package 4 paid cells used：`1` fresh Kilo top-2 repeat cell。No fresh paid smoke/debug cell was used.
