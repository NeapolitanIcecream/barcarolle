# Selector Final Demo Closeout

生成日期：2026-06-14

## 当前有效结论

- Demo 主线 selector：`HRD v3 70/30`。
- Demo 推荐 Agent：`Kilo + GPT mainline`。
- COD-lite 的角色：算法 bakeoff 表中的普通候选项，不是最终 demo 主算法。
- 本次最终收口没有启动新的 paid cells。

## Wrapper / reporting policy

输出以三件事为核心：

1. Agent 排名；
2. 选择建议；
3. 证据表。

状态只保留用户可读的三类：

| State | 含义 |
| --- | --- |
| `recommend` | 第一名有明确 Selection pass-rate 优势，给出推荐 |
| `top_tier` | 多个 Agent 表现接近，用户按成本、速度、稳定性破平 |
| `insufficient_data` | scoreable/common-valid cells 不足、缺 outcome row，或基础设施失败导致无法比较 |

paired wins/losses 和 bootstrap LCB 保留为证据字段，不再作为默认推荐 veto。

## HRD Selection / Holdout 矩阵

Selection:

| Agent | Pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Codex + GPT mainline | `7/10` |
| Kilo + Claude Sonnet | `7/10` |
| Kilo + GPT low-cost | `7/10` |

Holdout:

| Agent | Pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Kilo + Claude Sonnet | `8/10` |
| Kilo + GPT low-cost | `6/10` |
| Codex + GPT mainline | `5/10` |

Doubled-timeout top-2 repeat:

| Agent | Pass |
| --- | ---: |
| Kilo + GPT mainline | `9/10` |
| Codex + GPT mainline | `6/10` |

## Claim boundary

支持：在 frozen `boltons` demo slice 上，HRD v3 70/30 可以根据 Selection 推荐 Kilo + GPT mainline，后续 Holdout 和 top-2 repeat 也验证 Kilo 处于领先位置。

不支持：full predictive validity、严格击败强 random baseline、跨仓库或跨模型家族全局排名、COD-lite 作为最终 demo 主算法。

## Validation

| Command | Result |
| --- | --- |
| `PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q` | `43 passed` |
| `PYTHONPATH=experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_retrospective_predictive_signal.py -q` | `6 passed` |
| `git diff --check` | exit `0` |
| tracked artifact hygiene scan | no matches |
| diff secret/raw-artifact scan | no matches |
