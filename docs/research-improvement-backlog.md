# Research Ledger

Last reviewed: 2026-07-30.

Status: active algorithm development on SWE-bench Full.

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

| SWE-bench Full | H5 | H10 |
| --- | ---: | ---: |
| Full-history MAE | `0.078554` | `0.062579` |
| Always-zero MAE | `0.098671` | `0.099916` |
| Random mean MAE | `0.086606` | `0.073798` |
| Oracle MAE | `0.013093` | `0.007353` |
| Full minus Oracle | `0.065460` | `0.055226` |

Full is better than always zero and more than 99.9% of the frozen random
draws. Oracle is much better than Full. The data therefore has both nontrivial
prediction and large Selection headroom.

The H5 block-order permutation probability is `0.126437`. It did not pass the
`0.05` gate in the old conditional ALG-016U plan, so that plan correctly
stopped with no algorithm result. This says only that the plan's aggregate
block-order diagnostic was not strong enough. It does not make chronology a
prerequisite for every algorithm and does not close Full as a development set.

The old plan, result, summary, and boundary amendment remain unchanged:

- plan:
  `1c37db6ebd2b65a4acdb81c4e75aec1fcab54a7db31e84558c7435d5dadc4b32`;
- suitability result:
  `2f66df63186a6113255ced65e155cce8350aeb9b01eb4c187619e456fccbddf8`;
- summary:
  `b01b8bedc82f5311663a658cbf09ae226fd4895cf2c2171513ae1b68543d60d1`;
- interpretation:
  [`experiments/2026-07-30-swe-bench-full-suitability-and-transfer.md`](experiments/2026-07-30-swe-bench-full-suitability-and-transfer.md).

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

| Route | Mechanism | State | Decisive next evidence |
| --- | --- | --- | --- |
| Ordinary recency | Select the latest ten Tasks | ready control | H5/H10 MAE on the exact Full frame |
| Stationary response matching | Match the other Agents' historical response rates with an exact ten-Task subset | ready control | Direct target-Agent MAE and random position |
| ALG-015U | Combine full, recent, and linear response forecasts with AdaNormalHedge, then exact response matching | ready candidate | Direct MAE versus Full and stationary matching |
| ALG-016U | Forecast the other Agents with a shared change-point model, then exact response matching | ready candidate | First Full H5/H10 MAE |
| Task-content Selection | Match recent Task content without Agent outcomes | pending separate family | Open only if the response-based wave leaves meaningful uncertainty |
| Cached-target finite-horizon methods | Use the target Agent's known historical outcomes | measured separate case | Reopen only for a concrete cached-result product use |

ALG-016U remains the best previously measured H5 before-testing candidate on
Multi-SWE (`0.064013` versus Full `0.067348`) but reversed at H10
(`0.053912` versus Full `0.052807`). Those values neither predict nor replace
its missing Full result.

## Next Cycle

1. Freeze a separate `swe_bench_full_development` plan that binds the exact
   Full data and a finite candidate portfolio.
2. Implement a direct runner by reusing the existing Full loader, rolling
   frame, forecasts, and exact response matcher. Do not modify or bypass the
   old conditional runner.
3. Execute twice and require identical results.
4. Report candidate MAE, candidate minus Full, random position, repository and
   Agent directions, and repository-level uncertainty.
5. Keep, revise, or discard mechanisms from their direct MAE. Do not require
   another source before this development cycle.

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
