# Top-2 Repeatability Check

## 结论

本次只重复 `mahmoud/boltons` 的同一批 10 个 holdout tasks，Agent 矩阵为 Codex + GPT mainline 与 Kilo + GPT mainline，模型均为 `gpt-5.4`。

20 个 repeat cells 中完成 `13` 个，可评分 `10` 个，可评分率 `0.5`，acceptance reachable 为 `False`。

原 holdout 是 Kilo `9/10` 对 Codex `5/10`；当前 persisted repeat 是 Kilo `0/0` scoreable（`3` completed, `3` infra）对 Codex `7/10`。

repeat 被 Kilo adapter timeout 阻断，不能作为 scoreable ranking 结果；Codex repeat 完成但 Kilo repeat 不完整。

由于 Kilo repeat 没有达到可评分完整性，本次不能判断 Kilo holdout 领先是否稳定，也不能把变化归因于模型随机性；当前主要解释是 Kilo adapter/CLI timeout 基础设施问题。

## 实际矩阵

| Agent | Harness | Model |
| --- | --- | --- |
| Codex + GPT mainline | codex | gpt-5.4 |
| Kilo + GPT mainline | kilo | gpt-5.4 |

## 任务集

任务集完全沿用 `frozen_split.json` 的 holdout tasks：`boltons__clean_ext__017, boltons__hist__019, boltons__hist__020, boltons__hist__022, boltons__hist__023, boltons__hist__024, boltons__hist__025, boltons__hist__026, boltons__hist__027, boltons__hist__028`。

## Agent 汇总

| Agent | 原 holdout pass | repeat pass | 变化任务 | 成本 usage |
| --- | --- | --- | --- | --- |
| Codex + GPT mainline | 5 | 7/10 scoreable; 10 completed, 0 infra | boltons__hist__019, boltons__hist__027 | observed_tokens_estimated_cost |
| Kilo + GPT mainline | 9 | 0/0 scoreable; 3 completed, 3 infra | None | missing_usage_conservative_estimate |

## Task-level 稳定性

| Task | Source | Module | Codex 原->复 | Kilo 原->复 |
| --- | --- | --- | --- | --- |
| boltons__clean_ext__017 | clean_outcome_unseen | timeutils.py | P->P | P->I |
| boltons__hist__019 | canonical_history | ioutils.py | F->P | F->I |
| boltons__hist__020 | canonical_history | timeutils.py | P->P | P->I |
| boltons__hist__022 | canonical_history | iterutils.py, iterutils.rst | F->F | P->M |
| boltons__hist__023 | canonical_history | tbutils.py | F->F | P->M |
| boltons__hist__024 | canonical_history | dictutils.py | P->P | P->M |
| boltons__hist__025 | canonical_history | funcutils.py | P->P | P->M |
| boltons__hist__026 | canonical_history | dictutils.py | P->P | P->M |
| boltons__hist__027 | canonical_history | cacheutils.py, tests.yaml | F->P | P->M |
| boltons__hist__028 | canonical_history | iterutils.py | F->F | P->M |

## 重点失败任务

| Task | Codex 原->复 | Kilo 原->复 | repeat 关系 |
| --- | --- | --- | --- |
| boltons__hist__022 | F->F | P->M | F/M |
| boltons__hist__023 | F->F | P->M | F/M |
| boltons__hist__027 | F->P | P->M | P/M |
| boltons__hist__028 | F->F | P->M | F/M |

## Later canonical_history

holdout 中 `canonical_history` 任务 `9` 个。repeat 中 Codex 通过 `6/9` scoreable；Kilo 为 `0/0` scoreable，另有 `2` 个 infra、`7` 个 not run，因此不能判断 Kilo 是否仍强于 later canonical_history。

## 基础设施与成本 caveat

repeat 中有 `3` 个非可评分/基础设施相关 cell，需要单独排查。

成本仍不能作为 production-value winner 的依据：Codex repeat usage 覆盖与 Kilo repeat usage 覆盖不对称时，Kilo 成本继续按 conservative per-cell estimate 标记，报告只把 pass/fail 稳定性作为主要结论。

## 下一步建议

建议下一步优先做更多 repeats 或修复 Kilo usage normalization 后再讨论成本；不要基于这次单仓库 top-2 repeat 进入第二仓库扩展、prompt/tool tuning、learned selector 或 rolling-origin paid validation。
