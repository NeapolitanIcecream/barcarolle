# Agent Selection Demo Post-demo Diagnostics

生成日期：2026-06-13

本报告只使用已提交的 sanitized artifacts 和 certified task metadata：

- `experiments/agent_selection_demo/results/frozen_split.json`
- `experiments/agent_selection_demo/results/task_pool_audit.json`
- `experiments/agent_selection_demo/results/selection_score_table.csv`
- `experiments/agent_selection_demo/results/holdout_score_table.csv`
- `experiments/agent_selection_demo/results/*_cost_ledger.jsonl`
- `experiments/agent_selection_demo/results/*_submissions.jsonl`
- `experiments/agent_selection_demo/results/recommendation_lock.json`
- `experiments/agent_selection_demo/results/holdout_check.json`

没有读取 raw prompts、raw completions、raw transcripts、solver workspaces、
verifier workspaces 或 `results/raw/...` 下的文件。

## 诊断结论

selection/holdout 反转有一个足够具体的解释，但还不能被解释成稳定的
Agent 排名。

1. selection 推荐 `Codex + GPT mainline` 不是因为它在质量上单独领先。
   `Codex + GPT mainline` 和 `Kilo + GPT mainline` 在 selection 上同为
   `15/20` verified pass，scoreable cell 都是 `20/20`，hidden verifier
   failure 都是 `5`。推荐锁定在 Codex，是因为预声明规则在质量打平后用
   cost per solved task 破平。
2. 这个 cost 破平很脆弱。Codex 的 20 个 selection usage 全部是 observed
   token estimate；所有 Kilo 组合的 usage 都没有解析出来，只用了 `$0.5`
   conservative per-cell estimate。因此 production-value recommendation
   依赖一个跨 harness 不可比的成本字段。
3. holdout 反转主要来自 task split 的分布变化。selection 中 `55%`
   是 2015-2019 的 `supply_expansion_20260526` 任务，holdout 中 `90%`
   是 2022-2023 的 `canonical_history` 任务。`Kilo + GPT mainline` 在
   holdout 的 canonical history 任务上是 `8/9`，Codex 是 `4/9`。
4. non-scoreable cells 不是 top-2 反转的解释。selection 中 4 个
   non-scoreable cells 都发生在 `Kilo + GPT low-cost` 或
   `Kilo + Claude Sonnet`，top-2 两个 Agent 在 selection 和 holdout
   都是 `100%` scoreable。
5. 当前 artifacts 能支持“fresh holdout 必要，因为 selection 推荐可能由
   split 差异和成本破平共同驱动”这个解释。它们不能区分 stochasticity
   和真实 harness/repo 行为差异，因为每个 Agent/task 只有一次 paid run。

## Task Split 对比

| 维度 | Selection tasks | Holdout tasks | 诊断含义 |
| --- | ---: | ---: | --- |
| 任务数 | 20 | 10 | 满足 demo 最小 split。 |
| 来源 | 11 supply, 6 canonical history, 3 clean | 9 canonical history, 1 clean | holdout 明显更偏后期 canonical history。 |
| 年份范围 | 2015-2022 | 2022-2023 | selection median year 为 2018.5，holdout median year 为 2023。 |
| 主要模块 | tbutils 5, iterutils 3, cacheutils/funcutils/setutils 各 2 | timeutils/iterutils/dictutils 各 2 | holdout 引入 dictutils、ioutils 等 selection 未覆盖或弱覆盖模块。 |
| size bucket | s: 7, xs: 6, m: 3, l: 1, blank: 3 | s: 5, m: 2, xs: 2, blank: 1 | 大小分布相近，不是主要解释。 |
| changed files median | 2 | 2 | 文件数相近。 |
| test files median | 1 | 1 | oracle 文件数相近。 |
| changed lines median | 30 | 35 | 规模相近，holdout 略大。 |
| oracle files median | 1 | 1 | verifier 形状相近。 |
| allowed context ref | 15 PR, 5 issue | 9 PR, 1 issue | holdout 更偏 PR context。 |
| statement source | 17 certified, 3 sanitized public | 9 certified, 1 sanitized public | statement 形状相近。 |

这张表说明：反转不是由明显的 verifier 文件数、changed file 数或 size bucket
差异解释的。更可解释的差异是时间和来源：selection 更像旧任务和 supply
expansion 的混合，holdout 更像后期 canonical history 检查。

## Agent 总览

| Stage | Agent | Verified pass | Scoreable | Usage observed | Estimated cost | Median latency |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| selection | Codex + GPT mainline | 15/20 | 20/20 | 20/20 | 5.139240 | 101.048 |
| selection | Kilo + GPT mainline | 15/20 | 20/20 | 0/20 | 10.000000 | 48.297 |
| selection | Kilo + GPT low-cost | 13/20 | 18/20 | 0/20 | 10.000000 | 50.696 |
| selection | Kilo + Claude Sonnet | 14/20 | 18/20 | 0/20 | 10.000000 | 79.561 |
| holdout | Codex + GPT mainline | 5/10 | 10/10 | 10/10 | 3.287837 | 110.617 |
| holdout | Kilo + GPT mainline | 9/10 | 10/10 | 0/10 | 5.000000 | 47.921 |
| holdout | Kilo + GPT low-cost | 6/10 | 10/10 | 0/10 | 5.000000 | 52.400 |
| holdout | Kilo + Claude Sonnet | 8/10 | 10/10 | 0/10 | 5.000000 | 275.456 |

## 分来源表现

| Stage | Source | Tasks | Codex GPT | Kilo GPT | Kilo mini | Kilo Claude |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| selection | canonical_history | 6 | 5/6 | 4/6 | 4/6 | 4/6 |
| selection | clean_outcome_unseen | 3 | 3/3 | 3/3 | 3/3 | 3/3 |
| selection | supply_expansion_20260526 | 11 | 7/11 | 8/11 | 6/11 | 7/11 |
| holdout | canonical_history | 9 | 4/9 | 8/9 | 5/9 | 7/9 |
| holdout | clean_outcome_unseen | 1 | 1/1 | 1/1 | 1/1 | 1/1 |

关键点：selection 里 canonical_history 很少，而且 Codex 在那 6 个任务上
看起来更好；holdout 几乎全是 canonical_history，且是更晚的 2022-2023
任务，Kilo GPT mainline 在这些任务上明显领先。

## Per-Agent/Per-Task Outcome Matrix

Legend：`P` = verified pass，`F` = scoreable verified fail，`NS` =
non-scoreable cell。

| Stage | Task | Source | Year | Module | Size | Lines | Codex GPT | Kilo GPT | Kilo mini | Kilo Claude |
| --- | --- | --- | ---: | --- | --- | ---: | --- | --- | --- | --- |
| selection | boltons__supply_expansion_20260526__001 | supply | 2015 | tbutils | s | 74 | F | F | F | F |
| selection | boltons__supply_expansion_20260526__002 | supply | 2015 | tbutils | s | 24 | P | F | NS | P |
| selection | boltons__supply_expansion_20260526__003 | supply | 2015 | tbutils | xs | 16 | P | P | P | P |
| selection | boltons__supply_expansion_20260526__004 | supply | 2015 | tbutils | xs | 6 | F | P | F | NS |
| selection | boltons__supply_expansion_20260526__006 | supply | 2015 | cacheutils | xs | 12 | P | P | F | P |
| selection | boltons__supply_expansion_20260526__019 | supply | 2015 | iterutils | m | 86 | P | P | P | P |
| selection | boltons__supply_expansion_20260526__048 | supply | 2016 | strutils | m | 134 | F | P | P | F |
| selection | boltons__supply_expansion_20260526__066 | supply | 2017 | tbutils | xs | 11 | P | P | P | P |
| selection | boltons__supply_expansion_20260526__093 | supply | 2018 | timeutils | xs | 8 | P | P | P | P |
| selection | boltons__supply_expansion_20260526__095 | supply | 2018 | cacheutils | s | 31 | P | P | P | P |
| selection | boltons__supply_expansion_20260526__107 | supply | 2019 | mathutils | s | 49 | F | F | F | F |
| selection | boltons__clean_ext__001 | clean | 2020 | iterutils | unknown | unknown | P | P | P | P |
| selection | boltons__hist__006 | history | 2020 | funcutils | xs | 12 | F | F | F | NS |
| selection | boltons__hist__007 | history | 2020 | socketutils | s | 80 | P | P | P | P |
| selection | boltons__clean_ext__008 | clean | 2020 | setutils | unknown | unknown | P | P | P | P |
| selection | boltons__clean_ext__010 | clean | 2020 | setutils | unknown | unknown | P | P | P | P |
| selection | boltons__hist__011 | history | 2020 | iterutils | m | 126 | P | F | NS | F |
| selection | boltons__hist__013 | history | 2021 | funcutils | s | 30 | P | P | P | P |
| selection | boltons__hist__014 | history | 2021 | fileutils+jsonutils | l | 235 | P | P | P | P |
| selection | boltons__hist__017 | history | 2022 | urlutils | s | 22 | P | P | P | P |
| holdout | boltons__clean_ext__017 | clean | 2022 | timeutils | unknown | unknown | P | P | P | P |
| holdout | boltons__hist__019 | history | 2022 | ioutils | m | 176 | F | F | F | P |
| holdout | boltons__hist__020 | history | 2022 | timeutils | s | 22 | P | P | P | P |
| holdout | boltons__hist__022 | history | 2023 | iterutils | s | 78 | F | P | P | P |
| holdout | boltons__hist__023 | history | 2023 | tbutils | s | 35 | F | P | F | F |
| holdout | boltons__hist__024 | history | 2023 | dictutils | s | 32 | P | P | P | P |
| holdout | boltons__hist__025 | history | 2023 | funcutils | xs | 11 | P | P | P | P |
| holdout | boltons__hist__026 | history | 2023 | dictutils | xs | 17 | P | P | P | P |
| holdout | boltons__hist__027 | history | 2023 | cacheutils | s | 46 | F | P | F | P |
| holdout | boltons__hist__028 | history | 2023 | iterutils | m | 112 | F | P | F | F |

Top-2 反转集中在 holdout 的后期 history 任务上：

- `boltons__hist__022`：Codex fail，Kilo GPT pass；
- `boltons__hist__023`：Codex fail，Kilo GPT pass；
- `boltons__hist__027`：Codex fail，Kilo GPT pass；
- `boltons__hist__028`：Codex fail，Kilo GPT pass；
- `boltons__hist__019`：两者都 fail。

这不是单个异常任务造成的。Kilo GPT mainline 在 10 个 holdout 任务中只失
败了 `ioutils` 的 `boltons__hist__019`，而 Codex 失败了 5 个。

## Non-scoreable Cells

| Stage | Agent | Task | Failure category | Source | Module | Size | Lines |
| --- | --- | --- | --- | --- | --- | --- | ---: |
| selection | Kilo + GPT low-cost | boltons__supply_expansion_20260526__002 | exceeded budget or timeout | supply | tbutils | s | 24 |
| selection | Kilo + GPT low-cost | boltons__hist__011 | exceeded budget or timeout | history | iterutils | m | 126 |
| selection | Kilo + Claude Sonnet | boltons__supply_expansion_20260526__004 | no meaningful change | supply | tbutils | xs | 6 |
| selection | Kilo + Claude Sonnet | boltons__hist__006 | no meaningful change | history | funcutils | xs | 12 |

这些 non-scoreable cells 没有发生在推荐 Agent 或 nearest competitor 上，
因此不能解释 Codex/Kilo GPT mainline 的 selection tie 或 holdout reversal。

## Cost Usage 覆盖审计

| Stage | Runs | Usage observed | Codex observed | Kilo GPT observed | Kilo mini observed | Kilo Claude observed |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| smoke | 4 | 1 | 1/1 | 0/1 | 0/1 | 0/1 |
| selection | 80 | 20 | 20/20 | 0/20 | 0/20 | 0/20 |
| holdout | 40 | 10 | 10/10 | 0/10 | 0/10 | 0/10 |

主 scored run 的 observed usage coverage 是 `30/120 = 25%`。包含 smoke
后是 `31/124 = 25%`。覆盖缺口不是随机缺失，而是 harness 相关：

- Codex + GPT mainline：`31/31` usage observed；
- 所有 Kilo 组合：`0/93` usage observed；
- Kilo 的 cost_method 全部是 `conservative_per_cell_estimate`；
- Codex 的 cost_method 全部是 `observed_token_estimate`。

从现有 sanitized ledgers 无法恢复 Kilo token usage，因为 ledger 中没有
Kilo token counts，只保留了 `$0.5` conservative estimate。若不读取 raw
transcripts，就只能把这些成本继续标为 estimate。下一轮要么让 Kilo adapter
产出 normalized usage record，要么在 recommendation rule 中禁止用这个
字段破平。

建议的 normalized cost schema：

| 字段 | 含义 |
| --- | --- |
| `cost_observation_kind` | `observed_tokens`、`gateway_billed_cost`、`conservative_estimate`、`missing` |
| `input_tokens` | provider/harness reported input tokens，缺失为 null |
| `cached_input_tokens` | provider/harness reported cached input tokens，缺失为 null |
| `output_tokens` | provider/harness reported output tokens，缺失为 null |
| `estimated_cost_usd` | 根据冻结 pricing table 计算的估算值，必须标记方法 |
| `billed_cost_usd` | 若 gateway 提供真实账单成本则填写，否则 null |
| `usage_source` | `codex_usage_line`、`kilo_usage_json`、`gateway_ledger`、`static_estimate` 等 |

## 推荐规则敏感性

| Scenario | Selection recommendation | 原因 |
| --- | --- | --- |
| 原始锁定规则 | Codex + GPT mainline | Codex 与 Kilo GPT mainline 质量同为 15/20，cost per solved 较低。 |
| 移除 cost tie-breaker，继续用 latency 破平 | Kilo + GPT mainline | top-2 质量、scoreable、hidden failure 全同，Kilo median latency 更低。 |
| 所有 Agent 都用统一 `$0.5` per-cell cost | Kilo + GPT mainline | top-2 cost per solved 也打平，下一 tie-breaker 是 latency。 |
| 只允许 observed cost 参与 production-value view | 无法给单一 production-value winner | 只有 Codex 有 observed usage，Kilo 成本不可比。 |
| Kilo GPT mainline 实际 per-task cost < `$0.256962` | Kilo 可在 cost tie-breaker 中不输给 Codex | selection 中 Kilo 15 solve、20 run；`20*x/15 < 0.34261597` 时 Kilo 更便宜。 |

结论：成本口径直接影响 selection recommendation。质量视图本应报告
`Codex + GPT mainline` 和 `Kilo + GPT mainline` 在 selection 上打平；
production-value view 在 usage coverage 不对称时不应给出单一成本赢家。
holdout 的 `9/10` 对 `5/10` 质量差异不依赖成本字段。

## Recommendation Rule 修订建议

下一次 paid run 前建议修订规则：

1. primary quality view 只按 verified solve rate、scoreable/replay policy
   failures 和预声明的质量类 failure 破平。成本和 latency 作为并列说明，
   不再隐藏在质量推荐中。
2. production-value view 只有在每个候选 Agent 的 usage coverage 达到同一
   阈值后才允许给单一赢家。建议阈值为每个候选至少 `95%` observed or
   gateway-billed usage；否则报告 observed cost、estimated cost 和 billed
   cost 三列，并把 winner 标为 cost-inconclusive。
3. 若 selection 质量打平且 cost-inconclusive，锁定 top-2 repeatability
   check，而不是用估算成本强行推荐单一 Agent。

## Top-2 Repeatability Check 建议

建议执行，但不要扩展候选集，也不要同时进入第二仓库。

当前 artifacts 已足够解释“为什么需要 fresh holdout”，但不足以判断 holdout
反转是否稳定。最小可执行 repeat 是：

- 只重复 `Codex + GPT mainline` 和 `Kilo + GPT mainline`；
- 只重复同一批 10 个 holdout tasks；
- task text、visible check、hidden verifier、endpoint policy、timeout 和
  outer retry policy 不变；
- 不调 prompt、tools、test policy 或 workspace policy；
- 报告 task-level stability，而不是把 repeat 解释成全局 Agent 排名。

执行前必须重新确认：

- worker shell 中 `LLM_BASE_URL` 和 `LLM_API_KEY` 存在，且不回退到其他
  provider-specific variables；
- smoke/gate 仍通过，尤其是 endpoint proof 和 secret isolation；
- raw prompts、raw completions、transcripts、solver/verifier workspaces 留在
  ignored raw paths；
- stop conditions 包含 endpoint policy failure、scoreable rate 不达标、
  hidden verifier leakage、需要 raw transcripts 才能解释结果等。

成本修复不是这个 repeat 的硬阻塞，因为 repeat 的核心问题是 pass/fail
稳定性。但如果继续报告 production-value view，就必须把 Kilo 成本标为
estimate 或先修 adapter usage 输出。

## 第二仓库 Gate 建议

不建议现在进入第二仓库 gate。原因：

- 当前 boltons 结果已经暴露 selection/holdout 反转和成本破平脆弱性；
- top-2 repeatability 还没有回答随机性问题；
- Kilo usage coverage 仍为 0，第二仓库 paid run 会放大同一个成本口径问题；
- follow-up plan 明确要求不要跳到更大 paid validation 或更多矩阵。

第二仓库 gate 可以在 top-2 repeat 或 cost repair 至少完成一个之后再做。
届时 gate 应只回答一个具体问题：第二个目标仓库是否也会出现 plausible
selection recommendation 不能通过 fresh holdout 的情况。

## 可以讲和不能讲

可以讲：

- Barcarolle 在 `mahmoud/boltons` 上完成了真实 Coding Agent selection demo；
- selection tasks 上 `Codex + GPT mainline` 和 `Kilo + GPT mainline` 质量打平；
- 原始 recommendation 依赖成本 tie-breaker，而成本 coverage 对 Codex/Kilo
  不对称；
- fresh holdout contradicted selection recommendation，说明目标仓库 Agent
  selection 需要 holdout check；
- task split 差异，尤其是旧 supply/早期 history 与后期 canonical history
  的差异，是当前最可解释的反转原因。

不能讲：

- 不能说 Kilo 或 Codex 在一般意义上更好；
- 不能说 learned selector、Agent tuning 或跨仓库 predictive validity 已被证明；
- 不能把 estimated cost 说成真实账单成本；
- 不能说反转一定不是随机性，因为当前没有 repeat；
- 不能说第二仓库 paid run 已经通过 gate。
