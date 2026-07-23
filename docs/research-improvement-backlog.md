# Research Findings And Improvement Backlog

Last reviewed: 2026-07-23.

Status: living research record.

This document records cross-module findings, improvement proposals, research
questions, and validation criteria for Barcarolle. It is not an intended-system
specification. The design documents define intended behavior, the code and
tests show current enforcement, and `PROCESS.md` records the active research
direction.

## Maintenance Rules

Use the following evidence labels:

- `reproduced`: demonstrated with a local counterexample or measurement;
- `code-confirmed`: established by tracing current implementation behavior;
- `experiment-needed`: a proposed improvement whose benefit is not established;
- `preserve`: a boundary that should not be removed without new evidence.

Use the following decision labels:

- `complete-contract`: the target boundary is required and current work should
  finish it;
- `simplify-implementation`: preserve the capability while removing duplicate
  paths, caller-supplied identity, or unused state;
- `future-work`: retain a documented design and reopening trigger, but do not
  implement it before its prerequisites or measurement threshold;
- `defer`: do not prepare a generic abstraction; revisit with a concrete
  algorithm or deployment need.

Use priorities as follows:

- `P0`: can invalidate benchmark or research evidence, leak future information,
  or cause uncontrolled paid execution;
- `P1`: materially affects reliability, cost, prediction quality, or auditability;
- `P2`: cleanup, scale preparation, or documentation maintenance;
- `P3`: deferred until the required data or earlier protocol work exists.

When a finding is resolved, keep its identifier, record the validating test or
experiment, and move it to the resolved section. Do not mark a field or policy
as enforced when it is only persisted. Every new algorithm proposal must state
its estimand, pre-origin inputs, baselines, ablations, and failure criterion.

## Current Conclusion

The solver/verifier split, hidden-oracle timing, diff replay, structured Result
cache identity, append-only repricing, and rolling-origin freeze order are sound
boundaries. The main risks are gaps between those boundaries: records can be
individually valid while their combined Task, Check, Agent, pricing, denominator,
or time claims are false.

Stage 0 evidence integrity is now closed in the current implementation. The
certification, Result Store, monotonic-timing, behavior-digest, deterministic
resume, immutable run-context, boundary-helper, and Selector-infrastructure
slices are also closed. Stage 2 now has one executable fitting boundary, actual
FeatureSnapshot validation at inference, and one shared-cell plan for several
Selectors. Batch evaluation remains counterfactual-only. Strict-prospective
evaluation now uses the intended two-phase contract: freeze the Selection and
planned window, then bind a later immutable Task Pool through the existing
EvaluationCellSet and reuse the same Result resolver, matrices, and scorer.
Both pool source windows, the mature/censored future cohort, unchanged shared
Task/Check records, and the ordered full Agent identities are replayable by
Reporting and the offline CLI. Before either Task Pool is read, the prospective
Runner also reloads Selector and FeatureSnapshot evidence and proves that
deterministic inference reproduces the frozen Selection. The frozen strict
Origin is not rewritten. After the immutable selection-time Task Pool is
validated, Runner replays `task_count` and every `task_stratum` value, timestamp,
scope, and source digest against that Origin and its TaskRecords before the
future pool is opened. Reporting uses the same direct Selection contract.
`FeatureConfig` now has one executable input axis: a non-empty unique set of
supported feature names, normalized to builder order. Leakage classes are
derived from those names, so no caller-supplied class list or no-op permutation
can create a second config identity for the same extraction behavior.
Learned-Selector evidence also fixes the complete ordered Agent treatment across
training Origins. Every training Result cache identity must project back to
that frozen AgentRecord digest before its outcome can affect fitted weights.
Training also receives the same frozen Task Pool records, replays every Origin
and Snapshot against them, and binds both pre-origin and outcome Result cache
identities to their exact Task/Check records. Any bound CellSet or Matrix cell
must also match its Result ID/digest, Agent/Task/Check, required cache identity,
and outcome through one Records-owned predicate shared by online scoring,
training, and Reporting. Batch resume resolves all Results bound by reusable
CellSets in one read and applies that predicate before planning missing cells or
invoking an Agent. Matrix exclusions are separately derived from Result invalid
ownership and the existing join semantics, so exact binding alone cannot remove
a normal Result from the denominator.
The offline Stage 3 data boundary now separates arrival from label
maturity, retains censored refs, persists an auditable source-event frame, and
runs symmetric repeated certification pairs. Dependency blocking is also
separate from Selector-visible sampling strata. Requested model names are now
separate from proven immutable snapshots; unresolved aliases are scoped to a
declared campaign and execution window. The Pylint experiment layer can freeze
a deterministic, stratified paired-replicate schedule without opening Results
and can execute it only through a separate campaign authority ledger. That
ledger binds the schedule, Task Pool, Agents, Workspace/Runtime configs,
endpoint digest, total budget, a per-call estimated-cost limit, the
schedule-derived call cap, and pricing before any Agent call. Remaining budget
must cover one per-call limit before reservation. Its concrete dependency
artifact derives components from trusted reference-patch path overlap and is replayed before
paid stages. A concrete CLI now loads those frozen records and Pylint adapter
bindings, exposes separate `authorize`, `preflight`, and `run-next` operations,
and emits bounded summaries without adding a core execution path. Task Pool
expansion is deferred until a concrete Task Generator is selected; a generator
may itself require the unavailable model endpoint. Run-variation and outcome
comparisons still require another
explicitly authorized evidence-producing paid run; no campaign authority
ledger was created by this maintenance sprint.

Rolling-origin cohort controls now reject truthy substitutes and non-string
cluster filters before policy identity is formed. Verification rejects coercive
raw execution state and ambiguous normalization configuration. Batch paid-call
preflight validates immutable Check and Agent bindings once per unique identity,
while the existing per-cell rechecks remain the final guard.

YAGNI applies to implementation machinery, not to the known end-to-end contract.
Barcarolle does not need a Feature Store service, model registry, workflow DAG,
distributed scheduler, generic plugin host, or general experiment framework.
It needs durable records, direct function calls, and algorithm-specific fitting
inside Selection.

## Maintainer Principles

The following principles are authoritative inputs to decisions in this backlog:

1. Prefer boring technology, KISS, and YAGNI. The system architecture should be
   explainable to a new intern without hiding behavior behind a framework.
2. Design toward the known final form. An incomplete final-form contract should
   be completed rather than removed merely because the current experiments have
   not exercised it.

When the principles appear to conflict, keep the stable record and function
boundary required by the final data flow, and defer interchangeable machinery
behind that boundary until a concrete caller exists.

## Target End State

The eight existing modules remain sufficient. The target data flow is:

```text
Task source
  -> immutable, certified Task Pool
  -> RollingOrigin + pre-origin Result view + FeatureSnapshot
  -> frozen SelectorInput
  -> train_selector -> executable SelectorRecord
  -> select_with_selector -> frozen Benchmark Selection
  -> Runner plans the union of exact required cells
  -> Workspace + Verification -> append-only Agent Results
  -> Selection evaluation -> Reporting
```

Rules and learned methods share the same `SelectorRecord`, `SelectorInput`, and
selection output. Rule Selectors may ignore feature values, but they still bind
the same frozen input and leakage provenance. A first data-efficient learned
method may store compact fitted coefficients in `SelectorRecord.parameters`.
Add an external model artifact ref and digest only when a concrete model is too
large or unsafe to store there.

`train_selector` and `select_with_selector` are the stable algorithm boundary:

- `train_selector` fits one configured family from frozen evidence strictly
  earlier than its deployment origin and returns an executable record;
- `select_with_selector` is inference only and cannot open training or future
  result sources;
- choosing among previously evaluated Selectors remains a separate operation;
- fixed rule Selectors use an explicit constructor and do not pretend to train.

This keeps algorithm complexity inside Selection while Runner remains a direct
orchestrator of owner-module calls.

## Verification Snapshot

The 2026-07-23 implementation sprint used no network, paid call, or benchmark
Agent run.

- `uv run ruff check .`: passed.
- `uv run pyright`: zero errors.
- `uv run pytest -q`: 837 passed, 2 skipped.
- Cross-module tests now mutate frozen Task/Check content, rolling-origin future
  and censored refs, source-event artifacts, policy fields, dependency/stratum
  classification, symmetric certification attempts, Agent candidates,
  pre-origin denominators, paired MAE evidence/weights, Result pricing views,
  process descendants, and paid endpoint/harness bindings.
- Core record tests replace Task, Check, and Agent string IDs, Task text and
  sequence fields, and a nested Result cache identity with non-reloadable
  values. Public validation rejects each at the initial latest-schema gate.
  A temporary deterministic audit replaced each of 256 fields across all 16
  public record validators and observed no base-record failure or exception.
  Canonical serialization also collapses floating `-0.0` to `0.0`, so nested
  JSON and self-digests cannot fork on signed zero.
- Task Pool tests apply the same mismatch to its generator-config digest and
  creation timestamp and to its rejected-candidate collection, and pass
  malformed scalar/container candidate fields through both accepted and
  pre-certification-excluded source paths. They also reject all non-string
  freeze metadata before Task Pool identity construction. A temporary audit of
  all 20 Task Pool record fields and all 21 Task/Check member fields observed no
  artifact-validator exception. Separate no-change audits also disturbed all 17
  SourceEvent fields and 23 top-level/nested certification-evidence fields with
  no exception.
- Selection tests collapse integer/float-equivalent continuous rule parameters
  to one Selector identity, reject noncanonical external executable records,
  prove nested parameter mappings are snapshotted, and require rule-mixture
  weights to use one complete scale-invariant unit-simplex representation.
- Result Store tests require positive and negative zero scoring rates to share
  one canonical float mapping and pricing-view identity. ResultQuery filters
  and availability bounds also validate before store existence can affect the
  outcome. Exact cache-identity computation validates Task, Check, Agent,
  WorkspaceConfig, RuntimeConfig, and Task/Check linkage before construction;
  Result construction additionally validates WorkspaceRun before linkage and
  cache projection. Task Pool certification and Workspace execution preflight
  reuse the same config contract before Check or Agent execution. Runner also
  applies it before Task Pool candidate resolution, and Workspace validates the
  config before repository binding.
- Replicate campaign tests mutate authority and completion evidence, exercise
  all Runtime-slot preflights, recover a Result after completion-event
  interruption, reject an unfunded next call and a per-call cost overrun, and
  prove stopped paid cells do not retry.
- Strict-prospective tests freeze a Selection before its planned window, link a
  later source-complete Task Pool, retain censored refs without execution,
  reject dropped source coverage and same-ID Agent drift before execution, and
  withhold report claims when the future pool is absent. A separate adversarial
  spec changes the persisted Selection to another eligible history ref and
  proves deterministic replay rejects it before Task Pool reads.
- The current full-signal Cremona scan covers 38 first-party Python files and
  reports 112 hotspots (0 now / 36 soon / 76 monitor), no structural
  regression, and no dead-code candidate.

These checks establish implementation behavior, not predictive validity. The
algorithm and data questions later in this ledger still require experiments.

## Evidence Integrity

### RI-001: Bind Results To The Frozen Task Pool

Priority: P0. Evidence: code-confirmed. State: resolved 2026-07-22.

Current Runner steps accept `TaskPoolRecord`, Tasks, and Checks separately.
Membership checks primarily compare IDs, while Result identity is built from
the separately supplied Task and Check content. Reporting checks Task Pool
artifacts and matrix-to-Result bindings, but does not trace each Result's
repository, base commit, solver material, and Check identity back to the frozen
Task and Check artifacts.

Evidence pointers:

- `Runner.run_agents`, `Runner.fill_results`, and `_ensure_refs_in_task_pool` in
  [`runner.py`](../src/barcarolle/runner.py);
- `_result_identity_trace_errors` in
  [`reporting.py`](../src/barcarolle/reporting.py).

Risk: records with unchanged Task and Check IDs but changed task text, hidden
material, or resource limits can form an internally consistent report for work
that was not in the frozen pool.

Direction:

- provide one strict `load_validated_task_pool_bundle` path;
- pass the validated bundle through Runner instead of three drifting inputs;
- trace every Result identity back to the frozen Task and Check in Reporting;
- bind the complete candidate Agent set to evaluation evidence.

Acceptance: a cross-module test changes Task or Check content while retaining
its ID and recomputing local digests. Every execution and reporting entry point
must reject it before an Agent call or supported claim.

Resolution: Runner loads and validates the frozen Task Pool bundle and rejects
same-ID content drift before execution. Reporting traces matrix Results back to
the exact frozen Task/Check records and supplied Agent identities.

### RI-002: Require An Immutable Base Commit

Priority: P0. Evidence: code-confirmed. State: resolved 2026-07-22.

`TaskRecord.base_commit` only needs to be non-empty. Workspace fetches the
stored string and checks out `FETCH_HEAD` without proving that the resulting
HEAD equals an immutable commit recorded in the Task. Result cache identity
uses the original string.

Evidence pointers:

- `validate_task` and `build_result_cache_identity` in
  [`records.py`](../src/barcarolle/records.py);
- `_checkout_repository` in
  [`workspace.py`](../src/barcarolle/workspace.py).

Risk: a movable ref such as `main` can resolve to different commits during
certification and execution while retaining the same cache identity.

Direction: resolve the ref when creating or certifying a Task, store the full
commit OID, reject symbolic refs for scoreable Tasks, and verify checkout HEAD.
Support the repository's object format instead of assuming a 40-character SHA-1.

Acceptance: moving a branch or tag between certification and execution must
fail before solver material is exposed or a cached Result is selected.

Resolution: Task construction resolves symbolic revisions once, Task validation
requires a full repository-format OID, and Workspace verifies checked-out HEAD.

### RI-003: Publish Immutable Task Pool Artifact Bundles

Priority: P0. Evidence: code-confirmed. State: resolved 2026-07-22.

Task Pool builds default to fixed paths such as `records/tasks.jsonl`, and
`write_jsonl_records` replaces existing files. A later build can therefore
change files referenced by an older frozen `TaskPoolRecord`. The three files
are individually atomic but not published as one bundle.

Evidence pointers:

- Task Pool defaults and writes in [`runner.py`](../src/barcarolle/runner.py);
- `write_jsonl_records` in [`records.py`](../src/barcarolle/records.py).

Direction: write content-addressed or Task-Pool-ID-addressed directories, stage
and validate all members, then atomically publish a manifest. Existing targets
may only be reused when their content digests match. Resolve relative refs from
an explicit artifact root, not the current working directory.

Acceptance: building two different pools cannot overwrite the first pool's
artifacts, and an injected failure at any publish step leaves the earlier bundle
fully verifiable.

Resolution: Task Pool artifacts publish as validated content-addressed bundles;
existing targets are reused only when every member matches.

### RI-004: Preserve A Common Agent Comparison Denominator

Priority: P0. Evidence: code-confirmed. State: resolved 2026-07-22.

`agent_invalid_policy="exclude"` removes a cell for one Agent. Evaluation then
computes each Agent's pass rate over its own remaining cells and accepts some
`complete_with_exclusions` matrices for Selector fitting.

Evidence pointers:

- `ResultJoinConfig` and `_matrix_cell` in
  [`result_store.py`](../src/barcarolle/result_store.py);
- matrix completeness and `_pass_rates` in
  [`selection/evaluation.py`](../src/barcarolle/selection/evaluation.py).

Risk: an Agent can appear better because its invalid outcomes occurred on hard
tasks and were removed only from its denominator.

Direction:

- comparative metrics and Selector training count Agent-attributable invalid
  outcomes as failures;
- diagnostic per-Agent exclusion forces abstention;
- benchmark-infrastructure invalidity removes the same Task and Check for all
  Agents and remains visible in the report;
- Reporting distinguishes common, scoreable exclusions from missing or
  Agent-specific exclusions.

Acceptance: the two-Agent hard-task counterexample must abstain or count the
invalid outcome as a failure. A common infrastructure exclusion may remain
scoreable only when every Agent retains the same denominator.

Resolution: Agent-attributable invalidity remains a failure, partial Agent
exclusion abstains, and only task-wide benchmark-infrastructure exclusion can
retain a common scoreable denominator.

### RI-005: Enforce Rolling-Origin Policies And Persist Provenance

Priority: P0. Evidence: reproduced. State: resolved 2026-07-22.

`RollingOriginPolicy.eligibility_mode` and `holdout_overlap_policy` were recorded
but did not affect the split. The former cluster whitelist acted only as a filter, but
there is no general history/future overlap enforcement. Policy digests are
caller supplied. `RollingOriginRecord` lacks the same self-digest and validator
coverage as other evidence records.

The audit reproduced an origin declared `disjoint` whose history and future
Tasks had the same cluster.

Evidence pointers:

- `RollingOriginPolicy` and `build_rolling_origin` in
  [`selection/origin.py`](../src/barcarolle/selection/origin.py);
- record digest dispatch in [`records.py`](../src/barcarolle/records.py);
- `Runner.evaluate_selector` in [`runner.py`](../src/barcarolle/runner.py).

`Runner.evaluate_selector` constructs Origin, FeatureSnapshot, and SelectorInput
objects, but does not return or persist them with the Selection, cell set,
matrix, and metric. Offline Reporting therefore cannot prove that a frozen
Selection was produced by the claimed pre-origin inputs.

Direction:

- define exact `strict_prospective` and `counterfactual_replay` claims;
- enforce or remove every policy field;
- derive policy digests from behavior fields;
- validate and persist Origin, Selector, FeatureSnapshot, SelectorInput,
  Selection, cell set, matrix, and metric as one auditable chain;
- replay deterministic baseline Selectors during Reporting.

Acceptance: changing future refs, Agent candidates, policy fields, or pre-origin
denominators without updating the full chain must make the report unsupported.
Counterfactual replay must not be reported as a prospective publication event.

Resolution: policy digests are derived from enforced behavior fields;
`strict_prospective` and `counterfactual_replay` have distinct eligibility
semantics; overlap policy is enforced; all chain records have validators and
self-digests; Runner persists the chain before opening future Results; Reporting
requires exact links and replays deterministic Selectors. Supported performance
summary names include the eligibility mode.

### RI-006: Separate Executions From Pricing Views

Priority: P1. Evidence: reproduced. State: resolved 2026-07-22.

Repricing appends a Result view with the same `result_execution_digest`.
`build_result_report` currently counts every Result record as an execution and
sums its outcome, latency, usage, and cost.

The audit passed two pricing views of one execution to Reporting. It reported
two Results, counted latency twice, and added both alternative prices.

Evidence pointers:

- repricing in [`result_store.py`](../src/barcarolle/result_store.py);
- `build_result_report` in [`reporting.py`](../src/barcarolle/reporting.py).

Direction:

- report `execution_count` and `pricing_view_count` separately;
- deduplicate outcome, latency, and usage by `result_execution_digest`;
- require one requested scoring configuration for a total cost, or show costs
  in separate pricing-version columns;
- persist enough currency, rate, and measured-versus-estimated provenance for
  Reporting to recompute cost.

Acceptance: adding any number of repricing views cannot change execution count,
outcome count, latency, or usage. It changes only the selected or grouped cost
view.

Resolution: Reporting groups execution evidence by
`result_execution_digest`, reports pricing views separately, and emits one
numeric total only for a single scoring configuration.

### RI-007: Bind Certification And Hidden Material To Executed Behavior

Priority: P1. Evidence: code-confirmed. State: resolved 2026-07-22.

Certification evidence binds Task, Check, patch, and outcomes, but not all
workspace, runtime, adapter, or bound-command behavior. Hidden directory digests
cover paths and contents but omit some filesystem semantics such as executable
mode; directory injection may merge with pre-existing content.

Evidence pointers:

- certification records in [`task_pool.py`](../src/barcarolle/task_pool.py);
- hidden injection and tree digests in
  [`verification.py`](../src/barcarolle/verification.py) and
  [`workspace.py`](../src/barcarolle/workspace.py).

Direction: bind certification to the verifier execution adapter and relevant
runtime identity. Use one canonical tree digest covering path, entry type,
content, and executable bit; reject or define symlink behavior. Require the
hidden destination and reserved `.barcarolle` namespace to be absent before
Barcarolle creates them.

Acceptance: changing the executed Check command, file mode, unexpected hidden
directory member, or reserved-path type must change evidence identity or fail
closed.

Resolution: certification evidence now binds Workspace and Runtime configs,
the exact Check execution binding, and the built-in verifier adapter. Workspace
and Verification share one canonical hidden-material tree digest covering
relative path, entry type, file content, and executable bits. Symlinks and
unsupported entries fail closed. Hidden injection requires both the reserved
`.barcarolle` namespace and the destination to be absent, copies without merge,
and rehashes the resulting tree before Check execution.

## Architecture And Implementation Convergence

| ID | Priority | Evidence | Finding | Direction |
| --- | --- | --- | --- | --- |
| RI-008 | P1 | reproduced, resolved 2026-07-22 | The former `train_selector` returned the first candidate or built a static rule record. | `train_selector` now fits only the concrete rule-mixture family from replayed expert Selections, paired selected/future matrices, recomputed MAE, exact Result bindings, and origins before a declared deployment origin. Fixed rules use `build_rule_selector`; candidate choice is separate. |
| RI-009 | P1 | reproduced, resolved 2026-07-22 | The former inference path could accept only a FeatureSnapshot ID while public rule helpers bypassed snapshot validation. | `select_with_selector` now requires the materialized, self-validated FeatureSnapshot, checks its exact SelectorInput binding, cutoff, and allowed leakage classes, and is the sole public inference path. Training additionally resolves exact pre-origin Results used by snapshots. |
| RI-015 | P2 | code-confirmed, resolved 2026-07-22 | Large experiment scripts duplicated ledger-event loading, fsync, snapshot folding, and paid-cost accounting. Endpoint, exact-cell recovery, pricing validation, and scoreability differ by experiment. | `examples/experiment_ledger.py` now owns only the shared single-writer reservation/completion log, complete-line check, durable append, atomic snapshot, and cost folding. It validates the shared timestamp and finite nonnegative accounting boundary; Boltons and Pylint retain their direct experiment-specific guards. Temporary replay of the 10-call boltons ledger and both 2-call and 20-call Pylint ledgers preserved calls, spent cost, and remaining budget exactly. |
| RI-034 | P2 | static-audit plus temporary full-suite branch coverage | active; ninety-five evidence-boundary slices resolved through 2026-07-23 | Evidence validators and report builders still contain several independent checks in long functions. The current 38-file scan remains `strained`/`investigate_soon`, with full signal health, 112 hotspots (0 now / 36 soon / 76 monitor), no Ruff/Complexipy critical findings, 19 Lizard critical findings, and no dead-code candidates. Runner `train_selector`, prospective Task Pool report replay, Task Pool construction, SourceEvent finalization, certification-evidence reconciliation, matrix alignment, Claim Boundary evaluation, Selector-batch preflight, bounded subprocess execution, shared resource-ledger snapshot reconstruction, and Records payload-state validation now have direct phase boundaries. Exact Result-cache identity and construction, schema-first shared validator/latest-schema typing including Task Pool/member/Result/config inputs, ordered Task Pool artifact prerequisites, non-coercive candidate and Task Pool metadata ingestion, canonical Selector parameters including scale-invariant rule-mixture weights, canonical JSON and immutable scoring inputs including signed zero, typed optional pre-origin and ResultQuery bounds, relative Workspace artifact refs, confined typed report filenames, implementation-owned Metric consumption, typed rolling-origin cohort controls, canonical persisted floats, and Check normalization are fixed contracts instead of placeholder, coercion, or truthiness controls; certification repeat count and all evidence/execution configs fail at batch, binding, and just-in-time entry boundaries. Complete-plan binding checks deduplicate immutable Check and Agent identities while retaining per-cell revalidation. The shared CellSet resolver and `evaluate_selectors` retain explicit orchestration dependencies rather than one-use context objects. Companion-log, Reporting, and Task Pool candidate/context checks remain linear in existing boundaries. | Continue one characterized evidence boundary at a time; keep validation strength and module ownership. The Claim Boundary directly orchestrates five stable claim predicates and evaluates only requested claims; the shared CellSet execution orchestrator remains an explicit audit surface. Do not hide contracts with `**kwargs`, duplicate execution dependencies, or add a validation framework, one-use context object, or baseline during the large active change set. |
| RI-035 | P1 | reproduced, resolved 2026-07-22 | A Result-linked FeatureRecord could name Task, Check, or Agent fields from another in-origin cell because validation checked only the Result/source and optional cache digest. | Present Task, Check, Agent, and cache-identity links now must match the exact visible Result. Fields remain nullable, and origin-level aggregate digest/count behavior is unchanged. A characterization test reproduces both cross-ref and cross-Agent drift. |
| RI-036 | P1 | reproduced, resolved 2026-07-22 | `build_rolling_origin` silently skipped missing Task Pool Task/Check records or a Check with the wrong owner, allowing an incomplete denominator to be constructed under the complete Task Pool digest. | Origin construction now requires every Task Pool member record and exact Task/Check owner linkage before cohort derivation. Record supersets remain allowed and filtered to the Task Pool. Characterization covers missing Task, missing Check, and wrong owner. |
| RI-037 | P1 | reproduced, resolved 2026-07-22 | Result and excluded cells could omit outcomes, missing cells could carry exclusion/outcome payloads, excluded Result bindings could be partial, and ResultMatrix `scoreable_state` was not checked against cells or abstention. | Records now enforce one explicit ResultCellRef payload state machine and derive the allowed matrix scoreability state from cells/abstention. Four Selection fixtures were corrected to use production-valid states. |
| RI-038 | P1 | reproduced, resolved 2026-07-22 | A self-consistent RollingOrigin could carry an `as_of_cutoff` that contradicted `as_of_cutoff_rule`, an invalid explicit cutoff rule, or a future window beginning before the cutoff. | RollingOrigin validation now binds the cutoff to the declared rule and orders cutoff, future-window start, and future-window end. Replay semantics and stored behavior can no longer drift while IDs/digests remain valid. |
| RI-039 | P1 | reproduced, resolved 2026-07-22 | SourceEvent validation raised while deriving label maturity from malformed material timestamps, and a rejected event could use an empty string as its reason. | Material-time parsing now fails closed through `ValidationResult`; disposition validation requires every present rejection reason to be a non-empty string. The three-disposition state machine remains centralized and explicit. |
| RI-040 | P1 | reproduced, resolved 2026-07-22 | The paired-replicate scheduler accepted non-string campaign IDs, integer-valued floats as repeat counts, and two Agent records whose execution configurations differed only by `agent_id`. | Schedule preflight now validates protocol scalars exactly and requires two behaviorally distinct Agent configurations before any schedule or paid campaign authority can be created. |
| RI-041 | P1 | reproduced, resolved 2026-07-22 | The historical Pylint summary loaded every Result with the pilot Agent IDs and pricing config, so a different Runtime identity could alter counts, rates, pairs, cost, and completion claims. Completion also ignored ledger state. | Summary reconstruction now filters by the exact current execution identities and declares completion only with all 20 exact Results plus 20 completed resource-ledger calls. Per-effort and paired derivations are separate pure helpers. |
| RI-042 | P1 | reproduced, resolved 2026-07-22 | A self-consistent SelectorInput could declare a `selection_budget_limit` that disagreed with `budget_digest`; intrinsic uniqueness and cutoff checks lived only in Selection. Reporting also treated the order of separately supplied Agent records as evidence, so reordering an identical Agent set revoked a valid claim. | Records now owns SelectorInput membership, budget, cutoff, identity, and self-digest validation through direct helpers; Selection delegates to that one contract. Reporting compares the supplied Agent records as a set while preserving exact frozen SelectorInput/ResultMatrix order. |
| RI-043 | P1 | reproduced, resolved 2026-07-23 | Task Pool artifact validation first rejected a scalar certification `rejection_reasons` value, then raised `TypeError` while linking the same malformed evidence to SourceEvents. Independently, accepted evidence could claim `pass` together with `timed_out=true` or a failure label, or `fail` without a failure label. | Cross-record SourceEvent reconciliation now normalizes only sequence-shaped reasons after the record-level validator reports malformed input. Attempt evidence enforces the normalized Verification state machine: passing attempts have no failure label, non-passing attempts have a non-empty failure label, and timeouts are invalid outcomes. Validation returns errors instead of raising. |
| RI-045 | P1 | reproduced, resolved 2026-07-23 | `evaluate_selectors` accepted `strict_prospective`, although that mode must freeze an Origin with no future refs. The Runner then persisted selection evidence and could invoke Agents for selected cells even though the same immutable Task Pool could never supply post-origin traffic, leaving no valid future denominator. | Batch evaluation now rejects strict mode before side effects. `evaluate_prospective_selection` separately reloads the frozen strict chain, links a later Task Pool through `EvaluationCellSet`, materializes mature/censored refs, and reuses the one Result/matrix/scoring path. Reporting and the offline CLI require and replay both snapshots. |
| RI-046 | P1 | reproduced, resolved 2026-07-23 | A later Task Pool carried creation time and member digests but not the source interval it had observed, so it could not prove complete coverage of a planned future window. Treating event inventory as generator configuration would also make every later observation look like behavior drift. | Task Pools now persist canonical source-window bounds, reject accepted or certified events outside them, and bind the bounds into pool identity. Generator digest is behavior-only; SourceEvent/Task/Check digests bind inventory. Prospective replay requires the later window to preserve the earlier start and cover the planned future end. |
| RI-047 | P0 | reproduced, resolved 2026-07-23 | `SelectorInput` froze only Agent IDs. Between strict Selection and later evaluation, a caller could reuse an ID with changed harness/model/prompt/tool evidence and reach future-pool validation or execution. | `SelectorInput` now binds full canonical `AgentRecord` digests in Agent order. Runner rejects ID/order or record-digest drift before Task Pool reads and Agent calls; Reporting rechecks the same binding while treating separately supplied Agent records as an unordered container. |
| RI-048 | P0 | reproduced, resolved 2026-07-23 | Strict prospective evaluation reloaded Selection, Origin, and SelectorInput but did not reload Selector/FeatureSnapshot or replay deterministic inference before opening Task Pools. A self-digested Selection could change to another eligible history ref and reach the execution path; Reporting rejected it only later. | Selection now owns one semantic replay assertion. Prospective Runner loads and validates the complete Selector→Origin→FeatureSnapshot→SelectorInput→Selection chain and replays it before Task Pool reads or Agent calls. Reporting, training, and stratified diagnostics reuse the same assertion. |
| RI-049 | P0 | reproduced, resolved 2026-07-23 | Strict prospective replay did not resolve the pre-origin Results frozen by SelectorInput. Missing or drifted Result evidence could therefore reach Task Pool reads, while Reporting rejected the same chain only after execution. | Selection now owns one ordered SelectorInput Result-evidence assertion covering exact ID/digest resolution, Origin Agent/history/cutoff scope, and FeatureSnapshot Result provenance. Input construction, training, and prospective Runner reuse it before supply reads. |
| RI-050 | P0 | reproduced, resolved 2026-07-23 | Result cache-identity links to Agent/Task/Check records were maintained independently by Result Store, Selection, and Reporting. A fully redigested pre-origin Result/Snapshot/Input/Selection chain could drift those fields and reach supply reads or execution before Reporting rejected it. | Records now owns direct Agent projection and Task/Check mismatch functions. Strict Runner checks the frozen Agent projection before pool reads, then replays Origin and Task/Check identity against the validated selection-time pool before reading the future pool or invoking Agents. Result Store, Selection, and Reporting reuse the same field contract. |
| RI-051 | P0 | reproduced, resolved 2026-07-23 | `task_metadata` FeatureRecords were only checked for Origin membership and cutoff. A fully redigested FeatureSnapshot/SelectorInput/Selection chain could change `task_stratum`, deterministically select a different benchmark, and reach the future Task Pool while its value, observation time, and source digest disagreed with the frozen TaskRecord. | Selection now owns direct Task metadata provenance replay. Snapshot construction, strict Runner, and Reporting verify Origin/config binding, exact `task_count`, and exact `task_stratum` coverage/value/time/source against the validated selection-time Task Pool. Unknown Task metadata fails closed. |
| RI-052 | P1 | reproduced, resolved 2026-07-23 | `FeatureConfig` accepted empty, duplicate, and unknown feature names, silently ignored unknown names during extraction, and let callers separately declare leakage classes. Permutations and no-op entries therefore produced different config digests for the same executable builder behavior. | `FeatureConfig` now accepts only feature names, rejects empty/duplicate/unsupported inputs, normalizes them to the explicit builder order, and derives leakage classes from a three-entry name-to-class map. Production callers no longer maintain a redundant class list. |
| RI-053 | P0 | reproduced, resolved 2026-07-23 | Learned-Selector training compared only `agent_ids` across Origins. A fully redigested Input/Selection/Matrix/Metric chain could use the same ID with a changed model/prompt/harness digest; even changing every Input consistently while retaining Results from the old Agent was accepted. | Training now requires one ordered `(agent_id, agent_record_digest)` treatment across all Origins and projects every bound training Result cache identity back to that frozen Agent digest before fitting. |
| RI-054 | P0 | reproduced, resolved 2026-07-23 | Learned-Selector training had only Task Pool IDs/digests from Origins, not the frozen Task/Check records. A fully redigested Result/Matrix/Metric chain could change every Result base commit or Check identity and still fit. Snapshot Task metadata also could not be source-replayed at training time. | Selection training now explicitly receives the common Task Pool and records. Runner loads them from the validated bundle. Training replays all Origins and Snapshots, plus every pre-origin and outcome Result Task/Check cache projection, before fitting. |
| RI-055 | P0 | reproduced, resolved 2026-07-23 | Reporting traced a bound Matrix cell to its Result ID, Agent/Task/Check, and required cache identity but omitted outcome. A fully redigested CellSet/Matrix chain could claim a different outcome while retaining the original Result. Runner scoring treated the same contradiction as a missing cell instead of rejecting it. | Records now owns one direct seven-field ResultCell-to-Result mismatch predicate covering Result ID/digest, Agent/Task/Check, required identity, and outcome. Result Store, Runner, Selection training, and Reporting use it; contradictory bound outcomes fail closed. |
| RI-056 | P0 | reproduced, resolved 2026-07-23 | Batch evaluation structurally validated reused CellSets, then executed pending Selector cells, and only during scoring resolved the reused CellSets' bound Results. A drifted reused outcome could therefore cause an unrelated paid Agent call before RI-055 rejected it. | Runner batches all Result IDs bound by reusable CellSets into one read and applies the complete ResultCell predicate before missing-result planning or Agent execution. Genuine persisted missing/abstained evidence remains immutable and reusable. |
| RI-057 | P0 | reproduced, resolved 2026-07-23 | Runner loaded Results from every bound Matrix cell, including `excluded`, but Selection's exact training coverage considered only `result` cells. Valid common benchmark exclusions were rejected as extra Results through Runner, while a direct trainer could omit the excluded evidence entirely. | Training now requires and validates the Result for every cell carrying a Result ID/digest, independent of cell state. Truly unbound excluded and missing cells remain skipped. A `complete_with_exclusions` training specification covers both acceptance and missing-evidence failure. |
| RI-058 | P0 | reproduced, resolved 2026-07-23 | Exact ResultCell fields did not prove that a Matrix cell's `excluded` state and reason were justified. A normal passing Result could be marked as a common exclusion, removed from the denominator, and still support a Reporting identity claim or learned-Selector fit. | Result Store now reconstructs allowed Matrix cells from exact Results: benchmark-invalid is task-wide with its canonical reason, agent-invalid follows a supported policy, and normal Results cannot invent exclusions. Selection training and Reporting share the check. |
| RI-059 | P0 | reproduced, resolved 2026-07-23 | RI-058 initially accepted each agent-invalid cell against either supported policy independently. One Matrix could therefore exclude one invalid Result and count another as failure even though no single join policy could produce that denominator. | Result Store now reconstructs the complete Matrix under each supported `ResultJoinConfig` and accepts it only when one whole configuration matches. Selection and Reporting inherit the same Matrix-wide contract without a new policy registry or persisted config record. |
| RI-060 | P0 | reproduced, resolved 2026-07-23 | Matrix cells could match a supported policy while the redigested record declared another join/denominator policy. A policy-derived abstention reason could also be renamed. Metrics and reports would then compare or describe evidence under a false policy identity. | Result Store now replays all four currently executable missing-cell/agent-invalid combinations and requires one exact match across join and denominator digests, cells, abstention reason, and scoreable state. The builder and validator share the agent-exclusion predicate; no registry or new record was added. |
| RI-061 | P1 | reproduced, resolved 2026-07-23 | Replicate campaign authority creation trusted annotations for several runtime inputs. A string `pricing_sources` value was persisted as characters; non-string endpoint, scope, or accounting values could publish a ledger that later validation rejected, while overwrite protection prevented correction. | The initializer now validates its timestamp, every non-empty string, and the non-string sequence of non-empty pricing-source strings before creating either ledger file. Six public malformed-input cases assert zero file side effects. Small helpers keep the validator below the structural threshold. |
| RI-062 | P0 | reproduced, resolved 2026-07-23 | Result writes enforced one digest per `result_id`, but loading an existing JSONL accepted duplicate IDs. Callers then disagreed: raw queries kept both, the live session indexed the first, and reused-CellSet preflight indexed the last. A damaged store could therefore resolve evidence differently by path. | The one shared Result Store loader rejects every second `result_id` occurrence, identical or conflicting, with a line-numbered error before filtering or indexing. Ordinary and locked-session reads share the rule; the linear uniqueness pass does not change load complexity. |
| RI-063 | P1 | reproduced, resolved 2026-07-23 | Runner's companion-log append helper returned on the first matching semantic ID. If the existing log contained a second identical or conflicting ID, append reported an idempotent resume while later ID-based readers rejected the same log or other consumers observed duplicate cardinality. | The shared append path scans the complete existing log and rejects every duplicate semantic ID before matching or appending. Same-digest and first-observation-time resume semantics are unchanged; the uniqueness set is linear beside the existing full parse. Two Selection-log cases cover identical and conflicting duplicates. |
| RI-064 | P0 | reproduced, resolved 2026-07-23 | Reporting validated each top-level record but did not require unique Selection, CellSet, Matrix, or Metric IDs before grouping them. `benchmark_selection_frozen` remained supported for duplicate Selection evidence. The direct Result report and Agent/Result identity claim likewise accepted duplicate Result or Agent IDs through last/first-wins indexes. | Reporting now applies one linear semantic-ID uniqueness check at each claim boundary. Result summaries reject duplicate Result/Agent IDs; frozen-Selection and cache claims reject duplicate Selection/Matrix IDs; Selector performance additionally rejects duplicate CellSet/Metric IDs; Agent/Result identity rejects duplicate Matrix/Result/Agent evidence. Six public cases cover every path. |
| RI-065 | P0 | reproduced, resolved 2026-07-23 | Task Pool SourceEvent coverage compared candidate-ID sets. Two distinct certification-rejected SourceEvents could therefore reuse one `candidate_id`, match the same evidence and rejection reasons, inflate the source denominator, and still make `validate_task_pool_artifacts` return success. | The existing SourceEvent collection pass now requires every non-null `candidate_id` to be unique before set coverage is evaluated. Excluded/right-censored events retain null candidate IDs. One fully redigested public bundle counterexample now fails closed. |
| RI-066 | P1 | reproduced, resolved 2026-07-23 | `certification_evidence_records` canonically sorted evidence by candidate ID, but persisted Task Pool validation accepted a reordered sequence and only compared rejected candidate sets. A redigested bundle could therefore claim a valid producer replay with noncanonical evidence and rejected-ID order. | Artifact validation now requires certification evidence in candidate-ID order and exact ordered rejected-candidate coverage. The shared Runner Task Pool fixture was corrected to use the same producer order. |
| RI-067 | P0 | reproduced, resolved 2026-07-23 | Runner certifies every candidate in one Task Pool with one WorkspaceConfig and one RuntimeConfig, but persisted validation only required those per-record digests to be non-empty. Accepted and rejected candidates certified under different environments could be mixed into one redigested, apparently comparable pool. | Task Pool artifact validation now requires exactly one non-empty Workspace digest and one Runtime digest across all certification evidence. Reference-patch and Check-execution binding digests remain candidate-specific. One two-record characterization covers both drift axes. |
| RI-071 | P1 | reproduced, resolved 2026-07-23 | Direct SourceEvent validation treated a scalar string or mapping `rejection_reasons` as an iterable of valid reasons and raised `TypeError` for an integer. A self-digested record could therefore validate and serialize but fail latest-schema reload, or make a validator raise instead of returning errors. | SourceEvent rejection reasons must be a tuple of non-empty strings before element checks. Disposition binding, reason shape/content, and material maturity are separate direct checks. Three public malformed-container cases now return a failed `ValidationResult`; the existing empty-reason and material-time behavior is unchanged. |
| RI-072 | P1 | reproduced, resolved 2026-07-23 | ResultCell state validation used truthiness for payload fields. A result cell with `exclusion_reason=""`, an excluded cell with a non-string reason, or result bindings made from truthy non-strings could validate in memory but fail schema reload after serialization. | Records now requires nonempty string Result bindings, exact null exclusion on result cells, a nonempty string exclusion reason on excluded cells, and either two nonempty string Result bindings or two nulls. State dispatch and the three payload checks are direct helpers; existing error order and Matrix scoreability derivation remain intact. |
| RI-073 | P1 | reproduced, resolved 2026-07-23 | Metric dimension and completeness validation used truthiness. Scalar strings could masquerade as Agent pairs; non-string Agent IDs, aggregation levels, optional refs, and abstention reasons were accepted; unused dimensions could use empty strings instead of null. Self-digested Metrics could validate in memory but fail or change shape on JSONL reload. | Records now requires exact dimension shapes: one nonempty Agent ID, one two-element tuple of nonempty Agent IDs, or one nonempty aggregation level, with unused dimensions null. Optional budget/stratum refs and incomplete-state reasons are nonempty strings when present. Dimension, optional-reference, and completeness checks are direct helpers; seven public malformed-shape cases pass. |
| RI-074 | P0 | reproduced, resolved 2026-07-23 | `CertificationResult.accepted` was trusted by truthiness. An integer `1` with otherwise valid accepted evidence passed SourceEvent finalization and `freeze_task_pool`, so a non-boolean decision could enter a valid immutable Task Pool bundle. | Certification evidence serialization, SourceEvent finalization, and frozen-result indexing share one exact `bool` guard. Finalization separately indexes complete candidate coverage, projects each SourceEvent, then orders and validates the records; cross-artifact Task/Check/evidence reconciliation remains only at freeze. Three public-boundary counterexamples now fail closed. |
| RI-075 | P1 | reproduced, resolved 2026-07-23 | `validate_task_pool_artifacts` correctly classified a non-object certification-evidence item, then SourceEvent linkage unconditionally called `.get()` on the same item and raised `AttributeError`. A public validator therefore failed to return its accumulated evidence errors. | SourceEvent indexing ignores non-mapping evidence after the record parser reports it. The retained certification reconciler now delegates per-record parsing/semantics, record-set/config checks, accepted Task/Check coverage, and rejected/summary coverage to direct helpers. One public malformed-record case returns a failed `ValidationResult`; existing multi-error order remains characterized. |
| RI-076 | P0 | reproduced, resolved 2026-07-23 | Public `evaluate_selection` checked Selection/Origin IDs but not their eligibility modes. A re-digested Selection that claimed `strict_prospective` could be scored against a counterfactual Origin, same-pool CellSet, and matrices, producing ordinary MAE; Runner and Reporting rejected the relation only outside this scoring boundary. | Matrix alignment now rejects Selection/Origin eligibility-mode drift before Metric construction. Its ordered contract has 18 characterized reasons, including the three prospective branches previously missing from the “every branch” test, and delegates provenance, mode-specific denominator, and cell-identity phases to direct helpers. |
| RI-077 | P0 | reproduced, resolved 2026-07-23 | `ClaimConfig` exposed two unused-by-production switches that could weaken Matrix completeness and Metric validity requirements; they also accepted integer truth values. Malformed or behavior-equivalent requested-claim collections produced noncanonical identities. More seriously, `agent_result_identity` could be supported without any Agent record or with a supplied Agent whose execution identity disagreed with the Result cache identity; the Claim Boundary also omitted Agent manifests from its source digests. | ClaimConfig now has one axis: a unique supported claim tuple canonicalized to stable order. Matrix completeness and Metric validity are fixed claim semantics and cannot be disabled. The identity claim requires every Result Agent to exist and match the Agent projection frozen in its cache identity, and records Agent manifest digests in the report. `build_claim_boundary` evaluates only requested claims and directly orchestrates five claim predicates; local Selection/Matrix/Metric/CellSet evidence phases and existing provenance replay remain separate without a context object or registry. |
| RI-078 | P0 | reproduced, resolved 2026-07-23 | `MetricConfig` had no scoring-behavior fields: callers supplied an arbitrary `metric_config_digest` and an optional budget digest already frozen by Selection. Identical scoring could therefore receive different evidence identities. Separately, `evaluate_selectors` appended a valid first Selector before discovering that a later Selector had invalid executable parameters. | Selection now derives one versioned metric-protocol digest from the ordered implemented metric names and aggregation level; every Metric binds the Selection's frozen budget, and the identity-only `MetricConfig` plus its public parameters are removed. Add a configuration axis only when it changes concrete scoring behavior. Runner materializes and validates the complete Selector batch, including executable parameters, then validates Agents, mode, and origin schedule before Task Pool reads or companion writes. The `MetricRecord` schema and retained final-form Selector path are unchanged. |
| RI-080 | P1 | reproduced, resolved 2026-07-23 | `WorkspaceArtifactConfig.path_mode` exposed a one-value placeholder because absolute artifact refs are forbidden. Its stdout/stderr and diff switches accepted truthy non-booleans, so a caller-provided `"false"` could retain material unexpectedly; malformed summary containers failed only at execution. | Relative refs below `output_root` are now a fixed artifact-hygiene invariant. The placeholder path field and one-use runtime validator are removed. The two retention switches require exact booleans, and both summary modes validate at config construction. Four public malformed-control cases and all 71 Workspace tests pass. |
| RI-081 | P0 | reproduced, resolved 2026-07-23 | `CertificationConfig` accepted boolean, float, string, null, and nonpositive repeat counts. In particular, `True` executed one base/patched Workspace pair but serialized a boolean count that persisted validation rejects; other malformed values failed only later in certification. | `repeat_count` now requires an exact positive integer at config construction. The weaker runtime `< 1` branch is removed, so malformed values cannot execute checks or enter a certification-config digest. Six public malformed-control cases and all 63 Task Pool tests pass. |
| RI-082 | P1 | reproduced, resolved 2026-07-23 | `ReportConfig` accepted absolute paths, traversal, nested paths, and swapped Markdown/JSON suffixes as “filenames”. Because an absolute right operand overrides `output_dir`, a report write could escape its configured directory; wrong suffixes could also write the wrong serialization. | Markdown and JSON outputs now require direct, whitespace-stable `.md` and `.json` filenames at config construction. Both slash forms, absolute/nested/traversal paths, and swapped suffixes fail before evidence loading or report writes. Six public cases and all 56 Runner tests pass. |
| RI-083 | P0 | reproduced, resolved 2026-07-23 | After RI-078 made Metric construction implementation-owned, training, paired Selector comparison, and Reporting still accepted any internally consistent `metric_config_digest`. A fully redigested unknown protocol with recomputable coincident values could therefore train a Selector or support a performance trace. | Selection now preflights every consumed Metric against the current versioned protocol before training or paired comparison; Reporting marks an unknown protocol unsupported before value recomputation. Records remains version-neutral so evidence can load and fail at the algorithm boundary. One shared batch guard replaces “all arbitrary digests equal” state without a registry or schema change. Two public counterexamples and all 229 Selection/Reporting tests pass. |
| RI-084 | P0 | reproduced, resolved 2026-07-23 | `future_holdout_known` was interpreted by truthiness in both `RollingOriginPolicy` and persisted Origin validation. Values such as `"false"`, `0`, or `1` could change cohort behavior or create a second policy/origin identity without being booleans. | Policy construction and `RollingOriginRecord` validation now require an exact boolean before strict/counterfactual branching or behavior-digest use. Four constructor counterexamples and one fully redigested record counterexample fail closed. |
| RI-085 | P0 | reproduced, resolved 2026-07-23 | Raw Check state was coercive: `exit_code=False` compared equal to pass code 0, a string `"false"` timeout became true, and boolean, negative, or nonfinite durations could produce scoreable outcomes or invalid measurements. | `normalize_outcome` now accepts only an exact boolean timeout, an integer-or-null exit code excluding booleans, and a finite nonnegative numeric duration. Malformed execution state becomes normalized benchmark-invalid evidence with zero duration; five public counterexamples can no longer score as pass. |
| RI-086 | P0 | reproduced, resolved 2026-07-23 | `CheckNormalizationConfig` allowed pass and invalid exit-code sets to overlap, accepted boolean exit codes and truthy text controls, and deferred malformed labels, excerpt bounds, or redaction markers until normalization. Because pass codes are checked first, an overlapping invalid code could become pass. | The config now validates its small direct contract at construction: integer code tuples are disjoint, failure labels are nonempty strings, excerpt length is a positive integer, markers are strings, and the raw-text switch is an exact boolean. Six public malformed configs fail before Check evidence is interpreted. |
| RI-088 | P0 | reproduced, resolved 2026-07-23 | Rolling-origin dependency filters accepted scalar strings and non-string tuple members. A value such as `(1,)` entered policy/origin identity, matched no string Task cluster, and could silently empty a cohort; mixed or unhashable values could also make validation raise. | Policy construction and persisted Origin validation require one tuple of nonempty strings before duplicate/sort checks or cohort filtering. Two constructor cases and one fully redigested record case fail closed without adding a cluster abstraction. |
| RI-089 | P0 | reproduced, resolved 2026-07-23 | The only two persisted fields declared as `float` accepted integer values during record validation. A fully redigested Selection with weight `1` or Metric with value `0` validated in memory and could be appended, but latest-schema loading normalized it to `1.0` or `0.0` and rejected the original line as noncanonical. | `BenchmarkSelectionRecord.selected_weights` now requires finite positive built-in floats and `MetricRecord.metric_value` requires a finite built-in float. Production builders already emit floats, and Runner companion logs already validate before append, so two public red specs close the write boundary without changing the loader, schema, or generic writer. |
| RI-090 | P1 | reproduced, resolved 2026-07-23 | `ScoringConfig` accepted integer and float forms of the same cost rate but digested their JSON representations differently, so identical pricing behavior could create redundant Result pricing views. Its frozen dataclass also retained the caller's mutable rate mapping; changing that source dictionary changed the config digest after construction. | Construction now validates the pricing version and rate mapping, normalizes every finite nonnegative numeric rate to a float in sorted key order, and stores a read-only snapshot. Equivalent numeric inputs share one digest, source and attribute mutation cannot drift it, and Runner retains the pre-Agent defensive recheck. Six red public cases close the boundary without adding a pricing schema or registry. |
| RI-091 | P2 | reproduced, resolved 2026-07-23 | `select_benchmark` represented an absent pre-origin Result lower bound by constructing `TimeRange("", cutoff)`. Every real TimeRange consumer requires parseable timestamps, so this one invalid sentinel overloaded a window type only to extract its empty `start` field; ResultQuery then interpreted the empty string as null by truthiness. | The shared pre-origin loader now accepts the actual contract, `result_available_after: str | None`. Selection-only calls pass null and rolling evaluation passes `history_window.start`; the public ResultQuery observation spec covers both. TimeRange, ResultQuery, and rolling-window semantics remain unchanged. |
| RI-092 | P0 | reproduced, resolved 2026-07-23 | Public persisted-record validators checked strict canonical JSON values and domain relations, but not the declared latest-schema scalar types. Task, Check, and Agent records with integer IDs each returned a successful `ValidationResult`; writing the same canonical line then failed reload because the loader requires strings. | Public record validation reuses the existing dataclass schema conversion as its initial gate. The three reproduced integer-ID shapes fail before domain semantics or evidence append/publication. No deep-freeze utility, schema registry, or second type system was added. |
| RI-093 | P0 | reproduced, resolved 2026-07-23 | `TaskPoolRecord` was the only top-level persisted evidence record whose artifact validator did not pass through the Records schema contract. A fully redigested pool with integer `generator_config_digest` passed Task/Check/certification/SourceEvent reconciliation but could not reload from its own published JSONL. | Records now owns a direct Task Pool required-shape, latest-schema, and self-digest validator. Task Pool member validation calls it and removes the duplicate local self-digest branch, so freeze, publication, loading, Runner, and Reporting share the same record check. One public bundle counterexample fails closed. |
| RI-094 | P1 | reproduced, resolved 2026-07-23 | Candidate import/filtering used `str(...)` on source identity, explicit candidate ID, task text, solver refs, dependency cluster, sampling stratum, and Check fields. The default candidate ID was computed from raw values before coercion, so integer and string spellings could create different candidate identities for the same emitted Task/SourceEvent text; excluded events also coerced labels without entering the candidate parser. | The direct candidate parser now requires declared string fields, validates solver-ref and resource-limit container shapes, and derives the default candidate ID only from validated values. Excluded SourceEvents use the same label rule. Nine public ingress cases cover accepted and pre-certification-excluded paths without adding a candidate schema class or ingestion framework. |
| RI-095 | P1 | reproduced, resolved 2026-07-23 | Stratified-forecast `dirichlet_alpha` and `weight_cap` accepted integer and float forms with identical algorithm behavior but different canonical JSON, `config_digest`, and `selector_id`. Fixed-rule construction also retained caller-owned nested group mappings, so later source mutation drifted a frozen Selector's parameters away from its digest. | The existing family-specific parsers now return one canonical parameter snapshot before Selector identity is derived: continuous values are floats and nested mappings are copied in stable key order. Executable external Selector records must already match that shape. Three public specs cover equivalent numeric forms, noncanonical self-digested records, and source-map mutation without adding a config class, registry, or deep-freeze framework. |
| RI-096 | P1 | reproduced, resolved 2026-07-23 | `freeze_task_pool` converted every required metadata field and optional `task_pool_id` with `str(...)`. Numeric repository IDs, artifact refs, config digests, or IDs could therefore cross the publication boundary as apparently valid string evidence, often failing only in an unrelated later relation check. | The existing metadata preflight now returns only required nonempty strings and rejects a non-string optional Task Pool ID. Freeze uses those validated values directly. Nine public cases cover every persisted metadata string; no metadata dataclass, schema layer, or compatibility conversion was added. |
| RI-097 | P1 | reproduced, resolved 2026-07-23 | Rule-mixture inference divides expert weights by their total. Scaling all weights, omitting a zero-weight expert, spelling the same zero explicitly, or using signed zero therefore preserved ranking behavior while creating different parameter, config, and Selector digests. A naive divide-by-total canonicalization also drifted by one ULP on a second pass for some extreme ratios. | Construction writes coverage/random/recency as complete built-in-float weights on one unit simplex and corrects at most one largest component by one ULP so `fsum` is exactly one. External records with scaled or omitted weights remain noncanonical; RI-102 later made signed-zero spelling globally identity-equivalent through canonical JSON. Two rejection cases, one signed-zero identity case, the fitted-trainer contract, 10,000 deterministic randomized probes, and all 169 Selection tests pass without changing the trainer or record schema. |
| RI-098 | P1 | reproduced, resolved 2026-07-23 | `ScoringConfig` normalized numeric rates to floats but preserved `-0.0`. Positive and negative zero computed the same costs yet serialized differently and produced different scoring-config digests, leaving two pricing-view identities for one behavior. | Existing construction maps either zero spelling to positive `0.0` before the immutable sorted snapshot and digest are created. One public spec proves identical identity and canonical JSON; no pricing schema or registry was added. |
| RI-099 | P0 | reproduced, resolved 2026-07-23 | A self-digested `TaskPoolRecord` with integer `created_at` produced the expected latest-schema error, but artifact reconciliation then passed that value to the shared UTC parser, which called `.endswith` and raised `AttributeError`. The public artifact validator therefore interrupted instead of returning its collected errors. | The existing `parse_utc_timestamp` contract now rejects a non-string with `ValueError`. The Task Pool artifact counterexample and direct timestamp contract both return/fail through their declared validation surfaces; no Task Pool exception fanout or second timestamp helper was added. |
| RI-100 | P0 | reproduced, resolved 2026-07-23 | Latest-schema replay ran only at the end of public record validation. Schema-invalid task text, sequences, nested cache identities, rolling-origin refs, feature records, and matrix/cell containers could therefore raise in domain semantics before reaching it. | The existing `_from_data` conversion moved to initial validation; a schema-invalid shape returns immediately and valid records no longer pay for a duplicate final replay. Three public cases cover string, sequence, and nested-record failures. A temporary one-field audit across all 16 public validators and 256 fields found zero base failures and zero exceptions. No validation framework, schema registry, or compatibility mode was added. |
| RI-101 | P0 | reproduced, resolved 2026-07-23 | Complete Task Pool artifact validation collected a top-level schema error but continued into member, certification, and SourceEvent reconciliation. Setting `rejected_candidate_ids=7` therefore reached `set(...)` in source-event coverage and raised `TypeError`, despite the Records validator already identifying the field as a non-array. | Validation now has two direct prerequisite gates: member validation returns immediately for an invalid `TaskPoolRecord`, and complete artifact validation returns immediately for an invalid record/member layer. Certification and SourceEvent reconciliation run only after those inputs are valid. One red public case and a temporary disturbance of all 20 Task Pool record fields found zero exceptions. No per-field catch list, validation framework, or new artifact layer was added. |
| RI-102 | P1 | reproduced, resolved 2026-07-23 | Result latency and Metric value records could replace `0.0` with `-0.0`, remain numerically equal and valid, yet serialize differently and produce different self-digests. Field-specific rejection would leave the same split in nested Feature values, Selector parameters, and other JSON payloads. | The one shared `canonical_data` boundary now emits every built-in floating zero as positive `0.0`. Canonical JSON, all record/config digests, writers, and strict loaders therefore use one representation at any nesting depth. One red canonical JSON/digest spec and direct Result/Metric probes prove the identity collapse. ScoringConfig keeps its existing in-memory normalization; no per-field registry or alternate encoder was added. |
| RI-103 | P0 | reproduced, resolved 2026-07-23 | Task Pool member validation ran Task/Check linkage before the existing record validators. Replacing `TaskRecord.check_ids` with an integer therefore raised `TypeError` during iteration, even though `validate_task` would have returned the exact latest-schema error. | The accepted-record prerequisite now validates each Task and Check before repository, digest, ID, or linkage relations. An invalid member returns immediately; valid members continue through the same direct relations. One red public bundle case and a temporary disturbance of all 21 Task/Check fields found zero exceptions. No member wrapper, schema copy, or catch list was added. |
| RI-104 | P1 | reproduced, resolved 2026-07-23 | `ResultQuery` had no boundary validation. A numeric filter returned `()` while the Result Store was absent, then raised `TypeError` after the same store contained a Result. Empty-string time bounds silently meant unbounded, and an inverted interval silently returned no matches. Query validity therefore depended on store state and could hide an incomplete Result view. | The existing `_query_time_bounds` entry step now validates all six filters as tuples of nonempty strings, requires each time bound to be null or a nonempty timezone-aware string, and rejects `after > before` before checking store existence. Eleven red public cases and all 76 Result Store tests pass. No query schema class, normalization object, or index was added. |
| RI-105 | P0 | reproduced, resolved 2026-07-23 | `build_result_record` validated WorkspaceRun and cache projections but not the supplied Task, Check, or Agent records before relations. Nine schema-invalid Task/Check fields that did not alter projected digests were accepted into a valid Result, while integer `TaskRecord.check_ids` raised `TypeError` during linkage. | Result construction now reuses all four existing record validators before linkage and cache-identity checks. Five public red cases cover Task scalar/container, Check, Agent, and WorkspaceRun shapes. A temporary disturbance of all 52 input fields found zero accepted invalid inputs and zero leaked exceptions. No Result-input wrapper, copied schema, or validation framework was added. |
| RI-106 | P0 | reproduced, resolved 2026-07-23 | `compute_result_cache_identity` can be called directly by missing-cell and cache-reuse planning, but it constructed identity before validating Task, Check, or Agent. Fifteen schema-invalid fields that were absent from the projection were accepted, while integer `TaskRecord.check_ids` leaked `TypeError`; later Result construction was not a sufficient guard for these direct callers. | Cache identity and Result construction now share one direct Task/Check/Agent record prerequisite, and both reuse one Task/Check linkage check. Four public red cases cover Task scalar/container, Check, and Agent shapes. Repeating the deterministic disturbance of all 36 fields found zero accepted invalid inputs and zero leaked exceptions. No input wrapper, copied schema, or validation framework was added. |
| RI-107 | P0 | reproduced, resolved 2026-07-23 | Exact cache-identity construction also lacked WorkspaceConfig and RuntimeConfig shape validation. Six schema-invalid fields absent from the direct identity projection, including the runtime timeout, produced valid-looking cache identities; an empty optional hardware digest was accepted as a third state beside null or a real digest. | Records now owns two direct config validators built on the existing latest-schema conversion. Result Store applies them before identity construction, requiring exact nonempty identity strings, a positive integer timeout, and null-or-nonempty hardware identity. Six public red cases and 13 deterministic type/semantic disturbances pass with zero accepted invalid inputs and zero leaked exceptions. No config wrapper, schema copy, or validation framework was added. |
| RI-108 | P0 | reproduced, resolved 2026-07-23 | Task Pool certification accepted invalid WorkspaceConfig/RuntimeConfig IDs, executed its first base Check, and then wrote digests of those malformed configs into certification evidence. Result Store validation could not protect this independent evidence-producing path. | `certify_task_candidate` now applies both Records-owned config validators before Task/Check construction or Check execution. Two public red cases replace either config ID and prove the Check runner is never called. No certification context or copied config schema was added. |
| RI-109 | P0 | reproduced, resolved 2026-07-23 | Workspace `preflight_run_bindings` accepted invalid WorkspaceConfig/RuntimeConfig IDs, including with an empty plan, while validating only Runtime timeout through a local branch. Direct Workspace callers could therefore cross the execution preflight with configs rejected by Result Store and Task Pool. | Workspace now applies both full shared validators before repository or plan state, so plan emptiness cannot change config validity. Runner reuses `validate_runtime_config` instead of hand-coding timeout type checks; the existing no-cell preflight remains. Two red public cases and the existing timeout contract pass, and `_run_agent_cells` loses two Lizard branches without hiding orchestration. |
| RI-110 | P1 | reproduced, resolved 2026-07-23 | Workspace repository binding accepted an invalid WorkspaceConfig and stored its repository source under `repository_checkout_config_digest`; later execution preflight rejected the same object. This made the immutable context boundary weaker than Agent and Check binding and allowed direct workspace construction to start from malformed config state. | `bind_repository_source` now applies the Records-owned WorkspaceConfig validator before examining the repository or returning a new context. Execution preflight retains its just-in-time recheck. One public red case closes the binding boundary without changing context keys or adding a registry. |
| RI-111 | P1 | reproduced, resolved 2026-07-23 | Runner Task Pool construction resolved candidates and repository commits before discovering malformed WorkspaceConfig/RuntimeConfig during per-candidate certification, repeating the same validation for every candidate. | `build_task_pool` now validates both configs once before candidate resolution; `certify_task_candidate` retains its pre-Check revalidation for direct calls and drift defense. Two public red cases prove candidate resolution is not reached. No TaskPoolConfig wrapper or generic preflight framework was added. |
| RI-112 | P1 | code-confirmed, resolved 2026-07-23 | The frozen Pylint schedule and campaign authority were executable only by manually assembling `ReplicateCampaignContext` in Python. That left endpoint-time file loading and action selection to ad hoc code immediately before an evidence-producing run. | `replicate_campaign_cli.py` loads the exact Agent, Runtime, schedule, Task Pool, and local Pylint bindings. It provides only explicit authority creation, no-call preflight, and one-cell execution; verifies pinned verifier-image digest, architecture, and base commit before a paid cell; confines campaign artifacts below one directory; and returns bounded JSON summaries. It does not generate experiment inputs or loop over paid cells. |
| RI-113 | P1 | maintainer decision | future-work | Expanding Task supply before the model endpoint exists assumes a Task Generator. Some intended generators may be LLM-driven, while deterministic importers have different source and certification prerequisites. | Do not build a generic generator or expand a pool without selecting one concrete source. Resume with an adapter-specific generator when its data and, where required, model endpoint are available; reuse the existing candidate, certification, SourceEvent, and immutable publication contracts. |

Decisions from the 2026-07-22 maintainer review:

- Complete RI-001 through RI-009. They are parts of the target evidence and
  Selector contracts, not optional abstractions.
- Implement RI-010 through RI-013 as focused refactors because they remove
  ambiguity and global state without changing the module graph.
- Resolve RI-014 by simplifying the representation while retaining prospective
  freeze evidence.
- RI-015 extracted only the duplicated single-writer ledger persistence needed
  by the planned replicate experiment; it did not add a general experiment API.
- Do not remove RollingOrigin, FeatureSnapshot, SelectorInput, training-source
  provenance, or the `train_selector` boundary because current rules underuse
  them.

### RI-034 Structural Audit Boundary

The scoped scan covered the 37 version-controlled Python files under `src`,
`examples`, and `scripts`. The first whole-worktree attempt also traversed
ignored historical virtual environments and failed on third-party source, so
those artifacts were excluded rather than treated as project debt. Early scans
had no coverage input. The current 38-file scan uses a temporary offline
coverage.py run of the full suite, with conservative 0% entries for non-imported
scripts/hidden checks and conventional 100% entries for two empty `__init__.py`
files. Signal health is now full. Coverage remains routing
evidence, not proof that a function is risky in production, and the temporary
artifact is not committed as a baseline.

After fifty evidence-boundary slices, the repository verdict remains
`strained`.
The original 37-file scan had 108 hotspots, 22 `refactor_now`, and
Ruff/Lizard/Complexipy critical counts of 8/31/8. The current 38-file scope,
which also includes the new replicate campaign executor, has 116 hotspots, 3
retained `refactor_now`, 43 `refactor_soon`, 70 `monitor`, and critical counts
of 0/21/0. Two later offline algorithm additions account for the two new
monitor entries: the Reporting stratified-diagnostic orchestrator and the
public EWMA evidence orchestrator. Both retain explicit evidence parameters
instead of adding one-use bundles. A later Selector-choice validation slice
removed one `refactor_soon`; the certification-attempt state helper moved a
second item from `refactor_soon` to `monitor`. The paired-MAE slice is directly
comparable within `selection/evaluation.py`: hotspots moved from 15 to 17 as
focused helpers became visible, `refactor_now` fell from 5 to 4, and critical
counts fell from 2/3/1 to 1/2/0. Its new helpers are monitor-only. The
Selector-provenance slice is directly comparable within `reporting.py`:
hotspots moved from 12 to 14, `refactor_now` fell from 5 to 4, and critical
counts fell from 2/5/2 to 1/5/1. `_selector_provenance_errors` fell from 177
NLOC / CCN 40 / cognitive 70 / Ruff 33 to 68 / 3 / below threshold / below
threshold. It remains `refactor_soon` only because its explicit evidence
contract has 11 parameters; a one-use argument bundle would add indirection
without reducing responsibility. The new indexing and required-evidence
helpers are monitor-only, and the other extracted helpers are below hotspot
thresholds. In a second directly comparable Reporting scan,
`_append_selector_input_link_errors` fell from 134 NLOC / CCN 35 / cognitive 54
/ Ruff 27 to 78 / 17 / 21 / 15. Reporting's hotspot count stayed at 14 while
`refactor_now` fell from 4 to 3 and critical counts fell from 1/5/1 to 0/4/0.
The two new helpers are below hotspot thresholds. The remaining linker is a
direct Selection/Origin/Snapshot/Agent consistency list; further extraction
would only move those checks behind forwarding functions. The Selector-report
slice is also directly comparable within `reporting.py`:
`build_selector_report` fell from 334 NLOC / CCN 70 / cognitive 48 / Ruff 11
to 132 / 12 / below threshold / below threshold and moved from `refactor_now`
to `monitor`. Reporting hotspots moved from 14 to 16 as pure row and digest
helpers became visible, `refactor_now` fell from 3 to 2, and critical counts
fell from 0/4/0 to 0/3/0. The new Selection-row and source-digest helpers are
monitor-only; the remaining helpers are below hotspot thresholds. The
Result-report slice is directly comparable within `reporting.py`:
`build_result_report` fell from 139 NLOC / CCN 33 / cognitive 30 to 44 / 7 /
below threshold after the earlier latency extraction. Reporting hotspots stayed
at 16, `refactor_now` fell from 2 to 1, and critical counts fell from 0/3/0 to
0/2/0. The new execution-state helper is monitor-only; the cost and limitation
helpers are below hotspot thresholds. The source-event slice is directly
comparable within `task_pool.py`: `_source_event_errors` fell from 122 NLOC /
CCN 42 / cognitive 58 / Ruff 25 to 74 / 12 / 16 / below threshold and moved to
`monitor`. Task Pool hotspots moved from 8 to 9, `refactor_now` fell from 3 to
2, and critical counts fell from 1/1/1 to 0/0/0. The accepted-event helper is
monitor-only; the other new helpers are below hotspot thresholds. The
coercion slice is directly comparable within `records.py`: `_coerce_value`
fell from 80 NLOC / CCN 42 / cognitive 63 / Ruff 27 to 16 / 8 / below
threshold / below threshold and left the hotspot list. Records hotspots stayed
at 9, `refactor_now` fell from 4 to 3, and critical counts fell from 1/2/1 to
0/1/0. The scalar helper is monitor-only; Union, tuple/list, and mapping helpers
are below hotspot thresholds. The training-input slice is directly comparable
within `selection/evaluation.py`: the cognitive/Ruff 46/27
`_validated_training_inputs` hotspot is replaced by snapshot indexing, input
indexing, and direct provenance-link validation. The active
`_validated_selector_inputs` helper is monitor-only at 20/13; evaluation
hotspots stayed at 17, `refactor_now` fell from 4 to 3, and critical counts fell
from 1/2/0 to 0/2/0. The training-Result slice is directly comparable in the
same file: `_validate_training_results` fell from 78 NLOC / CCN 23 / cognitive
40 / Ruff 15 to 12 / 1 / below threshold / below threshold and left the
hotspot list. Its indexing, per-cell binding, exact-coverage, and availability
helpers are all below hotspot thresholds. Evaluation hotspots fell from 17 to
16, `refactor_now` fell from 3 to 2, and critical counts stayed at 0/2/0. The
training-Metric slice is directly comparable in the same file:
`_validated_training_metrics` fell from 86 NLOC / CCN 26 / cognitive 33 / Ruff
17 to 17 / 1 / below threshold / below threshold and left the hotspot list.
Its indexing, provenance, recomputation, exact-coverage, completeness, and row
helpers are all below hotspot thresholds. Evaluation hotspots fell from 16 to
15, `refactor_now` fell from 2 to 1, and critical counts stayed at 0/2/0. The
training-ResultMatrix slice is directly comparable in the same file:
`_validated_training_matrices` fell from 73 NLOC / CCN 19 / cognitive 31 /
Ruff 18 to 15 / 1 / below threshold / below threshold and left the hotspot
list. Its indexing, provenance, role-pairing, and shared-future-evidence helpers
are all below hotspot thresholds. Evaluation hotspots fell from 15 to 14,
`refactor_now` fell from 1 to 0, critical counts stayed at 0/2/0, and the file's
routing pressure moved from `investigate_soon` to `watch_only`. The
FeatureSnapshot slice is directly comparable in `selection/features.py`:
`_ensure_feature_records_match_origin` fell from 55 NLOC / CCN 21 / cognitive
38 / Ruff 12 to 29 / 8 / below threshold / below threshold and left the
hotspot list. Scope/time and Result-provenance checks are now separate; the
Result helper is monitor-only, and the scope helper is below hotspot
thresholds. The file has no `refactor_now` hotspot and moved to `watch_only`.
The slice also closes RI-035 by rejecting Task, Check, or Agent fields that do
not match a FeatureRecord's bound Result. The RollingOrigin slice is directly
comparable in `selection/origin.py`: `build_rolling_origin` fell from
123 NLOC / CCN 22 / cognitive 36 / Ruff 13 to 88 / 6 / below threshold / below
threshold and moved to `monitor`. Member validation, cohort partitioning,
overlap policy, and record assembly are separate; the new cohort helper is
monitor-only. The file has no `refactor_now` or `refactor_soon`, and its verdict
moved from `strained/investigate_soon` to `stable/watch_only`. The slice also
closes RI-036 by rejecting missing Task Pool members and wrong Check owners
before denominator derivation. The certification-result slice is directly
comparable in `task_pool.py`: `_validated_certification_results` fell from 76
NLOC / CCN 25 / cognitive 39 / Ruff 17 to 16 / 4 / below threshold / below
threshold and left the hotspot list. Result indexing, exact frozen-pair
coverage, and Task/Check digest reconciliation are separate; the index helper
is monitor-only and frozen Checks use a direct index instead of a per-pair
scan. Task Pool hotspots stayed at 9, `refactor_now` fell from 2 to 1, and
critical counts stayed at 0/0/0. The certification evidence reconciler remains
listed because it directly performs five cross-record consistency checks;
further wrapper extraction would add
indirection without changing responsibility. The Cell-state slice is directly
comparable in `records.py`: `_validate_cells` fell from 45 NLOC / CCN 20 /
cognitive 35 / Ruff 15 to 30 / 8 / below threshold / below threshold and left
the hotspot list. Cell membership, state payload, exact full denominator, and
ResultMatrix scoreability are separate. Records hotspots stayed at 9,
`refactor_now` fell from 3 to 2, `refactor_soon` rose from 2 to 3, and critical
counts stayed at 0/1/0. The 30-line Result/excluded/missing payload state
machine remains centralized as an explicit audit surface. The slice also
closes RI-037 by rejecting incoherent Cell payloads and scoreability labels.
The RollingOrigin-validation slice is directly comparable in `records.py`:
`validate_rolling_origin` fell from 117 NLOC / CCN 36 / cognitive 34 / Ruff 22
to below every hotspot threshold. Mode, cohort, cluster, time, maturity,
cutoff-rule, and policy checks are separate; all new helpers are below hotspot
thresholds. Records hotspots fell from 9 to 8, `refactor_now` from 2 to 1, and
critical counts from 0/1/0 to 0/0/0. The slice also closes RI-038 by binding the
materialized cutoff to its rule and rejecting future windows before the cutoff.
The SourceEvent-validation slice is directly comparable in `records.py`:
`validate_source_event` fell from 83 NLOC / CCN 26 / cognitive 31 / Ruff 16 to
below every hotspot threshold. Material timestamps and disposition semantics
are separate; the material helper is below threshold. Records hotspots stayed
at 8, `refactor_now` fell from 1 to 0, `refactor_soon` rose from 3 to 4, and the
file moved from `investigate_soon` to `watch_only`; critical counts stayed at
0/0/0. The 39-line accepted/certification-rejected/excluded state machine
remains centralized as an explicit audit surface. The slice also closes RI-039
by returning errors for malformed times and rejecting empty reason strings.
The replicate-schedule input slice is directly comparable in
`examples/pylint_swe_bench_verified/replicate_schedule.py`: `_validate_inputs`
fell from 72 NLOC / CCN 37 / cognitive 32 / Ruff 20 to 21 / 1 / below threshold
/ below threshold. Protocol scalars, exact Task/Check members, paired Agent
treatments, and base Runtime validity are separate. File hotspots moved from 5
to 6 as the explicit member boundary became visible; `refactor_now` fell from 1
to 0, `refactor_soon` rose from 4 to 6, Lizard critical fell from 3 to 2, and
routing moved from `investigate_soon` to `watch_only`. The 27-line member helper
retains the direct one-Check-per-Task contract. The nine-parameter orchestrator
remains visible instead of adding a one-use input bundle. The slice also closes
RI-040 by rejecting invalid protocol scalar types and duplicate Agent
configurations before schedule construction.
The Pylint-pilot summary slice is directly comparable in `pilot.py`:
`summarize` fell from 119 NLOC / CCN 30 / cognitive 24 to below every hotspot
threshold. Exact Result selection, per-effort rows, paired rows, and completion
claims are separate. Pilot hotspots fell from 8 to 7, `refactor_now` from 1 to
0, Lizard critical from 1 to 0, and routing moved from `investigate_soon` to
`watch_only`; `refactor_soon` stayed at 1 and `monitor` at 6. All new helpers
are below hotspot thresholds. The slice also closes RI-041 by excluding Results
from other execution identities and requiring the completed ledger for a
complete summary.
The Selector-choice input slice is directly comparable in
`selection/evaluation.py`: `_validated_selector_choice_inputs` is now a small
orchestrator over registered-Selector validation and per-row coverage/value
normalization. Existing invalid registration, fallback, incomplete-row, and
invalid-value tests preserve the contract. Evaluation hotspots fell from 15 to
14 and `refactor_soon` from 4 to 3; `refactor_now` stayed at 0, `monitor` at 11,
and critical counts at 0/2/0. All new helpers are below hotspot thresholds.
At that slice, `_matrix_alignment_error` remained one ordered list because its
then-fourteen failure reasons and precedence were the responsibility. A
characterization covered those branches and verified that the earliest
mismatch wins. This raised
`selection/evaluation.py` combined coverage from 80% to 82% and its routing
branch fraction from 0.71 to 0.74 without changing hotspot counts.
The SelectorInput contract slice is directly comparable in `records.py`:
intrinsic membership/result-reference, budget, and Origin/feature checks are
three direct helpers, while the public validator retains identity and
self-digest ownership. `validate_selector_input` left the hotspot list; Records
now has 7 hotspots (0 now / 3 soon / 4 monitor), and the full scan fell from 119
to 118 hotspots and from 45 to 44 `refactor_soon`. The slice also closes RI-042:
the selection limit derives its budget digest, Agent IDs and eligible refs are
unique, the cutoff is canonical UTC, and Reporting no longer mistakes supplied
Agent-record order for a different set. Frozen SelectorInput and ResultMatrix
order remains exact. Selection removed its duplicate uniqueness checks.
The retained Task Pool certification reconciler now has executable specs for
malformed records, non-boolean acceptance, duplicate candidate IDs, duplicate
accepted Task/Check pairs, and certification-config mismatch. These are the
reconciler's cross-record responsibility, so no state object or validation
framework was added.
The twenty-fifth slice keeps that reconciler intact but closes RI-043 at its two
unsafe nested boundaries. SourceEvent linkage no longer iterates a malformed
scalar rejection-reason value after record validation has rejected it, and
attempt summaries now enforce the direct `outcome`/`failure_label`/`timed_out`
state machine produced by Verification. Four failing characterizations cover
the exception path and the three contradictory accepted-attempt states. The
38-file scan remains at 118 hotspots (2 now / 43 soon / 73 monitor), with full
signal health, critical counts 0/20/0, and no dead-code candidate; no validation
framework was added. One direct outcome-state helper moved
`_evidence_outcomes` out of the hotspot list.
The twenty-sixth slice keeps the replicate campaign API direct while removing
its redundant caller-supplied call cap, centralizing finite-number conversion,
and isolating the limits contract. The call cap is still authority evidence but
now derives from the frozen schedule. Campaign hotspots fall from five to three,
all monitor-only; the full scan falls from 118 to 116 hotspots without a config
object, validation framework, or schema change.
The twenty-seventh slice closes the reachable half of RI-045 before adding any
future-supply abstraction. A red public-Runner characterization showed that
strict-prospective evaluation could reach Agent execution without a future
denominator. The evaluator now accepts only counterfactual replay with a
predeclared holdout and rejects unsupported policies before Task Pool reads,
record writes, Result access, or Agent calls. Strict-prospective Selection and
the final-form Origin/Input/Selection/CellSet boundaries remain. In the same
slice, the unused stable-ID helper now derives the exact Selector ID used by the
builder from semantic fields instead of accepting the Selector self-digest.
No schema, training platform, or streaming service was added.
The twenty-eighth slice completes RI-045 and closes RI-046 and RI-047. Three
candidate shapes were checked: mutating the strict Origin, deriving a cohort
from a later pool without source coverage, and introducing a new frame record.
All but a source-window prerequisite either made the original claim false or
duplicated an existing boundary. Task Pools now bind that window while keeping
generator identity behavior-only. The existing EvaluationCellSet is the one
post-selection artifact: it links the later pool plus mature/censored refs, and
Runner and Reporting replay the same Selection-owned cohort function. A same-ID
Agent configuration counterexample then showed that IDs alone were not a
complete two-phase freeze; ordered full Agent-record digests now close it.
The full-signal scan rises from 116 to 123 hotspots (3 now / 47 soon / 73
monitor), primarily because the new shared resolver, prospective report replay,
and source-window checks are visible audit surfaces. They remain characterized;
no source service, generic frame, execution fork, parameter bundle, or baseline
was added.
The twenty-ninth slice closes RI-048 and removes duplicated Selection replay
logic. A red public-Runner specification changed a persisted strict Selection
to another eligible history ref while retaining valid self-digest and upstream
links; the old path reached its first Task Pool read. Selection now owns one
semantic replay assertion used before prospective supply reads and by
Reporting, training, and stratified diagnostics. The prospective entry point
falls from 126 NLOC / CCN 14 to 83 / 1; its 13 explicit orchestration parameters
still classify it `refactor_soon`, and no one-use config object was added. The
full-signal scan remains at 123 hotspots (3 now / 47 soon / 73 monitor), with
critical counts 0/21/0 and no dead-code candidate.
The forty-fifth slice revisits the source-window audit surface introduced by
the prospective Task Pool work. A direct characterization fixes every returned
error and its order across missing, malformed, noncanonical, reversed, and late
windows plus inside/outside SourceEvent reason alignment. `_source_window_errors`
now only composes a window-boundary parser with an event reconciler. The former
47 NLOC / Lizard CCN 21 / cognitive 23 / Ruff 13 hotspot and both new helpers
leave the hotspot list. The full scan falls from 118 to 117 hotspots (3 now /
45 soon / 69 monitor), with critical counts unchanged at 0/21/0. No state
object, validation framework, or behavior change was introduced.
The forty-sixth slice revisits the prospective Reporting replay surface. A
direct characterization fixes the exact duplicate-identity, mature/censored
drift, cohort-replay, and missing-pool error order. It also proves that later
Task Pool bundles are loaded lazily and at most once per referenced identity.
The public orchestrator now retains lookup and load order while one helper
indexes later pools and another compares one replayed cohort. The former 83
NLOC / Lizard CCN 19 / cognitive 24 / Ruff 14 helper becomes a 64-line CCN-14,
cognitive-16 `monitor` finding; both new helpers remain below thresholds. The
full scan remains at 117 hotspots but moves from 45 to 44 `refactor_soon` and
from 69 to 70 `monitor`; Ruff and Lizard each lose one warning. No context
object, cache service, validation framework, or behavior change was introduced.
The forty-seventh slice revisits the shared CellSet resolver. Existing
integration specifications cover shared-cell deduplication, sequential-cache
equivalence, partial execution recovery, reusable-Result preflight, explicit
missing evidence reuse, and strict-prospective use. A new ordering case proves
duplicate plan identities fail before the CellSet log is read. Plan indexing,
pending-union derivation, ResultCell uniqueness, and one-CellSet construction
are now direct helpers; the locked Result Store session remains visible in the
orchestrator. The resolver falls from 153 NLOC / Lizard CCN 21 / cognitive 25 /
Ruff 14 to 113 NLOC / CCN 11 with no cognitive or Ruff signal. Its one remaining
Lizard `refactor_soon` finding reflects nine explicit execution dependencies;
all four new helpers are below thresholds. The full scan remains at 117
hotspots (3 now / 44 soon / 70 monitor), while Ruff and Complexipy each lose
one warning. Duplicating those dependencies or adding a one-use context object
would increase system complexity, so the visible orchestrator is retained.
The forty-eighth slice closes RI-063 at Runner companion-log resume. Two red
cases show that a duplicate Selection ID, with either the same or a conflicting
digest, was hidden by the first-match return in the append helper. The helper
now finishes the existing O(N) scan, rejects any repeated semantic ID, and only
then applies its prior idempotent-digest or first-observation-time rule. This
also prevents a new append from extending a log corrupted under an unrelated
ID. The full scan remains at 117 hotspots (3 now / 44 soon / 70 monitor); the
append helper remains one cognitive-complexity `monitor` signal at 18. No
persistent index, automatic repair, lock redesign, or storage abstraction was
introduced.
The forty-ninth slice closes RI-064 at Reporting's public evidence boundary.
Red public cases show duplicate Selections still supporting the frozen claim
and duplicate Result/Agent evidence still supporting the Result summary. Four
additional cases bind cache completeness, Agent/Result identity, and duplicate
CellSet/Metric handling. Reporting now applies one direct O(N) identity check
to the record types used by each claim. Existing Origin/Snapshot/Input/Selector
provenance indexes keep their established multi-error behavior. The full scan
remains at 117 hotspots (3 now / 44 soon / 70 monitor) with unchanged tool
counts. No registry, validation framework, or record abstraction was added.
`build_claim_boundary` is also intentionally retained: its five ordered claim
predicates and exact abstention reasons are the audit surface, while extraction
would either repeat matrix validation or add a report-only evidence bundle. No
dead-code candidate has deletion authority.
The fiftieth slice separates Runner's Task Pool build boundary after its
publication contract stabilized. A three-case characterization proves that a
missing reference patch, Check command, or hidden-material path fails before
repository or Check material is bound into a Workspace context. The public
function now delegates three direct phases: candidate generation plus commit
resolution and resource preflight, Workspace binding plus certification, and
immutable bundle freeze plus publication. Its measured size falls from 139
NLOC / Lizard CCN 24 / cognitive complexity 24 to 7 / 2 / 1. The phase helpers
remain below high-priority thresholds. The full suite passes 672 tests with 2
skipped; the full-signal scan falls to 116 hotspots (3 now / 43 soon / 70
monitor), and Lizard and Complexipy each lose one finding. Existing error and
side-effect order is unchanged. No context object, pipeline framework, schema,
dependency, telemetry, network access, or paid call was added.
The fifty-first slice closes RI-065 and RI-066 at the persisted Task Pool
candidate frame. A fully redigested public bundle with two distinct rejected
SourceEvents for one candidate previously validated because set coverage erased
the duplicate. Candidate-linked SourceEvents now require unique non-null
candidate IDs. A second characterization requires certification evidence to
retain the producer's candidate-ID ordering; rejected candidate IDs now match
that ordered evidence exactly. The shared Runner fixture was corrected to use
the production ordering contract. The full suite passes 673 tests with 2
skipped. The full-signal scan remains at 116 hotspots (3 now / 43 soon / 70
monitor), with unchanged tool counts and no dead-code candidate. The retained
certification reconciler owns these direct sequence and coverage checks; no
registry, index, schema, framework, dependency, telemetry, network access, or
paid call was added.
The fifty-second slice closes RI-067 at Task Pool certification context. The
Runner has one WorkspaceConfig and RuntimeConfig per build, but persisted
evidence previously accepted a second candidate with a different digest for
either config. A two-axis characterization now fails both mixtures. One small
linear helper requires one non-empty value per shared config field; reference
patches and Check execution bindings remain candidate-specific. The full suite
passes 673 tests with 2 skipped. The full-signal scan remains at 116 hotspots
(3 now / 43 soon / 70 monitor) with unchanged tool counts; the helper is below
thresholds. No pool-level config copy, registry, context object, schema,
framework, dependency, telemetry, network access, or paid call was added.
The fifty-third slice closes RI-068 and separates bounded subprocess execution
after its containment contract stabilized. Seven request cases prove that an
empty command, nonpositive or nonfinite timeout, non-integer capture bound, and
negative or nonfinite termination grace fail before `Popen`. The public runner
now delegates request validation, stream-reader setup, bounded wait,
containment/drain, and exceptional cleanup while preserving TERM-to-KILL and
pipe behavior. It falls from 73 NLOC / Lizard CCN 20 / cognitive complexity 29
/ Ruff complexity 15 to 46 / 3 / 1 / below threshold and leaves
`refactor_soon`; every helper is below high-priority thresholds. The full suite
passes 680 tests with 2 skipped. The full-signal scan falls to 115 hotspots (3
now / 42 soon / 70 monitor), and Ruff, Lizard, and Complexipy each lose one
finding. No process wrapper class, state object, dependency, telemetry, network
access, or paid call was added.
The fifty-fourth slice closes RI-069 and separates shared resource-ledger
snapshot reconstruction after its reservation/completion contract stabilized.
The former accounting fold accepted negative costs, silently ignored string or
boolean costs, and let nonfinite budgets or costs reach canonical JSON writing;
the latter could leave a temporary snapshot file. Nine malformed accounting
cases now fail before any file write, while a stopped completion without known
cost remains valid evidence. The public function delegates event folding,
budget validation, and cost summation. It falls from 57 NLOC / Lizard CCN 21 /
cognitive complexity 27 / Ruff complexity 12 to 19 / 3 / 2 / below threshold;
the retained event state machine is `monitor` only. The full suite passes 690
tests with 2 skipped. The full-signal scan remains at 115 hotspots but shifts to
3 now / 41 soon / 71 monitor; Ruff and Lizard each lose one finding. No ledger
class, experiment framework, schema, dependency, telemetry, network access, or
paid call was added.
The fifty-fifth slice closes RI-071 at SourceEvent disposition validation. A
scalar string or mapping `rejection_reasons` previously passed as an iterable
of non-empty keys/characters, while an integer raised `TypeError`. Three direct
cases now return failed validation. The public helper delegates disposition
binding, exact tuple/content validation, and material-maturity checks. It falls
from 39 NLOC / Lizard CCN 20 / cognitive complexity 25 / Ruff complexity 12 to
9 / 1 / 0 / below threshold. The binding state machine remains a two-tool
`monitor` finding at 30 NLOC / CCN 15 / cognitive 20; the other helpers are
below thresholds.
The fifty-sixth slice closes RI-072 at ResultCell payload validation. Truthy
checks previously accepted an empty exclusion reason on a result cell and
truthy non-string IDs, digests, or exclusion reasons in other states. State
dispatch now delegates exact result, excluded, and missing payload checks. It
falls from 30 NLOC / Lizard CCN 21 / cognitive complexity 28 / Ruff complexity
13 to 8 / 4 / 3 / below threshold; all three state helpers are below
high-priority thresholds. Across both slices, 488 Records and consumer tests and
the full suite of 697 tests with 2 skipped pass. The full-signal scan falls to
114 hotspots (3 now / 39 soon / 72 monitor); Ruff loses two findings, and
Lizard and Complexipy each lose one. No generic type-validation framework,
schema, dependency, telemetry, network access, or paid call was added.
The fifty-seventh slice closes RI-073 at Metric runtime shape. Seven direct
records show that truthy non-string Agent IDs, Agent-pair containers,
aggregation levels, optional refs, and incomplete-state reasons, plus empty
unused dimensions, previously validated despite not matching the reload schema.
Metric validation now delegates exact scope dimensions, optional string refs,
and completeness/abstention state. The public helper falls from 47 NLOC /
Lizard CCN 20 / cognitive complexity 20 / Ruff complexity 12 to 22 / 3 / 2 /
below threshold. Its dimension table remains one Lizard `monitor` finding; the
other helpers are below thresholds. The full suite passes 704 tests with 2
skipped. The full-signal scan remains at 114 hotspots but shifts to 3 now / 38
soon / 73 monitor; Ruff and Complexipy each lose one finding. No generic
validation framework, schema, dependency, telemetry, network access, or paid
call was added.
The fifty-eighth slice closes RI-074 at Task Pool certification-decision
ingestion. An integer `accepted=1` previously reached both SourceEvent
finalization and an otherwise valid frozen bundle. One shared exact-boolean
guard now protects certification evidence serialization, finalization, and
freeze-time indexing. The finalizer delegates candidate-result coverage,
single-event projection, and ordered local validation; frozen cross-artifact
reconciliation is not duplicated. It falls from 66 NLOC / Lizard CCN 20 /
cognitive complexity 20 to 17 / 2 / 0 and leaves the hotspot list. All 56 Task
Pool tests and the full suite of 707 tests with 2 skipped pass. The full-signal
scan falls to 113 hotspots (3 now / 37 soon / 73 monitor); Lizard and Complexipy
each lose one finding. No schema, generic validation framework, dependency,
telemetry, network access, or paid call was added.
The fifty-ninth slice closes RI-075 at persisted certification-evidence
reconciliation. A non-object evidence item was reported by record parsing, then
raised `AttributeError` when SourceEvent linkage called `.get()` on it. The
linker now indexes mappings only, so the public artifact validator returns all
available errors. The one cross-record entrypoint delegates record parsing and
semantics, collection/config checks, accepted Task/Check coverage, and rejected
candidate/summary coverage. It falls from 79 NLOC / Lizard CCN 24 / cognitive
complexity 34 / Ruff complexity 17 to 13 / 1 / 0 / below threshold; all four
phase helpers stay below hotspot thresholds. All 57 Task Pool tests and the
full suite of 708 tests with 2 skipped pass. The full-signal scan falls to 112
hotspots (2 now / 37 soon / 73 monitor); Ruff and Complexipy each lose one
finding, and Task Pool leaves the agent investigation queue. No evidence bundle,
generic validator, schema, dependency, telemetry, network access, or paid call
was added.
The sixtieth slice closes RI-076 at Selection metric alignment. A self-digested
Selection could claim `strict_prospective` while its Origin and future CellSet
were counterfactual; direct `evaluate_selection` then emitted ordinary MAE even
though Runner and Reporting rejected the same relation. Scoring now checks the
mode before Metric construction. The ordered contract has 18 executable
reasons, including all prospective pool, denominator, and censoring branches,
and delegates provenance, mode-specific denominator, and cell-identity phases.
The public helper falls from 70 NLOC / Lizard CCN 24 / cognitive complexity 28 /
Ruff complexity 19 to 32 / 5 / 4 / below threshold; both phase helpers remain
below hotspot thresholds. All 154 Selection tests and the full suite of 709
tests with 2 skipped pass. The full-signal scan falls to 111 hotspots (1 now /
37 soon / 73 monitor); Ruff, Lizard, and Complexipy each lose one finding. No
matrix context object, policy registry, schema, dependency, telemetry, network
access, or paid call was added.
The sixty-first slice closes RI-077 at Reporting's Claim Boundary. Exact public
counterexamples showed configurable ClaimConfig flags weakening fixed claim
semantics, malformed or permuted requested-claim collections changing config
identity, and
`agent_result_identity` remaining supported with missing or drifted Agent
evidence. ClaimConfig now retains only canonical requested claims; Matrix
completeness and Metric validity are mandatory. The
identity claim requires the Result's frozen Agent projection to match a supplied
Agent and publishes the Agent manifest digest. The claim builder evaluates only
requested predicates, reuses the existing Selector source-digest and Task Pool
artifact-path projections, and delegates five stable claim decisions plus local
Selection/Matrix/Metric/CellSet evidence phases. It falls from 288 NLOC /
Lizard CCN 73 / cognitive complexity 21 to 133 / 14 / 5 and moves from
`refactor_now` to `monitor`; the Selector-metric decision is 43 / 8 / 1 and all
new phase helpers are below high-priority thresholds. The full suite passes 714
tests with 2 skipped. The full-signal scan reports 113 hotspots (0 now / 37 soon
/ 76 monitor), with critical counts 0/20/0 and no dead-code candidate. No claim
registry, context object, schema, dependency, telemetry, network access, or paid
call was added.
The sixty-second slice closes RI-078 at Selection's metric identity and
Runner's batch side-effect boundary. `MetricConfig` contained no scoring
behavior: callers could relabel identical metrics and restate the budget
already frozen by Selection. Selection now derives one versioned protocol
digest from the ordered implemented metric names and aggregation level; every
Metric still records the Selection budget. The identity-only class and its
public parameters are removed, while `MetricRecord` remains unchanged for
comparability. Runner now materializes and validates all Selector records and
executable parameters before Task Pool reads or companion writes, then
preflights Agents, evaluation mode, and the complete origin schedule. An
invalid later Selector therefore cannot leave a valid earlier Selector behind.
Extracting the pure mode/schedule validator removes one cognitive-complexity
signal without hiding the evaluator's 15 real dependencies. The full suite
passes 714 tests with 2 skipped. The full-signal scan falls to 112 hotspots
(0 now / 36 soon / 76 monitor), with critical counts 0/19/0 and no dead-code
candidate. No metric registry, configuration framework, schema, dependency,
telemetry, network access, or paid call was added.
The sixty-third slice closes RI-079 at Result Store's cache-control boundary.
`reuse_policy` advertised a choice that the system could never safely make:
every value except `exact_identity` failed later during resolution. The actual
`reuse_benchmark_invalid` switch accepted malformed truthy values and could
change a paid-work plan. Exact full-identity reuse is now an invariant;
`ResultCacheConfig` retains only one exact-boolean opt-in, and the replicate
campaign continues to forbid that opt-in. Five red public constructor cases
now fail closed. The 91 Result Store/campaign tests and the full suite of 719
tests with 2 skipped pass. The full-signal scan is unchanged at 112 hotspots
(0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no dead-code
candidate. No cache-policy registry, schema, compatibility layer, dependency,
telemetry, network access, or paid call was added.
The sixty-fourth slice closes RI-080 at Workspace artifact configuration.
`path_mode` was another one-value placeholder: only relative refs below the
configured root are safe and executable. Truthy non-booleans could also retain
stdout/stderr or a final diff unexpectedly, and malformed summary containers
failed only when a run began. Relative refs are now invariant. The two
retention flags and summary modes validate at config construction, and the
one-use runtime validator is removed. Four red public constructor specs and all
71 Workspace tests pass. The full-signal scan remains at 112 hotspots (0 now /
36 soon / 76 monitor) and critical counts 0/19/0, while Ruff findings fall from
21 to 20; there is still no dead-code candidate. No artifact-mode registry,
schema, compatibility layer, dependency, telemetry, network access, or paid
call was added.
The sixty-fifth slice closes RI-081 before Task Pool certification execution.
`CertificationConfig` accepted a boolean repeat count as one real Workspace
check pair, then produced evidence whose nested schema rejects that same
boolean. Floats, strings, nulls, and nonpositive integers also survived config
construction. Repeat count now requires an exact positive integer at
construction, and the weaker runtime comparison is gone. Six red public
constructor specs and all 63 Task Pool tests pass. The full-signal scan remains
at 112 hotspots (0 now / 36 soon / 76 monitor), with critical counts 0/19/0,
20 Ruff findings, and no dead-code candidate. No configuration framework,
schema, compatibility layer, dependency, telemetry, network access, or paid
call was added.
The sixty-sixth slice closes RI-082 at Runner report publication. An absolute
configured filename overrode `output_dir`; traversal and nested names escaped
or changed the intended write location, while swapped suffixes selected the
wrong serialization. `ReportConfig` now accepts only a direct `.md` filename
and direct `.json` filename, with both slash forms and surrounding whitespace
rejected at construction. Six red public specs and all 56 Runner tests pass.
The full-signal scan stays at 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, 20 Ruff findings, and no dead-code candidate. No path
wrapper, publication service, schema, compatibility layer, dependency,
telemetry, network access, or paid call was added.
The sixty-seventh slice closes RI-083 at Metric consumption. Construction had
become implementation-owned in RI-078, but training, paired comparison, and
Reporting still accepted an arbitrary common protocol digest. Selection now
preflights a Metric batch against the current versioned protocol; Reporting
marks an unknown protocol unsupported. Records stays version-neutral so future
or malformed evidence can load and fail at the algorithm boundary. Moving the
batch check out of `_validated_paired_metrics` avoids a transient complexity
regression; the helper is below hotspot thresholds and the paired validator
remains `monitor`. Two red public counterexamples and all 229
Selection/Reporting tests pass. The full suite passes 736 tests with 2 skipped.
The scan remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical
counts 0/19/0, 20 Ruff findings, and no dead-code candidate. No protocol
registry, schema, compatibility layer, dependency, telemetry, network access,
or paid call was added.
The sixty-eighth through seventieth slices close rolling-origin future-state
typing and Verification normalization. `future_holdout_known` is an exact
boolean at policy and record boundaries. Raw Check timeout, exit code, and
duration values cannot be coerced into pass evidence, and the small
normalization config rejects overlapping exit-code meanings or malformed
labels/redaction controls at construction. Sixteen red cases pass.
The seventy-first slice removes repeated immutable binding work from batch
preflight. Task/Check/Agent relations remain validated per plan, while hidden
Check material and full Agent bindings are checked once per unique identity;
the existing per-cell workspace and invocation rechecks are unchanged. A
transient 113-hotspot implementation was split into direct plan and Agent
binding helpers; the final scan returned to 112 hotspots.
The seventy-second slice requires rolling-origin dependency filters to be a
tuple of nonempty strings at policy and persisted-record boundaries. Non-string
members can no longer silently empty a cohort or enter policy identity. Three
red cases pass. The full suite passes 756 tests with 2 skipped. No schema,
registry, generic validation framework, dependency, network access, or paid
call was added.
The seventy-third slice compared three independent Stage 0 failure hypotheses.
Scoring configuration is validated before Agent cells and replicate campaign
calls; Task Pool source windows are canonicalized before certification. Those
paths remain lower-priority cleanup candidates rather than paid-boundary gaps.
Persisted float fields supplied the counterexample: integer-valued Selection
weights and Metric values validated with matching self-digests but became
noncanonical on latest-schema reload. Records now requires the exact float
representation already emitted by production builders, and companion logs
reject malformed records before append. Two red public specs pass without a
loader or schema abstraction. The full suite passes 758 tests with 2 skipped;
the 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
monitor), critical counts 0/19/0, and no dead-code candidate.
The seventy-fourth slice compared scoring identity, an internal open-lower-bound
`TimeRange` sentinel, and Selection's structural hotspot. Only scoring supplied
a behavioral counterexample: integer and float rate forms computed the same
cost but produced different digests, while mutating the constructor's source
mapping changed a frozen config's identity. `ScoringConfig` now validates and
normalizes once at construction, snapshots sorted float rates behind a read-only
mapping, and retains the paid-path recheck. The TimeRange sentinel remains a P2
cleanup candidate; Selection remains unchanged without a correctness finding.
The full suite passes 763 tests with 2 skipped. The 38-file full-signal scan
remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
0/19/0, and no dead-code candidate.
The seventy-fifth slice closes the retained TimeRange cleanup. Selection-only
pre-origin loading used an invalid empty-start TimeRange solely as a nullable
query sentinel. The loader now takes the nullable timestamp it actually needs:
`None` for an unbounded selection-only query and `history_window.start` for
rolling evaluation. One red public ResultQuery assertion and one bounded-query
characterization pass; no time-window type or ResultQuery contract changed.
The full suite passes 763 tests with 2 skipped, and the 38-file full-signal scan
remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
0/19/0, with no dead-code candidate.
The seventy-sixth slice compared mutable aliases in shallow-frozen Task Pool,
Selector, and replicate inputs before moving to the persisted-record boundary.
Those configurations either project content into digested records before use or
replay immutable schedule/authority evidence; no silent-drift counterexample
survived. Public Task, Check, and Agent validators did accept integer IDs that
their latest-schema loader rejects. Record validation now runs domain checks and
then the existing dataclass schema conversion, preserving specific errors while
closing the shared scalar-type gap. Three red public cases and the full suite of
766 tests with 2 skipped pass. No generic immutable-container layer or second
schema mechanism was added. The 38-file full-signal scan remains at 112 hotspots
(0 now / 36 soon / 76 monitor), full signal health, and no dead-code candidate.
The seventy-seventh slice closes the analogous top-level Task Pool gap. A
self-digested pool with an integer generator-config digest passed complete
artifact validation but failed its JSONL schema. Records now validates the
record shape and self-digest, while Task Pool retains cross-artifact ownership
and removes its duplicate digest check. One red bundle case passes.
The seventy-eighth slice rejects coercive candidate ingestion before identity
derivation. Required identity/task/Check fields and optional cluster/stratum
labels must be strings, solver refs must be a string sequence, and resource
limits must be a string-keyed mapping. The same label rule applies to excluded
SourceEvents. Nine red public cases and all 73 Task Pool tests pass; the full
suite passes 776 tests with 2 skipped. No candidate schema class, adapter
registry, or ingestion service was added. The 38-file full-signal scan remains
at 112 hotspots (0 now / 36 soon / 76 monitor), full signal health, and no
dead-code candidate.
The seventy-ninth slice closes a behavior-equivalent Selector identity split.
Stratified-forecast integer and float forms executed identically but produced
different config and Selector digests; coverage construction also retained a
caller-owned nested map. Family-specific parsing now returns the canonical
parameter snapshot used for both storage and identity, and the executable
record boundary rejects a self-digested noncanonical shape. Three red public
specs and all 166 Selection tests pass without a configuration framework.
The eightieth slice removes the remaining Task Pool publication-time string
coercions. Required metadata and the optional Task Pool ID must already be
strings before record construction. Nine red cases and all 82 Task Pool tests
pass; the full suite passes 788 tests with 2 skipped. No metadata record,
compatibility path, network access, paid call, or campaign authority was added.
The eighty-first slice canonicalizes the scale-free rule-mixture behavior that
the inference formula already implements. All three experts are stored as
float weights on one exact-`fsum` unit simplex; omitted weights and overall
scaling cannot create another executable identity. A one-ULP correction keeps
the transform idempotent for extreme ratios. RI-102 later moves signed-zero
equivalence to shared canonical JSON. Two rejection cases, one signed-zero
identity case, the trainer contract, 10,000 deterministic probes, and all 169
Selection tests pass.
The eighty-second slice maps scoring-rate `-0.0` to positive `0.0`, closing the
last reproduced duplicate pricing identity left by RI-090. One red public case
and all 65 Result Store tests pass. The full suite passes 792 tests with 2
skipped; no schema, registry, dependency, network access, paid call, or campaign
authority was added. The final 38-file full-signal scan remains at 112 hotspots
(0 now / 36 soon / 76 monitor), critical counts 0/19/0, with no dead-code
candidate; neither numeric helper remains a structural hotspot.
The eighty-third slice closes RI-099 at the shared timestamp boundary. An
integer Task Pool `created_at` was correctly reported by record-schema
validation, but the artifact validator continued collecting cross-record errors
and the UTC parser raised on `.endswith`. The parser now rejects non-strings as
`ValueError`; the new bundle case and timestamp unit contract pass without a
Task Pool-specific catch list.
The eighty-fourth slice closes RI-100 by moving the existing latest-schema
conversion ahead of domain semantics and removing its duplicate final replay.
Three red public cases reproduce unsafe string, sequence, and nested-record
shapes. Existing tests that intentionally mix a schema violation with a domain
violation now assert the schema layer; domain rules retain schema-valid cases.
All 125 Records tests and 83 Task Pool tests pass. A temporary deterministic
audit over all 16 public record validators, replacing every one of 256 fields
with an integer, found zero valid-base failures and zero exceptions. The full
suite passes 796 tests with 2 skipped. No validation framework, schema registry,
compatibility mode, network access, paid call, or campaign authority was added.
The refreshed 38-file full-signal scan remains at 112 hotspots
(0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no dead-code
candidate.
The eighty-fifth slice closes RI-101 at the cross-artifact prerequisite
boundary. `rejected_candidate_ids=7` produced a record-schema error and then
raised when SourceEvent coverage converted it to a set. Task Pool member
validation now returns an invalid record result before member relations, and
complete artifact validation returns an invalid member result before
certification or SourceEvent reconciliation. The red public case and a
temporary disturbance of all 20 Task Pool fields report zero exceptions. All
84 Task Pool tests pass; the full suite passes 797 tests with 2 skipped. The
change adds no per-field branch, catch list, validation framework, or artifact
layer. The refreshed 38-file full-signal scan remains at 112 hotspots
(0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no dead-code
candidate.
The eighty-sixth slice closes RI-102 at the canonical JSON boundary. Direct
probes showed that Result latency and Metric values using `-0.0` remained valid
and numerically equal to positive zero but produced different JSON and
self-digests. `canonical_data` now maps every built-in floating zero to positive
`0.0` recursively, covering arbitrary nested Feature and parameter payloads as
well as typed measurements. One red serialization/digest case and all 126
Records tests pass. The full suite passes 798 tests with 2 skipped. Per-field
rejection, constructor fanout, and a second JSON encoder were rejected as
incomplete or redundant. The refreshed 38-file full-signal scan remains at 112
hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
dead-code candidate.
The eighty-seventh slice closes RI-103 at the Task/Check member prerequisite.
`TaskRecord.check_ids=7` raised in linkage before `validate_task` could return
its latest-schema error. Accepted member records are now validated first; an
invalid Task or Check returns immediately, while valid records continue through
the same repository, digest, ID, and linkage relations. One red public case,
all 85 Task Pool tests, and a temporary disturbance of all 21 Task/Check fields
pass without exceptions. The full suite passes 799 tests with 2 skipped. No
member wrapper, copied schema, or catch list was added. The refreshed 38-file
full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, and no dead-code candidate.
The eighty-eighth slice closes RI-104 at the Result Store query boundary. A
numeric filter was accepted against an absent store and raised only after a
Result existed; empty time strings acted as null, and inverted bounds silently
matched nothing. `load_results` now validates the six filter tuples, nullable
nonempty timestamp shapes, UTC parsing, and bound order before store access.
Eleven red public cases and all 76 Result Store tests pass. The full suite passes
810 tests with 2 skipped. No Query schema class, normalization object, or index
was added. The first combined helper entered the monitor list; separating
filter-shape validation from timestamp parsing returned the refreshed 38-file
full-signal scan to 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
0/19/0, and no dead-code candidate.
The eighty-ninth slice closes RI-105 at Result construction. Direct disturbance
showed nine schema-invalid Task/Check fields could enter a valid Result because
only WorkspaceRun and cache projections were validated; integer `check_ids`
instead raised during linkage. `build_result_record` now validates Task, Check,
Agent, and WorkspaceRun before relations. Five red public cases, all 81 Result
Store tests, and a temporary disturbance of all 52 input fields pass with zero
accepted invalid inputs and zero leaked exceptions. The full suite passes 815
tests with 2 skipped. No Result-input wrapper, copied schema, or validation
framework was added. The refreshed 38-file full-signal scan remains at 112
hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
dead-code candidate.
The ninetieth slice closes RI-106 at exact cache-identity construction. This
entry point is used directly by missing-cell and cache-reuse planning, so it
cannot rely on a later Result builder. A temporary disturbance of all 36
Task/Check/Agent fields initially found 15 schema-invalid values accepted and
one `TypeError` from integer `TaskRecord.check_ids`. Compute and build now share
one three-record prerequisite and one Task/Check linkage check. Four red public
cases, all 85 Result Store tests, and the repeated disturbance pass with zero
accepted invalid inputs and zero leaked exceptions. The full suite passes 819
tests with 2 skipped. No input wrapper, copied schema, validation framework,
network access, paid benchmark call, or campaign authority was added. The
refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
monitor), critical counts 0/19/0, and no dead-code candidate.
The ninety-first slice closes RI-107 at the two configuration inputs. Six
schema-invalid WorkspaceConfig/RuntimeConfig fields absent from direct identity
projection still produced valid-looking identities, and an empty optional
hardware digest was accepted beside null or a real digest. Records now owns two
direct validators that reuse latest-schema conversion; Result Store applies
them before identity construction. Six red public cases, all 91 Result Store
tests, and 13 deterministic type/semantic disturbances pass with zero accepted
invalid inputs and zero leaked exceptions. The full suite passes 825 tests with
2 skipped. No config wrapper, schema copy, validation framework, network access,
paid benchmark call, or campaign authority was added. The refreshed 38-file
full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, and no dead-code candidate.
The ninety-second slice closes RI-108 at Task Pool certification. Invalid
WorkspaceConfig/RuntimeConfig IDs previously reached the first base Check and
then entered certification evidence through their config digests. Certification
now applies both Records validators before Task/Check construction or Check
execution. Two red public cases prove no Check call occurs, and all 87 Task Pool
tests pass. No certification context or schema copy was added.
The ninety-third slice closes RI-109 at Workspace preflight. Invalid config IDs
previously passed even with an empty plan because only Runtime timeout had a
local check. Workspace now validates both complete configs before repository or
plan state, and Runner replaces its duplicate timeout type branches with the
shared Runtime validator. Two red public cases and all 74 Workspace tests pass;
the full suite passes 829 tests with 2 skipped. No config wrapper, execution
context, network access, paid benchmark call, or campaign authority was added.
The refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon
/ 76 monitor), critical counts 0/19/0, and no dead-code candidate;
`_run_agent_cells` loses two Lizard branches while remaining explicit.
A ninety-fourth slice closes RI-110 at Workspace repository binding. Unlike
Agent and Check binding, it accepted malformed WorkspaceConfig state and
returned an immutable context before later preflight rejected it. Binding now
validates first, while execution preflight retains its recheck. One red public
case and all 75 Workspace tests pass.
A ninety-fifth slice closes RI-111 at Runner Task Pool construction. Both
configs now fail once before candidate or commit resolution; candidate
certification still rechecks immediately before Check execution. Two red public
cases and all 58 Runner tests pass. The full suite passes 832 tests with 2
skipped. No TaskPoolConfig wrapper, generic preflight framework, network access,
paid benchmark call, or campaign authority was added. The refreshed 38-file
full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor),
critical counts 0/19/0, and no dead-code candidate.

## Runtime, Storage, And Cost Efficiency

| ID | Priority | Evidence | State | Finding | Direction and validation |
| --- | --- | --- | --- | --- | --- |
| RI-016 | P0 | code-confirmed | resolved 2026-07-22 | Agent and Check execution buffered unbounded stdout/stderr, and timeout did not reliably terminate descendants. | The shared bounded subprocess runner now hashes full output, retains bounded head/tail excerpts, owns a process group, and escalates TERM to KILL. Persistent-grandchild and multi-megabyte-output tests pass. |
| RI-068 | P1 | reproduced | resolved 2026-07-23 | `NaN` timeout or termination grace and a non-integer capture bound passed the initial comparisons, so malformed requests could start a process and fail only inside `wait` or a reader thread. | One direct validator rejects empty commands, nonpositive/nonfinite time bounds, and nonpositive/non-integer capture bounds before process start. Execution now exposes validation, stream setup, wait, containment/drain, and exceptional cleanup phases without changing the process-group policy. Seven invalid-request cases plus eleven existing containment/output cases pass. |
| RI-017 | P1 | code-confirmed | resolved 2026-07-22 | `store_result` and filtered loads repeatedly parsed the entire JSONL store, producing approximately `O(KN + K^2)` work when appending K cells to N records. | Runner now holds one indexed `ResultStoreSession` across resolution, execution, repricing, and final resolution. New Results update that live index; batch callers serialize once and fsync once. The local three-run median benchmark remained linear from 100 through 10,000 records, so JSONL remains appropriate. |
| RI-018 | P1 | code-confirmed | resolved 2026-07-22 | Append logs lacked a complete lock, fsync, and truncated-tail recovery contract. | Result writes now hold a POSIX advisory file lock, append complete canonical lines through one writer, flush and fsync each durable Runner result, and fsync the directory on first creation. Reads take a shared lock. Unterminated tails fail closed until explicit recovery either completes a parseable JSON value or truncates only an unparseable final byte tail; complete invalid lines are never removed. |
| RI-019 | P1 | code-confirmed | resolved 2026-07-22 | Invalid or duplicate plans and endpoint drift could reach the paid-call loop. | Runner now validates the complete missing-cell plan before the first Agent; Workspace rechecks repository, Check material, timeouts, harness command/content, and the `OPENAI_BASE_URL`/`OPENAI_API_KEY` proof before workspace creation and immediately before invocation. Cache-only operations do not require credentials. |
| RI-087 | P1 | reproduced | resolved 2026-07-23 | Complete-plan preflight rehashed and revalidated the same immutable Check material once per Agent cell and the same Agent harness once per Task/Check cell. The required just-in-time per-cell rechecks remained separate, so this batch repetition added cost without stronger evidence. | Batch preflight still validates every Task/Check/Agent relation, but expensive binding checks run once per unique Check and full Agent record. Per-cell workspace and invocation revalidation is unchanged. A direct call-count spec and all 72 Workspace tests pass; the final scan returns to the prior 112-hotspot structural baseline. |
| RI-079 | P0 | reproduced | resolved 2026-07-23 | `ResultCacheConfig` exposed `reuse_policy` even though only `exact_identity` was valid, and accepted integers, strings, or nulls as the boolean `reuse_benchmark_invalid` control. Truthy malformed values could reuse benchmark-invalid infrastructure evidence and alter a later paid-work plan. | Exact full-identity reuse is now a fixed Result Store invariant rather than a configurable placeholder. `ResultCacheConfig` retains only `reuse_benchmark_invalid` and rejects every non-`bool` value at construction; the replicate campaign retains its stricter ban on enabling the flag. Five public malformed-control cases and 91 Result Store/campaign tests pass. |
| RI-044 | P0 | reproduced | resolved 2026-07-23 | The replicate campaign allowed another paid call whenever `remaining_usd` was positive, even when the balance was smaller than any authorized call estimate. The total budget could therefore be exceeded before returned usage exposed the cost. | Campaign ledger v2 binds one positive maximum estimated cost per call, no larger than the total budget. Preflight requires the remaining balance to cover that amount; each Result must fit the per-call and cumulative limits. A result above a limit stops the cell and cannot retry. The exact call cap is derived from the frozen schedule instead of supplied redundantly. Three offline public-path specs cover invalid authority, pre-call exhaustion, and post-call overrun. Provider-side enforcement remains the Agent runtime budget's responsibility. |
| RI-069 | P0 | reproduced | resolved 2026-07-23 | Shared resource-ledger reconstruction accepted negative costs, treated string and boolean costs as zero, and allowed `NaN` or infinite budget/cost values to reach snapshot serialization. A negative completion cost increased remaining paid authority; nonfinite values could leave a temporary file. | Snapshot reconstruction now requires a nonempty string timestamp and finite nonnegative budget and known call costs before writing. Missing cost remains allowed for a stopped or interrupted call and is not guessed as zero evidence. Event folding, budget validation, and cost summation are direct helpers; nine malformed cases assert no snapshot or temporary-file side effect. |
| RI-070 | P0 | reproduced | resolved 2026-07-23 | `load_resource_ledger` returned a no-event initial snapshot without reconciling its recorded totals. Before the first reservation, an empty ledger could claim `remaining_usd` above its budget, or claim prior spend without any event evidence, and reach experiment paid-call guards as authority. | The shared loader now validates persisted timestamp and finite amounts for an empty ledger and requires exactly zero spend plus remaining budget equal to the authorized budget. This check applies only when both calls and events are empty; event-backed ledgers continue to rebuild from their log, including an actual over-budget completion. Four public load cases cover inflated remaining authority, unproven spend, malformed spend, and timestamp shape. |
| RI-020 | P1 | code-confirmed | resolved 2026-07-22 | Existing monotonic Agent and Check durations were discarded; Result latency was reconstructed from wall-clock timestamps. | New Workspace runs persist monotonic `agent_seconds`, `verification_seconds`, and total `workspace_seconds` in the existing latency mapping. Result construction copies those measurements without deriving duration from wall-clock timestamps, and Reporting summarizes each available phase while retaining older total-only evidence. |
| RI-021 | P1 | code-confirmed and experiment-needed | measurement contract resolved 2026-07-22; cache experiment pending | Each cell creates separate solver and verifier repositories by fetching the exact base commit and its ancestors. | Current runs now persist solver/verifier checkout, diff replay, Agent, Check, and cleanup durations through one monotonic latency mapping; Reporting exposes phase coverage and checkout-plus-cleanup share without filling older Results with zeros. Evaluate a per-base sanitized object cache only when new measurements cross the reopening threshold below. Never expose a full source-repository object store. |
| RI-022 | P1 | reproduced, resolved 2026-07-22 | Evaluating one Selector at a time repeated result resolution and could repeat paid work across Selector studies. | `evaluate_selectors` freezes and persists every Selector/origin Selection before future resolution, executes the first-occurrence union once, reconstructs each CellSet in its own ref order, and reuses persisted CellSets on resume. Cached fixed-clock tests match sequential outputs exactly. |
| RI-023 | P2 | code-confirmed | resolved 2026-07-22 | JSONL loading accepted more representational freedom than the latest-schema and canonical-record policy implied. | Core JSONL loading now requires exact latest-schema keys and recursively valid field types, rejects blank or noncanonical records with line-numbered errors, and also type-checks unstructured root records. Certification evidence uses that loader plus an exact nested outcome schema. Result Store separately fails closed on an unterminated tail until explicit conservative recovery; one-off migrations remain separate. |
| RI-024 | P1 | code-confirmed | resolved 2026-07-22 | A model alias could retain the same recorded string while the provider changed its backing snapshot. | `AgentRecord` and `ResultCacheIdentity` now store the requested model separately from a nullable proven snapshot. Without a snapshot, a campaign ID plus positive UTC window is mandatory, enters exact-cache identity, and is rechecked before paid execution. Existing paid Results have a non-destructive one-off migration that conservatively treats the old value as an alias and requires a declared historical campaign scope containing every migrated execution. No model registry or provider resolver was added. |
| RI-033 | P1 | experiment-needed | future-work | Runner executes independent exact cells serially, so a larger paired history has wall time close to the sum of all Agent runs. | Target a bounded worker pool with immutable run contexts and one Result writer. Keep `max_concurrency=1` as the default and do not add a distributed scheduler. |

Checkout optimization is accepted future work. It is not selected for immediate
implementation because existing process notes show that paid Agent time
dominates the measured workflow. Shared-cell planning, Result indexing, and
failed-call prevention should be measured first.

### RI-021 Decision: Git Checkout Remains Future Work

The current local serial pilot measured a total orchestration overhead factor of
1.009. That result does not justify replacing the exact-base fetch path now. It
also does not close the issue for larger repositories, offline certification,
or a faster model endpoint.

Before changing checkout behavior:

1. record solver checkout, verifier checkout, diff replay, Agent, Check, and
   cleanup durations separately using monotonic clocks;
2. measure warm and cold p50/p95 times on small, medium, and large target
   repositories;
3. reopen optimization when checkout and cleanup exceed 5 percent of total
   scoreable-cell wall time, or when their p95 blocks the target throughput;
4. compare the current exact fetch with a cache keyed by repository identity and
   exact base OID that contains only that base's reachable ancestors;
5. verify that remotes, transient fetch refs, sibling-base objects, and known
   later commits are unavailable from the Agent workspace.

Step 1 is now enforced for current Workspace runs. `workspace_seconds` ends at
run-record construction; `cleanup_seconds` is separate, and Reporting uses
their sum only when all checkout and cleanup fields are present. This is
observability, not evidence that a cache would help. Steps 2 through 5 remain
the reopening gate.

If the cache wins, use ordinary Git repositories or worktrees and local files.
Do not introduce a checkout service, content-addressed filesystem, or custom Git
object manager.

### RI-017 Local Scaling Check

The 2026-07-22 local check generated canonical current-schema Result records,
appended each scale in one locked batch, then loaded one Result ID through the
normal filtered loader. Each value below is the median of three runs; generation
time is excluded. The 10,000-record file was 19,108,890 bytes.

| Records | Batch append median | Filtered load median |
| ---: | ---: | ---: |
| 100 | 0.011906 s | 0.021087 s |
| 1,000 | 0.118368 s | 0.209489 s |
| 10,000 | 1.183159 s | 2.144343 s |

Both paths scaled approximately linearly over this range. The filtered loader
still scans JSONL once, but Runner reuses the resulting in-memory index for the
whole operation. A persistent index or database is not justified by this
evidence; reopen that decision only when one scan becomes material to an actual
run or concurrent reader requirements change.

### RI-033 Decision: Bounded Parallel Execution Is The Target

Parallel execution belongs in the final Runner, but only as a bounded loop over
an already frozen set of unique exact cells. The target shape is:

```text
freeze all relevant Selections
  -> plan and deduplicate exact cells
  -> worker pool executes Workspace runs
  -> one coordinator appends Results
```

Prerequisites:

- RI-012 replaces mutable global bindings with immutable run context;
- RI-016 contains the full process tree and bounds output;
- RI-017 through RI-019 provide indexed, recoverable single-writer storage and
  duplicate-call preflight;
- API concurrency and rate limits are explicit run configuration;
- experiment design randomizes treatment order independently of worker timing.

Validation starts with deterministic offline Agents, then a small paid matrix
only when authorized. Compare serial and parallel runs for required identities,
outcomes, usage, cost, failure labels, and report evidence. Measure throughput,
API throttling, host contention, and invalid-rate changes. A speedup does not
count if it changes the evaluated cells or run conditions.

Use a fixed-size standard-library worker pool and `max_concurrency=1` by
default. Reopen implementation when a planned serial run exceeds one hour or
the server/API capacity is ready for controlled concurrency. Do not add a queue
service, distributed executor, or scheduler framework.

## Research Validity And Data Pipeline

### RI-025: Separate Task Arrival From Label Maturity

Priority: P0. Evidence: code-confirmed. State: contract resolved 2026-07-22;
empirical comparison pending.

The current origin split uses the maximum of source resolution, task material,
and Check material availability for both history and future membership. This
estimates performance on future tasks whose labels are already mature, not
necessarily on tasks arriving in future traffic.

Direction:

- define the future cohort by task arrival or task-material availability;
- make Check and Result availability conditions for training labels;
- score a frozen future cohort after a fixed maturity lag;
- report unresolved or unmatured source events as right-censored instead of
  silently dropping them.

Validation: compare the current label-time cohort with an arrival-time cohort
under several predeclared maturity lags. Report inclusion rate, label-delay
distribution, task count, and MAE on the same source-event frame.

Resolution: `RollingOriginRecord` now freezes cohorts by
`task_material_available_at`, records the maturity lag and cutoff, and separates
mature from censored history/future refs. Runner executes only mature refs;
empty mature future cohorts abstain. Training requires each training origin's
label-maturity cutoff to precede deployment. Reporting exposes the offline
arrival-versus-label-time counts, overlap, inclusion rate, and label-delay
distribution. Comparing MAE across several lags remains experiment work because
the repository does not yet contain a sufficiently large real paired history.

### RI-026: Build An Auditable Source-Event Frame

Priority: P1. Evidence: code-confirmed. State: resolved 2026-07-22.

Core Task supply currently filters caller-provided source events. It does not
collect issues, pull requests, or commits, and a frozen pool retains only an
inventory digest rather than a loadable sanitized inventory. Events that never
become candidates are therefore not auditable.

Direction: either rename the current function to describe filtering, or add
concrete source adapters. Persist a sanitized source frame containing event
identity, candidate eligibility, certification decision, rejection stage and
reason, label maturity, and dependency cluster.

Do not use inverse-propensity weighting until inclusion probabilities and the
source denominator are defensible.

Resolution: Task Pool now uses `CandidateBatch` to retain pre-certification
exclusions, joins every candidate with its certification decision, and persists
the ordered `SourceEventRecord` sequence in the immutable pool bundle. The frame
binds source identity, arrival, nullable label maturity, disposition, rejection
stage/reasons, accepted Task/Check links, dependency cluster, and sampling
stratum. Reporting validates the exact frame and summarizes disposition,
right-censoring, and label delay. Source collection remains adapter-specific;
the core did not gain a generic ingestion framework.

### RI-027: Use Dependency Clusters, Not Difficulty Labels

Priority: P1. Evidence: code-confirmed and experiment-needed. State: offline
adapter contract resolved 2026-07-22; broader relations and empirical
dependence remain pending.

Build a deterministic graph from issue/PR relations, revert or cherry-pick
links, and trusted certification-side patch overlap. Use connected components
as dependency clusters. Keep difficulty as a sampling stratum. Do not expose
reference-patch-derived features to the tested Selector.

Use two explicit estimands:

- realistic traffic, where clusters may recur and inference is cluster-blocked;
- unseen-cluster generalization, where future clusters are absent from history.

Current boundary: `dependency_cluster_id` is used only for origin filtering and
history/future blocking. `sampling_stratum` is separate and is exposed, when
requested, as `task_stratum`; dependency IDs never enter the FeatureSnapshot.
The fixed Pylint adapter uses difficulty only as a sampling stratum. It now
persists a self-digested `records/dependency-evidence.jsonl` containing trusted
reference-patch digests, repository-relative changed-path footprints, exact
path-overlap edges, and deterministic connected components. The Task Pool's
generator-config digest binds the evidence ref, protocol, and digest. Loading
re-derives the evidence from local trusted patches and replays SourceEvent
clusters before paid execution. Solver material and FeatureSnapshots exclude
the evidence and cluster values.

The historical ten-task Pylint material produces one edge: instances `6528`
and `7080` both change `pylint/lint/expand_modules.py`; the resulting component
sizes are `2, 1, 1, 1, 1, 1, 1, 1, 1`. This is an offline replay audit, not a
claim that all singleton tasks are independent. Add issue/PR, revert, or
cherry-pick relation sources only when a concrete adapter supplies auditable
data. Do not add a generic graph-ingestion service.

### RI-028: Measure Run-Level Variation

Priority: P0 before controller training. Evidence: code-confirmed and
experiment-needed. State: offline scheduling and paid-execution-boundary
contracts resolved 2026-07-22; empirical variation pending.

The current Pylint pilot contains ten low/high pairs, one run per cell, and one
discordant pair. It cannot separate reasoning-effort effects from run noise or
support a controller.

Next paired history should:

- repeat a predeclared 20 to 30 percent stratified task sample two or three
  times;
- randomize low/high order within Task;
- use an immutable model snapshot when available;
- separate task-sampling uncertainty from run-level variation.

Replicates should be explicit experiment evidence. Do not change the current
exact-cache rule to select the latest or best duplicate Result.

Resolution of the offline boundary: the Pylint-specific schedule tool freezes
the validated Task Pool members, two exact and behaviorally distinct Agents,
base Runtime config,
campaign, seed, largest-remainder stratified 20–30 percent subset, two or three
total observations, randomized within-Task Agent order, and every execution
cell. Replicate indices derive distinct campaign-scoped Runtime configs through
the existing stochastic-settings identity. Exact resume therefore addresses a
named observation slot and cannot choose among duplicates. The tool strictly
replays its self-digested artifact and refuses overwrite. No generic experiment
framework or new core record was added. Measuring run-level variation remains
blocked on the explicitly authorized paid history, not on scheduling code.

The consumer replays the entire schedule before Result access, resolves every
cell with its named Runtime slot in one locked Result Store session, preserves
the frozen order, and returns at most the first exact missing slot. Drift fails
before the store is opened.

The Pylint-specific campaign executor remains outside Core Runner. Its
self-digested authority ledger binds the schedule, Task Pool, Agent set,
Workspace and base Runtime configs, endpoint digest, total budget, per-call
estimated-cost limit, schedule-derived call cap, and ScoringConfig.
Preflight checks the current credential-backed endpoint, enough balance for one
per-call limit, and every remaining Runtime slot. Execution reserves and runs
only the first missing cell, appends its Result durably, and requires the
completion event to match the Result and cost limits. A Result written before
an interrupted completion event is reconciled; a stopped cell or a reservation
without an exact Result forbids automatic retry. The initializer refuses
overwrite, rejects malformed authority shapes before file creation, and must be
called only after explicit authorization. No authority ledger, Agent call, or
run-variation estimate was produced during implementation.

### RI-029: Predeclare Metrics And Uncertainty

Priority: P1. Evidence: code-confirmed and experiment-needed. State: offline
contract resolved 2026-07-22; empirical calibration pending.

Report at least:

- macro-origin MAE;
- future-task-count-weighted MAE;
- paired loss difference against a frozen fallback;
- deterministic random-seed-bank mean and variation for stochastic Selectors;
- cluster or time-block uncertainty intervals when the number of independent
  units supports them.

`future_coverage` and `future_invalid_rate` describe common holdout evidence.
They are diagnostics, not Selector performance measures.

Resolution: [`statistical-protocol.md`](statistical-protocol.md) fixes the
estimands and `summarize_selector_mae` executes them. It requires complete
paired Origin rows with exact common future Result evidence, reports
macro-Origin and scoreable-future-Task/Check-weighted MAE, and emits canonical
A-minus-B loss differences so any predeclared fallback has a direct paired row.
Exact non-seed Selector behavior defines stochastic seed banks. With at least
eight Origins, the summary emits a deterministic 10,000-resample paired
Origin-block percentile interval; below that threshold it records
`insufficient_origin_blocks` and null bounds. Reporting publishes this summary
only after full provenance validation and metric recomputation. Origin-block
interval calibration, cluster-robust intervals, and run-level uncertainty still
require the larger real paired/replicated history.

### RI-045: Link Prospective Future Traffic Separately

Priority: P1. Evidence: reproduced. State: resolved 2026-07-23.

`strict_prospective` correctly forbids future refs in the Origin frozen for a
Selection. `evaluate_selectors` nevertheless accepted that policy. A public
Runner counterexample reached Agent execution for selected cells after
persisting the selection chain, while its future denominator was necessarily
empty. Adding later tasks to the same immutable Task Pool or copying them into
the frozen Origin would make the evidence claim false.

Resolution:

- `evaluate_selectors` requires `counterfactual_replay` with
  `future_holdout_known=true`;
- unsupported policies fail before Task Pool loading, record writes, Result
  access, or Agent calls;
- `select_benchmark` retains strict-prospective selection and accepts the
  predeclared future window;
- `evaluate_prospective_selection` reloads the persisted Selection, Origin, and
  SelectorInput, verifies exact Agents, validates both immutable pools,
  materializes the later cohort, and calls the shared CellSet resolver and
  scorer;
- `EvaluationCellSet` binds the later Task Pool plus mature and censored refs;
  censored refs never enter execution;
- Reporting and `barcarolle report` require the linked future-pool JSONL and
  replay the same cohort derivation before supporting a strict claim.

The strict Origin remains the pre-exposure artifact and contains no future
refs. No generic source frame, stream processor, evaluator fork, or new module
was added.

### RI-046: Bind Task Pools To Their Observed Source Window

Priority: P1. Evidence: reproduced. State: resolved 2026-07-23.

A counterexample used a later pool whose accepted inventory was internally
valid but whose records could not establish whether collection covered the
strict Origin's complete future interval. `created_at` proves observation time,
not the start and end of source coverage. Reusing the generator-config digest
for actual events would prevent later snapshots from sharing one behavior
identity.

Resolution:

- generated and imported Task Pools persist canonical `source_window_start`
  and `source_window_end` values in their frozen record and bundle digest;
- the window cannot end after pool creation;
- accepted or certification-rejected SourceEvents outside it fail validation,
  while excluded outside events must record `outside_source_time_range`;
- generator configuration now describes collection mode and source family;
  SourceEvent, Task, Check, and certification digests describe observed
  inventory;
- prospective replay requires the later source window to begin no later than
  the selection-pool window and end no earlier than the planned future window.

This is the minimum evidence needed for two immutable snapshots; it is not a
generic source-frame abstraction.

### RI-047: Freeze Exact Agent Records Across Prospective Phases

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

`SelectorInput.agent_ids` froze membership and order but did not bind the full
Agent records. A caller could select with one Agent configuration, then pass a
different harness/model/prompt/tool configuration under the same ID during
future evaluation. The Result cache would correctly treat it as new execution,
but the Selection evidence would not prove that this was the frozen candidate.

Resolution: `SelectorInput.agent_record_digests` stores the canonical digest of
each complete `AgentRecord` in `agent_ids` order and enters SelectorInput
identity. Runner compares both tuples before Task Pool reads or Agent execution.
Reporting reconstructs the ordered digest tuple from its unordered supplied
Agent-record container and rejects drift. No Agent registry or model service
was introduced.

### RI-048: Replay The Complete Strict Selection Before Supply Reads

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

The two-phase strict entry point reloaded Selection, Origin, and SelectorInput,
but it did not load SelectorRecord or FeatureSnapshot before opening the two
Task Pools. A validly self-digested Selection could keep its original ID and
provenance while replacing the chosen ref with another eligible history ref.
Origin membership accepted that ref, so Agent execution remained reachable.
Reporting's later deterministic replay would withhold the claim only after the
costly boundary had been crossed.

Three repairs were compared. Calling Reporting from Runner inverted module
ownership and required output evidence that does not exist before execution.
Adding another Runner field list would create a fourth replay contract. The
selected repair keeps one direct `ensure_selection_replay` function in
Selection. It runs ordinary deterministic inference and compares every semantic
Selection field while excluding only observation time and self-digest.
Prospective Runner loads Selector, Origin, FeatureSnapshot, SelectorInput, and
Selection and invokes that assertion before Task Pool reads. Reporting,
training, and stratified diagnostics now use the same function. No record,
validation framework, or Reporting dependency was added to Runner.

### RI-049: Resolve Frozen Pre-Origin Results Before Supply Reads

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

RI-048 made the intrinsic Selector chain replayable, but the strict entry point
still did not open the Result bindings frozen by SelectorInput. Removing one
referenced Result left Selector, Snapshot, Input, and Selection individually
valid and deterministic, so the evaluator opened Task Pool artifacts. The
Reporting linker would later reject the missing Result, wrong digest,
post-origin availability, wrong Agent/history scope, or mismatched
FeatureSnapshot Result view only after the execution boundary.

Three repairs were compared. Calling Reporting from Runner would invert module
ownership and import report-only error accumulation into fail-fast preflight.
A Runner-local field list would duplicate the construction and training
contract. The selected repair adds one direct
`ensure_selector_input_result_evidence` function to Selection. It resolves
Result IDs/digests in frozen SelectorInput order, validates the exact Origin
Agent/history/cutoff scope, and replays aggregate and per-Result
FeatureSnapshot provenance. Input construction and learned-Selector training
reuse the same assertion. Prospective Runner queries only the frozen Result IDs
and invokes it after deterministic Selection replay but before Task Pool reads.
Reporting keeps its multi-error claim diagnostics. No record, Result index,
registry, or generic validation framework was added.

### RI-050: Replay Pre-Origin Cache Identity Before Execution

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

RI-049 proved that the exact Result records existed, but `ResultCacheIdentity`
still had a separate semantic relation to the frozen Agent, Task, and Check.
Result construction, Selection feature construction, and Reporting each listed
those fields independently. A red counterexample changed `prompt_digest`, then
redigested Result, FeatureSnapshot, SelectorInput, and Selection; every strict
preflight check passed and the evaluator opened Task Pool artifacts. The same
mechanism could change base commit, solver material, or Check identity and be
rejected only by later Reporting.

Trusting the original construction check was rejected because reports and
resume reconstruct evidence from self-digested logs. Copying the field list
into Runner would create a fourth contract. A generic evidence registry or
validation framework would add more structure than the relation needs. The
selected repair keeps three direct Records functions: project an AgentRecord
from a Result cache identity, compare that projection to an Agent, and compare
the Task/Check projection to frozen records. Result Store, Selection, and
Reporting reuse them.

Strict preflight is intentionally phased. SelectorInput already freezes full
Agent-record digests, so pre-origin Result Agent projection is checked before
any Task Pool read. Task/Check records live in the selection-time immutable
bundle, so Runner reads and validates that one bundle, replays the Origin, then
checks every resolved pre-origin Result against its Task/Check records. Only
afterward may it read the future pool or invoke an Agent. No schema, registry,
new artifact, or paid call was added.

### RI-051: Replay Task Metadata Feature Sources

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

FeatureSnapshot validation and deterministic Selector replay proved that a
snapshot was internally self-consistent, but they did not prove that
`task_metadata` values came from the frozen Task Pool. A red strict-prospective
counterexample changed one `task_stratum` from `a` to `0`, redigested the
FeatureSnapshot and SelectorInput, and regenerated a deterministic Selection.
The chosen Task/Check set changed, yet the old evaluator opened the future Task
Pool because scope and cutoff checks did not compare the value, observation
time, or source digest with the TaskRecord.

Rebuilding a snapshot from `FeatureConfig` was rejected because only the
derived config digest is persisted, not a second materialized config record.
Putting the check in Reporting was rejected because Runner must fail before
future supply reads. Deferring the check until a learned model exists was also
rejected because `stratified_forecast` already consumes the field. Selection
now owns `ensure_feature_snapshot_task_metadata_provenance`, a direct assertion
for the two current Task Pool-backed features. It binds every FeatureRecord to
the Origin/config digest, replays `task_count` against the exact Origin and pool,
and requires one `task_stratum` per history ref with the exact Task value,
known-at time, and canonical Task digest. Unknown `task_metadata` names fail
closed until their builder and replay rule are added together.

Snapshot construction and Reporting use the same assertion. Strict Runner
first replays the intrinsic Selector and Result/Agent evidence, then validates
the selection-time Task Pool and Origin, invokes the metadata assertion, and
only afterward may open the future pool or invoke an Agent. The current fitted
rule-mixture trainer does not consume Task metadata values, so its API was not
expanded merely for a future model. The first learned feature consumer must
load its frozen Task Pool evidence and call this existing assertion. No schema,
feature registry, training framework, telemetry, dependency, network access,
or paid call was added.

### RI-052: Derive Feature Configuration From Executable Names

Priority: P1. Evidence: reproduced. State: resolved 2026-07-23.

`FeatureConfig` previously exposed two caller inputs: feature names and allowed
leakage classes. The builder already hardcoded the class of every supported
feature, so the second input duplicated implementation truth. The config also
accepted empty, repeated, and unknown names. Mixing `unknown` with `task_count`
changed `feature_config_digest` and every downstream snapshot identity while
the builder silently emitted only `task_count`; reversing or repeating names
created other identities without a different extraction.

Keeping both inputs and merely checking that they agreed was rejected because
it preserved the redundant state. A generic FeatureSpec registry was rejected
because three features do not justify a plugin system. `FeatureConfig` now
takes only a tuple of names, validates non-empty strings, uniqueness, and the
current supported set, then normalizes the tuple to the explicit builder order.
A three-entry mapping derives the ordered leakage classes. Every production and
test caller now uses the one-axis constructor.

This is an alpha API cleanup, not a record-schema migration. Existing persisted
FeatureSnapshots retain their digests and load normally; recreating a former
no-op permutation intentionally produces the one canonical config identity.
Adding a feature remains a code change that must add its builder, provenance
replay, and name-to-class entry together. No feature service, registry,
compatibility shim, dependency, network access, or paid call was added.

### RI-053: Freeze Agent Treatment Across Learned-Selector Evidence

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

The learned rule-mixture trainer required every SelectorInput to carry the same
ordered `agent_ids`, but did not compare `agent_record_digests`. A red public
training counterexample changed the second Origin's Agent prompt digest,
redigested its SelectorInput, regenerated all expert Selections, and rebound the
matrices and metrics. The old trainer accepted the evidence as comparable. A
second counterexample changed every Origin consistently while leaving training
Results bound to the original Agent cache identity; that also fitted
successfully.

Treating Agent IDs as stable aliases was rejected because the benchmark
treatment includes model resolution, harness, prompt, tools, retrieval, skills,
network policy, and adapter. Requiring callers to supply Agent records again
was unnecessary because SelectorInput already freezes their canonical digests.
Training now compares the ordered `(agent_id, agent_record_digest)` bindings
across every Origin. After exact matrix/Result validation, it projects each
training Result cache identity through the Records-owned Agent projection and
requires the canonical digest to match that frozen binding.

This completes the Agent half at the data already available to Selection. The
Task/Check half requires frozen Task Pool records and is closed separately in
RI-054 rather than hidden in an Agent helper. No record, schema, training
framework, telemetry, dependency, network access, or paid call was added.

### RI-054: Bind Training Evidence To Frozen Task/Check Records

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

Origins froze a Task Pool ID and digest, but Selection's training API received
neither the TaskPoolRecord nor its member records. A red public counterexample
changed every outcome Result's base commit, redigested the Results, rebound all
matrix cells and metric digests, and successfully fitted the old trainer. The
same missing data also prevented training from replaying RI-051's Task metadata
provenance or checking pre-origin Results against their Task/Check sources.

Trusting Result construction was rejected because training reconstructs
self-digested logs. A Runner-only check was rejected because the public
Selection trainer would retain weaker semantics. A generic training context or
dataset record was unnecessary. The selected API adds the existing common
`TaskPoolRecord`, ordered Tasks, and Check mapping. Runner loads them through
the validated Task Pool bundle; direct algorithm callers pass the already
available records.

Before fitting, Selection now requires the deployment and all training Origins
to validate against that pool, checks exact member order and record digests,
replays every training FeatureSnapshot's Task metadata sources, and applies the
Records-owned Task/Check cache-identity predicate to all pre-origin and outcome
Results. Origin's existing Task Pool digest already binds this evidence in the
fitted Selector's training-source chain, so no new Selector field was added.
No record, schema, TrainingDataset, context object, dependency, network access,
or paid call was added.

### RI-055: Bind Every ResultCell Outcome To Its Result

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

Reporting's Result trace checked each bound Matrix cell's Result ID/digest,
Agent/Task/Check, and required cache identity, but did not compare the cell
outcome with `ResultRecord.outcome`. A public claim-boundary counterexample
changed a Result cell from pass to fail, redigested its EvaluationCellSet and
Matrix, retained the original passing Result, and was still reported as
supporting `agent_result_identity`. A public Runner counterexample supplied the
same contradictory CellSet before the first score; scoring converted the
binding to a missing cell instead of rejecting the false evidence.

Adding separate checks to Runner and Reporting was rejected because Result
Store and Selection training already maintained their own versions of the same
field relation. Records now owns one direct predicate over the seven frozen
fields: Result ID, Result digest, Agent ID, Task ID, Check ID, required cache
identity digest, and outcome. Result Store uses it while resolving cells;
Runner rejects contradictory bound evidence before Matrix construction;
Selection uses it for training Results; Reporting uses it for claims. Bound
excluded cells receive the same check, while genuinely unbound missing or
excluded cells retain their existing state contract.

No record, schema, compatibility layer, validation framework, dependency,
telemetry, network access, or paid call was added.

### RI-056: Preflight Reused CellSet Results Before Pending Execution

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

The shared batch resolver validated every persisted EvaluationCellSet's shape,
provenance, expected Agent/Task/Check cells, and required execution identities
before executing pending plans. It did not load the Results already bound by a
reused CellSet until the later scoring loop. A public two-Selector resume
counterexample first persisted a valid recency CellSet, changed one bound
outcome, and then added a pending coverage Selector with a new exact cell. The
old path invoked the Agent for that new cell before RI-055 rejected the reused
CellSet during scoring.

Validating each reused CellSet with a separate Result query was rejected because
it would add repeated JSONL scans. Runner now deduplicates every Result ID bound
by reusable CellSets, loads them once, and applies the Records-owned complete
cell predicate to each CellSet before constructing the pending union, opening a
Result Store write session, or invoking an Agent. Missing-only and unbound
excluded CellSets require no Result read and keep their frozen resume semantics.
The later scoring path reuses the same pure binding validator; no second field
list was introduced.

No execution context, persistent index, record, schema, dependency, telemetry,
network access, or paid call was added.

### RI-057: Require Results For Bound Excluded Training Cells

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

Runner's training loader collected every `(result_id, result_digest)` present in
selected and future Matrices. Selection's exact Result coverage, however,
visited only cells with `cell_state="result"`. A Matrix with a legitimate bound
benchmark exclusion therefore produced an extra training Result through Runner
and could not fit. A direct Selection caller could make the opposite mistake:
omit that excluded Result entirely, leaving the exclusion that changed the
denominator without its source evidence.

Treating all excluded cells as unbound was rejected because Result Store binds
benchmark-invalid and agent-invalid exclusions to the Result that justifies the
state, outcome, and reason. Adding a separate excluded-Result input was also
redundant. Training now skips a cell only when both Result ID and digest are
absent. Every present binding, whether `result` or `excluded`, must resolve in
`training_results` and pass the Records-owned seven-field predicate. Existing
Matrix validation still rejects partial bindings, and genuinely unbound
excluded or missing cells retain their existing semantics.

A public `complete_with_exclusions` fixture with a nonempty remaining Agent
denominator now fits when the excluded Result is supplied and fails when that
one Result is removed. No exclusion policy, record, schema, context, framework,
dependency, telemetry, network access, or paid call was added.

### RI-058: Derive Matrix Exclusions From Exact Result Evidence

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

RI-055 proved that a bound cell named the exact Result and outcome; RI-057 made
that proof cover excluded training cells. Neither contract proved that the
`excluded` state itself was justified. Two public counterexamples marked a
normal passing Result as a common exclusion with an invented reason. Reporting
still supported `agent_result_identity`, and learned-Selector training accepted
the reduced denominator as `complete_with_exclusions`.

Putting `cell_state` into the Records field predicate was rejected because an
EvaluationCellSet freezes raw result resolution while Result Store applies join
policy when constructing a Matrix. Persisting another policy record or reverse
registry was also unnecessary for the current closed policy set. Result Store
now owns a direct Matrix-evidence check: it resolves every bound Result, derives
the fixed task-wide benchmark-invalid exclusion and canonical reason, and
reconstructs the two existing agent-invalid branches (`count_as_failure` or
`exclude`). A normal Result cannot create an exclusion, and an unbound cell can
be excluded only when another benchmark-invalid Result excludes the whole
Task/Check denominator.

Selection training applies this check after exact binding coverage; Reporting
uses it for provenance and identity claims. The implementation separates bound
Result resolution from derived cell-state comparison, and neither helper is a
structural hotspot. No join-policy registry, record, schema, context,
framework, dependency, telemetry, network access, or paid call was added.

### RI-059: Enforce One Agent-Invalid Policy Per Matrix

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

The first RI-058 implementation compared each Matrix cell with both supported
agent-invalid branches independently. With two agent-invalid Results for one
Agent, a fully valid `complete_with_exclusions` Matrix could therefore exclude
one cell and retain the other as an invalid failure. The Matrix passed evidence
validation even though neither `ResultJoinConfig()` nor
`ResultJoinConfig(agent_invalid_policy="exclude")` could construct it. That
mixed denominator could reach Selection training or support Reporting claims.

Adding a per-cell policy was rejected because the existing join contract is
Matrix-wide. Persisting a policy registry or another configuration record was
also unnecessary while the implementation has two explicit supported
branches. Result Store now reconstructs the entire ordered cell tuple under
each branch and requires the supplied Matrix to equal one complete variant.
Task-wide benchmark-invalid behavior remains common to both variants. A direct
Result Store specification keeps the mixed-policy counterexample executable;
Selection and Reporting inherit the rejection through their shared evidence
check.

The full suite passes 646 tests with 2 skipped. The full-signal 38-file scan
remains at 118 hotspots (3 now / 46 soon / 69 monitor); the modified helper is
below thresholds. No policy registry, persisted config record, schema, context,
framework, dependency, telemetry, network access, or paid call was added.

### RI-060: Replay The Declared Matrix Policy

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

RI-059 required all cells to match one supported policy, but it searched both
agent-invalid branches without comparing the winning branch to the Matrix's
`join_policy_digest` or `denominator_policy_digest`. A default-policy Matrix
with an agent-invalid failure could therefore be redigested with the
agent-exclusion policy identity and still pass. Because Metric and Reporting
comparability use those digests, valid-looking records could be grouped or
described under behavior that did not produce them. A second counterexample
kept the agent-exclusion cells and scoreability but renamed the derived
`agent_specific_invalid_exclusion` abstention as `missing_required_results`.

Persisting the whole configuration was unnecessary: `ResultJoinConfig`
currently exposes two missing-cell choices and two agent-invalid choices, while
benchmark-invalid and abstention behavior each have one supported value. Result
Store now replays those four executable combinations. A Matrix is accepted only
when one combination exactly reproduces its join and denominator digests,
ordered cells, abstention reason, and scoreable state. The builder and validator
share the small agent-exclusion predicate; Selection and Reporting inherit the
stronger check.

Two direct Result Store specifications preserve policy-digest and abstention
drift, while RI-059 retains the mixed-cell counterexample. Valid Selection and
Reporting fixtures now use derived policy digests instead of placeholder
strings. The full suite passes 648 tests with 2 skipped. The full-signal 38-file
scan remains at 118 hotspots (3 now / 46 soon / 69 monitor); the changed helpers
remain below thresholds. No policy registry, persisted config record, schema,
context, framework, dependency, telemetry, network access, or paid call was
added.

### RI-061: Reject Malformed Campaign Authority Before Publication

Priority: P1. Evidence: reproduced. State: resolved 2026-07-23.

`initialize_replicate_campaign_ledger` validated finite budgets but relied on
type annotations for the other authority inputs. Passing one string as
`pricing_sources` converted it to a list of characters that later validation
still considered a sequence of strings. Non-string endpoint, scope, or
accounting values were written and only rejected on reload. Because authority
creation refuses overwrite, those calls left an unusable campaign ledger. A
non-string approval timestamp escaped as `AttributeError` rather than the
declared validation error.

The initializer now validates a timezone-aware string timestamp, non-empty
string endpoint/scope/accounting fields, and a non-string sequence containing
only non-empty source strings before checking path existence or writing either
file. Six public cases cover every malformed shape and assert that neither the
snapshot nor event log exists afterward. This remains a direct examples-layer
contract; no generic validator or campaign schema was added.

The initial inline fix moved the seven-input validator from `monitor` to
`refactor_soon` (CCN 13 to 20). Three small, reusable-within-module scalar and
sequence helpers reduce it to CCN 6 and restore the full-signal scan to 118
hotspots (3 now / 46 soon / 69 monitor). The full suite passes 654 tests with 2
skipped. No campaign authority, evidence write, telemetry, network access, or
paid call occurred.

### RI-062: Reject Duplicate Result IDs At The Shared Load Boundary

Priority: P0. Evidence: reproduced. State: resolved 2026-07-23.

Locked append already returned an identical existing Result and rejected a
same-ID different-digest write. That guarantee did not apply when opening an
existing JSONL file. `load_results` returned every duplicate, the live
`ResultStoreSession` used `setdefault` and kept the first, and Runner's batched
EvaluationCellSet preflight used a dictionary comprehension and kept the last.
The same damaged evidence could therefore resolve differently by caller. Even
an identical duplicate inflated raw query multiplicity and concealed an
impossible write history.

The shared unlocked loader now performs one ordered `result_id` uniqueness pass
after latest-schema record parsing and before any filtering or index creation.
The second occurrence raises a file- and line-numbered error; a conflicting
digest is named explicitly. Both shared-lock reads and exclusive session opens
use this loader. Four public cases cover identical and conflicting records
through both paths.

The check is one O(N) hash pass adjacent to the existing O(N) JSONL parse and
does not add a persistent index or change the accepted exact-cache policy. The
full suite passes 658 tests with 2 skipped. The full-signal scan remains at 118
hotspots (3 now / 46 soon / 69 monitor), and the helper is below thresholds. No
schema, migration, service, dependency, telemetry, network access, or paid call
was added.

## Learned Selector Infrastructure Decision

The project should be able to add the first learned Selector without changing
module ownership or rebuilding historical evidence. The following work is
justified before the server and LLM API are available:

- persist and reload RollingOrigin, FeatureSnapshot, SelectorInput,
  SelectorRecord, Benchmark Selection, cell set, matrix, and metric records;
- validate the full origin-to-report chain and preserve append order needed for
  prospective claims;
- make value-config digests derived and make Selector construction repeatable;
- separate fixed-rule construction, fitting, inference, and cross-Selector
  choice in the Selection API;
- require every fitted Selector to bind training origins, input snapshots,
  target evidence, hyperparameters, seed, and deployment cutoff;
- make the trainer reject evidence at or after the deployment origin;
- keep compact fitted parameters directly in `SelectorRecord` and verify that a
  loaded record is executable without the training process;
- make Runner freeze several Selector plans before executing their deduplicated
  union of exact cells.

Training should consume sequences of existing Origin, SelectorInput, matrix,
and metric records keyed by origin. Do not add a generic TrainingDataset or
TrainingExample record. ALG-001 can fit from prior-origin metrics; a later
task-level model may add the specific label view it needs while retaining the
same SelectorRecord output and inference boundary. Training already receives
the frozen Task Pool records and replays Task metadata provenance, so the first
feature-consuming model does not need a new evidence-loading API.

These tasks complete the known data path and improve current auditability. They
do not depend on choosing a model family.

Defer the following until the first concrete model requires them:

- tensor or tabular matrix abstractions beyond the existing FeatureRecords;
- external model artifacts for parameters that fit in a SelectorRecord;
- a model registry, feature service, training service, plugin SDK, or generic
  hyperparameter-search engine;
- GPU, distributed training, online serving, or automated retraining;
- schema fields that cannot be filled and validated by the first algorithm.

The first fitting implementation should be a data-efficient method already in
the Algorithm Backlog, preferably ALG-001. Its code may be algorithm-specific.
Extract a shared trainer abstraction only after a second fitted family exposes
the same stable behavior.

## Algorithm Backlog

Every adaptive method uses an outer rolling-origin loop. At deployment origin
`t`, fitting and hyperparameter selection may use only evidence from origins
strictly earlier than `t`. Hyperparameter tuning needs a nested rolling-origin
loop within that history.

| ID | Priority | Proposal | Required baselines and failure criterion |
| --- | --- | --- | --- |
| ALG-001 | P1 | Offline choice rule implemented 2026-07-22; empirical comparison pending. Shrink paired improvement toward a fallback and switch only when the conservative score clears minimum-history, margin, and uncertainty gates. | Compare fixed experts, raw mean chooser, no-shrink, no-gate, and hindsight oracle. Reject if outer-origin paired MAE does not improve or switching is unstable. |
| ALG-002 | P1 | Offline rule, replay diagnostic, and report integration implemented 2026-07-22; empirical comparison pending. Forecast future stratum proportions with Dirichlet-smoothed trailing counts, allocate capacity-constrained largest-remainder quotas, and evaluate with capped post-stratification weights. | Compare random, recency, coverage, and unweighted stratified selection. Report proportion TV error, effective sample size, and weight caps. Reject if outer-origin paired MAE does not improve, TV error is not better than the unweighted mix, or weighting collapses effective sample size. |
| ALG-003 | P2 | Offline grid and choice rule implemented 2026-07-22; empirical comparison pending. Evaluate a frozen ten-point thirds-simplex rank-mixture grid, then choose toward equal weights with a one-standard-error rule. | Compare equal weights, individual experts, and the current inverse-MAE-style mixture. Reject gains that disappear in outer-origin evaluation or are dominated by seed variation. |
| ALG-004 | P2 | Offline drift-aware guarded choice implemented 2026-07-22; empirical comparison pending. Rank complete chronological paired losses by EWMA, then require the selected candidate to clear the unweighted full-history safe-switch. | Compare non-decayed history and half-lives 0.5/1/2/4 in nested origins. Reject if outer-origin paired MAE does not improve or half-life choice is unstable. |
| ALG-005 | P2 | Evidence path ready; prediction code deferred pending a concrete resource estimand and observed outer-origin cost problem. Existing Results retain usage, pricing-view cost, latency, exact matrix bindings, and availability time. | Before implementation, choose one predeclared target: per-Cell p90, whole-Selection total, or bounded-concurrency wall time. Then report the relevant error/resource Pareto frontier against unconstrained selection. Do not create a generic ResourceMetric or hide objectives in a scalar score. |
| ALG-006 | P3 | Model the four paired Agent outcomes with hierarchical partial pooling across repositories or clusters. | Attempt only after many independent clusters, repeated cells, and discordant pairs exist. Compare against the safe-switch baseline. |

The four current chooser APIs are offline analysis rules, not deployment
evidence boundaries. They validate internal Selection/Metric/future-matrix
pairing and comparability, but they do not receive selected matrices or exact
Results and therefore cannot independently recompute MAE or establish Result
provenance. Keep them out of Runner defaults. Before promoting one into an
adaptive deployed policy, require a complete training-style matrix/Result
replay and persist the choice's source provenance. Adding those inputs and a
new choice record now would be unused infrastructure, so this remains an
explicit promotion gate rather than a schema change.

ALG-001's offline boundary is `SafeSwitchConfig` plus
`choose_selector_with_safe_switch`. It reuses exact paired Selection/Metric/
future-matrix validation, computes fallback-minus-candidate improvements,
shrinks their mean toward zero, and applies a sample-standard-error gate. The
default uses prior strength 2, four Origins, zero margin, and multiplier 1.
Synthetic characterization covers stable improvement, noisy apparent gains,
minimum-history fallback, margin behavior, and no-shrink/no-gate ablations.
These defaults are predeclared starting points, not calibrated or empirically
preferred parameters. Runner behavior and stored record schemas are unchanged.

ALG-002's offline boundary is the executable `stratified_forecast` rule family
plus `summarize_stratified_forecast`. It requires exactly one pre-origin
`task_stratum` FeatureRecord per eligible Task/Check ref, forecasts over a
declared trailing ref count with symmetric Dirichlet alpha, handles finite
stratum capacity while allocating largest-remainder quotas, and uses a seeded
digest rank inside each stratum. `weight_cap=null` is the exact unweighted
ablation; otherwise the existing Benchmark Selection weights contain capped
`forecast_share / selected_share` values and the current MAE scorer consumes
them without another schema. The diagnostic replays Selector/Input/Snapshot/
Selection evidence before reporting forecast, unweighted, and capped-weighted
TV error, effective sample size, maximum weight, and cap activation. Reporting
now derives these rows from the validated frozen TaskRecords and binds their
digest only after the complete Selector provenance chain passes. Synthetic
tests establish mechanism and failure behavior only. Nested hyperparameter
selection, outer-origin baselines, and empirical benefit remain pending; the
family is not a Runner default.

ALG-003's offline boundary is `build_rule_mixture_grid`,
`SimplexChoiceConfig`, and `choose_rule_mixture_from_grid`. The builder creates
the ten nonnegative thirds weight triples for coverage/random/recency and binds
one seed, coverage map, feature contract, version, and grid-protocol digest.
Every point remains an ordinary executable `rule_mixture`; the chooser accepts
only the complete grid with identical non-weight behavior and reuses exact
paired Selection/Metric/future-matrix validation. With fewer than four prior
Origins it returns equal weights. Otherwise it finds the lowest-mean-MAE point
and chooses the grid point closest to equal weights whose mean is within that
best point's sample standard error. This deliberately requires measured
mixture Selections: averaging individual-expert losses is not accepted as a
surrogate. Synthetic and replay-chain tests establish the mechanism only.
Nested use, outer-origin baselines, seed-bank comparison, and empirical benefit
remain pending; the inverse-MAE trainer and Runner defaults are unchanged.

ALG-004's offline boundary is `EWMASwitchConfig` plus
`choose_selector_with_ewma_guard`. It reuses exact paired Selection/Metric/
future-matrix validation, then requires the exact self-validating training
Origin set plus an explicit deployment Origin. Training records must use the
deployment Task Pool and one comparable policy. Their origin times and cutoffs
precede deployment, and label-maturity cutoffs cannot exceed the deployment cutoff.
Losses are ordered by unique materialized `as_of_cutoff` instants rather than
input order or Origin ID. The function ranks all registered Selectors by EWMA
loss, using weights `2^(-age/half_life)`.
The fallback remains selected when history is short or it ranks first. Any
other ranked candidate is compared only with the fallback through ALG-001's
ordinary unweighted, full-history safe-switch; decayed weights are not assigned
a confidence interpretation. The default half-life is two Origins, while
0.5/1/2/4 and non-decayed history form the predeclared nested comparison. Tests
establish chronology, recent-trend ranking, gate refusal, exact Origin coverage,
and scalar validation only. Outer-origin evidence, half-life selection, and
empirical benefit remain pending; Runner defaults and schemas are unchanged.

ALG-005 does not need more infrastructure before evidence exists. `ResultRecord`
already retains validated usage, repricing-aware cost, phase latency, exact
execution identity, and `result_available_at`; selected matrices bind those
Results to each frozen Selector/Origin, and the training boundary can reject
post-deployment evidence. The unresolved decision is statistical rather than
architectural: per-Cell p90, whole-Selection total resource, and critical-path
wall time under bounded concurrency are different estimands and yield different
hard-cap behavior. Cost also requires one explicit pricing view. Adding a
generic resource Metric, feature record, trainer, or result bundle now would
freeze an unsupported choice. Reopen ALG-005 only when an authorized outer run
shows a material resource problem and predeclares the target, cap, no-feasible
behavior, Agent/runtime comparability, and nested tuning protocol. The first
implementation should be one direct Selection function plus a Pareto summary
over existing evidence; add no schema unless that function cannot replay from
current records.

Do not currently prioritize deep networks, embedding fine-tuning, LLM-judge
features, reinforcement learning, contextual bandits, change-point models,
Gaussian processes, conformal intervals, or a reasoning-effort controller. The
available evidence is too small, and those methods add leakage and tuning paths
before the evaluation protocol is stable.

## Certification And Task Quality

| ID | Priority | Evidence | State | Finding | Direction |
| --- | --- | --- | --- | --- | --- |
| RI-030 | P1 | code-confirmed | resolved 2026-07-22 | Certification ran the base Check once while `repeat_count` repeated only the patched side. | Certification now runs exactly `repeat_count` fresh base-fail/patched-pass pairs and rejects later inconsistency. Historical paid evidence is not relabeled. |
| RI-031 | P2 | code-confirmed and experiment-needed | offline diagnostic contract resolved 2026-07-22; empirical rates pending | Task acceptance can be biased toward checks with accidental or flaky behavior. | Reporting now derives certification yield with its denominator, exclusions and rejection stage/reason counts, repeated-certification outcome-conflict quarantine rate, and later benchmark-invalid execution and affected-Task/Check rates. Pricing views do not duplicate the latter rates. Keep these observational until a larger Task supply supports a gate; do not make mutation score a hard gate without evidence. |
| RI-032 | P2 | code-confirmed | source-frame part resolved 2026-07-22 | Task Pool summaries and documentation claimed more source, rejection, and time coverage detail than the implementation stored. | Reporting now derives only supported source disposition, censoring, rejection, validation, and label-delay summaries from the validated bundle. Continue narrowing any unsupported adapter-specific claim. |

Functionality decisions:

- Implement the validated Task Pool bundle, paid-call preflight, symmetric flaky
  certification, canonical hidden-tree digest, reserved-namespace check,
  immutable model identity handling, and resumable single-writer Result path.
  They support the target evidence boundary without adding a module.
- Implement the sanitized source-event frame because prediction bias cannot be
  audited without events that failed to become Tasks.
- Add source adapters one repository family at a time. Do not create a generic
  issue-tracker or repository-ingestion framework before two concrete adapters
  demonstrate a shared contract.
- Keep hardened host isolation as an adapter boundary. Do not turn the core
  Runner into a container or cluster orchestrator.
- Add replicate and scheduling evidence at the experiment layer first. Promote
  it into core Result identity only when repeated-run reuse requires a stable
  cross-experiment contract.

## Documentation Backlog

| ID | Priority | State | Required maintenance |
| --- | --- | --- | --- |
| DOC-001 | P1 | complete 2026-07-22 | `docs/statistical-protocol.md` defines arrival, maturity, weighting, dependency, replicate, evaluation-mode, uncertainty, and nested-fitting rules. |
| DOC-002 | P1 | complete 2026-07-22 | `docs/design/evidence-storage-and-recovery.md` defines immutable Task Pool publication, explicit and separate roots, exact Result reuse, execution versus pricing views, Result-tail recovery, companion-log limits, and best-effort raw artifacts. |
| DOC-003 | P1 | complete 2026-07-22 | Selection behavior and documentation now agree on overlap and eligibility enforcement. |
| DOC-004 | P1 | complete 2026-07-22 | Reporting and data flow now name the complete supported provenance chain and exact Result inputs. |
| DOC-005 | P2 | current, ongoing | Records field lists and Check identity match current dataclasses; add a schema-contract test only when manual drift recurs. |
| DOC-006 | P2 | complete 2026-07-22 | Task Pool documentation now describes filtering/import and validated source-frame summaries; it does not claim built-in source collection. |
| DOC-007 | P2 | complete 2026-07-22 | Coverage and invalid rate are labeled holdout-evidence diagnostics, not Selector losses. |
| DOC-008 | P1 | complete 2026-07-22 | Selection docs distinguish executable paths from deferred learned methods. |
| DOC-009 | P2 | ongoing | Keep the RI-021 checkout threshold and RI-033 bounded-parallel prerequisites current when new timing evidence replaces the 1.009 serial-pilot estimate. |
| DOC-010 | P1 | complete 2026-07-23 | The Pylint pilot report documents the frozen campaign inputs and exact `authorize`, `preflight`, and one-cell `run-next` sequence without embedding credentials or campaign-specific values. |

Avoid expanding design documents for fields without a current caller. Update
`PROCESS.md` only when the active research direction, paid-call boundary, claim
boundary, or handoff state changes.

## Boundaries To Preserve

These items are marked `preserve`:

- separate solver and verifier Workspaces;
- inject hidden material only after solver diff capture;
- replay the captured diff in a fresh verifier instead of trusting solver state;
- retain structured exact cache identity and first-append selection semantics;
- keep pricing configuration outside paid-execution identity;
- bind campaign total and per-call estimated-cost authority before reserving a
  paid cell;
- freeze all static selections before opening any future Result evidence;
- preserve the RollingOrigin, FeatureSnapshot, SelectorInput, SelectorRecord,
  and Benchmark Selection chain needed by rule and learned Selectors;
- keep fitting and inference behind direct Selection functions rather than a
  training platform;
- count Agent-attributable invalid outcomes as failures, exclude benchmark
  invalidity task-wide, and abstain on missing comparison evidence;
- keep raw prompts, completions, transcripts, workspaces, oracle material, and
  full logs outside normalized records and tracked artifacts;
- keep the cooperative default adapter separate from optional hardened host
  isolation;
- keep latest-schema runtime code and use bounded one-off migrations for
  valuable older paid evidence.

Rejected shortcuts include merging solver and verifier Workspaces, letting an
Agent run hidden checks in its solver Workspace, interleaving origin scoring
with later-origin selection, reducing Result identity to a few display IDs,
choosing the latest or best duplicate Result, deleting invalid cells per Agent,
or putting raw verifier and Agent output into normalized reports.

## Recommended Sequence

### Stage 0: Evidence Integrity

Status: complete through 2026-07-23. RI-001 through RI-006, RI-016, RI-019,
RI-044, RI-047 through RI-067, and RI-069 through RI-090 are enforced before
another evidence-producing paid run.

Exit criteria:

- immutable base OIDs and Task Pool bundles;
- full Task/Check/Agent/Result trace in Reporting;
- common-denominator enforcement;
- enforceable rolling-origin policy and provenance;
- repricing-safe execution and cost summaries;
- timeout terminates the full process tree and output memory is bounded;
- paid-call preflight rejects duplicate or invalid identities.
- campaign cost authority reserves one declared per-call limit before execution.
- malformed campaign authority scalars and pricing-source collections fail
  before either ledger file is created.
- resource-ledger snapshots reject malformed timestamps and nonfinite,
  negative, string, or boolean accounting values before writing; absent cost
  remains explicit for calls whose usage is unknown.
- before the first event, a resource ledger proves zero spend and requires its
  remaining amount to equal the authorized budget.
- SourceEvent rejection reasons have one tuple-of-nonempty-strings runtime
  shape; malformed direct records return validation errors rather than raising.
- ResultCell result/exclusion payloads use nonempty strings or exact nulls, so a
  directly validated record remains reloadable under the same schema.
- Metric scope dimensions, optional refs, and completeness reasons use exact
  tuple/string/null shapes shared by direct validation and JSONL reload.
- Result Store reads reject duplicate `result_id` values before filtering or
  building any caller-specific index.
- Runner companion-log appends reject duplicate semantic IDs before idempotent
  resume or extension.
- Reporting rejects duplicate semantic IDs before supporting Result,
  Selection, cache, Selector-performance, or Agent/Result identity claims.
- Task Pool SourceEvents contain at most one candidate-linked event per
  certification candidate; set coverage cannot hide a duplicate.
- Persisted certification evidence and rejected candidate IDs replay the
  producer's canonical candidate-ID order.
- All certification evidence in one Task Pool shares one WorkspaceConfig and
  one RuntimeConfig digest.
- prospective execution replays the complete frozen Selector chain before
  supply reads.
- prospective execution resolves the exact frozen pre-origin Result view and
  Feature provenance before supply reads.
- prospective execution replays pre-origin Result Agent identity before supply
  reads and Task/Check identity before future-pool reads or Agent execution.
- Task Pool-backed FeatureRecord values replay against their frozen Origin and
  TaskRecords before future-pool reads or Agent execution.
- Feature configuration has one canonical executable identity derived from
  supported names and their implementation-owned leakage classes.
- learned-Selector training uses one complete frozen Agent treatment across
  Origins and binds every training Result cache identity to it.
- every bound ResultCell matches the Result ID/digest, Agent/Task/Check,
  required cache identity, and outcome before scoring, training, or claims.
- resumed batch evaluation validates all Results bound by reused CellSets before
  planning or executing any pending Agent cell.
- learned-Selector training requires Results for bound excluded cells as well as
  result-state cells; only truly unbound cells are omitted.
- Matrix exclusion state and reason must be derivable from benchmark-invalid or
  agent-invalid Results; a normal Result cannot be removed from the denominator.
- One complete Matrix must follow one agent-invalid join policy; cell-local
  mixtures cannot alter the denominator.
- Matrix join/denominator digests, cells, abstention reason, and scoreable state
  must all replay under that one declared policy.
- learned-Selector training validates its common Task Pool records, replays
  Snapshot Task metadata, and binds every Result Task/Check cache identity.

### Stage 1: Runtime, Storage, And Focused Refactoring

Status: complete through RI-068 on 2026-07-23.

Complete RI-007, RI-010 through RI-013, RI-017 through RI-020, and RI-068.

Exit criteria:

- hidden and reserved paths fail closed;
- one indexed, recoverable Result write path exists;
- monotonic timing separates Agent and verification work;
- malformed bounded-process limits fail before process start.

### Stage 2: Complete The Selector Infrastructure

Status: complete on 2026-07-22. RI-008, RI-009, RI-014, and RI-022 are
enforced without a model service or training framework.

Complete RI-008, RI-009, RI-014, and RI-022 as one coherent
record-and-function path. RI-005 claim safety and persistence are complete;
Stage 2 reuses that chain for training and multi-Selector execution.

Exit criteria:

- all existing Selector evidence records persist and reload through one path;
- `train_selector` fits one family instead of selecting the first candidate;
- fixed rules have an explicit construction path;
- fitting, inference, and choosing evaluated Selectors are separate operations;
- training evidence is strictly earlier than deployment origin;
- a loaded compact fitted Selector is executable without retraining;
- several frozen Selectors share one deduplicated execution plan without future
  leakage.

Validation includes wrong Selector digests, non-replayable Selections, forged
MAE, incomplete Result bindings, cutoff-equal prospective Results, two training
origins with cutoff-specific leakage policies, pre-origin feature provenance,
reverse ref order, cached sequential equivalence, partial execution recovery,
and persisted missing CellSet reuse.

Do this before the model server arrives. Do not add model services or generic
training frameworks.

### Stage 3: Research Protocol And Data

Complete the offline contracts for RI-025 through RI-030 and the source-frame
part of RI-032, then run the empirical parts only with authorized evidence.

Exit criteria:

- arrival and label times have separate roles (complete);
- censored events are auditable (complete), and deterministic dependency-edge
  provenance is complete for the concrete Pylint adapter;
- a larger paired history includes randomized repeated cells (paid experiment
  pending);
- all baselines share frozen origins and common future evidence (complete);
- strict-prospective performance evidence links a later Task Pool or source
  frame to the original frozen Origin without rewriting either snapshot
  (complete for the later-Task-Pool path; empirical evidence pending);
- estimands and uncertainty rules are predeclared (offline contract complete;
  empirical calibration pending).

The concrete Pylint campaign entry is complete. Task Pool expansion is not a
generic prerequisite: select one Task Generator first, and wait for the model
endpoint when that generator is LLM-driven.

### Stage 4: Adaptive Algorithms

Evaluate ALG-001 and ALG-002 first. Continue to ALG-003 through ALG-005 only
when outer-origin evidence shows a remaining error or cost problem. ALG-006
requires substantially more independent data.

### Stage 5: Scale Optimization

Use RI-021 and RI-033 as the accepted final-shape decisions. Implement checkout
caching or bounded parallelism only after their prerequisites and reopening
thresholds are met. Adopt only variants that preserve the Stage 0 evidence tests
and show material wall-clock or paid-cost improvement.

## Resolved Findings

- RI-001: Runner and Reporting bind Results to the frozen Task Pool bundle.
- RI-002: scoreable Tasks use immutable full commit OIDs and verified checkout
  HEADs.
- RI-003: Task Pool artifacts publish as immutable content-addressed bundles.
- RI-004: comparative metrics preserve one common Agent denominator.
- RI-005: rolling-origin behavior is enforced and the complete Selector evidence
  chain is persisted, reloaded, validated, and deterministically replayed.
- RI-006: Reporting separates executions from alternative pricing views.
- RI-007: certification binds the executed Check, Workspace/Runtime configs,
  verifier adapter, and canonical hidden-material tree; reserved destinations
  and symlinks fail closed.
- RI-008: Selection fits the existing rule-mixture from complete, replayable
  prior-origin evidence and returns an executable Selector with category-bound
  training-source digests. Fixed rules have a non-training constructor.
- RI-009: inference requires the materialized FeatureSnapshot and validates its
  exact input, cutoff, leakage classes, and pre-origin Result provenance.
- RI-010: budget, join/denominator, claim, feature, leakage, and origin policy
  digests are derived from their canonical behavior fields; callers cannot
  provide a conflicting label. External execution-environment digests remain
  binder-verified inputs.
- RI-011: stable semantic IDs remain unchanged. On resume, Runner reuses the
  first persisted Selector, Benchmark Selection, or Metric when every field
  except its observation timestamp and self-digest is identical, and returns
  that exact record downstream. Any behavior or provenance drift under the
  same ID still fails closed.
- RI-012: Repository, Agent harness, and Check bindings live in an immutable
  `WorkspaceRunContext` passed explicitly through Runner, Task Pool, and
  Workspace. Every bind returns a new context, is idempotent for an identical
  value, and rejects a conflicting same-context rebind. Independent contexts
  can bind the same semantic Check differently without cross-run state.
- RI-013: Records owns the one timezone-aware UTC parse/format contract and the
  canonical Check-command digest used by Workspace and Verification. Naive
  record times, rolling origins, TimeRange boundaries, Result query cutoffs,
  and Runner origin schedules fail instead of being silently interpreted as
  UTC. Path containment uses `Path.is_relative_to`. The two runtime workspace
  values remain separate because one owns checkout lifecycle while
  `VerifierWorkspace` carries only the Verification adapter binding; merging
  them would add verifier-only nullable state to solver workspaces.
- RI-014: `BenchmarkSelectionRecord` is frozen by construction and no longer
  carries unused exposure state, exposure time, or exposure scope fields. The
  behavior-free `SelectionConfig` was removed; inference now takes only a
  frozen `SelectorInput` and executable `SelectorRecord`. Runner persists every
  Selection before opening future outcomes, and Reporting rejects a
  strict-prospective performance chain when a bound future Result was already
  available at Selection creation time.
- RI-015: paid examples share one small event-sourced single-writer resource
  ledger while keeping endpoint, pricing, scoreability, and exact-cell rules
  local.
- RI-016: subprocess output is bounded and timeout cleanup owns descendants.
- RI-019: paid missing-cell execution has one batch preflight plus Workspace
  just-in-time revalidation; endpoint credentials and raw URLs are not stored.
- RI-017: Runner uses one locked, live Result index per operation; batch append
  and filtered-load scaling is linear through 10,000 local records.
- RI-018: Result JSONL has a single-writer lock, fsync policy, line-numbered
  failures, and explicit conservative tail recovery.
- RI-020: Result latency preserves monotonic Agent, Verification, and Workspace
  phase measurements.
- RI-022: multi-Selector evaluation freezes all Selections first, executes one
  deduplicated exact-cell union, reconstructs per-Selection order, and resumes
  without repeating durable cells or rewriting CellSets.
- RI-023: core evidence JSONL accepts only exact current-schema, canonical
  records; Result Store retains its separate explicit tail-recovery contract.
- RI-024: requested and resolved model identities are separate; unresolved
  aliases cannot execute or reuse exact cache evidence outside their campaign
  scope.
- RI-025 (contract): rolling origins use arrival cohorts, fixed label-maturity
  lag, and explicit mature/censored history and future refs; Runner never
  executes censored refs.
- RI-026: immutable Task Pool bundles persist and validate the complete
  sanitized source-event denominator, including exclusions and right-censoring.
- RI-027 (offline Pylint adapter contract): trusted reference-patch footprints
  produce persisted exact-path relation edges and deterministic components;
  Task Pool identity binds the artifact and replay rejects drift before paid
  execution.
- RI-028 (offline execution contract): a self-digested Pylint schedule freezes
  the stratified repeated subset, paired seeded order, and exact Runtime
  observation slots before Result access. A separate self-digested campaign
  authority binds endpoint, total budget, per-call estimated-cost limit, call
  cap, pricing, and ledger evidence; execution advances only the first missing
  slot. Empirical variation remains pending.
- RI-029 (offline contract): comparable Selector evidence now produces
  predeclared macro/weighted MAE, paired differences, seed-bank variation, and
  sample-size-gated deterministic Origin-block intervals; Reporting withholds
  the summary when provenance or recomputation fails.
- RI-030: every certification repeat is a fresh base-fail/patched-pass pair.
- RI-031 (offline diagnostic contract): Reporting exposes certification yield,
  rejection and repeated-outcome-conflict diagnostics, plus deduplicated later
  benchmark-invalid rates without changing task acceptance.
- RI-032 (source-frame scope): Task Pool reports derive only claims supported by
  the validated source-event, Task, Check, and certification bundle.
- RI-035: every present Task, Check, Agent, and cache-identity link on a
  Result-level FeatureRecord matches the exact visible Result; origin-level
  aggregate evidence remains bound to the complete Result view.
- RI-036: RollingOrigin construction requires all Task Pool Task/Check records
  and exact Check ownership before it derives mature or censored denominators.
- RI-037: ResultCellRef payloads and ResultMatrix scoreability now form one
  fail-closed state machine: Result, excluded, missing, and abstained evidence
  cannot carry contradictory bindings, outcomes, or scoreability labels.
- RI-038: RollingOrigin cutoff rules, materialized cutoffs, and future windows
  are mutually consistent before an Origin can enter the evidence chain.
- RI-039: SourceEvent material timestamps fail closed through validation, and
  every recorded rejection reason is a non-empty string.
- RI-040: a replicate schedule requires exact protocol scalar types and two
  behaviorally distinct Agent configurations, not merely distinct Agent IDs.
- RI-041: the historical Pylint report uses only its exact execution identities
  and cannot claim completion without a complete resource ledger.
- RI-042: SelectorInput budget, set-membership, cutoff, identity, and self-digest
  invariants share one Records contract; Reporting treats separately supplied
  Agent records as an unordered set without relaxing frozen matrix order.
- RI-043: malformed certification reason payloads fail closed through Task Pool
  artifact validation, and accepted attempt summaries cannot contradict the
  normalized Verification outcome, failure-label, or timeout state.
- RI-044: replicate campaign v2 reserves a declared per-call estimated-cost
  limit before execution, derives its exact call cap from the frozen schedule,
  and rejects Results above the per-call or cumulative authority.
- RI-045: strict-prospective evaluation links one later immutable Task Pool
  through the existing EvaluationCellSet, retains mature/censored refs, and
  reuses the counterfactual Result/matrix/scoring machinery without mutating
  the frozen Origin.
- RI-046: Task Pools bind canonical observed source windows separately from
  behavior-only generator identity, so later snapshots can prove complete
  future-window coverage without pretending inventory is configuration.
- RI-047: SelectorInput freezes ordered canonical Agent-record digests as well
  as IDs; prospective Runner and Reporting paths reject same-ID behavior drift.
- RI-048: prospective Runner reloads and deterministically replays the complete
  Selector/Origin/FeatureSnapshot/SelectorInput/Selection chain before Task
  Pool reads; Reporting, training, and diagnostics share the same assertion.
- RI-049: prospective Runner resolves every Result ID/digest frozen by
  SelectorInput and replays its Origin scope and Feature provenance before Task
  Pool reads; construction and training share the same assertion.
- RI-050: Records owns Result cache-identity projection against Agent/Task/Check
  records; prospective Runner checks Agent identity before supply reads and
  Task/Check identity after validating the selection pool but before future
  supply or Agent execution.
- RI-051: Selection owns Task metadata Feature provenance. Snapshot
  construction and Reporting share it; prospective Runner replays exact
  `task_count` and `task_stratum` sources after validating the selection pool
  and before future supply or Agent execution.
- RI-052: FeatureConfig has one behavioral input. It rejects empty, duplicate,
  and unsupported names, normalizes supported names to builder order, and
  derives leakage classes instead of accepting a redundant caller list.
- RI-053: learned-Selector training requires one ordered full Agent identity
  binding across Origins and replays every training Result's Agent cache
  projection before fitting.
- RI-054: learned-Selector training explicitly receives the common frozen Task
  Pool records, replays every Origin/Snapshot against them, and binds all
  pre-origin and outcome Result Task/Check cache projections before fitting.
- RI-055: Records owns the complete ResultCell-to-Result field relation. Result
  Store, Runner, Selection training, and Reporting reject a bound cell whose
  ID/digest, Agent/Task/Check, required identity, or outcome differs from its
  Result.
- RI-056: batch resume resolves and validates every Result bound by reusable
  CellSets in one read before missing-result planning or pending Agent calls.
- RI-057: training exact-coverage and Runner loading agree that every cell with
  a Result ID/digest, including `excluded`, requires the matching Result.
- RI-058: Result Store derives allowed Matrix exclusion states and reasons from
  exact Result invalid ownership; Selection training and Reporting reuse it.
- RI-059: one complete Matrix must match one supported Result join policy;
  agent-invalid cells cannot mix denominator treatment within the Matrix.
- RI-060: the complete Matrix must replay under its declared policy digests,
  including policy-derived abstention and scoreability.
- RI-061: campaign authority input shapes fail closed before immutable ledger
  publication, including scalar `pricing_sources` values.
- RI-062: the shared Result Store loader rejects duplicate Result IDs before
  raw queries, live-session indexes, or CellSet preflight can disagree.
- RI-063: every Runner companion-log append validates complete semantic-ID
  uniqueness before idempotent resume or extension.
- RI-064: Reporting requires unique semantic IDs for every top-level evidence
  type consumed by a supported claim.
- RI-065: candidate-linked SourceEvents are one-to-one with certification
  evidence; duplicate non-null candidate IDs cannot inflate the source frame.
- RI-066: persisted certification evidence and rejected candidate IDs retain
  the producer's canonical candidate-ID order.
- RI-067: every certification decision in one Task Pool binds the same
  Workspace and Runtime configuration digests.
- RI-068: bounded-process requests validate finite time bounds and an integer
  capture bound before starting a process; containment phases remain direct.
- RI-069: shared resource-ledger reconstruction validates its timestamp,
  budget, and every known call cost before publishing the derived snapshot;
  unknown cost remains absent rather than being guessed.
- RI-070: a no-event resource ledger must prove zero spend and preserve the
  authorized budget exactly before its first reservation.
- RI-071: SourceEvent rejection reasons have one runtime container and malformed
  direct records fail validation without raising.
- RI-072: ResultCell state payloads require exact null or nonempty string
  bindings and remain reloadable after direct validation.
- RI-073: Metric dimensions, optional refs, and completeness reasons have exact
  reloadable tuple/string/null shapes.
- RI-074: every transient certification decision uses an exact boolean before
  it can become SourceEvent, certification, or frozen Task Pool evidence.
- RI-075: malformed top-level certification evidence returns accumulated Task
  Pool validation errors instead of raising during SourceEvent linkage.
- RI-076: public Metric construction requires Selection and Origin eligibility
  modes to match before aligning prospective or counterfactual matrices.
- RI-077: ClaimConfig has only canonical requested claims; completeness and
  validity cannot be weakened, and an Agent/Result identity claim requires and
  digests matching supplied Agent evidence.
- RI-078: metric identity is derived from the versioned implemented scoring
  protocol and frozen Selection budget; batch Selector, Agent, mode, and origin
  schedule validation completes before Task Pool reads or companion writes.
- RI-079: exact full-identity Result reuse is not configurable, and the only
  benchmark-invalid reuse switch accepts an exact boolean before it can alter
  cache resolution or a paid-work plan.
- RI-080: Workspace artifact refs are always relative; retention flags and
  summary modes fail at config construction instead of accepting malformed
  truthy controls or reaching Agent execution.
- RI-081: certification repeat count is an exact positive integer before any
  base/patched Workspace checks or certification evidence construction.
- RI-082: report filenames are direct typed children of `output_dir`; absolute,
  nested, traversal, and format-swapped paths fail before report construction.
- RI-083: training, paired Selector comparison, and Reporting accept only the
  current implementation-owned Metric protocol; unknown protocols remain
  loadable records but cannot support an algorithm or claim.
- RI-084: rolling-origin future-holdout state is an exact boolean at policy and
  persisted-record boundaries.
- RI-085: malformed raw timeout, exit-code, or duration values normalize to
  invalid and cannot become pass evidence.
- RI-086: Check normalization configuration has disjoint typed exit semantics
  and validated failure-label/redaction controls before use.
- RI-087: batch preflight validates immutable Check and Agent bindings once per
  unique identity while preserving every per-cell just-in-time recheck.
- RI-088: rolling-origin dependency filters contain only nonempty string IDs and
  cannot silently change cohorts through type mismatch.
- RI-089: persisted Selection weights and Metric values use exact finite float
  representations, so validation cannot approve a line that canonical reload
  rejects after numeric coercion.
- RI-090: scoring rates are validated, float-normalized, and snapshotted at
  construction, so equivalent pricing behavior has one stable digest and one
  pricing view identity.
- RI-091: an absent pre-origin Result lower bound is null rather than an invalid
  empty-start TimeRange sentinel.
- RI-092: public record validators supplement semantic checks with the existing
  latest-schema scalar conversion before accepting persisted evidence.
- RI-093: the Task Pool record itself passes the Records schema and self-digest
  contract before cross-artifact reconciliation.
- RI-094: candidate and excluded-event ingestion requires declared scalar and
  container types before candidate or SourceEvent identity derivation.
- RI-095: executable Selector parameters use one canonical numeric and nested
  mapping snapshot before config or Selector identity derivation.
- RI-096: Task Pool freeze metadata must already contain its declared string
  values; publication never converts arbitrary objects into evidence text.
- RI-097: rule-mixture construction uses one complete scale-free unit simplex
  that is idempotent under executable validation; shared canonical JSON owns
  signed-zero identity equivalence.
- RI-098: signed-zero scoring rates collapse to positive zero before pricing
  identity is derived.
- RI-099: shared UTC parsing rejects non-string timestamps through the declared
  validation exception, so Task Pool artifact validation returns collected
  schema errors instead of raising.
- RI-100: every public record validator gates domain semantics with the one
  existing latest-schema conversion, and valid records no longer repeat that
  conversion at the end.
- RI-101: Task Pool artifact validation treats the pool record and Task/Check
  member layer as prerequisites; invalid inputs cannot enter certification or
  SourceEvent reconciliation.
- RI-102: canonical JSON recursively maps floating signed zero to positive zero,
  so behavior-equivalent nested values cannot fork record or configuration
  identity.
- RI-103: Task Pool member validation proves each Task and Check record before
  any cross-member repository, digest, ID, or linkage relation.
- RI-104: ResultQuery validates filter containers, timestamp shapes, and bound
  order before Result Store state can affect the outcome.
- RI-105: Result construction validates Task, Check, Agent, and WorkspaceRun
  records before linkage or cache-identity projection.
- RI-106: exact cache-identity construction validates Task, Check, and Agent
  records plus Task/Check linkage before missing-cell or reuse planning can
  consume the identity.
- RI-107: WorkspaceConfig and RuntimeConfig use Records-owned latest-schema and
  semantic validation before exact cache-identity construction.
- RI-108: Task Pool validates both configs before any certification Check or
  certification-evidence digest.
- RI-109: Workspace validates both configs before execution preflight, while
  Runner reuses the shared RuntimeConfig contract instead of local type logic.
- RI-110: Workspace validates WorkspaceConfig before repository binding can
  create immutable run-context state.
- RI-111: Runner validates Task Pool build configs once before candidate
  resolution while retaining just-in-time certification checks.
- RI-112: the Pylint replicate CLI loads frozen campaign evidence and exposes
  explicit authority, preflight, and one-cell execution operations without a
  second executor or automatic paid loop.

## Update Log

- 2026-07-23: closed RI-112 and recorded RI-113. The Pylint replicate campaign
  now has one concrete CLI over its existing authority and executor APIs. Three
  actions keep authorization, no-call preflight, and single-cell execution
  separate; verifier images are replayed before paid execution; campaign
  artifacts are confined below one local directory and CLI summaries omit
  credentials and raw endpoint values. Five focused CLI specs
  cover explicit authority, no implicit ledger creation, exact frozen-input
  loading, image-verified preflight, and one-cell execution; the full suite
  passes 837 tests with 2
  skipped. Task Pool expansion is deferred until a concrete Task Generator and
  any required model endpoint exist. No campaign ledger, network request, paid
  call, Task Generator, or core Runner path was added.

- 2026-07-23: closed RI-110, RI-111, and RI-034's ninety-fourth and
  ninety-fifth boundary slices. Workspace repository binding now validates its
  config before returning an immutable context, and Runner Task Pool
  construction validates both configs before candidate resolution while
  retaining certification-time checks. Three red cases, all 75 Workspace tests,
  all 58 Runner tests, and the full suite of 832 tests with 2 skipped pass. The
  refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon /
  76 monitor), critical counts 0/19/0, and no dead-code candidate. No
  TaskPoolConfig wrapper, generic preflight framework, network access, paid
  benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-108, RI-109, and RI-034's ninety-second and
  ninety-third boundary slices. Task Pool certification now validates configs
  before Check execution, and Workspace validates them before repository or
  plan state even for an empty plan. Runner reuses the shared Runtime validator.
  Four red cases, all 87 Task Pool tests, all 74 Workspace tests, and the full
  suite of 829 tests with 2 skipped pass. The refreshed 38-file full-signal
  scan remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
  0/19/0, and no dead-code candidate. No config wrapper, execution context,
  copied schema, network access, paid benchmark call, or campaign authority was
  added.
- 2026-07-23: closed RI-107 and RI-034's ninety-first boundary slice. Records
  now owns direct WorkspaceConfig/RuntimeConfig validators, and Result Store
  applies them before exact identity construction. Six red cases and 13
  type/semantic disturbances reject every malformed input without leaked
  exceptions; all 91 Result Store tests pass, and the full suite passes 825
  tests with 2 skipped. The refreshed 38-file full-signal scan remains at 112
  hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
  dead-code candidate. No config wrapper, copied schema, validation framework,
  network access, paid benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-106 and RI-034's ninetieth boundary slice.
  `compute_result_cache_identity` and `build_result_record` now share the
  Task/Check/Agent record prerequisite and Task/Check linkage check. Four red
  cases and a repeated 36-field disturbance audit reject every malformed input
  without leaked exceptions; all 85 Result Store tests pass, and the full suite
  passes 819 tests with 2 skipped. The refreshed 38-file full-signal scan
  remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
  0/19/0, and no dead-code candidate. No input wrapper, copied schema,
  validation framework, network access, paid benchmark call, or campaign
  authority was added.
- 2026-07-23: closed RI-105 and RI-034's eighty-ninth boundary slice.
  `build_result_record` now validates all four input records before relations.
  Five public cases and a temporary 52-field disturbance audit reject every
  malformed input without leaked exceptions; all 81 Result Store tests pass,
  and the full suite passes 815 tests with 2 skipped. The refreshed 38-file
  full-signal scan remains at 112 hotspots (0 now / 36 soon / 76 monitor),
  critical counts 0/19/0, and no dead-code candidate. No Result-input wrapper,
  copied schema, validation framework, network access, paid benchmark call, or
  campaign authority was added.
- 2026-07-23: closed RI-104 and RI-034's eighty-eighth boundary slice.
  `load_results` now validates all ResultQuery filters and availability bounds
  before checking store existence. Eleven red cases cover six malformed filter
  containers, malformed items, numeric/empty time bounds, and an inverted
  interval; all 76 Result Store tests pass, and the full suite passes 810 tests
  with 2 skipped. After direct filter/timestamp helper separation, the refreshed
  38-file full-signal scan remains at 112 hotspots (0 now / 36 soon / 76
  monitor), critical counts 0/19/0, and no dead-code candidate. No query schema,
  normalization object, index, network access, paid benchmark call, or campaign
  authority was added.
- 2026-07-23: closed RI-103 and RI-034's eighty-seventh boundary slice. Task
  Pool member validation now runs the existing Task/Check validators before
  repository, digest, ID, and linkage relations. The `check_ids` red case, all
  85 Task Pool tests, and a temporary 21-field member disturbance audit pass
  without exceptions. The full suite passes 799 tests with 2 skipped. The
  refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon /
  76 monitor), critical counts 0/19/0, and no dead-code candidate. No member
  wrapper, schema copy, catch list, network access, paid benchmark call, or
  campaign authority was added.
- 2026-07-23: closed RI-102 and RI-034's eighty-sixth boundary slice. The
  shared canonical-data conversion now emits built-in floating `-0.0` as
  positive `0.0` at every nesting depth. A red JSON/digest spec and direct
  Result/Metric probes collapse previously distinct self-digests; all 126
  Records tests pass and the full suite passes 798 tests with 2 skipped. The
  refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36 soon /
  76 monitor), critical counts 0/19/0, and no dead-code candidate. No per-field
  registry, constructor fanout, alternate encoder, network access, paid
  benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-101 and RI-034's eighty-fifth boundary slice. Task Pool
  artifact validation now stops at an invalid pool record or Task/Check member
  layer instead of continuing into certification and SourceEvent relations.
  The `rejected_candidate_ids` red case, all 84 Task Pool tests, and a temporary
  20-field disturbance audit pass without exceptions. The full suite passes 797
  tests with 2 skipped. The refreshed 38-file full-signal scan remains at 112
  hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
  dead-code candidate. No per-field catch list, validation framework, artifact
  layer, network access, paid benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-099, RI-100, and RI-034's eighty-third and
  eighty-fourth boundary slices. Shared UTC parsing now rejects non-string
  values through `ValueError`; public record validators run the existing
  latest-schema conversion before domain semantics and no longer replay it a
  second time. Three representative record cases, one Task Pool timestamp
  case, 125 Records tests, and 83 Task Pool tests pass. A temporary audit of all
  16 public record validators and 256 one-field disturbances found zero base
  failures and zero exceptions. The full suite passes 796 tests with 2 skipped.
  The refreshed 38-file full-signal scan remains at 112 hotspots (0 now / 36
  soon / 76 monitor), critical counts 0/19/0, and no dead-code candidate.
  No validation framework, schema registry, compatibility mode, network access,
  paid benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-097, RI-098, and RI-034's eighty-first and
  eighty-second boundary slices. Rule-mixture construction now freezes one
  complete float unit simplex for its scale-invariant ranking behavior; external
  records with scaled or omitted weights fail executable validation, while
  RI-102 later makes signed-zero spelling share canonical identity. The
  transform survived 10,000 deterministic randomized
  idempotence probes. Scoring configuration now maps `-0.0` rates to positive
  zero before digesting. Four new public cases pass; Selection and Result Store
  have 169 and 65 passing tests, and the full suite has 792 passed with 2
  skipped. The 38-file scan remains at 112 hotspots (0 now / 36 soon / 76
  monitor), critical counts 0/19/0, and no dead-code candidate. No schema,
  registry, training framework, dependency, network access, paid benchmark
  call, or campaign authority was added.
- 2026-07-23: closed RI-092 through RI-096 and RI-034's seventy-sixth through
  eightieth boundary slices. Shared record validators and the Task Pool record
  now agree with latest-schema loading; candidate and Task Pool metadata
  ingestion no longer stringify malformed evidence inputs. Selector
  construction collapses integer/float-equivalent continuous parameters to one
  identity, snapshots nested maps, and rejects noncanonical external executable
  records. Twelve new public cases pass; Selection and Task Pool have 166 and
  82 passing tests, and the full suite has 788 passed with 2 skipped. No schema
  registry, deep-freeze framework, metadata/config object, compatibility mode,
  network access, paid benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-091 and RI-034's seventy-fifth boundary slice. Runner
  no longer constructs an invalid empty-start TimeRange to mean “no lower
  Result-availability bound”; its pre-origin helper accepts an explicit nullable
  timestamp, while rolling evaluation still forwards the declared history
  start. One red query assertion and one bounded-query characterization pass.
  The full suite passes 763 tests with 2 skipped; the 38-file scan retains full
  signal health and 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
  0/19/0, 20 Ruff findings, and no dead-code candidate. No schema, time-range
  abstraction, dependency, network access, paid benchmark call, or campaign
  authority was added.
- 2026-07-23: closed RI-090 and RI-034's seventy-fourth boundary slice.
  `ScoringConfig` now turns integer/float-equivalent rates into one immutable
  canonical float mapping and rejects malformed pricing at construction.
  External dictionary mutation cannot change its digest, and Runner still
  rechecks the config before Agent execution. Six red public cases and 173
  affected Result Store/Runner/campaign tests with 1 skipped pass; the full
  suite passes 763 tests with 2 skipped. The 38-file scan retains full signal
  health and 112 hotspots (0 now / 36 soon / 76 monitor), critical counts
  0/19/0, 20 Ruff findings, and no dead-code candidate. The internal TimeRange
  sentinel remains P2 cleanup, and no Selection refactor was inferred from
  complexity alone. No schema, registry, dependency, network access, paid
  benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-089 and RI-034's seventy-third boundary slice. The two
  persisted `float` fields now reject integer representations before companion
  append, matching latest-schema canonical reload. Scoring-config and Task Pool
  source-window alternatives were traced to pre-execution validation and kept
  as lower-priority cleanup rather than misclassified evidence gaps. Two public
  counterexamples and the affected 412 Records/Selection/Runner/Reporting tests
  pass; the full suite passes 758 tests with 2 skipped. The 38-file scan retains
  full signal health and 112 hotspots (0 now / 36 soon / 76 monitor), critical
  counts 0/19/0, 20 Ruff findings, and no dead-code candidate. No schema,
  generic writer validation, dependency, network access, paid benchmark call,
  or campaign authority was added.
- 2026-07-23: closed RI-084 through RI-088 and RI-034's sixty-eighth through
  seventy-second boundary slices. Exact rolling-origin future-state and
  dependency-filter types now protect cohort behavior and policy identity.
  Malformed raw Check state normalizes to invalid, and ambiguous normalization
  configs fail at construction. Complete-plan preflight validates immutable
  Check and full Agent bindings once per unique identity while retaining the
  existing per-cell workspace/invocation checks. Twenty red cases and the full
  suite of 756 tests with 2 skipped pass. A transient preflight complexity
  regression was split into direct plan and Agent-binding helpers; the final
  38-file scan remains at 112 hotspots (0 now / 36 soon / 76 monitor), critical
  counts 0/19/0, 20 Ruff findings, and no dead-code candidate. No schema,
  registry, generic validation framework, dependency, network access, paid
  benchmark call, or campaign authority was added.
- 2026-07-23: closed RI-083 and RI-034's sixty-seventh boundary slice. Training,
  paired comparison, and Reporting accepted any internally consistent Metric
  protocol after construction became implementation-owned. Selection now
  preflights consumed batches against the current protocol; Reporting marks an
  unknown protocol unsupported, while Records stays version-neutral. The
  direct batch guard keeps `_validated_paired_metrics` at `monitor`. Two red
  specs, all 229 Selection/Reporting tests, and the full suite of 736 with 2
  skipped pass. The 38-file scan remains at 112 hotspots (0 now / 36 soon / 76
  monitor), critical counts 0/19/0, 20 Ruff findings, and no dead-code
  candidate. No protocol registry, schema, compatibility layer, dependency,
  telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-082 and RI-034's sixty-sixth boundary slice. Absolute,
  traversal, nested, and format-swapped report filenames could escape
  `output_dir` or select the wrong serialization. `ReportConfig` now accepts
  only direct `.md` and `.json` filenames. Six red specs and all 56 Runner
  tests pass. The 38-file scan stays at 112 hotspots (0 now / 36 soon / 76
  monitor), critical counts 0/19/0, 20 Ruff findings, and no dead-code
  candidate. No path wrapper, publication service, schema, compatibility
  layer, dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-081 and RI-034's sixty-fifth boundary slice. A boolean
  certification repeat count executed one check pair and then produced
  unreplayable evidence; floats, strings, nulls, and nonpositive integers also
  survived config construction. `CertificationConfig` now requires an exact
  positive integer, and the weaker runtime comparison is removed. Six red
  specs and all 63 Task Pool tests pass. The 38-file scan remains at 112
  hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, 20 Ruff
  findings, and no dead-code candidate. No config framework, schema,
  compatibility layer, dependency, telemetry, network access, or paid call was
  added.
- 2026-07-23: closed RI-080 and RI-034's sixty-fourth boundary slice.
  `WorkspaceArtifactConfig.path_mode` exposed a one-value placeholder, while
  truthy non-booleans could unexpectedly retain Agent output or a final diff.
  Relative refs are now invariant; the real retention and summary controls
  validate at config construction, and the one-use runtime validator is gone.
  Four red specs and all 71 Workspace tests pass. The 38-file scan remains at
  112 hotspots (0 now / 36 soon / 76 monitor) and critical counts 0/19/0;
  Ruff findings fall from 21 to 20, with no dead-code candidate. No artifact
  mode registry, schema, compatibility layer, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: closed RI-079 and RI-034's sixty-third boundary slice.
  `ResultCacheConfig.reuse_policy` exposed a one-value placeholder, while the
  real benchmark-invalid reuse flag accepted malformed truthy values. Exact
  full-identity reuse is now a fixed invariant; the config retains only one
  exact-boolean opt-in, and the replicate campaign still forbids it. Five red
  constructor specs, 91 Result Store/campaign tests, and the full suite of 719
  with 2 skipped pass. The 38-file full-signal scan is unchanged at 112
  hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
  dead-code candidate. No cache-policy registry, schema, compatibility layer,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-078 and RI-034's sixty-second boundary slice. The
  removed `MetricConfig` carried no behavior: arbitrary caller digests could
  relabel identical metrics, while its optional budget duplicated the frozen
  Selection budget. Selection now derives a versioned protocol digest from the
  implemented metric names and aggregation level; `MetricRecord` remains
  unchanged. Runner preflights the complete Selector batch, executable
  parameters, Agents, mode, and origin schedule before Task Pool reads or
  companion writes. The pure schedule validator removes one cognitive signal;
  `evaluate_selectors` retains only its explicit 15-dependency Lizard warning.
  All 50 Runner tests, the relevant 212 Selection/Runner/example tests, and the
  full suite of 714 with 2 skipped pass. The 38-file full-signal scan reports
  112 hotspots (0 now / 36 soon / 76 monitor), critical counts 0/19/0, and no
  dead-code candidate. No metric registry, context object, schema, dependency,
  telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-077 and RI-034's sixty-first boundary slice. Public
  counterexamples showed ClaimConfig switches weakening fixed claim gates,
  malformed or permuted claim collections changing config identity, and
  `agent_result_identity` remaining supported without Agent evidence or with a
  drifted Agent. ClaimConfig now retains only canonical requested claims;
  Matrix completeness and Metric validity are mandatory. The identity
  predicate requires every Result Agent to exist and match its frozen cache
  projection, and the report binds Agent manifest digests. The Claim Boundary
  evaluates only requested predicates, reuses existing source/artifact
  projections, and delegates stable claim and record-evidence phases. The
  public builder falls from 288 NLOC / Lizard CCN 73 / cognitive complexity 21
  to 133 / 14 / 5; both it and the 43 / 8 / 1 Selector-metric decision are
  `monitor`. All 73 Reporting tests and the full suite of 714 with 2 skipped
  pass. The 38-file full-signal scan reports 113 hotspots (0 now / 37 soon / 76
  monitor), critical counts 0/20/0, and no dead-code candidate. No claim
  registry, context object, schema, dependency, telemetry, network access, or
  paid call was added.
- 2026-07-23: closed RI-076 and RI-034's sixtieth boundary slice. A red public
  scoring case showed a self-digested strict-prospective Selection producing
  ordinary MAE against a counterfactual Origin, CellSet, and matrices. Matrix
  alignment now checks that relation before Metric construction. Its ordered 18
  failure reasons, including three previously uncharacterized prospective
  branches, are covered in precedence order. The implementation delegates
  provenance, mode-specific denominator, and cell-identity phases; the public
  helper falls from 70 NLOC / Lizard CCN 24 / cognitive complexity 28 / Ruff 19
  to 32 / 5 / 4 / below threshold, and both phase helpers remain below hotspot
  thresholds. All 154 Selection tests and the full suite of 709 with 2 skipped
  pass. The 38-file full-signal scan falls to 111 hotspots (1 now / 37 soon / 73
  monitor); Ruff, Lizard, and Complexipy each lose one finding, critical counts
  remain 0/21/0, and no dead-code candidate appears. No matrix context object,
  policy registry, schema, dependency, telemetry, network access, or paid call
  was added.
- 2026-07-23: closed RI-075 and RI-034's fifty-ninth boundary slice. A public
  non-object certification-evidence item was first reported correctly, then
  raised `AttributeError` in SourceEvent linkage. The linker now indexes only
  mapping-shaped evidence. The certification reconciler keeps one visible
  entrypoint and separates record parsing/semantics, collection/config checks,
  accepted Task/Check coverage, and rejected/summary coverage. It falls from 79
  NLOC / Lizard CCN 24 / cognitive complexity 34 / Ruff 17 to 13 / 1 / 0 /
  below threshold; its four direct phase helpers remain below hotspot
  thresholds. All 57 Task Pool tests and the full suite of 708 with 2 skipped
  pass. The 38-file full-signal scan falls to 112 hotspots (2 now / 37 soon / 73
  monitor); Ruff and Complexipy each lose one finding, Task Pool leaves the
  investigation queue, critical counts remain 0/21/0, and no dead-code
  candidate appears. No evidence bundle, generic validator, schema, dependency,
  telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-074 and RI-034's fifty-eighth boundary slice. Three
  public-boundary cases showed that integer `accepted=1` passed evidence
  serialization, SourceEvent finalization, and an otherwise valid Task Pool
  freeze. One direct guard now
  requires an exact boolean wherever CertificationResults become persisted
  evidence. The finalizer separates exact candidate coverage, per-candidate
  SourceEvent projection, and ordered local validation while leaving
  cross-artifact reconciliation at freeze. It falls from 66 NLOC / Lizard CCN
  20 / cognitive complexity 20 to 17 / 2 / 0 and leaves the hotspot list. All 56
  Task Pool tests and the full suite of 707 with 2 skipped pass. The 38-file
  full-signal scan falls to 113 hotspots (3 now / 37 soon / 73 monitor); Lizard
  and Complexipy each lose one finding, critical counts remain 0/21/0, and no
  dead-code candidate appears. No schema, generic validation framework,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-073 and RI-034's fifty-seventh boundary slice. Seven
  self-digested Metric counterexamples showed truthy non-string Agent IDs,
  Agent pairs, aggregation levels, optional refs, and abstention reasons being
  accepted, while empty unused dimensions stood in for null. Records now owns
  direct scope-dimension, optional-reference, and completeness checks. The
  public validator falls from 47 NLOC / Lizard CCN 20 / cognitive complexity 20
  / Ruff 12 to 22 / 3 / 2 / below threshold; its dimension helper is monitor-
  only. All 338 Records/Selection/Reporting tests and the full suite of 704 with
  2 skipped pass. The 38-file full-signal scan remains at 114 hotspots but
  shifts to 3 now / 38 soon / 73 monitor; Ruff and Complexipy each lose one
  finding, critical counts remain 0/21/0, and no dead-code candidate appears.
  No generic validation framework, schema, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: closed RI-071, RI-072, and RI-034's fifty-fifth and fifty-sixth
  boundary slices. SourceEvent validation previously accepted string and mapping
  rejection-reason containers and raised on an integer. ResultCell validation
  accepted empty exclusion data on result cells and truthy non-string Result or
  exclusion fields. Direct public cases reproduce both write/read contract
  gaps. Records now separates SourceEvent binding/reason/maturity checks and
  ResultCell result/excluded/missing payload checks. Their public helpers fall
  from 39 NLOC / CCN 20 / cognitive 25 / Ruff 12 to 9 / 1 / 0 / below threshold,
  and from 30 / 21 / 28 / 13 to 8 / 4 / 3 / below threshold. All 110 Records
  tests, 488 cross-module tests, and the full suite of 697 with 2 skipped pass.
  The 38-file full-signal scan falls to 114 hotspots (3 now / 39 soon / 72
  monitor); Ruff loses two findings, Lizard and Complexipy each lose one,
  critical counts remain 0/21/0, and no dead-code candidate appears. No generic
  type-validation framework, schema, dependency, telemetry, network access, or
  paid call was added.
- 2026-07-23: closed RI-070 at the first-call resource-ledger boundary. A
  public empty snapshot with USD 5 authority and USD 100 remaining previously
  loaded successfully; so did a snapshot claiming prior spend without a call
  event. The shared loader now validates the stored timestamp and amounts, then
  requires zero spend and `remaining_usd == budget_usd` only when calls and
  events are both empty. Event-backed overrun evidence still rebuilds normally.
  All 20 ledger tests, 72 ledger/consumer tests with 1 skipped, and the full
  suite of 694 with 2 skipped pass. The 38-file full-signal scan remains at 115
  hotspots (3 now / 41 soon / 71 monitor), critical counts remain 0/21/0, and
  no dead-code candidate appears. No schema, ledger class, experiment framework,
  dependency, telemetry, network access, ledger authority, or paid call was
  added.
- 2026-07-23: closed RI-069 and RI-034's fifty-fourth boundary slice. Nine red
  cases showed negative costs increasing remaining authority, string and
  boolean costs disappearing from spend, and nonfinite budgets or costs
  reaching serialization and leaving a temporary file. Shared snapshot replay
  now validates a nonempty timestamp plus finite nonnegative budget and known
  costs before writing; result-less stopped completions still retain unknown
  cost. Event folding, budget parsing, and cost summation are direct helpers.
  The public function falls from 57 NLOC / Lizard CCN 21 / cognitive complexity
  27 / Ruff 12 to 19 / 3 / 2 / below threshold. The ledger and three consumers
  pass 68 tests with 1 skipped; the full suite passes 690 with 2 skipped. The
  38-file full-signal scan remains at 115 hotspots but shifts to 3 now / 41 soon
  / 71 monitor; Ruff and Lizard each lose one finding, critical counts remain
  0/21/0, and no dead-code candidate appears. No ledger class, experiment
  framework, schema, dependency, telemetry, network access, or paid call was
  added.
- 2026-07-23: closed RI-068 and RI-034's fifty-third boundary slice. Seven
  cases show malformed timeout, capture, and termination-grace values failing
  before process start. Bounded execution now separates request validation,
  stream setup, wait, containment/drain, and exceptional cleanup while keeping
  POSIX process groups, TERM-to-KILL escalation, full-stream digests, bounded
  excerpts, and pipe-failure behavior unchanged. The public function falls from
  73 NLOC / Lizard CCN 20 / cognitive complexity 29 / Ruff 15 to 46 / 3 / 1 /
  below threshold. All 18 focused tests and the full suite of 680 passing with
  2 skipped succeed. The 38-file full-signal scan falls to 115 hotspots (3 now
  / 42 soon / 70 monitor); Ruff, Lizard, and Complexipy each lose one finding,
  critical counts remain 0/21/0, and no dead-code candidate appears. No wrapper
  class, state object, dependency, telemetry, network access, or paid call was
  added.
- 2026-07-23: closed RI-067 and RI-034's fifty-second boundary slice. A
  two-record certification characterization showed that accepted and rejected
  candidates could carry different Workspace or Runtime digests even though
  Runner uses one config for the whole Task Pool. One linear helper now
  requires one value for each shared field while preserving candidate-specific
  patch and Check bindings. The full suite passes 673 tests with 2 skipped. The
  38-file full-signal scan remains at 116 hotspots (3 now / 43 soon / 70
  monitor), with unchanged tool and critical counts and no dead-code candidate.
  No pool-level config copy, registry, context object, schema, framework,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-065, RI-066, and RI-034's fifty-first boundary
  slice. A fully redigested Task Pool with two distinct rejected SourceEvents
  sharing one candidate ID previously passed public artifact validation and
  inflated the source frame. Candidate-linked events now require unique IDs.
  Persisted certification evidence must also retain the producer's canonical
  candidate-ID order, and the rejected-ID tuple must match it exactly. The
  shared Runner fixture now emits production-order evidence. The full suite
  passes 673 tests with 2 skipped. The 38-file full-signal scan remains at 116
  hotspots (3 now / 43 soon / 70 monitor), with unchanged tool and critical
  counts and no dead-code candidate. No registry, index, schema, framework,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: completed RI-034's fiftieth boundary slice. Three public cases
  preserve the rule that missing candidate reference patches, Check commands,
  and hidden-material paths fail before Workspace binding. `build_task_pool`
  now exposes only resolve/preflight, bind/certify, and freeze/publish phases;
  commit resolution, errors, and side effects retain their original order. The
  public function falls from 139 NLOC / Lizard CCN 24 / cognitive complexity
  24 to 7 / 2 / 1, and all three helpers stay below high-priority thresholds.
  The full suite passes 672 tests with 2 skipped. The 38-file full-signal scan
  falls to 116 hotspots (3 now / 43 soon / 70 monitor); Lizard and Complexipy
  each lose one finding, critical counts remain 0/21/0, and no dead-code
  candidate appears. No context object, pipeline framework, schema, dependency,
  telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-064 and RI-034's forty-ninth boundary slice. Six public
  cases reproduce duplicate Result/Agent summaries, duplicate frozen
  Selections, duplicate Matrix cache evidence, duplicate Agent/Result identity
  evidence, and duplicate Selection/CellSet/Matrix/Metric Selector evidence.
  Reporting now runs one linear identity check over exactly the record types
  each claim consumes. The full suite passes 669 tests with 2 skipped. The
  38-file full-signal scan remains at 117 hotspots (3 now / 44 soon / 70
  monitor), with unchanged tool and critical counts and no dead-code candidate.
  No registry, validation framework, schema, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: closed RI-063 and RI-034's forty-eighth boundary slice. Two red
  Selection-log cases showed that an identical or conflicting second semantic
  ID was hidden by the append helper's first-match return. Runner now scans the
  complete companion log for duplicate IDs before applying the unchanged
  same-digest or first-observation-time resume rule. The pass stays O(N) beside
  the required parse and also rejects unrelated duplicate corruption before a
  new append. The full suite passes 663 tests with 2 skipped. The 38-file scan
  remains at 117 hotspots (3 now / 44 soon / 70 monitor); the append helper
  remains one cognitive-complexity `monitor` finding at 18, critical counts
  remain 0/21/0, and no dead-code candidate appears. No persistent index,
  automatic repair, lock redesign, schema, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: completed RI-034's forty-seventh boundary slice. Existing
  integration specifications preserve shared-cell union execution, cached
  sequential equivalence, partial-failure recovery, reusable-Result preflight,
  missing CellSet resume, and strict-prospective use. A new case fixes duplicate
  plan rejection before any CellSet-log read. Runner now separates plan
  indexing, pending-union derivation, ResultCell indexing, and one-CellSet
  construction while retaining the locked-session orchestration and its nine
  real dependencies. The resolver drops from 153 to 113 NLOC and CCN 21 to 11;
  its cognitive-25 and Ruff-14 signals disappear, leaving one Lizard signal.
  All four helpers remain below thresholds. The full suite passes 661 tests
  with 2 skipped. The 38-file scan remains at 117 hotspots (3 now / 44 soon /
  70 monitor), while Ruff and Complexipy each lose one warning; critical counts
  remain 0/21/0 and no dead-code candidate appears. No context object,
  execution fork, framework, schema, dependency, telemetry, network access, or
  paid call was added.
- 2026-07-23: completed RI-034's forty-sixth boundary slice. A direct
  prospective-report characterization fixes duplicate future-pool evidence,
  mature/censored ref drift, replay failure, missing-pool errors, and their
  order. It also proves lazy loading, skips unused pools, and loads one shared
  future bundle once. Reporting now separates pool indexing and one-cohort
  comparison while retaining visible load orchestration. The original helper
  moves from `refactor_soon` to `monitor` (83 to 64 NLOC, CCN 19 to 14,
  cognitive 24 to 16); both new helpers are below thresholds. The full suite
  passes 660 tests with 2 skipped. The 38-file full-signal scan remains at 117
  hotspots but shifts to 3 now / 44 soon / 70 monitor; Ruff and Lizard each
  lose one warning, critical counts remain 0/21/0, and no dead-code candidate
  appears. No context object, cache service, framework, schema, dependency,
  telemetry, network access, or paid call was added.
- 2026-07-23: completed RI-034's forty-fifth boundary slice. Exact source-window
  error-set/order characterization now covers absent, partial, invalid,
  noncanonical, reversed, late, inside, and outside cases. Task Pool separates
  window boundary parsing from per-event disposition/reason reconciliation.
  The 47-line CCN-21/cognitive-23/Ruff-13 helper leaves the hotspot list; both
  replacements are below thresholds. The full suite passes 659 tests with 2
  skipped, and the full-signal scan falls to 117 hotspots (3 now / 45 soon / 69
  monitor), with critical counts 0/21/0 and no dead-code candidate. No state
  object, framework, schema, dependency, telemetry, network access, or paid
  call was added.
- 2026-07-23: closed RI-062 and RI-034's forty-fourth boundary slice. Four
  public cases showed that existing JSONL with an identical or conflicting
  duplicate `result_id` was retained by raw reads, first-wins session indexes,
  and last-wins CellSet maps. The shared loader now rejects the second line
  before filtering or indexing. The added hash pass remains O(N) beside parsing.
  The full suite passes 658 tests with 2 skipped; the full-signal scan remains
  at 118 hotspots (3 now / 46 soon / 69 monitor), with critical counts 0/21/0,
  no regression, and no dead-code candidate. No schema, migration, persistent
  index, service, dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-061 and RI-034's forty-third boundary slice. Six public
  cases showed that malformed authority values could publish an unusable,
  non-overwritable campaign ledger; a scalar `pricing_sources` string was even
  persisted as characters. Timestamp, string, and source-sequence shapes now
  fail before snapshot or event-file creation. An initial inline implementation
  moved the validator from `monitor` to `refactor_soon`; three direct helpers
  reduce it from CCN 20 to 6 and restore the full-signal scan to 118 hotspots
  (3 now / 46 soon / 69 monitor), with critical counts 0/21/0 and no dead-code
  candidate. The full suite passes 654 tests with 2 skipped. No campaign
  authority, evidence write, telemetry, network access, or paid call occurred.
- 2026-07-23: closed RI-060 and RI-034's forty-second boundary slice. Two direct
  Result Store specifications showed that a Matrix could retain default-policy
  cells while declaring agent-exclusion digests, or rename a policy-derived
  abstention reason. Result Store now replays all four currently executable
  missing-cell/agent-invalid combinations and requires one exact match across
  policy digests, cells, abstention, and scoreability. Valid training and
  Reporting fixtures use derived policy identities. The full suite passes 648
  tests with 2 skipped; the full-signal 38-file Cremona scan remains at 118
  hotspots (3 now / 46 soon / 69 monitor), with critical counts 0/21/0, no
  regression, and no dead-code candidate. No policy registry, persisted config
  record, schema, framework, dependency, telemetry, network access, or paid
  call was added.
- 2026-07-23: closed RI-059 and RI-034's forty-first boundary slice. A direct
  Result Store specification showed that the first RI-058 check accepted one
  agent-invalid cell under `exclude` and another under `count_as_failure`, even
  though no single `ResultJoinConfig` could produce that scoreable Matrix.
  Result Store now reconstructs the complete ordered cells under each supported
  configuration and requires one whole-Matrix match. Selection and Reporting
  inherit the check. The full suite passes 646 tests with 2 skipped; the
  full-signal 38-file Cremona scan remains at 118 hotspots (3 now / 46 soon /
  69 monitor), with critical counts 0/21/0, no regression, and no dead-code
  candidate. No policy registry, persisted config record, schema, framework,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-058 and RI-034's fortieth boundary slice. Public
  training and Reporting specifications showed that a normal passing Result
  could be relabeled as a common exclusion, removed from the denominator, and
  still support fitting or `agent_result_identity`. Result Store now resolves
  Matrix bindings and separately reconstructs benchmark-invalid task-wide
  exclusions plus the two existing agent-invalid branches. Selection and
  Reporting reuse that contract. The full suite passes 645 tests with 2
  skipped; Ruff, Pyright, targeted formatting, and `git diff --check` pass. An
  intermediate scan rose to 120 hotspots; separating binding resolution,
  derived-state checking, and caller orchestration returns the full-signal
  38-file scan to 118 (3 now / 46 soon / 69 monitor), with critical counts
  0/21/0, no regression, and no dead-code candidate. No join-policy registry,
  record, schema, framework, dependency, telemetry, network access, or paid
  call was added.
- 2026-07-23: closed RI-057 and RI-034's thirty-ninth boundary slice. A public
  `complete_with_exclusions` training specification showed that Runner supplied
  bound excluded Results which Selection rejected as extra, while direct
  Selection could omit them. Training now validates every present Result
  binding independent of cell state and skips only cells with neither ID nor
  digest. The full suite passes 643 tests with 2 skipped; Ruff, Pyright,
  targeted formatting, and `git diff --check` pass. The full-signal 38-file
  Cremona scan remains at 118 hotspots (3 now / 46 soon / 69 monitor), with
  critical counts 0/21/0, no regression, and no dead-code candidate. No
  exclusion policy, record, schema, framework, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: closed RI-056 and RI-034's thirty-eighth boundary slice. A public
  two-Selector resume specification drifted an existing CellSet outcome and
  added one pending Selector cell; the old resolver invoked the pending Agent
  before later scoring rejected the old binding. Runner now batch-loads and
  validates all Results bound by reusable CellSets before constructing or
  executing the pending union. The full suite passes 642 tests with 2 skipped;
  Ruff, Pyright, targeted formatting, and `git diff --check` pass. The
  full-signal 38-file Cremona scan falls from 119 to 118 hotspots (3 now / 46
  soon / 69 monitor), with critical counts 0/21/0, no regression, and no
  dead-code candidate. The batched loader and pure validator are below hotspot
  thresholds. No execution context, persistent index, record, schema,
  dependency, telemetry, network access, or paid call was added.
- 2026-07-23: closed RI-055 and RI-034's thirty-seventh boundary slice. Two
  public red specifications changed a bound passing ResultCell outcome to fail
  while retaining the original Result. Reporting still supported
  `agent_result_identity`, and first-time Runner scoring downgraded the
  contradiction to a missing cell. Records now owns the seven-field
  ResultCell-to-Result mismatch predicate used by Result Store, Runner,
  Selection training, and Reporting. The full suite passes 641 tests with 2
  skipped; Ruff, Pyright, targeted formatting, and `git diff --check` pass. The
  full-signal 38-file Cremona scan remains at 119 hotspots (3 now / 46 soon /
  70 monitor), with critical counts 0/21/0, no regression, and no dead-code
  candidate; the new predicate is below hotspot thresholds. No record, schema,
  framework, dependency, telemetry, network access, or paid call was added.
- 2026-07-23: completed RI-034's thirty-sixth boundary slice. Runner
  `train_selector` now separates ordered training-record resolution,
  Selection-scoped outcome loading, and exact frozen Result binding without
  changing its public API, read order, or Selection call. Its measured
  CCN/NLOC falls from 24/125 to 4/47 and its classification moves from
  `refactor_soon` to `monitor`; all three new helpers are below hotspot
  thresholds. The full suite passes 639 tests with 2 skipped. The full-signal
  38-file Cremona scan remains at 119 hotspots, redistributed from 3/47/69 to
  3/46/70, with critical counts 0/21/0 and no dead-code candidate. The public
  seven-argument contract remains explicit instead of adding `**kwargs` or a
  one-use context object. No behavior, schema, dependency, telemetry, network
  access, or paid call was added.
- 2026-07-23: closed RI-054 and RI-034's thirty-fifth boundary slice. A red
  public training specification changed every outcome Result base commit,
  redigested Results, matrices, and metrics, and proved the old trainer still
  fitted. Selection's training API now receives the existing common Task Pool,
  ordered Tasks, and Checks. Runner supplies a validated bundle; Selection
  replays all training/deployment Origins, Snapshot Task metadata, and every
  pre-origin/outcome Result Task/Check cache projection. The full suite passes
  639 tests with 2 skipped; Ruff, Pyright, targeted formatting, and
  `git diff --check` pass. The full-signal 38-file Cremona scan remains at 119
  hotspots (3 now / 47 soon / 69 monitor), with critical counts 0/21/0, no
  regression, and no dead-code candidate. No record, schema, TrainingDataset,
  context object, dependency, network access, or paid call was added.
- 2026-07-23: closed RI-053 and RI-034's thirty-fourth boundary slice. Two red
  public training specifications fully rebound Input/Selection/Matrix/Metric
  evidence: one varied the same Agent ID across Origins, and one consistently
  changed every frozen Agent digest while retaining Results from the original
  Agent. The old trainer accepted both. Training now compares ordered full
  Agent bindings across Origins and projects every training Result cache
  identity back to the frozen AgentRecord digest. The full suite passes 638
  tests with 2 skipped; Ruff, Pyright, targeted formatting, and
  `git diff --check` pass. The full-signal 38-file Cremona scan remains at 119
  hotspots (3 now / 47 soon / 69 monitor), with critical counts 0/21/0, no
  regression, and no dead-code candidate. No schema, training framework,
  telemetry, dependency, network access, or paid call was added.
- 2026-07-23: closed RI-052 and RI-034's thirty-third boundary slice.
  FeatureConfig previously admitted empty, duplicate, unknown, and permuted
  names plus an independently supplied leakage-class list. Red specifications
  proved these states could alter config and snapshot identity without changing
  executable extraction. FeatureConfig now validates and canonicalizes the
  three supported names and derives leakage classes from them; all production,
  example, and test callers use the one-axis API. Persisted records require no
  migration. The full suite passes 636 tests with 2 skipped; Ruff, Pyright,
  targeted formatting, and `git diff --check` pass. The full-signal 38-file
  Cremona scan remains at 119 hotspots (3 now / 47 soon / 69 monitor), with
  critical counts 0/21/0, no regression, and no dead-code candidate. No schema,
  compatibility shim, feature registry, dependency, network access, or paid
  call was added.
- 2026-07-23: closed RI-051 and RI-034's thirty-second boundary slice. A red
  strict Runner specification changed one `task_stratum`, redigested the full
  FeatureSnapshot/Input/Selection chain, changed the selected Task/Check set,
  and proved the old path reached the future-pool read. Selection now owns one
  direct Task metadata provenance assertion for Origin/config binding, exact
  `task_count`, and complete `task_stratum` value/time/source replay. Snapshot
  construction, strict Runner, and Reporting reuse it; unknown Task metadata
  fails closed. Runner now rejects the counterexample after exactly one
  selection-pool read and before future supply or Agent execution. The full
  suite passes 632 tests with 2 skipped; Ruff, Pyright, targeted formatting,
  and `git diff --check` pass. The full-signal 38-file Cremona scan remains at
  119 hotspots (3 now / 47 soon / 69 monitor), with critical counts 0/21/0,
  no regression, and no dead-code candidate. No schema, training framework,
  telemetry, dependency, network access, or paid call was added.
- 2026-07-23: closed RI-050 and RI-034's thirty-first boundary slice. A fully
  redigested pre-origin Result/Snapshot/Input/Selection chain could change
  Result cache-identity Agent or Task/Check fields and reach supply reads or
  execution before Reporting rejected it. A red parameterized Runner
  specification proves Agent drift now fails before any pool read and base-
  commit drift fails after exactly the selection-time pool read, before the
  future pool or Agent. Records now owns the Agent projection and Task/Check
  mismatch contract used by Result Store, Selection, Runner, and Reporting.
  The full suite passes 629 tests with 2 skipped; Ruff, Pyright, and
  `git diff --check` pass. The full-signal 38-file Cremona scan drops from 122
  to 119 hotspots (3 now / 47 soon / 69 monitor), removes three duplicated
  identity-check monitor hotspots, keeps critical counts at 0/21/0, has no
  regression, and reports no dead-code candidate. No schema, telemetry,
  dependency, network access, or paid call was added.
- 2026-07-23: closed RI-049 and RI-034's thirtieth boundary slice. Strict
  prospective execution replayed the intrinsic Selector chain but did not
  resolve the pre-origin Results frozen by SelectorInput before supply reads.
  A red public Runner specification removed one referenced Result and proved
  the old path opened Task Pool artifacts. Selection now owns
  `ensure_selector_input_result_evidence`: it resolves frozen ID/digest bindings
  in Input order and replays Origin Agent/history/cutoff scope plus aggregate
  and per-Result Feature provenance. Input construction, training, and strict
  Runner preflight share it; Reporting retains multi-error claim diagnostics.
  The full suite passes 627 tests with 2 skipped; Ruff, Pyright, and
  `git diff --check` pass. The full-signal 38-file Cremona scan drops from 123
  to 122 hotspots (3 now / 47 soon / 72 monitor), keeps critical counts at
  0/21/0, has no regression, and reports no dead-code candidate. No telemetry,
  schema, dependency, network access, or paid call was added.
- 2026-07-23: closed RI-048 and RI-034's twenty-ninth boundary slice. A
  self-digested strict Selection could replace its chosen ref with another
  eligible history ref and reach Task Pool reads because prospective execution
  did not reload Selector/FeatureSnapshot evidence or replay inference.
  `ensure_selection_replay` now owns the semantic field comparison in Selection;
  prospective Runner invokes it before supply reads, and Reporting, training,
  and stratified diagnostics reuse it instead of maintaining separate lists.
  The prospective entry point falls from 126 NLOC / CCN 14 to 83 / 1 while its
  direct API remains unchanged. The full suite passes 625 tests with 2 skipped;
  Ruff, Pyright, and `git diff --check` pass. The full-signal 38-file Cremona
  scan remains at 123 hotspots (3 now / 47 soon / 73 monitor), critical counts
  0/21/0, no regression, and no dead-code candidate. No record, dependency,
  network access, paid call, or benchmark Agent run was added.
- 2026-07-23: completed RI-045 and closed RI-046 and RI-047. A later Task Pool
  could not prove that its source collection covered a strict Origin's planned
  future window, so Task Pools now bind canonical source-window bounds while
  generator identity remains behavior-only. The existing EvaluationCellSet is
  the sole post-selection link to that later pool and its mature/censored
  cohort. `evaluate_prospective_selection` reloads the frozen chain, validates
  both immutable bundles, and reuses the one Result resolver, matrix builder,
  and scorer; Reporting and the offline CLI replay both pools before supporting
  a strict claim. A second counterexample replaced an Agent configuration under
  the same ID between phases; ordered full Agent-record digests now enter
  SelectorInput identity and fail before pool reads or execution. The full suite
  passes 624 tests with 2 skipped; Ruff, Pyright, and `git diff --check` pass.
  The full-signal 38-file Cremona scan reports 123 hotspots (3 now / 47 soon /
  73 monitor), critical counts 0/21/0, no baseline regression, and no dead-code
  candidate. No source-frame service, new module, network access, paid call, or
  benchmark Agent run was added.
- 2026-07-23: closed RI-045's reachable execution gap while retaining its
  future-supply work. A public `evaluate_selectors` counterexample showed that
  `strict_prospective` could persist a selection chain and reach Agent execution
  even though its frozen Origin necessarily had no future denominator. The
  evaluator now requires counterfactual replay with a predeclared future
  holdout and rejects unsupported policies before Task Pool reads, record
  writes, Result access, or Agent calls. Strict-prospective Selection remains;
  performance evaluation reopens only when a later Task Pool or source frame is
  linked without changing the original Origin. A second red specification
  showed that the documented stable-ID helper and the Selector builder used
  different formulas. The builder now calls one record-semantic helper that
  excludes observation time, self-ID, and self-digest. The remaining direct
  paid routes were re-audited and are already covered by Workspace or
  experiment preflight; no additional guard was added. The full suite passes
  619 tests with 2 skipped; Ruff, Pyright, and `git diff --check` pass. The
  full-signal 38-file Cremona scan is unchanged at 116 hotspots (2 now / 43
  soon / 71 monitor), critical counts 0/20/0, and no dead-code candidate. No
  schema, service, network access, paid call, or benchmark Agent run was added.
- 2026-07-23: closed RI-044. A campaign with USD 0.0005 remaining could
  previously start another paid cell because the guard checked only
  `remaining_usd > 0`; the Result could reveal the budget overrun only after the
  provider call. Ledger v2 now binds a positive maximum estimated cost per call
  no larger than the total budget, requires that amount before reservation, and
  rejects a returned Result above the per-call or cumulative limit. Three
  failing public-path specs cover invalid authority, a funded first call
  followed by an unfunded second call, and a Result above its per-call limit.
  The Result remains durable and the stopped cell cannot retry. This guard does
  not claim provider-side billing control; the Agent runtime budget must make
  the declared per-call maximum credible. The redundant caller-supplied call
  cap was removed; ledger v2 derives it from the frozen schedule. The 26 focused
  campaign tests and the full 617-test suite pass with 2 skipped; Ruff, Pyright,
  and `git diff --check` pass. The full-signal 38-file Cremona scan reports 116
  hotspots (2 now / 43 soon / 71 monitor), two fewer monitor findings than the
  preceding scan, with no dead-code candidate. No campaign ledger, network
  access, paid call, or core Record change was made.
- 2026-07-23: closed RI-043 and RI-034's twenty-fifth boundary slice. A scalar
  `rejection_reasons` value was correctly rejected by certification-record
  validation but then raised `TypeError` during SourceEvent reconciliation;
  that boundary now treats only non-string sequences as linkable reasons.
  Accepted certification evidence also now rejects `pass` with a timeout or
  failure label and rejects non-passing outcomes without a non-empty failure
  label. Four red characterizations establish the former exception and the
  three contradictory states. The current 38-file Cremona scan remains at 118
  hotspots but moves one item from soon to monitor (2 now / 43 soon / 73
  monitor), with full signal health, critical counts 0/20/0, and no dead-code
  candidate. The stable-ID, Reporting-claim,
  and paid-preflight alternatives were audited first: public selection replay
  and the three paid endpoint/harness checks already close their reachable
  paths, while `benchmark_selection_frozen` does not claim prospective timing.
  Task Pool branch coverage rises from 0.74 to 0.75. The full suite passes 614
  tests with 2 skipped; Ruff, Pyright, and `git diff --check` pass. No schema,
  dependency, network access, paid call, or benchmark Agent run was added.
- 2026-07-22: closed RI-042 and RI-034's twenty-fourth boundary slice. A
  self-consistent SelectorInput with a changed selection limit and stale budget
  digest was previously valid; Records now binds the two and also owns Agent/ref
  uniqueness, pre-origin Result alignment, and canonical cutoff validation.
  Selection removed its duplicate uniqueness checks. Reporting now accepts the
  same supplied Agent-record set in any order while retaining exact frozen
  SelectorInput/ResultMatrix order. `validate_selector_input` left the hotspot
  list; the full 38-file scan now has full signal health, 118 hotspots (2 now /
  44 soon / 72 monitor), critical counts 0/20/0, and no dead-code candidate.
  The retained Task Pool reconciler gained specs for malformed, non-boolean,
  duplicate, and config-mismatched evidence. The offline coverage run passed
  610 tests with 2 skipped; Evaluation, Reporting, Records, and Task Pool have
  routing branch fractions 0.74, 0.81, 0.79, and 0.74. Ruff, Pyright, scoped
  formatting, and `git diff --check` pass. No dependency, Record field, paid
  call, or network access was added.
- 2026-07-22: closed ALG-004's deployment-time leakage gap. The public EWMA
  chooser now requires an explicit deployment Origin and accepts training rows
  only from validated, unique, same-pool Origins whose time, cutoff, and label-
  maturity boundary precede deployment under one comparable policy. Empty
  history still returns the validated fallback. Characterization covers an
  equal-time Origin and the no-history path; the targeted Evaluation scan stays
  at 14 hotspots (0 now / 3 soon / 11 monitor).
- 2026-07-22: supplied RI-034's previously missing coverage signal without
  adding a project dependency or committed artifact. An offline cached
  coverage.py run passed 603 tests with 2 skipped and measured the explicit
  38-file scope; non-package files absent from discovery received conservative
  0% line entries, while two empty `__init__.py` files retained conventional
  100% coverage. The final Cremona scan reports full signal health, 119 hotspots
  (2 now / 45 soon / 72 monitor), critical counts 0/20/0, and no dead-code
  candidate. `selection/evaluation.py`, Reporting, and Task Pool have 0.74,
  0.81, and 0.71 branch fractions in routing. A new Selection characterization
  covers all fourteen matrix-alignment failure reasons and first-error
  precedence; Evaluation combined coverage rose from 80% to 82% without code
  changes. The ordered alignment list remains centralized. Temporary coverage
  and audit files stay outside the repository; no baseline was created.
- 2026-07-22: audited ALG-005's minimum infrastructure boundary and deferred
  prediction code. Current Results, selected matrices, Origins, availability
  times, and pricing views can replay resource evidence; the unresolved choice
  is whether the hard constraint targets per-Cell p90, whole-Selection total, or
  bounded-concurrency wall time. Those estimands require different validation
  and abstention behavior. The protocol now records the reopening inputs and
  forbids a generic ResourceMetric, trainer, or scalarized objective before an
  authorized outer run demonstrates a material resource problem. No code,
  schema, network access, or paid call was added for ALG-005.
- 2026-07-22: completed RI-034's Selector-choice input slice. Registered
  Selector/fallback validation and per-Origin MAE row coverage/value
  normalization are now separate, direct helpers; existing characterization
  tests preserve empty history, invalid Selector families and configs,
  duplicate IDs, unknown fallback, incomplete rows, and invalid MAE behavior.
  Evaluation hotspots fell from 15 to 14 and `refactor_soon` from 4 to 3, with
  0 `refactor_now`, 11 `monitor`, and critical counts 0/2/0. The full 38-file
  scan fell from 120 to 119 hotspots and from 46 to 45 `refactor_soon`; the
  current totals are 2 retained `refactor_now`, 45 `refactor_soon`, 72
  `monitor`, critical counts 0/20/0, and no dead-code candidate. All 137
  Selection tests and the full 602-passed/2-skipped suite pass; Ruff, Pyright,
  scoped formatting, and `git diff --check` pass.
- 2026-07-22: implemented ALG-004's offline EWMA-guarded choice without a new
  model, trainer, schema, or confidence rule. `EWMASwitchConfig` declares a
  positive Origin half-life and embeds the existing safe-switch config.
  `choose_selector_with_ewma_guard` reuses complete paired evidence, requires
  the exact validated training Origin set and an explicit deployment Origin,
  checks Task Pool, policy, cutoff, and label-maturity chronology, orders history
  by unique `as_of_cutoff`, ranks by normalized EWMA loss, and admits only that
  ranked candidate through the ordinary unweighted full-history safe-switch.
  Tests cover a real recent-trend reversal, refusal when full-history improvement
  is absent, caller-order independence, missing Origin evidence, and invalid
  half-lives. At the initial gate, all 137 Selection tests passed and the full
  suite had 602 passing and 2 skipped; Ruff and Pyright passed. The targeted
  Evaluation scan had 15 hotspots
  (0 now / 4 soon / 11 monitor); the one new public evidence orchestrator is
  monitor-only. The final 38-file scan has 120 hotspots, 2 retained
  `refactor_now`, 46 `refactor_soon`, and 72 `monitor`, with critical counts
  0/20/0, no dead-code candidate, and missing coverage input. Scoped formatting
  and `git diff --check` pass. No Runner default, dependency, network access,
  paid call, or empirical advantage was added.
- 2026-07-22: closed ALG-002's report-integration gap without adding Metric or
  Record fields. `build_selector_report` now loads the validated frozen Task
  bundle, resolves each stratified Selector/Input/Snapshot/Selection/Origin,
  replays the selection, and publishes forecast/future proportions, quotas,
  three TV diagnostics, ESS, and cap behavior. The selector section binds the
  TaskRecords digest; any derivation failure withholds the performance claim.
  A real Runner-to-Reporting test covers the complete path. All 92 Reporting
  and Runner tests pass. The final targeted Reporting scan has 17 hotspots
  (1 retained now / 3 soon / 13 monitor); the new derivation helper is
  monitor-only. The joint final gate has 602 passing and 2 skipped, and the
  38-file structural counts are recorded in the ALG-004 entry above. No stored
  evidence, schema, network access, or paid call changed.
- 2026-07-22: implemented ALG-003's offline rank-mixture grid and discrete
  one-standard-error choice without another Selector family or trainer. The
  fixed builder emits all ten thirds-simplex points with one shared behavior
  contract. The chooser requires actual complete paired MAE for every mixture,
  falls back to equal weights under the history gate, and otherwise prefers the
  point closest to equal weights inside the best point's one-SE band. Tests
  cover grid completeness, vertices/equal point, uncertain-best shrinkage,
  clear-best retention, short history, mixed behavior rejection, config types,
  and the full public evidence chain. Selection has 128 passing tests; Ruff and
  Pyright pass; the full suite has 592 passing and 2 skipped. Targeted Cremona
  scans report zero hotspots in `algorithms.py` and the unchanged 14 hotspots
  (0 now / 4 soon / 10 monitor) in `evaluation.py`. The final 38-file scan also
  remains at 118 hotspots: 2 retained `refactor_now`, 46 `refactor_soon`, and 70
  `monitor`, with critical counts 0/20/0, no dead-code candidate, and missing
  coverage input. Scoped formatting and `git diff --check` pass. No schema,
  dependency, network access, paid call, or empirical claim was added.
- 2026-07-22: implemented ALG-002's offline stratified-forecast rule and
  replay-checked diagnostic without a schema or training framework. The rule
  consumes exact `task_stratum` snapshot records, applies symmetric Dirichlet
  smoothing over a declared trailing ref count, uses capacity-constrained
  largest-remainder quotas and seeded digest ranking, and stores either unit or
  capped post-stratification weights in the existing Selection mapping. Tests
  cover smoothing, capacity overflow, the unweighted ablation, cap activation,
  malformed parameters, missing stratum evidence, TV error, and effective
  sample size. The existing scorer already consumes selected weights. A first
  one-file scan exposed one 95-line `refactor_soon` diagnostic; separating
  evidence validation, proportion calculation, and weight summaries removed
  every hotspot from the file. All 119 Selection tests pass; the full suite has
  583 passing and 2 skipped. The final 38-file scan remains at 118 hotspots: 2
  retained `refactor_now`, 46 `refactor_soon`, and 70 `monitor`, with critical
  counts 0/20/0, no dead-code candidate, and missing coverage input. Ruff,
  Pyright, scoped formatting, and `git diff --check` pass. Reporting
  integration, nested tuning, outer-origin evidence, and any accuracy claim
  remain pending. No network or paid call occurred.
- 2026-07-22: implemented ALG-001's offline shrinkage safe-switch choice. New
  `SafeSwitchConfig` and `choose_selector_with_safe_switch` reuse the exact
  paired Selection/Metric/future-matrix validator. Candidate improvement is
  measured against a frozen fallback, shrunk toward zero, and admitted only
  after minimum-history, margin, and sample-standard-error gates. Stable and
  noisy synthetic histories, insufficient history, invalid configuration, and
  no-shrink/no-gate ablations are characterized; a complete evidence-chain test
  confirms the public path. The full 38-file structural counts remain 118
  hotspots, 2 retained `refactor_now`, 46 `refactor_soon`, 70 `monitor`, and
  critical counts 0/20/0. All 110 Selection tests pass; the full suite has 574
  passing and 2 skipped. Runner defaults, schemas, dependencies, network access,
  and paid evidence are unchanged. Outer-origin comparison remains pending.
- 2026-07-22: completed RI-034's Pylint-pilot summary slice and resolved RI-041.
  A failing characterization test reproduced a Result from another Runtime
  identity entering the pilot result set. Exact Result filtering now precedes
  per-effort and paired derivation; completion requires 20 exact Results and 20
  completed ledger calls. `summarize` fell from 119 NLOC / CCN 30 / cognitive
  24 to below every hotspot threshold. Pilot hotspots fell from 8 to 7,
  `refactor_now` and Lizard critical each fell from 1 to 0, and routing moved
  from `investigate_soon` to `watch_only`; the remaining counts are 1
  `refactor_soon` and 6 `monitor`. The current 38-file scan reports 118 hotspots,
  2 retained `refactor_now`, 46 `refactor_soon`, 70 `monitor`, no
  Ruff/Complexipy critical, 20 Lizard critical, no dead-code candidate, and
  missing coverage input. All 13 Pylint-pilot tests pass; the full suite has 571
  passing and 2 skipped. No dependency, network access, paid call, ledger
  mutation, or evidence write was added.
- 2026-07-22: completed RI-034's replicate-schedule input slice and resolved
  RI-040. Failing characterization tests reproduced a Boolean campaign ID, an
  integer-valued float repeat count, and two Agent records differing only by ID
  reaching schedule construction. Protocol, Task/Check member, Agent treatment,
  and Runtime checks are now separate. `_validate_inputs` fell from 72 NLOC /
  CCN 37 / cognitive 32 / Ruff 20 to 21 / 1 / below threshold / below threshold.
  File hotspots moved from 5 to 6, `refactor_now` fell from 1 to 0,
  `refactor_soon` rose from 4 to 6, Lizard critical fell from 3 to 2, and routing
  moved from `investigate_soon` to `watch_only`. The current 38-file scan reports
  119 hotspots, 3 `refactor_now`, 46 `refactor_soon`, 70 `monitor`, no
  Ruff/Complexipy critical, 21 Lizard critical, no dead-code candidate, and
  missing coverage input. All 23 replicate-schedule tests pass; the full suite
  has 569 passing and 2 skipped. No schedule schema, dependency, network access,
  paid call, campaign authority, or evidence write was added.
- 2026-07-22: completed RI-034's SourceEvent-validation slice and resolved
  RI-039. A failing characterization test reproduced a malformed material time
  escaping as an exception and an empty certification-rejection reason passing
  validation. Material/maturity checks and disposition semantics are now
  separate. `validate_source_event` fell from 83 NLOC / CCN 26 / cognitive 31 /
  Ruff 16 to below every hotspot threshold; the material helper is also below.
  The 39-line three-disposition state machine remains centralized and
  `refactor_soon`. Records hotspots stayed at 8, `refactor_now` fell from 1 to
  0, `refactor_soon` rose from 3 to 4, critical counts stayed at 0/0/0, and the
  file moved from `investigate_soon` to `watch_only`. The current 38-file scan
  reports 118 hotspots, 4 `refactor_now`, 44 `refactor_soon`, 70 `monitor`, no
  Ruff/Complexipy critical, 22 Lizard critical, no dead-code candidate, and
  missing coverage input. All 106 Records and 41 Task Pool tests pass; the full
  suite has 566 passing and 2 skipped. No schema, dependency, network access,
  or paid call was added.
- 2026-07-22: completed RI-034's RollingOrigin-validation slice and resolved
  RI-038. A failing characterization test reproduced three self-digested Origin
  states that independent validation accepted: cutoff drift from `origin_time`,
  an invalid explicit cutoff rule, and a future window beginning before the
  cutoff. Validation now binds those fields and separates mode, cohort,
  cluster, time, maturity, cutoff-rule, and policy checks.
  `validate_rolling_origin` fell from 117 NLOC / CCN 36 / cognitive 34 / Ruff
  22 to below every hotspot threshold; all new helpers are also below. Records
  hotspots fell from 9 to 8, `refactor_now` from 2 to 1, and critical counts
  from 0/1/0 to 0/0/0. The current 38-file scan reports 118 hotspots, 5
  `refactor_now`, 43 `refactor_soon`, 70 `monitor`, no Ruff/Complexipy critical,
  22 Lizard critical, no dead-code candidate, and missing coverage input. All
  107 Selection and 105 Records tests pass; the full suite has 565 passing and
  2 skipped. No schema, dependency, network access, or paid call was added.
- 2026-07-22: completed RI-034's Cell payload-state slice and resolved RI-037.
  A failing characterization test reproduced that Result cells could omit an
  outcome, excluded Result bindings could be partial, missing cells could carry
  exclusion/outcome payloads, and matrix scoreability could contradict its
  cells or abstention. Records now validates those cases as one explicit
  state machine. Cell membership, payload state, exact denominator coverage,
  and matrix scoreability are separate; `_validate_cells` fell from 45 NLOC /
  CCN 20 / cognitive 35 / Ruff 15 to 30 / 8 / below threshold / below threshold
  and left the hotspot list. The centralized 30-line three-state payload helper
  remains `refactor_soon` as the audit surface. Records hotspots stayed at 9,
  `refactor_now` fell from 3 to 2, `refactor_soon` rose from 2 to 3, and critical
  counts stayed at 0/1/0. The current 38-file scan reports 119 hotspots, 6
  `refactor_now`, 43 `refactor_soon`, 70 `monitor`, no Ruff/Complexipy critical,
  23 Lizard critical, no dead-code candidate, and missing coverage input. All
  105 Records tests and the full suite of 564 passing with 2 skipped preserved
  output. Four Selection fixtures were corrected to use production-valid cell
  states. No schema, dependency, network access, or paid call was added.
- 2026-07-22: completed RI-034's certification-result ingestion slice.
  CertificationResult validation/indexing, exact accepted Task/Check pair
  coverage, and frozen Task/Check digest reconciliation are now separate. The
  frozen Check lookup is indexed instead of scanning accepted Checks per pair.
  Characterization preserves a valid frozen pair and rejects duplicate pair
  evidence or frozen Task drift. `_validated_certification_results` fell from
  76 NLOC / CCN 25 / cognitive 39 / Ruff 17 to 16 / 4 / below threshold /
  below threshold and left the hotspot list; the index helper is monitor-only.
  Task Pool hotspots stayed at 9, `refactor_now` fell from 2 to 1, and critical
  counts stayed at 0/0/0. The current 38-file scan reports 119 hotspots, 7
  `refactor_now`, 42 `refactor_soon`, 70 `monitor`, no Ruff/Complexipy
  critical, 23 Lizard critical, no dead-code candidate, and missing coverage
  input. All 41 Task Pool tests and the full suite of 563 passing with 2 skipped
  preserved output. No evidence field, schema, dependency, network access, or
  paid call was added or removed.
- 2026-07-22: completed RI-034's RollingOrigin cohort slice and resolved
  RI-036. A failing characterization test reproduced that missing Task/Check
  records or a wrong Check owner were silently skipped while the Origin still
  bound the complete Task Pool digest. Origin construction now checks all pool
  members and linkage before cohort derivation; extra records remain harmless
  and excluded. Cohort partitioning is separate from overlap policy and record
  assembly. `build_rolling_origin` fell from 123 NLOC / CCN 22 / cognitive 36 /
  Ruff 13 to 88 / 6 / below threshold / below threshold and moved to `monitor`.
  The Origin file has no `refactor_now` or `refactor_soon` and moved from
  `strained/investigate_soon` to `stable/watch_only`. The current 38-file scan
  reports 119 hotspots, 8 `refactor_now`, 42 `refactor_soon`, 69 `monitor`, no
  Ruff/Complexipy critical, 23 Lizard critical, no dead-code candidate, and
  missing coverage input. All 106 Selection tests and the full suite of 562
  passing with 2 skipped preserved output. No schema, dependency, network
  access, or paid call was added.
- 2026-07-22: completed RI-034's FeatureSnapshot provenance slice and resolved
  RI-035. A failing characterization test reproduced that a Result-linked
  FeatureRecord could carry another in-origin Task/Check or Agent while keeping
  the correct Result/source digest. Present Task, Check, Agent, and cache links
  now match the exact visible Result; nullable fields and origin-level
  aggregate digest/count semantics are unchanged. Scope/time checks and Result
  provenance are separate. `_ensure_feature_records_match_origin` fell from 55
  NLOC / CCN 21 / cognitive 38 / Ruff 12 to 29 / 8 / below threshold / below
  threshold and left the hotspot list; its Result helper is monitor-only. The
  Features file has no `refactor_now` and moved to `watch_only`. The current
  38-file scan reports 118 hotspots, 9 `refactor_now`, 42 `refactor_soon`, 67
  `monitor`, no Ruff/Complexipy critical, 23 Lizard critical, no dead-code
  candidate, and missing coverage input. All 105 Selection tests and the full
  suite of 561 passing with 2 skipped preserved output. No schema, dependency,
  network access, or paid call was added.
- 2026-07-22: completed RI-034's learned-Selector training-ResultMatrix slice.
  Matrix validation/indexing, per-matrix provenance and scoreability, exact
  selected/future role pairing, and shared future Result evidence are now
  separate. Characterization tests preserve valid pairs and reject missing
  roles, mixed join policies, or per-Selector future-evidence drift.
  `_validated_training_matrices` fell from 73 NLOC / CCN 19 / cognitive 31 /
  Ruff 18 to 15 / 1 / below threshold / below threshold and left the hotspot
  list; all extracted helpers remain below hotspot thresholds. Evaluation
  hotspots fell from 15 to 14, `refactor_now` from 1 to 0, critical counts
  stayed at 0/2/0, and routing pressure moved to `watch_only`. The current
  38-file scan reports 118 hotspots, 10 `refactor_now`, 42 `refactor_soon`, 66
  `monitor`, no Ruff/Complexipy critical, 23 Lizard critical, no dead-code
  candidate, and missing coverage input. All 104 Selection tests and the full
  suite of 560 passing with 2 skipped preserved output. No training field,
  schema, dependency, network access, or paid call was removed or added.
- 2026-07-22: completed RI-034's learned-Selector training-Metric slice.
  Metric validation/indexing, matrix provenance, MAE recomputation, exact
  Selection coverage, within-origin completeness, and normalized training rows
  are now separate. Characterization tests preserve the valid recomputed rows
  and reject missing Selection metrics or mixed metric configurations.
  `_validated_training_metrics` fell from 86 NLOC / CCN 26 / cognitive 33 /
  Ruff 17 to 17 / 1 / below threshold / below threshold and left the hotspot
  list; all extracted helpers remain below hotspot thresholds. Evaluation
  hotspots fell from 16 to 15 and `refactor_now` from 2 to 1, while critical
  counts stayed at 0/2/0. The current 38-file scan reports 119 hotspots, 11
  `refactor_now`, 42 `refactor_soon`, 66 `monitor`, no Ruff/Complexipy
  critical, 23 Lizard critical, no dead-code candidate, and missing coverage
  input. All 103 Selection tests and the full suite of 559 passing with 2
  skipped preserved output. No training field, schema, dependency, network
  access, or paid call was removed or added.
- 2026-07-22: completed RI-034's learned-Selector training-Result slice.
  Result validation/indexing, matrix-cell binding, exact denominator coverage,
  and strict-prospective availability are now separate. Characterization tests
  preserve valid paired-matrix bindings and reject missing Results or cell
  identity drift. `_validate_training_results` fell from 78 NLOC / CCN 23 /
  cognitive 40 / Ruff 15 to 12 / 1 / below threshold / below threshold and
  left the hotspot list; all extracted helpers remain below hotspot thresholds.
  Evaluation hotspots fell from 17 to 16 and `refactor_now` from 3 to 2, while
  critical counts stayed at 0/2/0. The current 38-file scan reports 120
  hotspots, 12 `refactor_now`, 42 `refactor_soon`, 66 `monitor`, no
  Ruff/Complexipy critical, 23 Lizard critical, no dead-code candidate, and
  missing coverage input. All 102 Selection tests and the full suite of 558
  passing with 2 skipped preserved output. No training field, schema,
  dependency, network access, or paid call was removed or added.
- 2026-07-22: completed RI-034's learned-Selector training-input slice.
  FeatureSnapshot validation/indexing, SelectorInput validation/indexing, and
  per-origin provenance links are now separate while exact origin coverage,
  common Agent/budget/feature configuration, and all future training inputs
  remain mandatory. The former cognitive/Ruff 46/27
  `_validated_training_inputs` hotspot is replaced by a monitor-only 20/13
  active helper. Evaluation hotspots stayed at 17, `refactor_now` fell from 4
  to 3, and critical counts fell from 1/2/0 to 0/2/0. The current 38-file scan
  reports 121 hotspots, 13 `refactor_now`, 42 `refactor_soon`, 66 `monitor`, no
  Ruff/Complexipy critical, 23 Lizard critical, no dead-code candidate, and
  missing coverage input. All 101 Selection tests and the full suite of 557
  passing with 2 skipped preserved output. No training field, schema,
  dependency, network access, or paid call was removed or added.
- 2026-07-22: completed RI-034's latest-schema coercion slice. `_coerce_value`
  now dispatches Union, tuple/list, Mapping, nested dataclass, and scalar
  coercion to direct helpers while preserving canonical JSON, exact latest
  schema, null handling, recursive paths, and first-Union-error behavior. It
  fell from 80 NLOC / CCN 42 / cognitive 63 / Ruff 27 to 16 / 8 / below
  threshold / below threshold and left the hotspot list. Records hotspots
  stayed at 9, `refactor_now` fell from 4 to 3, and critical counts fell from
  1/2/1 to 0/1/0; only the scalar helper is monitor-only. The current 38-file
  scan reports 121 hotspots, 14 `refactor_now`, 42 `refactor_soon`, 65
  `monitor`, critical counts 1/23/0, no dead-code candidate, and missing
  coverage input. All 104 Records tests, 26 migration/schedule consumer tests,
  and the full suite of 557 passing with 2 skipped preserved output. No schema
  relaxation, dependency, network access, or paid call was added.
- 2026-07-22: completed RI-034's source-event evidence slice and retained the
  centralized claim boundary. Source-event collection/order, observation
  cutoff, per-record validity, accepted/rejected certification linkage, and
  denominator coverage are now separate checks. `_source_event_errors` fell
  from 122 NLOC / CCN 42 / cognitive 58 / Ruff 25 to 74 / 12 / 16 / below
  threshold and moved to `monitor`; Task Pool critical counts fell from 1/1/1
  to 0/0/0. A new characterization test covers repository/cutoff drift,
  missing certification evidence, frozen material drift, rejection-reason
  drift, and candidate coverage. `build_claim_boundary` remains one explicit,
  ordered claim audit surface rather than duplicating validation or adding a
  report-only state bundle. The current 38-file scan reports 121 hotspots, 15
  `refactor_now`, 42 `refactor_soon`, 64 `monitor`, critical counts 2/24/1, no
  dead-code candidate, and missing coverage input. The full suite has 557
  passing and 2 skipped tests. No schema, dependency, network access, or paid
  call was added.
- 2026-07-22: completed RI-034's Result-report summary slice. Execution-state,
  benchmark-invalid, cost, and limitation summaries now have direct helpers;
  `build_result_report` retains ReportSection construction and claim support.
  It fell from the post-latency-extraction 139 NLOC / CCN 33 / cognitive 30 to
  44 / 7 / below threshold and left the hotspot list. The one-file scan stayed
  at 16 hotspots, while `refactor_now` fell from 2 to 1 and critical counts
  fell from 0/3/0 to 0/2/0; the new execution summary is monitor-only. The
  current 38-file scan reports 120 hotspots, 16 `refactor_now`, 42
  `refactor_soon`, 62 `monitor`, critical counts 3/25/2, no dead-code candidate,
  and missing coverage input. All 57 Reporting tests and the full suite of 556
  passing with 2 skipped preserved output. No schema, dependency, network
  access, or paid call was added.
- 2026-07-22: completed RI-034's Selector-report derivation slice. Origin
  cohort rows, Selection/matrix/metric rows, MAE derivation, and source digests
  are now pure helpers while claim and error ordering remain in
  `build_selector_report`. The report builder fell from 334 NLOC / CCN 70 /
  cognitive 48 / Ruff 11 to 132 / 12 / below threshold / below threshold and
  moved from `refactor_now` to `monitor`. The one-file scan moved from 14 to 16
  hotspots, `refactor_now` from 3 to 2, and critical counts from 0/4/0 to 0/3/0;
  new visible helpers are monitor-only. The current 38-file scan reports 120
  hotspots, 17 `refactor_now`, 42 `refactor_soon`, 61 `monitor`, critical counts
  3/26/2, no dead-code candidate, and missing coverage input. Fifty-seven
  Reporting tests, the characterized Runner integration test, and the full
  suite of 556 passing with 2 skipped preserved output. No schema, dependency,
  network access, or paid call was added.
- 2026-07-22: completed RI-034's nested SelectorInput provenance slice.
  Pre-origin Result resolution now builds the eligible Task/Check set once and
  returns the resolved view; FeatureSnapshot Result-view, allowed-class, and
  feature-time checks are separate. `_append_selector_input_link_errors` fell
  from 134 NLOC / CCN 35 / cognitive 54 / Ruff 27 to 78 / 17 / 21 / 15 and
  moved from `refactor_now` to `refactor_soon`; both new helpers are below
  hotspot thresholds. A Runner integration test now characterizes missing
  pre-origin Results, Result-view drift, post-origin Results, and disallowed
  feature classes. The current 38-file scan reports 118 hotspots, 18
  `refactor_now`, 42 `refactor_soon`, 58 `monitor`, critical counts 3/27/2, no
  dead-code candidate, and missing coverage input. The full suite has 556
  passing and 2 skipped tests. No schema, dependency, network access, or paid
  call was added.
- 2026-07-22: completed RI-034's Selector-provenance orchestration slice.
  `_selector_provenance_errors` now delegates evidence indexing, required
  evidence checks, RollingOrigin-to-Task-Pool reconciliation, and per-Selection
  origin/snapshot/input links while preserving validation and error order. It
  fell from 177 NLOC / CCN 40 / cognitive 70 / Ruff 33 to 68 / 3 / below
  threshold / below threshold. The one-file Reporting scan moved from 12 to 14
  hotspots as helpers became visible, while `refactor_now` fell from 5 to 4 and
  Ruff/Lizard/Complexipy critical counts fell from 2/5/2 to 1/5/1. The current
  38-file scan reports 118 hotspots, 19 `refactor_now`, 41 `refactor_soon`, 58
  `monitor`, critical counts 4/28/3, no dead-code candidate, and missing
  coverage input. Fifty-seven focused Reporting tests and the full suite of 556
  passed with 2 skipped. No schema, dependency, argument-bundle abstraction,
  network access, or paid call was added.
- 2026-07-22: completed RI-034's paired-MAE evidence-boundary slice.
  `_paired_mae_by_origin` now delegates Selection, Metric, future-matrix, and
  comparability validation while preserving the public error order and output.
  The former 177-line / CCN 49 / cognitive 74 function left the hotspot list;
  its new helpers are monitor-only. Within `selection/evaluation.py`, hotspots
  moved from 15 to 17, `refactor_now` from 5 to 4, and
  Ruff/Lizard/Complexipy critical counts from 2/3/1 to 1/2/0. Twenty-eight
  focused paired-MAE tests and all 158 Selection/Reporting tests pass. The
  current 38-file scan reports 116 hotspots, 20 `refactor_now`, critical counts
  5/28/4, no dead-code candidate, and missing coverage input. No schema,
  dependency, validation framework, network access, or paid call was added.
- 2026-07-22: completed RI-028's examples-layer paid execution boundary without
  authorizing a campaign. `replicate_campaign.py` creates a non-overwritable,
  self-digested authority ledger binding the schedule, Task Pool, Agent set,
  Workspace/base Runtime configs, endpoint digest, budget, schedule-sized call
  cap, and ScoringConfig. Preflight covers every remaining Runtime slot;
  execution reserves and runs only the first missing cell, reconciles a durable
  Result after an interrupted completion event, checks completion evidence
  against that Result, and forbids automatic retry after a stopped or
  result-less reservation. Twenty focused schedule/campaign tests pass. A
  one-file Cremona scan reported `stable`, `watch_only`, five monitor hotspots,
  no refactor-now/soon hotspot, and no dead-code candidate; coverage input was
  absent. No campaign ledger, credential lookup, network access, Agent call,
  paid call, or historical evidence write occurred.
- 2026-07-22: opened RI-034 from a scoped Cremona structural audit. The scan
  covered 37 version-controlled production/example/script files, reported
  `strained` debt with `investigate_soon` routing pressure, had no dead-code
  candidates, and lacked coverage input. Pure Result latency extraction reduced
  `build_result_report` from 228 lines / CCN 55 / cognitive 60 to 139 / 33 /
  30. Responsibility-based Selector trace extraction removed its former
  216-line / CCN 66 / cognitive 109 function from the hotspot list.
  Certification-evidence characterization then separated record parsing,
  per-record semantics, and cross-record reconciliation, reducing its main
  function from 179 lines / CCN 56 / cognitive 86 to 76 / 23 / 33 without
  leaving the parser as a new hotspot. The final scan reduced `refactor_now`
  from 22 to 21 and Ruff/Lizard/Complexipy critical counts from 8/31/8 to
  6/29/5; 57 Reporting and 39 Task Pool tests preserved output. No baseline,
  dependency, schema, or validation framework was added.
- 2026-07-22: completed RI-021's measurement prerequisite without adding a
  checkout cache. Current Workspace runs record separate monotonic solver and
  verifier checkout, diff replay, Agent, Check, and cleanup durations; Result
  reports expose phase coverage and checkout-plus-cleanup share only for a
  complete denominator. Historical Results remain unchanged. Cache experiments
  still require warm/cold p50/p95 evidence across repository sizes and the
  documented reopening threshold.
- 2026-07-22: completed the offline RI-028 consumer. It strictly replays the
  schedule, resolves each cell with its exact Runtime slot in frozen order, and
  exposes only the first missing slot for resume. Tests cover identity, order,
  exact reuse, and failure before Result Store access on schedule drift. No
  Agent, network, paid call, or historical evidence write occurred; campaign
  execution remains gated on explicit authority.
- 2026-07-22: closed RI-015. Extracted the common reservation/completion event
  log, complete-line check, fsync, atomic snapshot, and cost folding into one
  examples-layer helper; the two paid scripts keep their distinct endpoint,
  pricing, scoreability, and resume validation. Temporary copies of all three
  historical ledgers rebuilt the same calls, spent cost, and remaining budget.
  No paid call or original evidence write occurred.
- 2026-07-22: closed the offline diagnostic part of RI-031. Task Pool reports
  now state certification yield and denominator, exclusions, rejection stages
  and reasons, and repeated-certification outcome-conflict quarantine. Result
  reports state later benchmark-invalid execution and affected-Task/Check rates
  after pricing-view deduplication. No acceptance gate or causal flaky label was
  added.
- 2026-07-22: closed DOC-002 with one enforced storage and recovery contract.
  It distinguishes immutable Task Pool publication, durable Result appends,
  single-writer companion logs, best-effort Workspace artifacts, and derived
  reports; defines exact cache and repricing scope; and records the current
  recovery limits without adding a storage service or schema. The same audit
  added staged-member, staging-directory, and post-rename parent fsyncs to Task
  Pool publication.
- 2026-07-22: closed the offline Pylint adapter part of RI-027. Added a small
  self-digested dependency artifact derived from trusted reference-patch path
  overlap, deterministic connected components, Task Pool generator binding,
  load-time patch/SourceEvent replay, and explicit non-exposure checks. The
  historical ten-task material replays to one edge and nine components; this
  does not prove singleton independence. No generic graph service, network
  access, or paid call was added. Verified 528 tests with 2
  environment-dependent skips plus Ruff and Pyright.
- 2026-07-22: closed the offline scheduling part of RI-028. Added a
  Pylint-specific immutable replicate schedule with exact Task Pool, Check,
  Agent, Runtime, campaign, seed, stratified subset, paired order, and cell
  bindings. Existing stochastic-settings identity names each observation slot,
  so resume cannot select a latest or best duplicate. No paid replicate was run
  and no run-level variation claim was made. Verified 519 tests with 2
  environment-dependent skips plus Ruff and Pyright.
- 2026-07-22: closed RI-024. Agent and Result cache identity now distinguish
  the requested model, a proven immutable snapshot, and a mutually exclusive
  bounded campaign scope. Paid preflight and just-in-time validation reject an
  unresolved alias outside its window. Added a non-destructive migration for
  the immediately preceding Result schema and verified it against 15 boltons
  and 20 Pylint paid Results in temporary outputs; source evidence was not
  changed. Verified 510 tests with 2 environment-dependent skips plus Ruff and
  Pyright. No network or paid benchmark call was made.
- 2026-07-22: closed RI-023. Core evidence JSONL loading now rejects unknown or
  missing latest-schema keys, wrong recursive field types, blank records,
  non-finite numbers, and noncanonical representations with line-numbered
  errors. Certification evidence also enforces exact top-level and nested
  outcome schemas. Result Store still owns the stronger durable-log rule for
  unterminated tails. Verified 505 tests with 2 environment-dependent skips
  plus Ruff and Pyright. No network or paid benchmark call was made.
- 2026-07-22: closed the offline RI-029 contract and DOC-001. Added the short
  statistical protocol and executable paired MAE summary with macro/weighted
  loss, canonical pair differences, exact seed-bank variation, and
  sample-size-gated deterministic Origin-block intervals. Reporting emits the
  summary only after complete provenance validation and metric recomputation;
  empty, non-scoreable, or fabricated evidence is withheld. Verified 496 tests
  with 2 environment-dependent skips plus Ruff and Pyright. No network or paid
  benchmark call was made.
- 2026-07-22: closed the offline RI-025 and RI-026 contracts, RI-030, and the
  source-frame part of RI-032. Rolling origins now separate arrival cohorts from
  label maturity and retain censored refs; immutable Task Pool bundles include
  exact sanitized SourceEvents; certification repeats symmetric base/patched
  pairs. RI-027 now separates protocol-only dependency clusters from
  Selector-visible sampling strata; deterministic relation provenance remains
  open. Verified 489 tests with 2 environment-dependent skips plus Pyright. No
  network or paid benchmark call was made.
- 2026-07-22: completed Stage 2 (RI-008, RI-009, and RI-022). Replaced the
  first-candidate training placeholder with evidence-replaying rule-mixture
  fitting, made materialized FeatureSnapshot validation mandatory for public
  inference, and added shared-cell multi-Selector evaluation with recovery.
  Cached fixed-clock plural and sequential outputs are identical. Verified 481
  tests with 2 environment-dependent skips plus Ruff and Pyright. No network or
  paid benchmark call was made.
- 2026-07-22: paused at a stable handoff after RI-014. No RI-008, RI-009, or
  RI-022 implementation was started. The next session should first make the
  fitted training and FeatureSnapshot inference boundaries coherent, then add
  shared-cell planning. No network or paid benchmark call was made.
- 2026-07-22: completed Stage 0 evidence integrity. Added immutable Task Pool and
  commit binding, common denominators, complete rolling-origin provenance,
  repricing-safe reports, bounded process containment, and fail-closed paid
  endpoint/harness preflight. Verified 442 tests with 2 environment-dependent
  skips; static checks passed. No network or paid benchmark call was made.
- 2026-07-22: completed the cohesive Stage 1 Result Store and timing slice
  (RI-017, RI-018, RI-020). Added one locked live index per Runner operation,
  durable append/recovery behavior, line-numbered load failures, and monotonic
  phase latency. The local 100/1,000/10,000-record scaling check was linear. No
  network or paid benchmark call was made.
- 2026-07-22: closed RI-010. Replaced caller-supplied budget, join,
  denominator, claim, feature, and leakage identifiers with canonical derived
  properties; RollingOrigin already used this contract. Behavior mutations are
  covered by focused tests (216 tests across the affected modules). No network
  or paid benchmark call was made.
- 2026-07-22: closed RI-011 without adding event schemas. Repeat training,
  selection freeze, and metric scoring reuse their first persisted observation;
  same-ID semantic drift remains an error. Public Runner resume tests cover all
  three paths. No network or paid benchmark call was made.
- 2026-07-22: closed RI-012. Replaced mutable process-global Repository, Agent,
  and Check binding dictionaries with one immutable, tuple-backed
  `WorkspaceRunContext` passed through certification and execution. Focused
  Workspace, Task Pool, Runner, pilot, and minimal-demo tests passed (130
  tests). No network or paid benchmark call was made.
- 2026-07-22: closed RI-013 without a utility framework. Centralized
  timezone-aware UTC parsing/formatting and Check-command identity in Records,
  rejected naive evidence and query times, renamed the Verification adapter
  value to `VerifierWorkspace`, and used standard `Path.is_relative_to` for
  containment. The affected 372-test suite and source static checks passed. No
  network or paid benchmark call was made.
- 2026-07-22: closed RI-014. Made Benchmark Selection frozen by construction,
  removed its unused publication-state fields and the redundant
  `SelectionConfig`, and added prospective Selection-to-future-Result timing
  validation. The affected 264-test suite and source static checks passed. No
  network or paid benchmark call was made.
- 2026-07-22: closed RI-007. Certification evidence now binds the complete
  built-in verifier execution identity, and hidden material uses one
  mode-aware, symlink-rejecting tree digest with no-merge injection. Focused
  Verification, Workspace, and Task Pool tests passed (112 tests). No network
  or paid benchmark call was made.
- 2026-07-22: incorporated maintainer principles to preserve known final-form
  contracts while keeping implementation simple. Reclassified Selector
  provenance and training as completion work, defined the minimal learned
  Selector boundary, and recorded explicit checkout and bounded-parallel future
  decisions with prerequisites and reopening thresholds.
- 2026-07-22: created from a read-only architecture, adversarial-boundary,
  algorithm, pipeline, performance, and documentation audit. Added reproduced
  counterexamples for holdout policy enforcement and repricing reports.
