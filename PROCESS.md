# Barcarolle Cross-Session Handoff

Last updated: 2026-07-28.

Current ledger: `docs/research-improvement-backlog.md`. Completed study:
`docs/experiments/2026-07-28-multi-repository-public-study.md`. Frozen prior
ledger: `docs/research-improvement-backlog-2026-07-27.md`.

## Preserve

- Keep Records, Task Pool, Verification, Workspace, Result Store, Selection,
  Reporting, and Runner direct.
- Runtime is one user repository, one local Task Pool, and one local Selection.
  Multiple repositories are offline research/training evidence units only.
- A policy fitted elsewhere may select only eligible history from the target
  repository. Never construct a mixed meta-pool.
- Generators end at a prepared package; user pools open read-only. Keep Task
  Pools and Results independent with exact reuse identity.
- User-supplied time, dependency cluster, and stratum require lineage.
  Historical projection remains counterfactual.
- Keep full history as the primary baseline and equal-budget random Selection
  as sampling-landscape calibration.
- Add no registry, embedding service, trainer service, scheduler, or core
  multi-repository path without a measured caller and a nominated algorithm.

## Current Evidence

The no-paid-call public study uses 500 SWE-bench Verified Tasks, three frozen
public Agent result vectors, seven wide repositories, three deep repositories,
and 68 repository-local Origins. Differences below are candidate MAE minus
full-history MAE; negative is favorable.

| Route | Wide macro difference | Decision |
| --- | ---: | --- |
| Recency | `+0.0189` | Retire |
| Difficulty coverage | `+0.0398` | Retire |
| History match | `-0.0064` | Compression control only |
| Cross-repository drift | `+0.0016` | Reject |
| Local trend | `-0.0064` | Chose zero trend in every fold |
| ALG-007 centroid | `+0.0015` | Retire on this source and panel |
| ALG-007 facility | `+0.0377` | Retire |
| Hindsight support | `-0.1589` | Representable, not identifiable yet |

History match is better than 93.75% of 20,000 equal-budget random draws, but it
misses the `-0.01` development gate, its interval crosses zero, and its deep
effect is only `-0.0014`. No route warrants independent or paid validation.
All evidence is counterfactual and panel-conditional; no Selector is a Runner
default.

## Current State

The experiment layer now has exact source and outcome identity, separate
wide/deep portfolios, repository-first aggregation, repository-cluster
bootstrap intervals, leave-one-cluster-out sensitivity, random calibration,
outer repository folds, local semantic replay, compact digests, and tests.
Core runtime did not change.

Infrastructure needed before another paid selector study is ready. The blocker
is a scientifically credible candidate, not a platform gap. This sprint made
zero paid API calls and zero coding-Agent calls.

## Reopen

A new mechanism may enter opened-data development only when it is motivated
without another parameter search over the observed outcomes. Before paid work
it must achieve:

1. wide difference at most `-0.01`;
2. negative direction in at least five of seven repositories;
3. every leave-one-repository-out difference negative;
4. negative deep direction;
5. better than at least 75% of random draws;
6. improvement over history match when forecasting Agent outcomes.

Then freeze independent source/panel identity, candidate code and parameters,
Origin schedule, budget, missing-cell policy, exclusions, and endpoint before
opening outcomes. Estimate repository count from that route's blinded pilot;
do not reuse nominal Origin counts or the failed-route range.

Paid evidence requires new authority and `OPENAI_BASE_URL` plus
`OPENAI_API_KEY`. Add RI-160's certification checkpoint only before the next
comparable pool, and RI-163 only before another Pylint campaign. Reopen checkout
caching above 5% measured wall time and bounded Agent parallelism only with
exact attribution, one writer, and campaign authority.
