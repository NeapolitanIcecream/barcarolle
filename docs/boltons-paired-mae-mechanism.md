# Boltons paired-MAE mechanism experiment

Date: 2026-07-15

## Scope Clarification

This five-Task H1 fixture is not the earlier Boltons 20-history-to-H10 study.
Do not use its zero held-out MAE to compare Task Pool prediction regimes. The
older H10 study reports full-visible-history MAE `0.136111` under scoreable
rates and `0.137500` under the scheduled denominator. The provenance and the
Multi-SWE comparison are recorded in
[`experiments/2026-07-30-multi-swe-failure-region.md`](experiments/2026-07-30-multi-swe-failure-region.md).

## Outcome

The two-stage Adaptive path completed without retries. All ten paid
Agent/Task/Check executions were scoreable: nine passed and one failed its
hidden Check. The rule mixture was fitted only from origin 1 evidence and its
origin 2 selection was frozen before either origin 2 outcome was executed.

On origin 2, the rule mixture's future pass-rate MAE was `0.00`. It tied the
coverage and random baselines and was lower than recency's `0.25`. This proves
the rolling-origin, paired-MAE, and fit-then-freeze mechanism works on the
fixture. It does not show that the mixture is better than all baselines or that
Barcarolle has real-world predictive validity.

## Protocol

- Target: five certified boltons tasks at commit
  `979fa9b613fa8c0a455ae16ea6f2ec91c11ecafe`.
- Agent configurations: `gpt-5.4-mini` with `low` and `high` reasoning.
- Selection budget: two Task/Check pairs.
- Baselines: coverage, random with seed 5, and recency.
- Origin 1: history tasks 1-3; task 4 is the future holdout.
- Origin 2: history tasks 1-4; task 5 is the future holdout.
- Execution order: freeze both baseline sets; execute the eight cells needed by
  origin 1; fit the rule mixture; freeze its origin 2 selection; execute the
  final two cells; evaluate from exact Results only.
- Paid execution code: Git commit
  `34e8bb0f0ba12c784ed634b46e325506dd53c029`.
- Provider retries and Codex subagents were disabled. Each CLI invocation could
  execute at most one paid cell.

## Agent results

| Task | Low | High |
| --- | ---: | ---: |
| `chunked_iter` count | pass | pass |
| positive `windowed` size | pass | pass |
| `parse_qsl` blank values | fail | pass |
| `OrderedMultiDict.update` keywords | pass | pass |
| `LRI`/`LRU.update` keywords | pass | pass |

| Configuration | Passes | Mean workspace latency | Uncached input | Cached input | Output | Estimated cost |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Low | 4/5 | 28.85 s | 67,443 | 361,984 | 8,456 | $0.11578305 |
| High | 5/5 | 47.89 s | 110,824 | 835,712 | 20,195 | $0.23667390 |
| Total | 9/10 | — | 178,267 | 1,197,696 | 28,651 | $0.35245695 |

In this five-task fixture, high reasoning produced one additional pass, used
about 2.04 times the estimated cost, and took about 1.66 times the mean
workspace latency. The sample is too small to generalize those ratios.

## Paired MAE

| Origin | Coverage | Random | Recency | Rule mixture |
| --- | ---: | ---: | ---: | ---: |
| Origin 1 training evidence | 0.25 | 0.00 | 0.25 | not fitted |
| Origin 2 held-out mechanism check | 0.00 | 0.00 | 0.25 | 0.00 |

Origin 1 produced mixture weights `coverage=0.75`, `random=1.00`, and
`recency=0.75`. The origin 2 mixture selection happened to match coverage's
selected pair. Its zero MAE therefore represents a tie with two baselines, not
an independent improvement over the best baseline.

## Evidence and cost integrity

- The Result Store contains ten distinct execution identities under one pricing
  configuration. The resource ledger contains ten reservations and ten matched
  completions; all are `completed` and `scoreable`.
- The resource ledger now uses the same examples-layer single-writer event
  persistence as the Pylint pilot. A temporary replay preserved the ten calls,
  `$0.35245695` spent cost, and remaining budget; the historical source files
  were not changed.
- Every raw Codex stream contains exactly one `turn.completed`, no
  `turn.failed` or error event, and no subagent or collaboration event.
- Raw completion usage, normalized Result usage, ledger usage, artifact
  digests, and recomputed cost agree for all ten cells.
- Reasoning tokens were treated as part of output tokens and were not priced a
  second time.
- Cost uses the [OpenAI standard API price for GPT-5.4 mini](https://developers.openai.com/api/docs/models/gpt-5.4-mini):
  $0.75/M uncached input, $0.075/M cached input, and $4.50/M output. This is an
  estimate; the authorized gateway does not publish an invoice rate.

## Claim boundary and follow-up

The tasks are hand-authored, their availability times are controlled, all use
one repository commit, and each origin has only one future task. The endpoint
also exposed the `gpt-5.4-mini` alias rather than an immutable snapshot ID.
These facts prevent a real predictive-validity claim.

The canary also showed that adapter v1 captured generated `.pytest_cache` and
`__pycache__` files. The paid Results remain unchanged and auditable under v1.
Commit `c052addc` excludes only those observed Python runtime caches and updates
the adapter identity to v2 for future runs.

The next predictive experiment should use a larger Task Pool with real task and
Check availability times, more than one future task per origin, and the same
fit-before-holdout discipline. Until then, this experiment is mechanism
evidence, not evidence that Adaptive selection improves future estimates in
practice.
