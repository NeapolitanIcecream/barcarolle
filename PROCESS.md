# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

## Research Question

For one target Agent and one repository, choose ten historical Tasks so that
the Agent's pass rate on those ten Tasks is close to its pass rate on the next
Tasks.

At each rolling Origin, compute the target Agent's absolute selected-versus-
future pass-rate error before aggregation. H5 and H10 mean the next five and
ten Tasks. Direct future pass-rate MAE is primary; surrogate and reliability
metrics remain diagnostic.

The deployment unit is one Agent and one repository. The repository-equal
headline is the average loss of the fixed research panel, not a pass-rate
estimate for one deployment cell.

## Current Data

SWE-bench Full is the active, outcome-open development set:

- 2,294 Tasks and eleven fixed Agent result vectors;
- ten repositories with enough history;
- 408 H5 Origins and 201 H10 Origins;
- Selection budget ten.

H20 and H40 are reliability views only. Existing candidates were not reranked
on them.

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
  p-value or evidence of temporal prediction.
- Future-open Oracles measure capacity. They are not algorithms and do not
  establish forecastability.
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
than most draws from the frozen random policy, but that fact does not establish
future-predictive structure.

The completed estimand audit found:

- 70/110 Agent-by-repository cells have pass rate below `0.10`; median
  prevalence is `0.03646`;
- zero future blocks are `68.19%` at H5 and `57.81%` at H10;
- the exact descriptive decomposition assigns `50.89%` of H5 and `67.68%` of
  H10 realized variation to fitted Agent, repository, and interaction sample
  means; these are not population variance or reliability estimates;
- within-cell block variance follows `1/H` with `R²=0.99886` on the common
  eight-repository horizon frame;
- each candidate improves the six-Agent RAG group mean and harms the
  five-Agent other-group mean at both horizons;
- same-future reference-to-target residual correlations are `0.392/0.437`,
  while previous-reference-to-next-target correlations are `0.176/0.177`;
- an exploratory repository-shared block permutation is positive only at H5
  (`0.001499`; H10 `0.211894`); the v2 contract records that this null was
  corrected after initial output was visible;
- the reference Oracle helps/harms/ties `71/17/22` joint cells at H5 and
  `68/20/22` at H10.

The metric implementation computes absolute error in the correct order. The
claim regression was interpreting one realized panel average and favorable
marginals as expected deployment evidence. Full beats zero and previous-block
controls on the panel average, which is consistent with useful local
prevalence; Selection has not yet shown that it predicts future deviations
from Full.

Evidence:

- `docs/experiments/2026-07-30-swe-bench-full-estimand-reliability-audit.md`;
- `examples/swe_bench_full_estimand_audit/evidence/summary.json`.

## Next Action

Freeze one bounded history-only replay of the next other-Agent Full residual:

1. compare only Full, stationary response matching, and ALG-015U;
2. report forecast, materialization, and final target-Agent direct-MAE losses;
3. retain all Agent-by-repository paired cells and repository leave-one-out
   directions;
4. report whether a gain is confined to the post-hoc RAG subgroup; that
   narrows the claim and blocks broad-Agent nomination rather than erasing the
   primary finite-panel result;
5. stop response-model work if no stable direct-MAE increment remains, then
   open one frozen Task-content or repository-process route.

Seek a separate confirmation boundary only after a candidate beats Full.

No paid Agent run, Generator work, generic source framework, or core-schema
change is needed.

Engineering triggers remain unchanged: optimize checkout only after it exceeds
5% of measured campaign time; add Agent parallelism only for a measured
campaign need with exact attribution and one Result writer.
