# Barcarolle Cross-Session Handoff

Last updated: 2026-07-29.

Current ledger: `docs/research-improvement-backlog.md`. Latest report:
`docs/experiments/2026-07-29-generator-calibrated-selection.md`.

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
| ALG-013 Response-Contrast Projection | future AUC `0.5530`, interval `[0.4579, 0.6572]`; history AUC `0.5104`, interval `[0.4689, 0.5500]` | Static embedding response transfer rejected. |
| ALG-014 Response-Composition Shrinkage | static AUC `0.9121`; H5 `+0.000992`; H10 `+0.001855` | Cross-Agent response structure exists; target next-cohort increment rejected. |
| THY-001R Git pressure | Multi H5/H10 vs full Task history `+0.17572`/`+0.21704`; Full-minus-Verified `+0.08751`/`+0.08807` | Retired; source, Origin, reproduction, and independent audits passed. |
| THY-002 Generator-calibrated exposure | H5/H10 vs full history `-0.006562`/`-0.006107`; intervals exclude zero; 27/40 and 28/40 favorable | Task-mix mechanism retained; Agent outcomes remain unopened. |

The experiments factor the problem:

1. a ten-Task subset can represent future Agent responses;
2. other Agent outcomes strongly describe same-Task difficulty;
3. fixed embeddings do not transfer that response structure across
   repositories under ALG-013; and
4. full/recent target history plus one-Task cross-repository shrinkage does not
   predict the next Task cohort under ALG-014; but
5. historical Generator yield per Git exposure combined with current exposure
   predicts the next Task-module mix slightly better than full Task history.

`THY-002S-A` now freezes that conversion as a deterministic budget-ten Brier
projection coreset on the common 11-repository Multi-SWE H10 frame. Its
outcome-free front gate must first show structural alignment with future Task
mix, full history, a stationary coreset, and equal-budget random sampling.
No Selector is nominated. No result authorizes paid validation, the sealed
holdout, a Runner default, or a validity claim.

Counterfactual research may use explicitly projected Task times and
retrospective patch-derived scoring labels; neither becomes native-arrival
evidence. The frozen `THY-001R` plan and its Git-only vocabulary audit failed
the full-history baseline. THY-002 then passed the outcome-free full-history
and component-ablation gates on 5,365 SWE-rebench V2 Tasks in 40 repositories.
Its projected Task and Git clocks support association, not native causality.

## Current State

The source-specific Multi-SWE research layer binds exact source, content, time,
embedding, outcome, plan, raw-result, reproduction, and compact evidence
digests. ALG-013 and ALG-014 stop at their first failed frozen gate. The
independent audit corrected RCP's diagnostic null to preserve complete
36-dimensional Task response vectors; its corrected rate remains `0.55` and
the rejection is unchanged. Tests cover target-repository exclusion, cutoff
safety, equal-repository pooling, bounded prior mass, and prequential inputs.

The Task-mix runners bind compact evidence to exact raw results and reject
source, repository, Origin, resource-boundary, and decision drift. THY-002's
two raw runs are byte-identical at `449e10c1…6ac8`; compact digest
`26233a42…aa31`. This remains research infrastructure, not a runnable Task Pool.
Solver/verifier material and source-specific certification are
campaign-triggered. Core Task Pool, Result, Selection, and Runner contracts did
not change. THY-001R and THY-002 remain direct example-layer studies; no core
schema or runtime service was added.

## Stop And Reopen

Stop nomination-oriented parameter search, representation search, and
unconditional replay on opened Agent outcomes. `THY-001R` is retired; do not
rescue it with another half-life, smoothing value, path map, source subset, or
horizon.

THY-002 supplies the previously missing independent source-family Task-mix
signal. The separately frozen `THY-002S-A` plan has digest
`cb83d866…b1b9a`. The next authorized step is its zero-paid Task-space replay.
Only a front-gate pass permits one focused executor amendment that binds the
frozen memberships to already-open public Agent results. The amendment may
add the join and predeclared aggregation only; it cannot change the algorithm,
controls, random indices, or gates. The six holdout Agents stay sealed.

Any reopened candidate must freeze its information set, code, parameters,
source, Origin schedule, controls, and gates before outcome replay. Open the
six SWE-bench holdout Agents only after every development gate passes. Paid
evidence requires explicit authority and `OPENAI_BASE_URL` plus
`OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% measured wall
time; bounded Agent parallelism only with exact attribution and one writer;
RI-160 before a comparable prepared pool; RI-163 before another Pylint
campaign.
