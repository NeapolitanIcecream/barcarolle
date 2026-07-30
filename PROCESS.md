# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

Current report:
`docs/experiments/2026-07-30-multi-swe-failure-region.md`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local
  Selection. Multiple repositories are offline evidence units.
- Generators end at a prepared package. User pools open read-only. Task Pool
  and Agent Results remain independent and reuse only under exact identity.
- Direct pass-rate MAE is primary. Full eligible history is the primary
  no-Selection baseline. Trivial controls, random, and oracle are mandatory
  diagnostics.
- Prediction difficulty belongs to the Task Pool, Agent panel, horizon, and
  aggregation together. Barcarolle may report or abstain in documented failure
  regions instead of weakening main-region performance.
- Cached-target compression and unseen-target Selection are separate claims.
- Runtime uses an absolute Selection budget and future `TimeRange`. Task-count
  horizons are research estimators or declared finite-cohort inputs.
- Add no registry, model or trainer service, scheduler, generic source adapter,
  or multi-repository Runner without a measured caller.

## Current Decision

The opened Multi-SWE projection has 1,632 Tasks, 36 public Agent
configurations, and 2,913 positive outcomes among 58,752 cells (`4.9581%`).

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `11 / 107` |
| All-zero Agent-Origin future blocks | `83.61%` | `71.94%` |
| Always-zero MAE | `0.059870` | `0.060395` |
| Full-history MAE | `0.067348` | `0.052807` |

This Task Pool and Agent-panel combination is an observed sparse-outcome
failure region for temporal pass-rate MAE. H5 is dominated by always predicting
zero. H10 contains signal, but no frozen unseen-target candidate beats full
history across both horizons.

Exact budget-ten hindsight still improves full history by about 48% at both
horizons. Selectable capacity exists after future outcomes open; pre-Origin
identification in this sparse regime remains unsolved.

The historical comparison is fixed: the current Boltons report is an H1
mechanism check; the older 20-history-to-H10 full-history MAE is `0.136111`
scoreable or `0.137500` scheduled; the approximately `0.20` result is a mixed
retrospective aggregate; SymPy H5 full-history MAE is `0.193290`. Horizon size
alone does not explain Multi-SWE's low MAE.

Finite-H cached calibration remains a grid-aware baseline, not a general
Selector. ALG-016U remains an H5 clue. Do not tune closed candidates again on
these opened outcomes.

## Next Action

Execute `FR-003`, a no-paid regime suitability atlas over compatible Boltons,
SymPy, SWE-bench Verified, and Multi-SWE evidence. Keep their estimands
separate. For each view report:

- outcome density, Agent dispersion, and zero/all-one future-block shares;
- always-zero, cutoff-safe climatology, full-history, random, and oracle loss;
- available and captured headroom with exact repository, Agent, horizon,
  budget, and denominator identity.

The atlas must either identify a reusable main-region development panel or
show that current panels are unsuitable and specify the smallest additional
outcome acquisition needed.

Do not make paid calls, open the six sealed SWE-bench Agents, or develop a
concrete Generator during the atlas.

## Stop And Reopen

- Stop Selector rescue search on the current opened Multi-SWE, Verified, and
  SymPy panels.
- A new algorithm needs an independently stated mechanism and a new evidence
  boundary. It must beat full history and the strongest trivial control.
- Reopen paid or sealed confirmation only after frozen development gates pass.
- Reassess Multi-SWE only for a different Agent panel, horizon, or outcome
  source.
- Add a Reporting warning or abstention only after the atlas fixes reusable
  meanings and a concrete caller needs it.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% of measured
campaign wall time; bounded Agent parallelism only with exact attribution and
one writer; source-specific certification before a comparable runnable pool.
