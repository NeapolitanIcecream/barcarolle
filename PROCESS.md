# Barcarolle Cross-Session Handoff

Last updated: 2026-07-28.

Current ledger: `docs/research-improvement-backlog.md`. Current reports:
`docs/experiments/2026-07-28-multi-repository-public-study.md` and
`docs/experiments/2026-07-28-theory-driven-selector-sprint.md`, followed by
`docs/experiments/2026-07-28-budget-horizon-sensitivity.md`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local Selection.
  Multiple repositories are offline research/training evidence units only.
- Generators end at a prepared package; user pools open read-only. Task Pools
  and Agent Results remain independent and reuse only under exact identity.
- A rolling-origin fit may consume only evidence available by the target
  Origin cutoff. Label complete other-repository histories retrospective.
- Keep full history as the primary baseline and equal-budget random Selection
  as sampling-landscape calibration.
- Keep repository-first aggregation, wide/deep views, temporal-null controls,
  and leave-one-Agent rematerialization.
- Keep absolute Selection budget and explicit future `TimeRange` as the product
  contracts. Research also reports compression fraction, future Task count,
  and realized calendar span.
- Distinguish source-time-cutoff-safe counterfactual evidence from strict
  historical replay and strict prospective evidence.
- Add no registry, embedding service, trainer service, scheduler, or
  multi-repository Runner without a nominated concrete caller.

## Current Evidence

The zero-paid-call program uses 500 SWE-bench Verified Tasks, seven wide
repositories, three deep repositories, 68 local Origins, 11 opened development
Agents, and six project-sealed holdout Agents. Negative values favor Selection.

| Route | Wide difference | Decisive result |
| --- | ---: | --- |
| History match, original 3 Agents | `-0.00637` | Compression control only; becomes `+0.00349` on the 11-Agent panel. |
| Joint response Markov | `-0.01911` | Retired: null `0.100`, leave-one-Agent 1/3 favorable, sealed replication `+0.00031`. |
| Cutoff-aware difficulty Markov | `-0.00888` | 97.78th random percentile, but 3/7 repositories favorable, deep `+0.00920`, leave-one-Agent 6/11 favorable. |
| Adaptive prequential difficulty | `-0.00235` | Null `0.194`, 3/7 favorable, deep `+0.00927`; current-pool temporal search closed. |
| Budget–horizon audit | Best `-0.00379` | Frozen budgets 5/10/15 × horizons 3/5/10; no passing cell or stable region; best cell deep `+0.02550`, leave-one-Agent 3/11 favorable. |
| Hindsight support | `-0.15890` | Subsets can represent future outcomes; safe identification remains unsolved. |

The original cross-repository Markov used 47.37% later-created training Tasks
and is retrospective only. Later difficulty fits enforce source-time cutoffs,
but their public labels are projected and remain counterfactual. A post-result,
outcome-free supply audit found a median of 11 completed training Origins from
a median of two other repositories; four target Origins have none and 35/68
have fewer than three training repositories.

No Selector is a Runner default. No candidate permits opening the six-Agent
holdout or making paid calls.

## Current State

The direct experiment layer now covers exact current and legacy official-result
schemas, metadata-only Agent allocation, source-time cutoffs, repository
uncertainty, random calibration, temporal nulls, sealed-panel replication,
leave-one-Agent transfer, and common-cohort budget–horizon audits. Core runtime
did not change.

Infrastructure is ready for the next fixed study. The blockers are a
scientifically credible mechanism and more source-time-eligible Origin supply,
not API availability or platform work.

## Reopen

A temporal candidate must be derived independently of the opened results or
use a larger source-time-eligible Origin portfolio. Do not tune another budget,
horizon, threshold, or state rule on the current panel. Before opening the
six-Agent holdout it must achieve:

1. wide difference at most `-0.01`;
2. at least five of seven repositories favorable;
3. every wide leave-one-repository-out result negative;
4. negative deep direction;
5. at least 75th random percentile and improvement over frozen controls;
6. temporal-null rate below `0.10`;
7. leave-one-Agent macro negative with at least 8/11 Agents favorable.

Paid evidence then requires explicit authority and `OPENAI_BASE_URL` plus
`OPENAI_API_KEY`. Fixed-universe reconstruction is a separate estimand: it may
use the 11 opened Agents when prioritized, but must not consume the six-Agent
temporal holdout or support a future-Task claim.

Reopen checkout caching only above 5% measured wall time, bounded Agent
parallelism only with exact attribution and one writer, RI-160 only before a
new comparable pool, and RI-163 only before another Pylint campaign.
