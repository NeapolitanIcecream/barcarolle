# Barcarolle Cross-Session Handoff

Last updated: 2026-07-29.

Current ledger: `docs/research-improvement-backlog.md`. Latest report:
`docs/experiments/2026-07-29-controlled-cold-start-pre-origin-theory.md`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local Selection.
  Multiple repositories are offline research/training evidence units only.
- Generators end at a prepared package; user pools open read-only. Task Pools
  and Agent Results remain independent and reusable only under exact identity.
- A rolling-origin fit may consume only evidence available by the target
  Origin cutoff. Label projected or retrospective evidence explicitly.
- Full history is the primary baseline. Equal-budget random Selection locates a
  candidate in the sampling landscape; it does not replace the baseline.
- Aggregate repository first. Keep candidate-appropriate wide/deep, horizon,
  temporal-null, Agent, harness, provider, model, and language audits.
- Runtime uses an absolute Selection budget and explicit future `TimeRange`.
  Task-count horizons are research controls.
- Add no registry, embedding service, trainer service, scheduler, generic
  source adapter, or multi-repository Runner without a nominated caller.

## Current Evidence

Negative candidate-minus-full-history values favor Selection. SWE-bench
Verified has 11 opened development Agents and six unread holdout Agents.
Multi-SWE has 1,632 Tasks, 36 complete public outcome vectors, 221 H5
Origins/13 repositories, and 107 H10 Origins/11 repositories. Its Task times
are projected PR times, so results are source-time-safe counterfactual
development evidence.

| Route | Result | Decision |
| --- | --- | --- |
| Verified adaptive routes | best nominated-scale wide `-0.01911`; all fail null, deep, Agent-transfer, or replication gates | Retired on this panel. |
| Multi-SWE ALG-012 semantic herding | H5 `-0.00027`; H10 `+0.00241` | Retired; task-space, deep, horizon, harness, and language gates fail. |
| Multi-SWE exact budget-ten hindsight | H5 `-0.03264`; H10 `-0.02562`; 328/328 optima certified | Budget-ten response capacity supported; leaked diagnostic only. |
| ALG-013 Response-Contrast Projection | pass-rate MAE H5/H10 `+0.001729`/`+0.005890` | Direct outcome replay rejects it; the earlier AUC stop did not hide a valid candidate. |
| ALG-014 Response-Composition Shrinkage | pass-rate MAE H5/H10 `+0.001992`/`+0.008170` | Direct outcome replay rejects it; static response structure does not forecast the next cohort. |
| THY-001R Git pressure | Multi H5/H10 vs full Task history `+0.17572`/`+0.21704`; Full-minus-Verified `+0.08751`/`+0.08807` | Retired; source, Origin, reproduction, and independent audits passed. |
| THY-002 Generator-calibrated exposure | H5/H10 vs full history `-0.006562`/`-0.006107`; intervals exclude zero; 27/40 and 28/40 favorable | Task-mix mechanism retained; its THY-002S mapping fails the Agent-outcome gate. |
| THY-002S Brier projection | pass-rate MAE H5 `-0.002594`, upper `+0.004724`; H10 `+0.002943`; random `0.93485`/`0.78260` | Frozen outcome gate also fails; original mapping retirement stands. |
| THY-003 registry-dated dependency lag | Continuous H5/H10 `-0.000223`/`-0.000404`; budget-ten `+0.009057`/`+0.000879`; null `0.9496` | Retired at Stage A; source admission and reproduction passed, prediction/materialization gates failed. |

The experiments factor the problem:

1. a ten-Task subset can represent future Agent responses;
2. other Agent outcomes strongly describe same-Task difficulty;
3. fixed embeddings do not transfer that response structure across
   repositories under ALG-013;
4. full/recent target history plus one-Task cross-repository shrinkage does not
   predict the next Task cohort under ALG-014;
5. THY-002S preserves some H5 Task-mix signal in Agent MAE, but below its
   effect and uncertainty requirements and not at H10;
6. historical Generator yield per Git exposure combined with current exposure
   predicts the next Task-module mix slightly better than full Task history;
   and
7. registry publication time is available and varied, but THY-003's smooth
   effect is weak and its nearest-regime budget-ten materialization fails.

When complete Agent outcomes already exist, use pass-rate MAE as the outcome
gate. AUC, Brier, embedding, and response-coordinate losses are diagnostics.
They may order paid acquisition when outcomes are absent; they may not suppress
an affordable outcome replay.

Counterfactual research may use explicitly projected Task times and
retrospective patch-derived scoring labels; neither becomes native-arrival
evidence. The frozen `THY-001R` plan and its Git-only vocabulary audit failed
the full-history baseline. THY-002 then passed the outcome-free full-history
and component-ablation gates on 5,365 SWE-rebench V2 Tasks in 40 repositories.
Its projected Task and Git clocks support association, not native causality.

## Current State

The Multi-SWE research layer binds source, content, time, embedding, outcome,
plan, raw-result, reproduction, and compact evidence digests. The post-decision
surrogate-gate audit materializes ALG-013/014 Stage-C primary MAE and the exact
THY-002S outcome contract. Its amendment chain now corrects two transcribed
logical identities and validates all twelve bindings before Selection. Two
accepted runs are byte-identical at `1eda7fe1…fc928`; result digest is
`1a105781…0599`, and committed evidence digest is `5f6098f3…fff39`. The
scientific payload equals the superseded pre-correction runs. ALG-013/014
secondary group-refit and temporal-null details remain under-specified, but
their primary positive differences already reject them.

The Task-mix runners bind compact evidence to exact raw results and reject
source, repository, Origin, resource-boundary, and decision drift. THY-002's
two raw runs are byte-identical at `449e10c1…6ac8`; compact digest
`26233a42…aa31`. This remains research infrastructure, not a runnable Task Pool.
Solver/verifier material and source-specific certification are
campaign-triggered. Core Task Pool, Result, Selection, and Runner contracts did
not change. THY-001R and THY-002 remain direct example-layer studies; no core
schema or runtime service was added.

THY-003 Stage A is complete. Addendum `f920d134…c739` and corrected execution
lock `4774fbfe…df673` bind 595 retained packuments, 1,539 state points, nine
repositories, and 119 Origins. Coverage is 97.47%; all Origins are supported.
Two runs are byte-identical at `02c18c81…01a7`; result `68acfaa5…ccd9` and
compact evidence `90456efc…1c17` retire the route. A raw-input reconstruction
verified the accepted result. No Agent outcome, sealed
holdout, paid call, core schema, or runtime service was opened or added.

## Stop And Reopen

Stop nomination-oriented parameter search, representation search, and
unconditional replay on opened Agent outcomes. `THY-001R` is retired; do not
rescue it with another half-life, smoothing value, path map, source subset, or
horizon.

THY-002 supplies an independent source-family Task-mix signal. THY-002S
preserves part of it in H5 Agent MAE, but fails its frozen effect, uncertainty,
and H10 gates. Do not lower the gate, tune the mapper, change the source frame,
or open the six holdout Agents.

There is no active outcome replay or paid plan. No additional core
infrastructure is currently warranted.

`THY-003` is retired without revision. Do not change peer-context parsing,
categories, distance, weights, budget, horizons, repositories, label, or gates
on this frame. Its source and reproduction gates passed; full-history, deep,
materialization, leave-one-repository-out, and temporal-null gates did not.
Stage B is prohibited. The six SWE-bench holdout Agents remain sealed.

The next research question is theory-gated, not implementation-ready: derive a
general forecast-to-budget-k materialization rule that preserves explicitly
frozen pre-Origin moments. Do not tune it on the closed THY-003 frame or add a
core service. A later plan needs an independent evidence boundary and must
separate continuous-forecast quality from subset discretization.

Any reopened candidate must freeze its information set, code, parameters,
source, Origin schedule, controls, and gates before outcome replay. Open the
six SWE-bench holdout Agents only after every development gate passes. Paid
evidence requires explicit authority and `OPENAI_BASE_URL` plus
`OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% measured wall
time; bounded Agent parallelism only with exact attribution and one writer;
RI-160 before a comparable prepared pool; RI-163 before another Pylint
campaign.
