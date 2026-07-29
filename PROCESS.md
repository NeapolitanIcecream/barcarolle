# Barcarolle Cross-Session Handoff

Last updated: 2026-07-29.

Current ledger: `docs/research-improvement-backlog.md`.

Latest reports:

- `docs/experiments/2026-07-29-prequential-response-assembly.md`;
- `docs/experiments/2026-07-29-finite-horizon-cached-assembly.md`;
- `docs/experiments/2026-07-29-finite-horizon-grid-audit.md`.

## Preserve

- Runtime is one user repository, one local Task Pool, and one local
  Selection. Multiple repositories are offline evidence units, never one
  mixed runtime pool.
- Generators end at a prepared package. User pools open read-only. Task Pool
  and Agent Results remain independent and reuse only under exact identity.
- Rolling-origin work consumes only evidence available by the target cutoff.
  Label projected and retrospective evidence explicitly.
- Full eligible local history is the primary baseline. Equal-budget random is
  a sampling-landscape diagnostic, not a replacement baseline or p-value.
- Aggregate repository first. Keep cached-target and unseen-target contracts
  separate.
- Runtime uses an absolute Selection budget and future `TimeRange`. A known
  Task count may parameterize a research estimator but does not replace the
  runtime time contract.
- When outcomes exist, direct pass-rate MAE is primary. Brier, AUC, embedding,
  and response losses are diagnostics.
- Add no registry, model service, trainer, scheduler, generic source adapter,
  or multi-repository Runner without a measured caller.

## Current Evidence

Multi-SWE is the current outcome-open development projection:

- 1,632 Tasks in 39 repositories;
- 36 complete public model/harness outcome vectors;
- standard H5: 221 Origins in 13 repositories;
- standard H10: 107 Origins in 11 repositories;
- minimum history 20 and standard budget 10.

Task time is projected GitHub PR `createdAt`. Public outcomes have no native
Result availability time and do not prove a complete production Agent
fingerprint. Cached-target results are retrospective same-configuration cache
counterfactuals, not prospective runtime evidence.

Negative candidate-minus-full-history MAE favors Selection.

| Method | Information contract | H5 | H10 | Decision |
| --- | --- | ---: | ---: | --- |
| ALG-007 | unseen target | `-0.002254` | `+0.002157` | Closed. |
| ALG-015C AdaNormalHedge | cached target | `-0.002235` | `-0.000246` | Closed; adaptive layer loses to simpler control. |
| ALG-015U AdaNormalHedge | unseen target | `-0.000530` | `+0.000854` | Closed. |
| ALG-016U shared-run-length BOCPD | unseen target | `-0.003335` | `+0.001105` | Best unseen H5 point estimate; no cross-horizon promotion. |
| H-blind quantized history | cached target | `-0.004365` | `-0.003774` | Retained cached KISS baseline. |
| ALG-018C/P finite-H median | cached target, known H | about `-0.0141` | about `-0.0041` | Grid-aware baseline, not a general Selector. |

The matched B5/B10 by H5/H10 audit uses one common 107-Origin frame. Plug-in
finite-H minus same-budget H-blind is:

| Cell | Difference | Paired repository 95% |
| --- | ---: | ---: |
| B5/H5 | `-0.000248` | `[-0.003337, +0.003425]` |
| B5/H10 | `+0.000467` | `[-0.001122, +0.002842]` |
| B10/H5 | `-0.010171` | `[-0.015755, -0.004738]` |
| B10/H10 | `-0.000684` | `[-0.002681, +0.001591]` |

The frozen terminal state is `grid_dominant`. B5/H5 and B10/H5 selected rates
are identical row by row; B10/H5 gains because H-blind can choose odd tenths
that a five-Task future rate cannot attain. Wrong-horizon actions worsen H5
and H10 by `+0.005789` and `+0.001834`. This is loss/score-support geometry,
not future Task prediction.

## Evidence Identities

- prequential plan/lock/result:
  `f1517fd0…58c84b` / `f4dcec2e…1a91d` / `04a2475d…186487`;
- finite-H plan/lock/result:
  `6602a349…264b7` / `10e28322…be4b` / `63662482…e045`;
- matched-grid plan/amendment/corrected lock/result:
  `8388fc58…c4b1d` / `80dd4596…618c` / `03c2dbfb…fcaa5` /
  `d7d92c6d…b630`.

The amendment records prior score access and changes only exact-zero direction
classification with tolerance `1e-15`. Corrected replay changes four B5/H5
favorable-repository counts; no MAE, interval, membership, diagnostic, or
terminal decision changes. Raw artifacts remain ignored.

No paid API call, new Agent-outcome call, embedding call, or sealed holdout
read was used. Core schemas and runtime services did not change.

## Stop And Reopen

- Close cached scalar/grid search on this opened panel. Do not sweep more
  budgets, horizons, priors, ties, ensembles, or smoothing values.
- Keep plug-in finite-H as the canonical known-H cached grid baseline and
  Jeffreys as a fixed sensitivity. Use H-blind when future count is unknown.
- Keep ALG-016U only as an unseen-target H5 development challenger. Reopen it
  only for an independently specified mechanism or evidence boundary.
- Do not open the six sealed SWE-bench Agents. No current route passes the
  gates for sealed confirmation or production nomination.
- A broader cached-result claim needs a new source with Result availability
  and complete Agent identity, or prospective evidence.
- A broader Selection claim needs a new unseen-target or Task-content
  mechanism that beats full history and grid-aware controls, including
  equal-grid cells.
- Paid evidence requires explicit authority and `OPENAI_BASE_URL` plus
  `OPENAI_API_KEY`.

Engineering triggers remain unchanged: checkout caching only above 5% measured
campaign wall time; bounded Agent parallelism only with exact attribution and
one writer; source-specific certification before a comparable runnable pool;
no generic infrastructure without a concrete caller.
