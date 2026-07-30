# Research Ledger

Last reviewed: 2026-07-30.

Status: active decisions and the next evidence boundary.

The current scientific interpretation is in
[`experiments/2026-07-30-swe-bench-full-suitability-and-transfer.md`](experiments/2026-07-30-swe-bench-full-suitability-and-transfer.md).
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
14. An unread exact Result blob and an unseen Agent are different seals.
    Opening the same Agent's outcomes on a materially overlapping Task
    denominator preserves a source/Check-specific byte seal but consumes the
    stronger unseen-Agent boundary.

## Current Evidence Decision

The bounded public suitability atlas is complete. Multi-SWE H5 is
always-zero dominated under its named estimator. Verified has nontrivial
variation and oracle headroom but fails its circular phase-alignment gate.
SWE-bench Full was the final predeclared source: it passed resolution,
nontrivial-prediction, and oracle-headroom gates, then failed the primary H5
joint-block-order gate.

| Full diagnostic | H5 | H10 |
| --- | ---: | ---: |
| Repositories / Origins | `10 / 408` | `10 / 201` |
| Always-zero MAE | `0.098671` | `0.099916` |
| Full-history MAE | `0.078554` | `0.062579` |
| Equal-budget random MAE | `0.086606` | `0.073798` |
| Exact B10 oracle MAE | `0.013093` | `0.007353` |
| Full-to-oracle headroom | `0.065460` | `0.055226` |
| Joint-block-order probability | `0.126437` | `0.326837` |

Full beats always zero with repository-bootstrap intervals
`[-0.029135, -0.010765]` at H5 and `[-0.047309, -0.027290]` at H10. It also
beats more than 99.9% of the frozen random draws, and the exact oracle shows
substantial remaining Selection capacity. The panel is therefore not a
triviality failure region.

The primary H5 block-order probability nevertheless exceeds the frozen
`0.05` threshold. This null destroys adjacency and order between complete
future blocks while preserving within-block joint Agent responses. Its failure
does not reject Task-feature or every change-point mechanism, but it does
reject admission of this panel under the frozen contract. ALG-016U was not
run, has no Full-panel MAE, and is neither supported nor refuted by this
result.

An independent audit reproduced the normalizer, 609 Origins, controls, random
expectation, block null, and every exact oracle with a separate per-Task MILP.
It also found a claim-boundary error: three Full submissions share Agent
identities with the six reserved Verified holdouts. The six exact Verified
result blobs remain unread, but only three Agent identities remain clean for a
pure unseen-Agent claim. The append-only correction is
[`../examples/swe_bench_full_transfer/evidence-boundary-amendment-1.json`](../examples/swe_bench_full_transfer/evidence-boundary-amendment-1.json).

No opened source is authorized as the main Stage C development boundary. Stop
public retrospective algorithm replay rather than weakening a gate or choosing
a favorable Agent subset after seeing results.

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

State: `measured`; rejected before algorithm execution.

The plan, result, summary, and evidence-boundary-amendment digests are:

- plan:
  `1c37db6ebd2b65a4acdb81c4e75aec1fcab54a7db31e84558c7435d5dadc4b32`;
- result:
  `2f66df63186a6113255ced65e155cce8350aeb9b01eb4c187619e456fccbddf8`;
- summary:
  `b01b8bedc82f5311663a658cbf09ae226fd4895cf2c2171513ae1b68543d60d1`;
- boundary amendment:
  `fd7d78def30fd8ca1a6bfe85c641e29dc9bd642b2396ce7dc97fdcb92dd20812`.

The result is `suitability_gate_rejects_before_algorithm`. Do not rerun with
another Agent panel, horizon, null, or algorithm on this opened source.

### Stage C: Theory-Driven Algorithm Research

State: `data-gated`; the public suitability route yielded no authorized
development boundary.

Specify the smallest concrete workload-matched source with native or
defensibly reconstructed Task time, a Result-availability policy, enough
independent Origins and repositories, and an identity-clean Agent panel.
Perform a candidate-free feasibility preflight before building an importer or
opening outcomes. Keep new theory independent of future outcomes and keep its
engineering as a direct experiment module.

Do not continue numeric tuning of ALG-007, ALG-012 through ALG-018,
THY-001R, THY-002S, or THY-003 on their opened panels. ALG-016U remains a
frozen mechanism clue, not a candidate authorized for rescue tuning.

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
| FR-006 | `measured` | Full passed resolution, nontrivial prediction, and headroom but failed H5 block-order chronology; no algorithm ran. |
| FR-007 | `data-gated` | Specify and candidate-free preflight one workload-matched, native-time source with a clean Agent identity panel. Do not build a generic source adapter first. |
| HOLDOUT-001 | `revised` | Six exact Verified result blobs remain unread; only three identities remain clean for unseen-Agent confirmation. Freeze a restricted or replacement panel before opening outcomes. |
| ALG-016U | `data-gated` | Preserve unchanged. It has no Full score; reopen only on a new predeclared evidence boundary that passes suitability. |
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
