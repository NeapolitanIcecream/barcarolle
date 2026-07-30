# Research Ledger

Last reviewed: 2026-07-30.

Status: active decisions and the next evidence boundary.

The current scientific interpretation is in
[`experiments/2026-07-30-multi-swe-failure-region.md`](experiments/2026-07-30-multi-swe-failure-region.md).
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

## Current Evidence Decision

The current Multi-SWE research projection contains 1,632 Tasks, 36 public
Agent configurations, and 2,913 positive outcomes among 58,752 cells
(`4.9581%`).

| Diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `13 / 221` | `11 / 107` |
| All-zero Agent-Origin future blocks | `83.61%` | `71.94%` |
| Always-zero MAE | `0.059870` | `0.060395` |
| Full-history MAE | `0.067348` | `0.052807` |
| Always-zero minus full history | `-0.007477` | `+0.007589` |

The earlier combined failure-region label is withdrawn. Under the frozen
end-aligned, equal-repository, scheduled-denominator, shared-unseen-target
estimator view, H5 full history and retained candidates are dominated by
always zero. At H10 full history has a favorable point estimate, but that sign
is sensitive to repository weighting, Origin anchoring, and cohort
construction. H5 and H10 use different repository and Origin frames; their
sign change is not a causal horizon result.

Exact budget-ten hindsight still reduces full-history loss by about 48% at both
horizons. Selection capacity exists after future outcomes are known.
Pre-Origin identification on this opened counterfactual panel remains
unresolved. More candidate search on the same outcomes cannot establish
general validity and is closed.

Historical correction:

- the current five-Task Boltons report is an H1 mechanism check;
- the older Boltons full-visible-history result is H10 with MAE `0.136111`
  under scoreable rates and `0.137500` under the scheduled denominator;
- the approximately `0.20` result belongs to an older mixed retrospective
  aggregate, while the later SymPy H5 full-history MAE is `0.193290`.

Future horizon averaging therefore does not explain Multi-SWE's low absolute
MAE.

## Next Research Program

### Stage A: Candidate-Free Null And Headroom Pilot

State: `ready`; plan digest
`c4f2d34be4fc454c434a9c711c56f40a7902ddaeee1052d2ea25bfb67d05a08d`;
no paid calls.

Run the frozen direct audit on Multi-SWE. It reports separate H5/H10 frames,
zero/one, a cached-target-only expanding climatology, full history, existing
random and certified oracle rows, both full-relative and trivial-relative
headroom, equal-repository uncertainty/LOO, pooled-Origin sensitivity, calendar
spans, and a joint-response within-repository circular-shift temporal null.

Exit: decide whether this panel shows only representational capacity, also
shows candidate-independent chronology alignment, or is unresolved at the
repository level. The panel remains `descriptive_only`; this Stage cannot
nominate a Selector or infer workload relevance.

### Stage B: Select The Next Development Boundary

State: `data-gated` until Stage A.

A main-region development panel should have:

- enough nonzero future blocks for pass-rate MAE to distinguish temporal
  prediction from a constant estimator;
- material full-history-to-oracle headroom;
- enough repositories or independent Origins to test portability;
- an Agent panel with useful pass-rate variation;
- a defensible Task-time and Result-availability claim for the intended use.

Use an existing public or already-paid panel when it meets the gate. A
cross-source catalog may index per-source audits, but must not average them or
select a main region from outcomes alone. SWE-bench Full is
`normalization-gated`: its source/time row is available, while its MAE row
needs an exact source-specific Result allowlist, Check identity, blob manifest,
normalizer, and panel digest. Do not authorize calls, open Full outcomes or the
six sealed SWE-bench Agents, or implement a concrete Generator from this
ledger.

### Stage C: Theory-Driven Algorithm Research

State: `data-gated` until one main-region development boundary is frozen.

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
| FR-003 | `ready` | Execute the frozen no-paid Multi-SWE null-and-headroom pilot once. |
| FR-004 | `data-gated` | Choose the next main-region development panel after FR-003. |
| FR-005 | `trigger-gated` | Add a Reporting warning or abstention only after FR-003 fixes reusable meanings and a concrete caller needs it. |
| FR-006 | `normalization-gated` | SWE-bench Full source/time capacity is usable; its pass-rate MAE row needs a source-specific allowlist, Check/Result binding, normalizer, and panel digest before outcomes are opened. |
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
