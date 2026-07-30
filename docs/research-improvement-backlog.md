# Research Ledger

Last reviewed: 2026-07-30.

Status: active decisions and the next evidence boundary.

The current scientific interpretation is in
[`experiments/2026-07-30-verified-suitability-audit.md`](experiments/2026-07-30-verified-suitability-audit.md).
`PROCESS.md` is the short cross-session handoff.

## Archive Lineage

The previous ledger is frozen at
[`research-improvement-backlog-2026-07-30.md`](research-improvement-backlog-2026-07-30.md).

- source commit:
  `4e755aaef58886ff264d712963dbc6879b32a414`;
- archived file SHA-256:
  `c61de6f939496e365b91d96ec3a1e8cdc44c3efe20b7e5641bbcf1930cede34e`;
- archive delta: only the status line changed from active to archived;
- earlier archive:
  [`research-improvement-backlog-2026-07-27.md`](research-improvement-backlog-2026-07-27.md);
- policy: do not amend archived evidence. Record corrections and changed
  decisions here with links to the original report.

The archive retains completed infrastructure work, all closed algorithm
families, detailed digests, and superseded plans. This ledger carries forward
only decisions that can change a future action.

## Maintenance Rules

Evidence states:

- `measured`: reproduced from bound evidence;
- `ready`: the next action needs no new authority or data;
- `data-gated`: wait for a stated source or outcome panel;
- `authority-gated`: wait for explicit paid-call or external authority;
- `trigger-gated`: act only after a recorded caller or threshold appears;
- `closed`: no action remains on the current evidence boundary.

Every algorithm plan must freeze its information contract, estimand, horizon,
full-history baseline, trivial baselines, random calibration, oracle
diagnostics, ablations, and rejection rule before candidate outcomes are
opened. Close routes instead of carrying their execution diaries forward.

## Stable Decisions

1. Runtime remains one user repository, one local Task Pool, and one local
   Selection. Multiple repositories are offline evidence units, not one mixed
   runtime pool.
2. Generators end at a prepared package. User Task Pools open read-only.
   Runner, Selection, Reporting, and Workspace do not depend on a Generator
   type.
3. Task Pool and Agent Results remain independent. Reuse requires exact Task,
   Check, Agent, Workspace, Runtime, and availability identity.
4. Direct future pass-rate MAE is the primary outcome metric when outcomes
   exist. Brier, AUC, embeddings, response losses, and task-mix loss are
   diagnostics.
5. Full eligible local history is the primary no-Selection baseline.
   Always-zero and always-one are estimator controls. A historical climatology
   is included only when its inputs are admitted by the same information
   contract. Equal-budget random and hindsight oracle describe the attainable
   selection space.
6. Prediction difficulty belongs to the joint Task Pool, Agent panel, Selection
   unit, information contract, horizon frame, denominator, Origin construction,
   and aggregation regime. A Task source is not permanently valid or invalid
   independent of those choices.
7. Barcarolle may have documented failure regions. Research should optimize
   the intended practical main region, detect or report unsupported regimes,
   and avoid rescue-tuning an extreme opened panel.
8. A low absolute MAE is not evidence of nontrivial prediction when a
   contract-matched trivial estimator obtains a similar or lower loss.
   Candidate-versus-full Selection evidence remains separate. A strong
   nomination requires both claims.
9. Cached-target compression and unseen-target Selection are different
   information contracts. Grid-aware cached calibration does not prove Task
   content or future-regime prediction.
10. Runtime horizon remains a future `TimeRange`. Task-count H values are
    research estimators or predeclared finite-cohort inputs, not a replacement
    runtime contract.
11. KISS and YAGNI constrain implementation machinery, not algorithmic
    research. Add no registry, model service, trainer service, scheduler,
    generic source adapter, or multi-repository Runner without a measured
    caller.
12. Paid evidence requires explicit authority and
    `OPENAI_BASE_URL` plus `OPENAI_API_KEY`.
13. A temporal null must name the structure it destroys and preserves.
    Circular shifts test absolute phase while preserving almost all adjacency;
    they are not a generic test that chronology contains no information.

## Current Evidence Decision

The bounded candidate-free atlas stopped after two independently reproduced
sources:

| H5 diagnostic | Multi-SWE, 36 configs | Verified, 11 Agents |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `7 / 68` |
| Always-zero MAE | `0.059870` | `0.359033` |
| Full-history MAE | `0.067348` | `0.183374` |
| Exact B10 oracle MAE | `0.034709` | `0.074019` |
| Full-to-oracle headroom | `0.032639` | `0.109355` |
| Frozen temporal-null probability | `0.111444` | `0.912044` |

Multi-SWE H5 is always-zero dominated under its named unseen-target estimator
view. Its H10 point estimate remains aggregation-, repository-, and
Origin-sensitive. The exact oracle confirms representational capacity but not
pre-Origin identification.

Verified is not a repeat of the Multi-SWE triviality regime. Full history
beats always zero by `0.175659`, with repository-bootstrap 95% interval
`[-0.248315, -0.063516]` and every leave-one-repository-out direction
negative. Equal-budget random MAE is `0.194647`; exact B10 oracle MAE is
`0.074019`, leaving `0.109355` Selection headroom.

Verified does not clear its frozen chronology gate. The circular statistic is
full-history minus zero MAE, where lower is favorable. In 1,824 of 2,000
within-repository circular shifts the statistic was at least as favorable as
the observed value, giving `p=0.912044`. This only rejects unusually favorable
absolute phase. Because the null preserves almost all response adjacency, it
does not prove that Task features, local persistence, or change points are
useless.

Do not weaken the gate after reading the result. The Verified panel remains
`descriptive_only`, with terminal state
`capacity_without_detected_history_persistence`. No opened source is currently
authorized as the main Stage C development boundary.

## Next Research Program

### Stage A: Candidate-Free Compatibility Audit

State: `measured`.

The Multi-SWE plan digest is
`c4f2d34be4fc454c434a9c711c56f40a7902ddaeee1052d2ea25bfb67d05a08d`;
its compact summary digest is
`6928409f03153a793c09b4e01cb3db05058593cbb35a12b5a90a107dd1ad85fe`.

The Verified eleven-Agent plan digest is
`59525b1a8168b909a4499f4658e10f5c4208e2fc5d659785d0ee42d44f63f550`;
its result and summary digests are
`2311d7da9a285b43dadf9382cebe281473c742ffd6aa79b0d9084cd1e4412ea4`
and
`48032bc07d64c693a7d3247b7af4ab8a750c56df93b972ea339e04f5f0392403`.

Both remain source-time counterfactual diagnostics. Neither nominates a
Selector or resolves workload relevance.

### Stage B: Normalize SWE-bench Full

State: `ready`; no paid calls and no sealed Agent open.

Before normalizing outcome bytes, freeze:

- the exact checked eleven-Agent allowlist and each official result blob;
- the 2,294-Task denominator, source revision, Check meaning, and
  source-specific normalizer;
- the Agent panel digest and rules for ordinary unlisted, no-generation,
  missing-log, and schema-variant Tasks;
- H5 and H10 frames, equal-repository aggregation, full, fixed trivial,
  equal-budget random, and exact-oracle diagnostics;
- temporal diagnostics by their exact null. Predeclare an adjacent-H5
  joint-block permutation to test local persistence; label circular shifts as
  phase alignment if retained.

Run once. Full remains an opened retrospective development source and cannot
serve as independent confirmation. If it fails the frozen headroom,
nontrivial-prediction, resolution, or chronology gates, stop the public atlas
and specify a workload-matched source with native Task and Result time.

### Stage C: Theory-Driven Algorithm Research

State: `data-gated` until Stage B yields one exploratory development boundary.

Start from a mechanism stated without target future outcomes. New theory may
be algorithmically complex; engineering remains a direct experiment module.
Evaluate full history, trivial controls, random landscape, and oracle in the
same plan. Use repository-held-out or later-source validation, report H5/H10
or deployment-derived horizons without choosing the favorable one afterward,
and reject routes that gain only from pass-rate grid geometry.

Do not continue numeric tuning of ALG-007, ALG-012 through ALG-018,
THY-001R, THY-002S, or THY-003 on their opened panels. ALG-016U remains a
recorded H5 mechanism clue, not a candidate authorized for rescue tuning.

### Stage D: Independent Confirmation

State: `authority-gated`.

Only a candidate with a frozen Selection/compression claim against full
history, a separately frozen nontrivial-prediction claim against an
information-contract-matched control, and a deployment-derived practical gate
may consume a later source, sealed Agent panel, prospective campaign, or paid
Agent outcomes. Confirmation must preserve exact endpoint, Agent, Task, Check,
availability, and cost identity.

### Stage E: Product Reporting

State: `trigger-gated`.

After Stage A stabilizes the diagnostic meanings, decide whether Reporting
should emit a suitability warning or abstention when a deployment panel falls
outside its declared operating region. Keep this as a computed report over
existing records. Add no global Task-Pool registry or generic policy engine.

## Active Work Ledger

| ID | State | Next action or reopening condition |
| --- | --- | --- |
| FR-001 | `revised` | H5 is zero-dominated only under the named unseen-target estimator view; H10 is unresolved and sensitivity-bound. The combined failure-region label is withdrawn. |
| FR-002 | `measured` | Statistical protocol now requires trivial baselines and regime diagnostics before candidate interpretation. |
| FR-003 | `measured` | Multi-SWE candidate-free H5/H10 audit completed and independently reproduced. |
| FR-004 | `measured` | Verified opened eleven-Agent H5 audit completed; capacity is present but the frozen phase-alignment gate failed. |
| FR-005 | `trigger-gated` | Add a Reporting warning or abstention only after a practical operating region and concrete caller exist. |
| FR-006 | `ready` | Freeze the SWE-bench Full checked-eleven allowlist, Check/Result binding, normalizer, panel digest, H5/H10 frames, and named temporal nulls before outcome normalization. |
| ALG-016U | `closed` on current panel | Preserve as the best unseen-target H5 point estimate. Reopen only through an independently derived mechanism on a new evidence boundary. |
| THY-002 | `task-mix-pass` | Preserve generator-calibrated exposure as projected Task-mix evidence. Its THY-002S outcome mapping remains closed. |
| Parent work intent | `data-gated` | Reopen only with complete timestamped planning-node history, versioned Task material, and pre-arrival component labels. |
| Fixed-universe compression | `trigger-gated` | Treat held-out-Agent score reconstruction as a separate estimand when it becomes a product priority. |
| Runnable external Task Pool | `trigger-gated` | Add source-specific certification only for a concrete campaign; do not generalize a Generator framework. |

## Retained Engineering Triggers

- Reopen checkout caching only when checkout plus cleanup exceeds 5% of
  measured campaign wall time.
- Reopen bounded Agent parallelism only for a measured campaign need, with
  exact attribution, default concurrency one, and one Result writer.
- Add a single-writer certification checkpoint before the next comparable
  generated pool and replay retained entries before reuse.
- Before another Pylint campaign, replace whole-file behavior identity with an
  explicit version payload and direct-helper digests.
- Use structural audit signals only after reproducing a boundary or
  maintenance problem. Do not split modules from a score alone.

All omitted algorithm and infrastructure history remains recoverable in the
2026-07-30 archive.
