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
- Uniform random ten-Task subsets locate a method in the sampling space.
- The existing future-open Oracle measures the best attainable subset and is
  not an algorithm.
- The best previously measured method under the same input rules is the
  incumbent when claiming a new best method.

## Current Evidence

On Full:

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.078554` | `0.062579` |
| Random mean MAE | `0.086606` | `0.073798` |
| Oracle MAE | `0.013093` | `0.007353` |

Full has enough variation and Selection headroom for algorithm development.
Its block-order diagnostic is `p=0.126437` at H5. That result closed one
conditional ALG-016U plan; it is not a general gate on further algorithms.
ALG-016U still has no Full MAE.

The old plan, result, and summary remain unchanged. New work uses a separate
outcome-open development plan and cannot retroactively change the old gate.

## Next Action

Freeze and run a bounded Full development portfolio. At minimum compare
ordinary recency, stationary response matching, adaptive expert response
matching, and ALG-016U at H5 and H10. Add a task-content family only as a
separate mechanism, not as parameter rescue.

Report direct MAE, candidate minus Full, random position, repository and Agent
directions, and uncertainty. Development-set results decide what to keep or
discard. A later data boundary is needed only after a candidate exists and we
want to check that the choice was not specific to Full.

No paid Agent run, Generator work, generic source framework, or core-schema
change is needed.

Engineering triggers remain unchanged: optimize checkout only after it exceeds
5% of measured campaign time; add Agent parallelism only for a measured
campaign need with exact attribution and one Result writer.
