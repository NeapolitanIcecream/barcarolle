# Research Ledger (Archived 2026-07-31)

Last reviewed: 2026-07-30.

Status: outcome-open estimand audit v2 complete; one bounded response-forecast
replay remains open before the response route is retained or retired.

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

The deployment unit is one target Agent and one repository. The
repository-equal headline is an average over the fixed development panel, not a
pass-rate estimate for one deployment cell.

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
  repositories are averaged equally;
- direct absolute error is computed before aggregation;
- every summary retains Agent-by-repository paired cells as well as repository
  and Agent marginals.

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

H20 has 98 Origins on the same ten repositories and H40 has 47 Origins on eight
repositories. They are reliability diagnostics only. Existing candidates were
not reranked on them.

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
H10 (`+0.001719`). Full was better than `99.97%` and `99.975%` of the frozen
random draws. Candidate midranks describe macro loss under the frozen random
policy; they do not establish future-predictive structure or deployment-cell
improvement.

This result is reproduced byte-for-byte. The candidate memberships are
materially different, and no candidate is favorable in more than four of ten
repositories.

The estimand audit found:

- 70 of 110 Agent-by-repository pass rates are below `0.10`; the median is
  `0.03646`;
- zero future blocks are `68.19%` at H5 and `57.81%` at H10;
- Full beats the previous-block control on matched rows at every diagnostic
  horizon; H40 matched Full is `0.037527` versus previous `0.044676` on
  `451/517` available rows;
- the exact descriptive decomposition assigns `50.89%`, `67.68%`, `84.96%`,
  and `89.76%` of H5/H10/H20/H40 realized variation to fitted Agent,
  repository, and interaction sample means; these are not population variance
  or reliability estimates;
- on the common eight repositories, within-cell variance follows `1/H` with
  `R²=0.99886`, consistent with finite-block averaging;
- each candidate improves the six-Agent RAG group mean and harms the
  five-Agent other-group mean at both horizons;
- same-future reference-to-target residual correlation is `0.392` at H5 and
  `0.437` at H10, while the information-valid previous-reference-to-next-target
  values are only `0.176` and `0.177`;
- a post-hoc corrected repository-shared block permutation is positive only at
  H5 (`0.001499`; H10/H20/H40 are `0.211894/0.099450/0.457271`);
- the reference Oracle helps/harms/ties `71/17/22` joint cells at H5 and
  `68/20/22` at H10.

The v2 contract records that adversarial review corrected the permutation null
after initial output was visible. The permutation rates are exploratory, not
pre-registered confirmation.

Full beats zero and previous-block controls on the panel average, which is
consistent with useful local prevalence. The current evidence does not
establish that Selection predicts future deviations from it. The reference
Oracle shows contemporaneous macro capacity on this finite panel, not
forecastability or reliable local cross-Agent transport.

Evidence:

- [`experiments/2026-07-30-swe-bench-full-direct-mae-development.md`](experiments/2026-07-30-swe-bench-full-direct-mae-development.md);
- [`experiments/2026-07-30-swe-bench-full-estimand-reliability-audit.md`](experiments/2026-07-30-swe-bench-full-estimand-reliability-audit.md);
- `examples/swe_bench_full_development/evidence/summary.json`;
- `examples/swe_bench_full_development/evidence/diagnostic-summary.json`;
- `examples/swe_bench_full_estimand_audit/evidence/summary.json`.

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
6. A repository-equal panel average is not a pass-rate estimate for one
   Agent-by-repository deployment cell.
7. Repository and Agent marginals can both hide a harmful joint cell; committed
   evidence must retain the joint cells.
8. Random midrank measures position under one sampling policy. It does not
   prove temporal prediction.
9. A future-open reference Oracle measures same-future macro capacity. It does
   not prove pre-Origin forecastability or uniform local transport.
10. Realized next-H fidelity and latent future-traffic pass probability are
    different estimands. Direct MAE remains primary for the former.
11. Descriptive finite-panel sums-of-squares are not population variance,
    causal attribution, or a formal reliability coefficient.

## Active Approach Registry

| Route | State | Reason |
| --- | --- | --- |
| Ordinary recency | control retained | Simple temporal comparison; worse than Full |
| Stationary response matching | control retained | Best H10 ten-Task method; still worse than Full |
| ALG-010 | retired unchanged on this frame | Worse than Full at both horizons |
| ALG-015U | retain only in bounded replay | Nearly tied at H5; harms the five-Agent other-group mean |
| ALG-016U | retired unchanged on this frame | Worse than Full at both horizons |
| Exact response matcher | control only | Future-open macro capacity exists; local transport and forecastability remain open |
| New response-model portfolio | closed | Do not add mechanisms before the bounded replay resolves the timing link |
| Cached-target methods | separate case | Use extra target-Agent information |
| Task-content/process methods | next orthogonal route | Open one frozen wave if the bounded response replay fails |

## Next Cycle

1. Freeze one history-only forecast of the next other-Agent Full residual.
2. Compare only Full, stationary response matching, and ALG-015U at H5 and
   H10.
3. Report forecast error, selected-to-forecast error, selected-to-future error,
   and final target-Agent direct MAE.
4. Retain all Agent-by-repository cells and repository leave-one-out
   directions. Report post-hoc subgroup confinement separately; it blocks a
   broad-Agent claim but does not redefine the primary finite-panel result.
5. If forecast diagnostics improve but direct MAE does not, record
   forecast-to-action coupling as the response-route blocker.
6. If the forecast increment is unstable or absent, retire further response
   forecasting and open one frozen Task-content or repository-process route.
7. Seek an independent data boundary only after a candidate beats Full.

The estimand audit now binds a canonical manifest of all repository Python
execution sources and dependency declarations. Preserve complete execution
source and pinned-runtime binding in the next evidence run. Also add an
end-to-end `materialize_portfolio` regression that perturbs one target Agent's
entire outcome column and requires that Agent's memberships to remain
unchanged.

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
