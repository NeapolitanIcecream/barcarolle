# Doubled-timeout Agent Reliability Gate

生成日期：2026-06-14

## 结论

Kilo + GPT mainline 在 doubled-timeout reliability gate 中通过。

本 package 在 no-paid preflight 通过后，只花费 `1` 个新的 paid cell。该 cell 使用新 policy：

- adapter timeout: `1800s`
- outer workspace timeout: `1860s`
- verifier timeout: `360s`
- endpoint/proxy upstream timeout: `3600s`

运行结果是 `verified_pass`，`scoreable_cell=true`，`acut_exit_code=0`，没有 adapter timeout，也没有 provider/adapter 空 patch 问题。因此 Kilo 在本 runbook 的 doubled-timeout gate 下可进入 Package 5 的 repeat evidence 路径。

## No-paid preflight

| Gate | Result |
| --- | --- |
| `LLM_BASE_URL` / `LLM_API_KEY` | present |
| `/models` includes `gpt-5.4` | ready |
| planned models present | `claude-sonnet-4-6`, `gpt-5.4`, `gpt-5.4-mini` |
| secret isolation | ready; child sees no real endpoint secrets |
| repository gate | ready |
| reference replay sample | `3/3` passed |
| raw/workspace paths ignored | ready |
| generated Kilo command | contains `--timeout 1800` |
| generated Kilo outer timeout | `1860s` |

Adapter/workspace tests:

```text
PYTHONPATH=experiments/phase0_headroom/tools uv run --project experiments/phase1_compiler pytest experiments/phase0_headroom/tools/test_cli_workspace_adapters.py experiments/phase0_headroom/tools/test_workspace_acut_run.py experiments/phase0_headroom/tools/test_workspace_usage_import.py -q
```

Result: `39 passed in 4.47s`.

## Paid cell used

| Run | Task | Status | Scoreable | Timeout | Latency | Usage | Estimated cost |
| --- | --- | --- | --- | --- | ---: | --- | ---: |
| `doubled_timeout_gate__kilo_gpt_5_4__boltons__hist__031__attempt1` | `boltons__hist__031` | `verified_pass` | `true` | none | `46.861s` | observed | `$0.1560355` |

Token usage:

| Input | Cached input | Output |
| ---: | ---: | ---: |
| `179113` | `145792` | `2419` |

Patch digest:

```text
d9d997f5a4c322c851dc110813cf6a0eddbf58eec5204ac2bbf28cc32d9b9f78
```

Raw stdout/stderr/patch paths were written only under ignored phase0 raw artifact storage.

## Gate interpretation

Kilo did not hit the previous failure pattern in this gate:

- no exit `124`;
- no empty patch/stdout reliability failure;
- no repeated provider error surfaced to the harness;
- hidden verifier ran and passed.

This is a reliability-gate pass, not a global model-quality claim. It only says that, under the new `1800s` policy, Kilo is currently scoreable enough to run the Package 5 doubled-timeout repeat evidence within the remaining paid-cell cap.

## Paid accounting

| Item | Count |
| --- | ---: |
| New paid cells in Package 4 | `1` |
| Runbook hard cap | `42` |
| Remaining cap after Package 4 | `41` |

No second Kilo smoke/debug cell was run because the first doubled-timeout cell was scoreable and passed.
