# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

Current result:
`docs/experiments/2026-07-30-verified-suitability-audit.md`.

No next experiment plan is frozen.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local
  Selection. Multiple repositories are offline evidence units.
- Generators end at a prepared package. User pools open read-only. Task Pool
  and Agent Results remain independent and reuse only under exact identity.
- Future pass-rate MAE is primary. Full eligible history is the primary
  no-Selection baseline. Fixed trivial controls, equal-budget random, and
  future-open oracle are separate diagnostics.
- Prediction difficulty belongs to the Task Pool, Agent panel, Selection unit,
  information contract, horizon, denominator, Origin construction, and
  aggregation together.
- Candidate-versus-full Selection evidence and candidate-versus-trivial
  prediction evidence are separate. Cached-target compression and unseen-target
  Selection are also separate claims.
- Runtime uses an absolute Selection budget and future `TimeRange`. Task-count
  horizons are research estimators or declared finite-cohort inputs.
- KISS/YAGNI constrain engineering, not algorithmic research. Add no registry,
  trainer service, scheduler, generic source adapter, or multi-repository
  Runner without a measured caller.

## Current Decision

The candidate-free audits are complete and independently reproduced:

| H5 diagnostic | Multi-SWE, 36 configs | Verified, 11 Agents |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `7 / 68` |
| Always-zero MAE | `0.059870` | `0.359033` |
| Full-history MAE | `0.067348` | `0.183374` |
| Exact B10 oracle MAE | `0.034709` | `0.074019` |
| Full-to-oracle headroom | `0.032639` | `0.109355` |
| Frozen temporal-null probability | `0.111444` | `0.912044` |

Multi-SWE H5 is zero-dominated under the named estimator contract. Verified
has substantial outcome variation, Full beats zero with repository-bootstrap
95% interval `[-0.248315, -0.063516]`, and the oracle shows large Selection
capacity. Verified nevertheless fails its frozen chronology gate: 1,824 of
2,000 circular shifts are at least as favorable as the observed phase.

Circular shift is a narrow phase-alignment diagnostic. It preserves almost all
response adjacency, so failure does not prove that Task content, change
points, or local persistence are useless. Do not weaken the frozen gate after
seeing the result. Neither opened panel is a Stage C development boundary, and
no Selector is nominated.

The six SWE-bench Verified holdout Agents remain sealed. No paid call or
Generator development occurred.

## Next Action

Freeze a source-specific SWE-bench Full normalization and suitability plan
before reading normalized Full outcomes:

1. bind the exact checked eleven-Agent allowlist, official result blob
   identities, 2,294-Task denominator, Check meaning, source revision,
   normalizer, and panel digest;
2. predeclare H5/H10 frames, aggregation, full, fixed trivial, random, and
   exact-oracle rows;
3. name temporal diagnostics by the property they destroy or preserve. Add an
   adjacent-H5 joint-block permutation for local persistence; keep circular
   phase alignment separate if retained;
4. execute once without treating Full as independent confirmation.

If Full clears the frozen headroom, nontrivial-prediction, resolution, and
chronology gates, it may become an exploratory counterfactual Stage C
development boundary. If it does not, stop public retrospective atlas work
and specify the smallest workload-matched source with native Task and Result
time.

This route needs no paid Agent run and no sealed Agent. It may require public
metadata/result retrieval, but outcome bytes must not be normalized before the
plan commit.

## Stop And Reopen

- Do not run more candidates, Agent subsets, horizons, or rescue diagnostics
  on the opened Multi-SWE, Verified-500, or SymPy panels.
- A new algorithm needs an independently stated mechanism and a new evidence
  boundary. Report direct MAE against full history and the declared trivial
  control separately.
- Open sealed Agents or make paid calls only after a frozen development
  candidate passes its gates.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% of measured
campaign wall time; bounded Agent parallelism only with exact attribution and
one writer; source-specific certification before a comparable runnable pool.
