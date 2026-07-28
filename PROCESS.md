# Barcarolle Cross-Session Handoff

Last updated: 2026-07-28.

Current ledger: `docs/research-improvement-backlog.md`. Latest report:
`docs/experiments/2026-07-28-multi-swe-semantic-selector.md`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local Selection.
  Multiple repositories are offline research/training evidence units only.
- Generators end at a prepared package; user pools open read-only. Task Pools
  and Agent Results remain independent and reuse only under exact identity.
- A rolling-origin fit may consume only evidence available by the target
  Origin cutoff. Label projected or retrospective evidence explicitly.
- Full history is the primary baseline. Equal-budget random Selection measures
  location in the sampling landscape; it does not replace the baseline.
- Aggregate repository first. Keep wide/deep, horizon, temporal-null, Agent,
  model, provider, harness, and language audits appropriate to the candidate.
- Product contracts use an absolute Selection budget and explicit future
  `TimeRange`; Task-count horizons are research controls.
- Add no registry, embedding service, trainer service, scheduler, generic
  source adapter, or multi-repository Runner without a nominated caller.

## Evidence

Negative candidate-minus-full-history values favor Selection. On SWE-bench
Verified, 11 development Agents are open and six holdout Agents remain sealed.

| Verified route | Wide difference | Decision |
| --- | ---: | --- |
| Joint response Markov | `-0.01911` | Retired: null `0.100`, leave-one-Agent 1/3 favorable, sealed replication `+0.00031`. |
| Difficulty Markov | `-0.00888` | Retired: deep `+0.00920`, leave-one-Agent 6/11 favorable. |
| Adaptive difficulty | `-0.00235` | Retired: null `0.194`, deep `+0.00927`. |
| Budget–horizon audit | best `-0.00379` | No passing budget 5/10/15 × horizon 3/5/10 cell or stable region. |
| Hindsight support | `-0.15890` | Budgeted subsets can represent future outcomes; safe identification is unsolved. |

Multi-SWE is the primary outcome-open development source: 1,632 Tasks, 36
complete public outcome vectors, H5 221 Origins/13 repositories, and H10 107
Origins/11 repositories. Times are projected GitHub PR creation times, so
results are source-time-safe counterfactual evidence.

| Multi-SWE route | H5 difference | H10 difference | Decision |
| --- | ---: | ---: | --- |
| ALG-012 minimax semantic herding | `-0.00027` | `+0.00241` | Retired: H5 interval crosses zero; deep, task-space, harness, and language gates fail. |
| Unchanged ALG-007 control | `-0.00225` | `+0.00216` | Retired; do not tune. |

ALG-012 is at the 81.59th percentile of equal-budget random H5 outcome
Selections, but its effect against full history is nearly zero. In semantic
task space it is at the 99.14th random percentile while worsening MMD² by
`+0.03563` in 13/13 repositories. The algorithm uses sampling structure, but
ten-Task compression plus its prediction error erase any useful advantage.

No Selector is a Runner default. No result authorizes the sealed holdout, paid
validation, or a validity claim.

## Current State

The source-specific Multi-SWE layer now binds:

- the exact 39-file, 1.60 GB dataset revision and 1,632 issue-text projection;
- projected Task times and 36 public outcome vectors;
- 384-dimensional local embeddings with no embedding API;
- deterministic H5/H10 memberships, task-space results, outcome results, and
  compact self-digested summaries.

This is research infrastructure, not a runnable Multi-SWE Task Pool. Solver and
verifier material plus source-specific certification remain campaign-triggered.
Core Task Pool, Result, Selection, and Runner contracts did not change.

Next: freeze and run one post-result hindsight support search at budget ten on
the existing H5/H10 data. It may use future outcomes only to distinguish
representational capacity from pre-Origin identification. It is descriptive,
cannot nominate a Selector, opens no sealed data, and makes no paid call.

After that diagnostic, choose between:

1. a new theory-driven, repository-held-out predictive mechanism;
2. one direct partial-pooling experiment; or
3. stopping algorithm work until a later source or prospective campaign.

Do not select among these from the hindsight memberships themselves.

## Reopen Boundaries

- Do not tune another budget, horizon, threshold, embedding, or semantic target
  from the opened ALG-012 or Verified results.
- A new candidate must freeze its information set, code, parameters, source,
  Origin schedule, controls, random calibration, transfer audits, and
  source-relative gate before outcome replay.
- Open the six SWE-bench holdout Agents only after every applicable development
  gate passes. Multi-SWE and Full cannot provide independent confirmation
  because their outcomes are open.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.
- Reopen checkout caching only above 5% measured wall time; bounded Agent
  parallelism only with exact attribution and one writer; RI-160 only before a
  comparable prepared pool; RI-163 only before another Pylint campaign.
