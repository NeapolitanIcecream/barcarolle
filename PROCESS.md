# Barcarolle Internal Process Notes

Last updated: 2026-07-24.

This is the short cross-session handoff. Intended behavior lives in
`docs/design/`; completed findings and future work live in
`docs/research-improvement-backlog.md`.

## Current State

The generic pre-Generator infrastructure is at its stop line:

- Downstream evidence-producing Runner paths consume a validated complete
  `TaskPoolBundle`, not Generator objects or parallel Task/Check lists.
- A Generator, adapter, or user process may hand over one strict,
  language-neutral prepared-candidate package. Barcarolle loads its candidates,
  excluded events, certification material, optional adapter sidecar, and
  optional generation provenance; it still owns certification and immutable
  Task Pool publication. Generic packages are external evidence: they cannot
  claim Barcarolle-managed runs or source-authoritative frames.
- A user-maintained latest-schema Task Pool can be opened and validated in
  place through the read-only API or `barcarolle task-pool validate`. Opening
  does not generate, copy, recertify, or republish it.
- Generation provenance is optional. When present it independently digests
  Generator behavior, source protocol, observed frame, run authority, outputs,
  and adapter evidence. Binding it replaces any pre-binding Task Pool ID with
  the final content-derived ID. A frame must have an exact sorted event
  inventory and receipt/attestation semantics. Every frame observation must be
  no later than run completion, which must be no later than Task Pool creation.
  Without the manifest, both behavior and source-protocol digests are null;
  absence remains valid but supports no Generator, frame, or population claim.
  Reports enumerate the manifest plus its frame inventory and adapter sidecar.
- The existing fixed Pylint pilot binds dependency evidence as run-specific
  adapter sidecar data together with sanitized F2P/P2P summaries, keeps core
  certification evidence schema-exact and behavior identity
  inventory-independent, and opens the complete bundle before paid stages.
  This is migration of an existing adapter, not a new Generator implementation.
- External Results are admitted through a content-digested source manifest and
  immutable import receipt into the local append-only Result Store. Import
  checks Task/Check membership and Agent/Workspace/Runtime identity, leaves the
  source byte-identical, labels external attestation, and applies an explicit
  availability policy. The implementation records the first local observation
  time; receipt replay is read-only and reuses that time.
- Default external availability is
  `max(source_result_available_at, evidence_imported_at)`. Historical
  availability requires the explicit producer-attested policy and is labeled
  as such in Reporting.
- Equal cache identity plus different execution evidence is ambiguous and
  cannot be auto-reused. Repricing or evidence views of the same execution may
  coexist. Records derives and validates every Result ID from execution,
  scoring, and evidence identity; historical views choose the lowest Result ID
  per identical execution, independent of append order.
- Multi-origin selection reads one physical Result snapshot and derives every
  cutoff view from it. `fill_results` and `prepare_evaluation_cells` replay the
  persisted Selection, Origin, SelectorInput, FeatureSnapshot, Selector, and
  frozen Agent identities before cache or Agent access. Lazy fill persists an
  exact `EvaluationCellSet`. Its identity binds the requested scoring config
  and benchmark-invalid reuse policy: changing either creates a new resolution
  view, while an unchanged policy resumes the frozen cells.

No concrete built-in Generator, Generator registry, plugin host, workflow
engine, model service, Feature Store, simulator platform, distributed
scheduler, network call, or paid benchmark call was added in this work.

## Design Decisions

1. Keep the eight-module graph. Generator implementations end at the prepared
   package; Task Pool remains the downstream boundary.
2. Keep Task Pool and Result storage independent. Reuse is by exact
   Task/Check/Agent/Workspace/Runtime cell identity, never by Task Pool ID.
3. Keep build and open distinct:
   `package -> certify -> publish` versus
   `existing bundle -> read-only validate/use`.
4. Do not invent provenance for a direct user pool. Missing provenance causes
   claim abstention, not a dummy Generator identity.
5. Treat evidence support as a lattice, not a ladder. Bundle consistency,
   Result-cell completeness, generated-pool prediction, observed-frame bridge
   evidence, Check/semantic calibration, and field calibration are separate
   axes. No axis is implied by another.
6. The v1 observed-frame bridge intentionally supports zero/one output per
   source event in core records. Zero/one/many derivation edges remain in an
   adapter sidecar until two concrete adapters demonstrate a simpler shared
   relation.
7. Strict-prospective comparison requires bound, unchanged Generator behavior
   and source protocol plus a later immutable Task Pool whose source window
   covers the declared future interval. The later pool may be incremental or
   cumulative; overlapping same-ID Task/Check records must remain unchanged.
   Counterfactual replay and direct pool use do not require Generator
   provenance.
8. Report Generator strata separately by default. A declared disjoint-strata
   union is an operational pool, not an estimated target mixture. Automatic
   mixture weights wait for a target frame, overlap/positivity, event weights,
   and an outer holdout.
9. Programmatic Workspace bindings remain the local execution boundary for a
   user-maintained pool. Add a binding-file CLI only when a concrete command
   needs it; the existing binders already prove repository, command, manifest,
   and hidden-material digests before Agent execution.

## Research Route

The next concrete Generator is deliberately not selected or implemented in
this phase. When Generator work resumes:

1. Choose one actual source and declare whether the adapter imports a frozen
   dataset, wraps official code, or reimplements a published paradigm.
2. Use the prepared-package contract unchanged. Add only source-specific
   collection and sidecar evidence.
3. Start with a static classic paradigm whose source and oracle material are
   locally available. Use the first synthetic/base-overlay paradigm as the
   second contract test before extracting shared adapter code.
4. For a native Generator, predeclare the classic failure it targets, the
   common frame, event-level multiplicity/weights, compute budget, funnel,
   semantic and Check audits, crossed Agent treatments, and later-pool metric.
5. Managed LLM generation waits for a concrete adapter, API endpoint, immutable
   authority, and budget. Large-pool certification waits for that workload.
6. A concrete simulator-conditioned interactive adapter may later define one
   narrow episode contract. A held-out human branch-policy pilot gates claims
   that simulator behavior stands in for human interaction, not implementation
   of the adapter itself; field calibration remains a separate study.

The existing offline Selector algorithms remain candidates, not empirical
winners. Learned selection waits for sufficient authorized rolling-origin
evidence, but its persisted training/inference boundary is retained.

## Paid-Call Boundary

Benchmark and evidence-producing calls must use only:

```text
OPENAI_BASE_URL
OPENAI_API_KEY
```

If either is missing, source `~/.zshrc` and check again. Do not use subscription
authentication or alternate provider variables unless the user changes this
rule. Repository maintenance and PR review use local Codex authentication.

Every paid Agent or managed-Generator call needs an immutable authority binding
the schedule or generation plan, inputs, endpoint/model identity, configs,
call and cost caps, and pricing basis. Raw URLs and credentials are not
persisted. No authority can be inferred from the historical USD 300 note.

## Claim Boundary

- `task_pool_bundle_internal_consistency` proves only that the supplied bundle
  and its cross-record links validate.
- `future_pass_rate_mae` is Generator/Check-process-conditional future
  Task/Check prediction error, not real-work utility.
- Imported Results prove accepted producer attestation, not
  Barcarolle-managed execution.
- Source-authoritative and producer-attested observed frames are distinct.
  Neither proves representativeness of a target work population.
- Interactive simulator outcomes are treatment-conditional and cannot stand in
  for held-out human responses without calibration.
- Missing evidence produces an unsupported claim or abstention, never an
  inferred value.

## Storage And Deferred Scale Work

Core readers accept only the latest schema. Use non-destructive one-off
migrations for valuable older Results; do not add runtime compatibility
branches. A Result migration changes canonical Result IDs/digests; rebuild
FeatureSnapshots, SelectorInputs, Selections, fitted Selectors, CellSets,
matrices, and metrics that bind them. Raw prompts, completions, trajectories,
workspaces, credentials, and large outputs stay under ignored paths.

- Reopen checkout caching only when warm/cold repository-size measurements put
  checkout plus cleanup above 5% of scoreable-cell wall time or p95 blocks
  target throughput.
- Reopen bounded parallelism when a planned serial campaign exceeds one hour
  or the API has explicit controlled concurrency. Keep one Result writer and
  `max_concurrency=1` by default.
- Reopen certification checkpoints only after a concrete measured Generator
  workload demonstrates material interruption loss.

## Handoff

Before any Generator or paid campaign work, keep the full suite, Ruff, Pyright,
and `git diff --check` green. If old managed Results need the new provenance
fields, run `scripts/migrate_result_evidence_provenance.py` into a new file and
rebuild the complete derived evidence chain named above. The next research
decision is source-specific: select a concrete adapter and evidence source,
then reopen only the matching deferred items above.
