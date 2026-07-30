# Research Ledger

Last reviewed: 2026-07-30.

Status: active reference-response forecasting research on SWE-bench Full.

`PROCESS.md` is the short handoff. Completed history is preserved in
[`research-improvement-backlog-2026-07-30.md`](research-improvement-backlog-2026-07-30.md)
and the earlier
[`research-improvement-backlog-2026-07-27.md`](research-improvement-backlog-2026-07-27.md).
Do not amend archived evidence.

## Goal

For a target Agent and repository, select ten historical Tasks whose measured
pass rate is closer than Full history to the Agent's pass rate on the next
Tasks.

The primary score is direct future pass-rate MAE. A lower value is better.
Full history is the no-Selection baseline. Uniform random ten-Task subsets
show where an algorithm sits in the sampling space. A future-open Oracle shows
how much improvement the Task Pool permits; it is not an algorithm.

## Experiment Contract

At every rolling Origin:

- history and future Tasks come from one repository;
- H5 and H10 mean the next five and next ten Tasks;
- Selection contains exactly ten history Tasks;
- the target Agent's future outcomes are used only to score the Selection;
- the primary before-testing-an-Agent lane may use Task data and the other
  Agents' historical outcomes, but not the target Agent's outcome column;
- candidates, Full, and random use the same Tasks, Agent identities, Checks,
  outcomes, Origins, and aggregation;
- target Agents and Origins are averaged inside each repository, then
  repositories are averaged equally.

Task order is the time variable. Agent outcomes can be generated or imported
later and then partitioned by Task order. Their storage or import timestamp is
not part of the offline algorithm.

A cached-result method that reads the target Agent's historical outcomes is a
useful but different case. Report it separately; do not compare its additional
information with a before-testing method without saying so.

## Active Data

SWE-bench Full is an outcome-open development set:

- 2,294 Tasks;
- eleven fixed Agent result vectors;
- ten eligible repositories;
- 408 H5 Origins and 201 H10 Origins;
- budget ten.

The source is suitable for repeated algorithm development. Because its outcomes
have already influenced research decisions, its best observed method will
later need a separate check before we claim the choice generalizes beyond
Full. That later check may hold out later Tasks, repositories, Agents, or a
different source according to the claim being made. New Agent identities are
required only for a claim about transfer to a previously unseen Agent.

## Current Measurements

| Direct MAE on SWE-bench Full | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.078554` | `0.062579` |
| Ordinary recency | `0.083039` | `0.069464` |
| Stationary response match | `0.081205` | `0.064299` |
| ALG-010 | `0.082618` | `0.069371` |
| ALG-015U | `0.078673` | `0.067178` |
| ALG-016U | `0.080082` | `0.065610` |
| Reference-future Oracle | `0.065864` | `0.052649` |
| Target-future Oracle | `0.004013` | `0.002395` |

No frozen candidate beat Full. ALG-015U was nearly tied at H5
(`+0.000119`); stationary response matching was the best ten-Task method at
H10 (`+0.001719`). All candidates remained better than most random ten-Task
subsets, but Full itself was better than `99.97%` and `99.975%` of the frozen
random draws. Those midranks describe the frozen policy that shares one random
membership across target Agents at an Origin; they are calibration, not
p-values.

This result is reproduced byte-for-byte. The candidate memberships are
materially different, and no candidate is favorable in more than four of ten
repositories.

The post-result reference-future Oracle hides the target Agent, opens the other
ten Agents' next-H response rates, and uses the same exact matcher. It beats
Full by `0.012690` at H5 and `0.009930` at H10, with a repository-bootstrap
interval below zero and eight favorable repositories at both horizons. The
target-future Oracle is near zero.

Within the tested response-matching family, the evidence locates the current
failure in forecasting the next reference-Agent response regime and making a
budget-ten action robust to forecast error. It does not support reopening Task
Pool capacity or the existence of cross-Agent signal as the primary problem.
The reference Oracle recovers only about 17% of target-Oracle headroom, so it
does not establish response forecasting as the project's only route or exact
L1 as the optimal action under forecast uncertainty. It also does not prove
that realized future reference rates are predictable from history.

Evidence:

- [`experiments/2026-07-30-swe-bench-full-direct-mae-development.md`](experiments/2026-07-30-swe-bench-full-direct-mae-development.md);
- `examples/swe_bench_full_development/evidence/summary.json`;
- `examples/swe_bench_full_development/evidence/diagnostic-summary.json`.

## Corrections Carried Forward

1. Result storage or import time is not an algorithm-data requirement for
   offline rolling-origin research. It matters only when auditing what a live
   system knew at an actual past decision.
2. There is no requirement for a “clean development Agent panel.” Development
   data is open by definition.
3. Reusing an Agent identity is correct when the claim concerns that same
   Agent on future Tasks. Disjoint Agent identities are needed only for a
   stronger new-Agent transfer claim.
4. Full and Verified contain overlapping Tasks and cannot provide an
   independent unseen-Task check of each other. This does not limit Full's use
   for development.
5. A candidate-independent temporal null is a diagnostic, not a substitute for
   measuring candidate pass-rate MAE.

## Active Approach Registry

| Route | State | Reason |
| --- | --- | --- |
| Ordinary recency | control retained | Simple temporal comparison; worse than Full |
| Stationary response matching | control retained | Best H10 ten-Task method; still worse than Full |
| ALG-010 | retired unchanged on this frame | Worse than Full at both horizons |
| ALG-015U | retain only as H5 incumbent | Nearly tied at H5, clear reversal at H10 |
| ALG-016U | retired unchanged on this frame | Worse than Full at both horizons |
| Exact response matcher | retain as control | It beats Full with a perfect reference forecast; noisy-forecast robustness remains open |
| Cached-target methods | separate case | Use extra target-Agent information |
| Task-content methods | conditional orthogonal route | Open one frozen wave if response history lacks stable predictable gain |

## Next Cycle

1. For stationary, ALG-015U, and ALG-016U, report forecast-to-future response
   L1, selected-to-forecast L1, selected-to-future response L1,
   reference-Oracle regret, and target-Agent direct MAE.
2. Add a predeclared noise-to-regret curve around the reference Oracle to
   measure how much forecast error budget-ten Selection can tolerate.
3. Explain whether the loss comes from repository shift, Agent dependence,
   horizon aggregation, or forecast-to-action quantization.
4. If response history has predictable gain, freeze at most three directions:
   repository-aware empirical-Bayes shrinkage, a rank-one shared-difficulty
   forecast, and reliability-shrunk or minimax materialization.
5. If it does not, stop stacking response models and run one frozen task-only
   semantic or repository-process route.
6. Require lower direct MAE than Full at both H5 and H10 before retaining a
   candidate, then seek an independent data boundary.

Before the next evidence run, bind the complete execution commit or tree rather
than only selected direct implementation files. Also add an end-to-end
`materialize_portfolio` regression that perturbs one target Agent's entire
outcome column and requires that Agent's memberships to remain unchanged.

Partial pooling is a training/research method across repositories. It does not
change the product contract: each Origin and Selection remains inside one
target repository.

No paid Agent call, Generator development, generic source adapter, trainer,
registry, scheduler, or core-schema change is authorized or needed for this
cycle.

## Engineering Triggers

- Optimize checkout only when checkout plus cleanup exceeds 5% of measured
  campaign time.
- Add Agent parallelism only for a measured campaign need, with exact
  attribution and one Result writer.
- Add source-specific certification only for a concrete runnable campaign.
- Structural audit scores alone do not justify splitting modules.
