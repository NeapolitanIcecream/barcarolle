# Agent Tuning Feedback Summary

生成日期：2026-06-13T12:50:55+00:00

本报告由 CLI 从 committed sanitized results 生成，不读取 raw prompts、raw completions、transcripts、solver workspaces 或 verifier workspaces。

生成命令：

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler python experiments/agent_selection_demo/tools/agent_selection_demo.py tuning-feedback-summary --output experiments/agent_selection_demo/reports/agent_tuning_feedback_summary_zh.md
```

## Boundary

这是 feedback input，不是 tuning result。它不声称任何 Agent 已经经过 tuning，也不声称任何配置修改已经提升效果。

## Per-Agent Failure Taxonomy

| Agent | Cells | Scoreable | Pass | Infra | Usage | Failures |
| --- | --- | --- | --- | --- | --- | --- |
| Codex + GPT mainline | 41 | 41 | 28 | 0 | 1.0 | hidden verifier failure: 13 |
| Kilo + Claude Sonnet | 31 | 29 | 23 | 2 | 0.0323 | hidden verifier failure: 6, no meaningful change: 2 |
| Kilo + GPT mainline | 34 | 31 | 25 | 3 | 0.0294 | exceeded budget or timeout: 3, hidden verifier failure: 6 |
| Kilo + GPT low-cost | 31 | 29 | 20 | 2 | 0.0323 | exceeded budget or timeout: 2, hidden verifier failure: 9 |

## Example Follow-Up Tasks

| Agent | Stage | Task | Failure | Status |
| --- | --- | --- | --- | --- |
| Codex + GPT mainline | selection | boltons__supply_expansion_20260526__001 | hidden verifier failure | verified_fail |
| Codex + GPT mainline | selection | boltons__supply_expansion_20260526__004 | hidden verifier failure | verified_fail |
| Codex + GPT mainline | selection | boltons__supply_expansion_20260526__048 | hidden verifier failure | verified_fail |
| Kilo + Claude Sonnet | selection | boltons__supply_expansion_20260526__001 | hidden verifier failure | verified_fail |
| Kilo + Claude Sonnet | selection | boltons__supply_expansion_20260526__004 | no meaningful change | invalid_output |
| Kilo + Claude Sonnet | selection | boltons__supply_expansion_20260526__048 | hidden verifier failure | verified_fail |
| Kilo + GPT mainline | selection | boltons__supply_expansion_20260526__001 | hidden verifier failure | verified_fail |
| Kilo + GPT mainline | selection | boltons__supply_expansion_20260526__002 | hidden verifier failure | verified_fail |
| Kilo + GPT mainline | selection | boltons__supply_expansion_20260526__107 | hidden verifier failure | verified_fail |
| Kilo + GPT low-cost | selection | boltons__supply_expansion_20260526__001 | hidden verifier failure | verified_fail |
| Kilo + GPT low-cost | selection | boltons__supply_expansion_20260526__002 | exceeded budget or timeout | acut_harness_error |
| Kilo + GPT low-cost | selection | boltons__supply_expansion_20260526__004 | hidden verifier failure | verified_fail |

## Shared Failure Tasks

| Stage | Task | Failing agents | Categories |
| --- | --- | --- | --- |
| holdout | boltons__hist__019 | 3 | hidden verifier failure: 3 |
| holdout | boltons__hist__023 | 3 | hidden verifier failure: 3 |
| holdout | boltons__hist__027 | 2 | hidden verifier failure: 2 |
| holdout | boltons__hist__028 | 3 | hidden verifier failure: 3 |
| selection | boltons__hist__006 | 4 | hidden verifier failure: 3, no meaningful change: 1 |
| selection | boltons__hist__011 | 3 | exceeded budget or timeout: 1, hidden verifier failure: 2 |
| selection | boltons__supply_expansion_20260526__001 | 4 | hidden verifier failure: 4 |
| selection | boltons__supply_expansion_20260526__002 | 2 | exceeded budget or timeout: 1, hidden verifier failure: 1 |

## Unstable Repeat Tasks

| Task | Codex | Kilo | Repeat relation |
| --- | --- | --- | --- |
| boltons__hist__019 | F->P | F->I | P/I |
| boltons__hist__027 | F->P | P->M | P/M |

## Infrastructure Blockers

| Agent | Task | Status | Failure | Latency |
| --- | --- | --- | --- | --- |
| kilo_gpt_5_4 | boltons__clean_ext__017 | acut_harness_error | exceeded budget or timeout | 900.009 |
| kilo_gpt_5_4 | boltons__hist__019 | acut_harness_error | exceeded budget or timeout | 900.009 |
| kilo_gpt_5_4 | boltons__hist__020 | acut_harness_error | exceeded budget or timeout | 900.692 |

## Cost And Usage Coverage

Usage coverage is included per Agent above. Cost comparisons remain feedback-only when usage coverage differs by harness or when rows use conservative missing-usage estimates.

Recommended tuning backlog interpretation: first fix infrastructure and usage observability blockers; then use stable verifier-backed hidden failures as exemplars for prompt/tool/config changes. Do not use this report as proof that a learned selector or tuned Agent is valid.
