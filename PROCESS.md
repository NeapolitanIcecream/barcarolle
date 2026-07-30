# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

## Research Question

For one target Agent and one repository, choose ten historical Tasks so that
the Agent's pass rate on those ten Tasks is close to its pass rate on the next
Tasks.

The primary experiment repeats this at rolling Origins:

1. order Tasks inside each repository;
2. expose only the Origin's history to Selection;
3. select exactly ten history Tasks;
4. measure the absolute difference between the target Agent's selected and
   future pass rates;
5. average target Agents and Origins inside each repository, then average
   repositories equally.

H5 and H10 mean the next five and next ten Tasks. Direct future pass-rate MAE
is the outcome. Brier, AUC, embedding distance, forecast loss, and temporal
nulls may explain a mechanism but cannot replace MAE.

## Current Data

SWE-bench Full is the active, outcome-open development set:

- 2,294 Tasks and eleven fixed Agent result vectors;
- ten repositories with enough history;
- 408 H5 Origins and 201 H10 Origins;
- Selection budget ten.

Task order comes from pull-request `created_at`. Agent outcomes may be
collected or imported later; their storage timestamp is not an input to this
offline estimator.

For the primary before-testing-an-Agent experiment, each target Agent gets its
own Selection. Membership may use Task data and the other ten Agents'
historical outcomes, but not the target Agent's outcomes or any future Task or
outcome. A separate cached-result experiment may use the target Agent's
historical outcomes and must be reported separately.

## Baselines

- Full history is the no-Selection baseline.
- The frozen random policy samples one ten-Task subset per Origin and shares it
  across target Agents. Its distribution is a calibration reference, not a
  p-value or every possible random policy.
- The existing future-open Oracle measures the best attainable subset and is
  not an algorithm.
- The best previously measured method under the same input rules is the
  incumbent when claiming a new best method.

## Current Evidence

The frozen Full development wave compared recency, stationary response
matching, ALG-010, ALG-015U, and ALG-016U. Two complete runs were identical.

| Method | H5 MAE | H10 MAE |
| --- | ---: | ---: |
| Full history | `0.078554` | `0.062579` |
| Best ten-Task candidate | ALG-015U `0.078673` | stationary `0.064299` |
| Reference-future Oracle | `0.065864` | `0.052649` |
| Target-future Oracle | `0.004013` | `0.002395` |

No implementable candidate beat Full. The candidates were nevertheless better
than most random ten-Task subsets and selected materially different
memberships.

The future-open reference Oracle hides the target Agent but knows the other ten
Agents' next-H response rates. It beat Full by `0.012690` at H5 and `0.009930`
at H10, helped eight of ten repositories at both horizons, and had
repository-bootstrap intervals below zero. The history pool, cross-Agent
response signal, and exact matcher therefore have useful capacity. Within the
tested response-matching family, the main unresolved component is forecasting
the next reference-response regime and turning an uncertain forecast into a
robust budget-ten action. The reference Oracle recovers only about 17% of the
target-future Oracle headroom, so this is not a claim that response forecasting
is the project's only possible route.

The earlier H5 block-order result `p=0.126437` remains a diagnostic that closed
one old conditional plan; it is not a gate on this development evidence.

## Next Action

First decompose each existing response method into forecast error,
materialization error, realized reference mismatch, and final target-Agent MAE.
Then freeze at most three new directions: repository-aware empirical-Bayes
shrinkage, a rank-one shared-difficulty forecast, and a reliability-shrunk or
minimax budget-ten action. Partial pooling learns from multiple research
repositories; every runtime Origin and Selection remains inside one target
repository.

Forecast and materialization losses are explanatory only; they cannot replace
direct MAE. If historical responses show no stable forecastable increment,
switch one bounded wave to a task-only semantic or repository-process route.
Do not reopen source admission, Result timestamps, disjoint development Agent
identities, or Task Pool capacity without new evidence. Seek a separate
confirmation boundary only after a candidate beats Full on development.

No paid Agent run, Generator work, generic source framework, or core-schema
change is needed.

Engineering triggers remain unchanged: optimize checkout only after it exceeds
5% of measured campaign time; add Agent parallelism only for a measured
campaign need with exact attribution and one Result writer.
