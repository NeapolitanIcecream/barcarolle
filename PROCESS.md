# Barcarolle Cross-Session Handoff

Last updated: 2026-07-30.

Current ledger: `docs/research-improvement-backlog.md`.

Current audit:
`docs/experiments/2026-07-30-regime-route-independent-audit.md`.

Frozen next plan:
`examples/multi_swe_research/suitability-audit-plan.json`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local
  Selection. Multiple repositories are offline evidence units.
- Generators end at a prepared package. User pools open read-only. Task Pool
  and Agent Results remain independent and reuse only under exact identity.
- Direct pass-rate MAE is primary. Full eligible history is the primary
  no-Selection baseline. Trivial controls, random, and oracle are mandatory
  diagnostics.
- Prediction difficulty belongs to the Task Pool, Agent panel, Selection unit,
  information contract, horizon frame, denominator, Origin construction, and
  aggregation together.
- Cached-target compression and unseen-target Selection are separate claims.
- Candidate-versus-full Selection evidence and candidate-versus-trivial
  nontrivial-prediction evidence are separate claims. A strong nomination needs
  both.
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

The combined H5/H10 failure-region label is withdrawn. Under the frozen
end-aligned, equal-repository, shared-unseen-target estimator view, H5 full
history is dominated by always zero. H10 has a favorable full-history point
estimate, but it is aggregation-, repository-, and Origin-sensitive. The two
rows use different frames, so their sign change is not a causal horizon result.

Exact budget-ten hindsight still improves full history by about 48% in both
frames. Selectable capacity exists after future outcomes open. Whether the real
chronology contains detectable candidate-independent signal is the next
question.

The historical comparison is fixed: the current Boltons report is an H1
mechanism check; the older 20-history-to-H10 full-history MAE is `0.136111`
scoreable or `0.137500` scheduled; the approximately `0.20` result is a mixed
retrospective aggregate; SymPy H5 full-history MAE is `0.193290`. Horizon size
alone does not explain Multi-SWE's low MAE.

Finite-H cached calibration remains a separate information contract, not a
general unseen-target Selector. ALG-016U remains an H5 clue. Do not tune closed
candidates again on these opened outcomes.

## Next Action

Execute `FR-003` once on Multi-SWE as the frozen candidate-free
null-and-headroom pilot. Report zero/one, contract-matched cached climatology,
full history, random, oracle, repository bootstrap/LOO, pooled sensitivity,
calendar spans, and a joint-response within-repository circular-shift null.

The pilot must separate estimator support, budget-ten capacity, temporal
alignment, and repository-level resolution. It cannot nominate a Selector or a
practical main region. Extend the same direct function to another source only
if this pilot changes the data-versus-algorithm decision.

SWE-bench Full remains `normalization-gated`: source/time capacity is available,
but pass-rate MAE needs an exact source-specific Result allowlist, Check
identity, blob manifest, normalizer, and panel digest.

Do not make paid calls, open Full outcomes or the six sealed SWE-bench Agents,
or develop a concrete Generator during the pilot.

## Stop And Reopen

- Stop Selector rescue search on the current opened Multi-SWE, Verified, and
  SymPy panels.
- A new algorithm needs an independently stated mechanism and a new evidence
  boundary. Report its improvement over full history separately from its
  improvement over a contract-matched trivial estimator.
- Reopen paid or sealed confirmation only after frozen development gates pass.
- Add a Reporting warning or abstention only after reusable meanings and a
  concrete caller exist.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching above 5% of measured
campaign wall time; bounded Agent parallelism only with exact attribution and
one writer; source-specific certification before a comparable runnable pool.
