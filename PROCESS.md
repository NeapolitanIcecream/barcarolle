# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

Current result:
`docs/experiments/2026-07-30-swe-bench-full-suitability-and-transfer.md`.

No next experiment plan is frozen.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local
  Selection. Multiple repositories are offline evidence units.
- Generators end at a prepared package. User pools open read-only. Task Pool
  and Agent Results remain independent and reuse only under exact identity.
- Future pass-rate MAE is primary. Full history is the no-Selection baseline;
  trivial controls, equal-budget random, and future-open oracle are distinct
  diagnostics.
- Suitability belongs to Task Pool, Agent panel, Selection unit, information
  contract, horizon, denominator, Origin construction, and aggregation
  together.
- An unread exact Result blob is not automatically an unseen Agent. Check
  Agent/submission and Task-denominator overlap before opening any panel.
- Runtime uses an absolute Selection budget and future `TimeRange`. H5/H10 are
  research estimators.
- KISS/YAGNI constrain engineering, not algorithmic research. Add no generic
  source adapter, registry, trainer service, scheduler, or multi-repository
  Runner without a measured caller.

## Current Decision

The final public candidate-free source audit is complete:

| SWE-bench Full diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `10 / 408` | `10 / 201` |
| Always-zero MAE | `0.098671` | `0.099916` |
| Full-history MAE | `0.078554` | `0.062579` |
| Equal-budget random MAE | `0.086606` | `0.073798` |
| Exact B10 oracle MAE | `0.013093` | `0.007353` |
| Block-order null probability | `0.126437` | `0.326837` |

Full is nontrivial, beats more than 99.9% of frozen random draws, and has
substantial oracle headroom. It nevertheless fails the frozen primary H5
block-order gate (`p > 0.05`). The terminal state is
`suitability_gate_rejects_before_algorithm`.

ALG-016U was not executed and has no Full-panel MAE. Do not interpret this as
an algorithm failure or rerun it by weakening the gate. Multi-SWE, Verified,
Full, SymPy, and Boltons are closed to further candidate replay.

The six exact Verified source/Check-specific result blobs remain unread. Full
opened outcomes for three of the same Agent identities on all 500 overlapping
instance IDs, so only three holdout identities remain clean for a pure
unseen-Agent claim. See the append-only boundary amendment linked from the
current report.

No paid call, new Agent outcome, Generator work, or core-schema change
occurred. The implementation, two byte-identical runs, and an independent
per-Task MILP audit agree.

## Next Action

Specify—not yet implement—the smallest concrete workload-matched evidence
source with:

1. repository-local coding Tasks;
2. native or defensibly reconstructed Task time;
3. native Result availability or a frozen replay policy;
4. enough independent H5/H10 Origins and repositories;
5. an Agent panel checked against every reserved holdout.

Run a zero-outcome feasibility preflight before building an importer or
opening normalized outcomes. Keep ALG-016U frozen unchanged for a new source
that passes a candidate-free gate. Paid runs remain premature.

## Stop And Reopen

- Do not run more algorithms, Agent subsets, rescue horizons, or post-hoc
  nulls on opened panels.
- Do not claim the three overlapping Verified identities as unseen Agents.
- A new algorithm needs an independently stated mechanism and a new evidence
  boundary, with direct MAE against Full and the contract-matched trivial
  control.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% of measured
campaign wall time; bounded Agent parallelism only with exact attribution and
one writer; source-specific certification before a comparable runnable pool.
