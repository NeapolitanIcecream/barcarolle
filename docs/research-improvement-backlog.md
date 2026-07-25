# Research Findings And Improvement Backlog

Last reviewed: 2026-07-25.

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
maturity, retains censored refs, persists a complete supplied source-event
ledger, and runs symmetric repeated certification pairs. Dependency blocking
is also separate from Selector-visible sampling strata. Requested model names are now
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
and emits bounded summaries without adding a core execution path.

The Task-supply audit confirms the original source-agnostic direction but
narrows its meaning. Built-in and user generators should hand Barcarolle one
strict prepared-candidate package; Barcarolle then owns certification and
immutable publication. A user-maintained complete `TaskPoolBundle` is a
separate, read-only input that must be validated in place without generator
execution or republication. Runner, Selection, Reporting, and Workspace should
not know a generator type. This generic boundary is now complete: prepared
packages preserve exclusions and local material digests, optional provenance
separates stable behavior/protocol from frame/run/output identity, high-level
Runner paths preflight complete bundles, and existing bundles open read-only.
Static classic paradigms can now converge through adapter-specific evidence;
interactive paradigms still require a later episode-execution contract, not a
larger Generator abstraction.

The Generator-validity sprint further narrows the scientific claim.
`SourceEventRecord` is currently a complete ledger only for events supplied to
one Task Pool build; it is not evidence that the source adapter observed the
declared work population. `future_pass_rate_mae` is a
Generator-conditional prediction loss on one later mature Task/Check pool, not
an end-to-end real-work quality score or a pure Selector-error component.
Generator behavior and the observed source frame therefore need independent
identities and receipts. Interactive user simulation is additionally a
benchmark-side environment policy whose counterfactual responses are not
identified by one logged trajectory. A concrete adapter may implement one
narrow treatment-conditional episode contract, but a held-out human branch
pilot must pass before simulator outcomes can support human-interaction claims.
Real-work calibration stays a prospective field experiment, not an inference
from bundle integrity, conversion yield, distribution similarity, or simulator
difficulty.

The 2026-07-25 model study has explicit campaign authorities and is producing
the first paid run-variation evidence. Its Results remain experiment-layer
evidence until RI-159 reaches the predeclared repeatability gates; no core cache
or controller policy changes merely because repeats now exist.

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

## Infrastructure Closure Sprint Contract

The 2026-07-24 sprint completed the generator-agnostic infrastructure justified
by RI-120 through RI-153. It stopped before implementing, running, or
optimizing a concrete Generator.

Success requires all of the following:

- every high-level evidence-producing Runner path consumes or reloads one
  complete validated Task Pool bundle before repository, Result, or Agent side
  effects;
- untrusted prepared candidates and a user-maintained immutable Task Pool have
  separate build and read-only open/use paths;
- external Results are admitted without modifying their source, cannot backfill
  pre-origin evidence by default, and cannot silently win an exact-cache
  conflict;
- Generator behavior, source protocol, observed-frame inventory, run authority,
  and outputs are independently bound without adding a Generator runtime;
- Reporting treats bundle consistency, generated-pool prediction, observed
  frame, Generator bridge, Check/semantic calibration, and field calibration as
  separate evidence axes;
- latest-schema migration, public red/green contract tests, the full quality
  suite, documentation replay, and an independent adversarial audit pass.

The following do not count as completion: a record with no enforcing consumer;
a CLI wrapper that bypasses public APIs; validating only Task/Check members;
renaming a claim while preserving a broader interpretation; treating a Boolean
as source-capture proof; copying external Results without conflict and
availability rules; or adding plugin, workflow, simulator, telemetry, mixture,
or concrete-Generator machinery.

The working route registry is:

| Route | Thesis and decisive test | Status / reopening condition |
| --- | --- | --- |
| A. Task-supply boundary | One strict prepared package plus one read-only bundle handle is sufficient. A damaged certification or SourceEvent artifact must stop every high-level execution path before side effects. | Complete: RI-120–RI-124, RI-148, and the infrastructure part of RI-137/RI-138. |
| B. Result admission and phase order | Existing Result Store and cache identity are sufficient if provenance, effective availability, canonical Result identity, conflict classification, one physical snapshot, Selection replay, and resolution-policy-specific CellSets are enforced. The source artifact must remain byte-identical and receipt replay must be read-only. | Complete: RI-131–RI-135, RI-141/RI-142, RI-147, RI-151, and RI-153. |
| C. Scientific evidence identity | Independently digested manifest sections can support observed-frame and behavior claims without a registry or service. Pools without provenance remain usable but cannot carry Generator behavior or source-protocol identity; pools without a frame cannot claim frame coverage. | Complete at the generic boundary: RI-121, RI-136, RI-137, RI-143–RI-146, RI-149/RI-150, RI-152, DOC-006/DOC-015. Promote a shared frame record only if two concrete adapters need it. |
| D. Concrete and interactive Generators | Common infrastructure should not guess adapter behavior, episode semantics, field utility, or mixture weights. | Retired for this sprint. Reopen only with a concrete adapter, branch-policy pilot, authorized field protocol, or calibrated outer holdout as specified in RI-125–RI-130 and RI-139/RI-140. |

The allowed terminal states are verified completion, a demonstrated
incompatibility that forces a narrower documented contract, or a specific
external blocker. A partial schema, passing unit subset, or polished design note
is not a terminal state while an in-scope implementation or audit remains.

## Target End State

The eight existing modules remain sufficient. The target data flow is:

```text
Built-in or user generator -> prepared candidate package
  + independently digested Generator behavior
  + observed source-frame protocol/inventory receipt
  -> Barcarolle certification -> immutable Task Pool

User-maintained immutable Task Pool
  -> read-only complete-bundle validation

User-maintained Result bundle
  -> validate + normalize provenance/availability
  -> append-only Result Store

Validated Task Pool + leakage-safe pre-origin Result view
  -> RollingOrigin + FeatureSnapshot
  -> frozen SelectorInput
  -> train_selector -> executable SelectorRecord
  -> select_with_selector -> frozen Benchmark Selection
  -> exact selected-cell cache lookup
  -> Workspace + Verification only for missing cells
  -> append-only Agent Results
  -> Selection evaluation -> Reporting

Optional research evidence outside the execution path:
  same-frame Generator bridge -> Generator-validity report
  prospective real work -> field-calibration report
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

## Task Supply And Generator Architecture Decision

### Scope

The original design is preserved with one qualification: the current core is
generator-agnostic for static, single-repository, final-diff tasks with an
executable aggregate Check. It is not yet a complete arbitrary-generator
integration.

The target has two operations with different responsibility and trust:

```text
build:
  built-in or user generator
    -> strict prepared-candidate package
    -> Barcarolle certification
    -> immutable TaskPoolBundle

open:
  user-maintained immutable TaskPoolBundle
    -> read-only complete validation
    -> Runner / Selection / Reporting
```

`build` accepts untrusted candidate data and Barcarolle decides admission.
`open` accepts only a complete latest-schema Barcarolle bundle; it does not run
a generator, copy the bundle, republish it, or silently recertify it. A plain
external task list is candidate input to `build`, not an uncertified Task Pool.

The downstream boundary is the existing `TaskPoolBundle`. Generator code,
classes, lifecycle, credentials, and paper-specific fields do not enter Runner,
Selection, Reporting, or Workspace. One Task Pool continues to contain one
target repository; adapters partition multi-repository corpora into several
pools. A collection index can be added later if a concrete cross-pool operation
needs it.

### Task Pool use, imported Results, and lazy execution

Task Pools and Results should keep separate storage and publication lifecycles,
but they are joined by exact execution cells. A cached Result belongs to:

```text
Task + Check + Agent + WorkspaceConfig + RuntimeConfig
```

It does not belong to a Task Pool as a whole. The current
`ResultCacheIdentity` already has this shape and correctly excludes Task Pool
and pricing identity. Adding `task_pool_id` or `task_pool_digest` to the cache
key would prevent reuse when an unchanged Task/Check appears in a later pool.
Every use must instead prove exact Task/Check membership in the current
validated bundle. Agent-by-pool coverage is a derived cell view, not a nested
Result map inside the immutable Task Pool. Pools that want cross-snapshot reuse
must preserve the exact content-derived Task/Check identities; do not add fuzzy
matching or alias resolution.

The direct-use flow should be:

```text
complete TaskPoolBundle
  + optional external Result bundle
  + Agent/Workspace/Runtime identities
  -> validate and import eligible Results into one local Result Store
  -> construct the cutoff-safe pre-origin Result view
  -> freeze SelectorInput and Benchmark Selection
  -> resolve only selected exact cells against the full cache
  -> execute missing cells
  -> append Results and pricing views
  -> freeze exact EvaluationCellSet bindings
```

This is the deployment/direct-use path. Offline Selector evaluation also
resolves its already frozen future-holdout cells because those outcomes define
prediction error; it must still freeze every Selection first and execute only
the union of cells required by the frozen evaluation plans.

The first implementation should import normalized records into the existing
single append-only Result Store. It should not add a composite read-only-store
overlay or modify the user's source file. Result JSONL is small compared with
repositories, images, and Agent calls; copying validated records preserves one
lock, one conflict rule, one resolver, and one writer. Reconsider mounted
sources only after measured import size or shared-storage requirements justify
them.

An external Result bundle needs a small source manifest and import receipt. The
receipt binds the source artifact digest, producer/authority, import time,
availability policy, target Task Pool, Agent/config projections, original
Result IDs/digests, and normalized local Result IDs/digests. Import validates
the complete Task Pool first, then requires every admitted Result to:

- pass latest-schema, self-digest, state, timestamp, and measurement checks;
- match one exact Task/Check in that bundle;
- match a supplied Agent, WorkspaceConfig, and RuntimeConfig projection;
- retain enough usage to reprice without rerunning when possible;
- use an explicitly accepted external producer authority.

Schema validity cannot prove that an external Check actually ran. Imported
outcomes are therefore `external_attested`, not
`barcarolle_managed`, and reports must preserve that distinction. Local use
does not need signatures because the user is the trust root; untrusted remote
exchange can add authentication only when it becomes real.

Result availability needs a separate import rule because it controls
rolling-origin leakage. By default, normalize
`result_available_at = max(source result availability, import time)`. This
allows immediate post-Selection cache reuse but cannot backfill an earlier
pre-origin view. Preserving the producer's earlier availability requires an
explicit historical-evidence mode, a source manifest that binds that claim,
and an external-attestation label in Reporting.

The normalized Result should persist an evidence-source kind and source-manifest
digest. Those fields and effective availability belong to Result record
identity and digest, but not `ResultCacheIdentity` or
`result_execution_digest`. This lets two provenance/availability observations
share one execution cache identity without colliding as evidence records.
Existing managed Results need a one-off latest-schema migration, not a runtime
compatibility branch.

Cache conflict behavior also needs tightening before import:

- identical Result ID/digest is idempotent;
- the same cache identity and execution digest with another pricing view is
  reusable or repriceable;
- the same cache identity with different execution digests is ambiguous and
  must not be selected by append order;
- intentional replicate observations must have distinct frozen stochastic
  setting or observation-slot identity.

The phase boundary is already partly correct. `evaluate_selectors` freezes all
Selections before resolving target cells, and `fill_results` resolves cached
selected cells before running missing ones. Preserve that order. One evaluation
must materialize one Result Store snapshot and derive every origin view from it.
The cutoff-safe pre-origin view is the only Result view visible during
Selection. Public lazy execution must resolve and replay the durable Selection
and complete Task Pool bundle before the full cache opens.

### Required prepared-candidate package

`CandidateBatch` is the correct in-memory nucleus, but it is not a complete
interchange format. A versioned prepared-candidate package also needs:

- exactly one repository identity and declared source scope or window;
- candidates plus all known excluded or right-censored SourceEvents needed for
  the denominator;
- content-digested references to reference patches, Check commands/manifests,
  hidden material, environment material, and any synthetic base state;
- one sanitized generator-provenance sidecar;
- optional adapter-specific evidence and exact derivation edges, with the
  existing `dependency_cluster_id` as their conservative Selection projection.

The package schema must reject unknown fields. The current candidate parser
silently ignores them, so an `interaction_protocol` field can presently be
discarded while the row is accepted as an ordinary static task. Relative refs
and content digests form identity; machine-local repository, image, command,
and hidden-material paths belong in an ignored use-time binding file.

Built-ins may call direct functions. User and third-party generators may emit
the same language-neutral package from any process or language. Barcarolle does
not need Python entry-point discovery, a generator base class, or a plugin
lifecycle. Launching unknown generator code is not an isolation boundary and
is not required for interoperability.

### Generator identity and evidence

Current behavior has opposite failure modes:

- Runner hashes only `mode + source_family`, so different implementations,
  versions, prompts, models, filters, or seeds can look identical;
- the Pylint adapter includes inventory-dependent dependency evidence in the
  same digest, so one unchanged generator observed over a later window can look
  like changed behavior.

This matters because strict-prospective evaluation requires the two Task Pools'
`generator_config_digest` values to match. The persisted provenance should
therefore separate:

- `behavior`: adapter family and version, implementation digest, canonical
  behavior config, and, where applicable, model/prompt/tool/sampling/retry/seed
  policy;
- `inputs`: repository or dataset revisions, source query/window/cutoff, and
  sanitized input or dependency-evidence refs/digests;
- `run`: producer, time, campaign, and managed or external authority;
- `outputs`: the existing candidate, SourceEvent, Task, Check, rejection, and
  certification identities.

`generator_config_digest` should be derived only from `behavior`. A new opaque
provenance ref/digest on the Task Pool should bind the other sections without
teaching core records about mutation operators, forecast families, or paper
stages.

A content-valid externally produced bundle proves schema, digest, member, and
coverage consistency. It does not prove that the producer actually executed
the declared generator or certification. Reports must distinguish
Barcarolle-managed evidence from external producer attestation. Do not add
signatures or a transparency service until untrusted remote pool exchange is a
real requirement.

### Classic paradigms

The following matrix uses the exact two-plus name **SWE-Bench++**, not the
unrelated single-plus SWE-Bench+ work.

| Paradigm | Fit to current static Task/Check | Required adapter work |
| --- | --- | --- |
| [SWE-bench](https://www.swebench.com/original.html) | Fits after import or PR mining. One aggregate Check can enforce both F2P and P2P. | Bind dataset, harness, image, source, gold/test patch, F2P/P2P, and dependence evidence. Provide separate names for dataset import and mining. |
| [SWE-Bench++](https://arxiv.org/html/2512.17419) | Its final tasks fit, but ordinary base-fail/reference-pass evidence does not prove the Base/Before/After classification or distinguish an expected feature-request build failure from a broken environment/parser. | Retain three-state, environment-synthesis, parser, repeatability, and QA evidence in a sidecar. The public repository currently documents evaluation of the released dataset, not the paper's full generator, so call an implementation a dataset importer or paper-paradigm reimplementation unless exact official code is available. |
| [SWE-smith](https://swesmith.com/guides/create_instances/) | Fits after the bugged solver state has an immutable identity. Its `patch` introduces the bug; it is not the solver's gold repair. | First materialize the final solver state as a full Git commit and retain upstream/overlay lineage. Add a commit-plus-overlay core model only if a concrete adapter cannot materialize a commit. Keep mutation, issue-generation, F2P/P2P, environment, and combination lineage in sidecars. |
| [SWE-Future](https://arxiv.org/html/2606.18733) | A final executable task of the described form can fit. The missing contract is generation-time causal evidence, not the final Check. | Bind the pre-forecast cutoff and inputs, frozen forecast, later retrospective-validation window, task-generation snapshot, leakage audit, and family-to-task lineage. Later PR patches cannot become hidden generation inputs merely because they were used to validate a forecast family. |
| [SWE-Together](https://github.com/Togetherbench/SWE-Together) and [SWE-Interact](https://github.com/scaleapi/SWE-Interact) | Do not fit the static contract faithfully. The solver receives requirements over multiple turns and the benchmark-side simulator observes evolving work. A source trajectory does not identify human responses on a new Agent's branches. | A concrete adapter may add one separate episode-execution contract with pre-interaction/dynamic state, simulator/scenario identity and seed, disclosure and termination, persistent Workspace interaction, separate simulator usage/cost, sanitized event evidence, final verification, and interaction metrics. RI-127's held-out human branch-policy pilot gates human-proxy claims, not implementation of that adapter. Do not build a generator workflow DAG. |

Built-in names must state fidelity, for example `swebench_dataset_import`,
`swebench_miner`, `swebench_pp_paper_reimplementation`, or
`sweinteract_protocol_import`. Each adapter keeps a small config, primary-source
revision, golden fixtures, and fidelity tests. Paper names alone are not
evidence of reproduction.

Barcarolle-native research generators use exactly the same boundary. Their
evaluation must predeclare which classic failure they target, the source
population and time cutoffs, compute and LLM budget, classic baselines,
ablations, certification yield, later invalid rate, leakage and dependence
controls, task diversity, and downstream predictive utility. A trained
generator additionally binds training evidence and cutoff in its behavior/run
provenance. This needs an experiment-specific comparison over ordinary Task
Pools, not a generator-training framework in the core.

### Counterexamples closed at the generic boundary

The audit found four concrete gaps, all closed at the generic boundary by this
sprint:

1. `Runner._candidate_batch` supports only file import or caller-provided
   source events; a programmatic adapter must duplicate the certification and
   publication orchestration to use `CandidateBatch`.
2. `run_agents` and `fill_results` validate parallel Task/Check members but do
   not load certification and SourceEvent artifacts. A missing or damaged
   complete bundle can therefore reach Agent execution through those public
   paths.
3. The public `candidate_batch` constructor cannot accept pre-certification
   excluded SourceEvents even though the internal validated constructor can;
   user generators must either lose denominator evidence or instantiate the
   dataclass directly.
4. The Pylint adapter adds `swe_bench_status` to core certification evidence,
   while the latest core schema rejects that unknown key. The local schema
   counterexample reports an unknown `swe_bench_status` key, and the adapter's
   historical load path does not use the complete bundle loader.

The fourth gap is closed by moving adapter-specific counts to a
Task-Pool-bound sidecar rather than allowing arbitrary keys in core
certification evidence. The fixed Pylint example now writes its F2P/P2P
summaries and dependency evidence into that sidecar while core certification
evidence remains schema-exact.

### Implemented order and remaining adapter work

1. Completed: require a completely loaded `TaskPoolBundle` before every
   evidence-producing Runner side effect.
2. Completed: add a read-only `open/validate/use` path for a complete external
   bundle. Existing programmatic Workspace binders remain the local execution
   boundary; a binding-file CLI waits for a concrete command.
3. Completed: add one strict prepared-candidate package and a direct
   `CandidateBatch + materials + provenance -> certify -> publish` path.
4. Completed: separate Generator behavior, source protocol, observed frame,
   run, output, and adapter identities, reject unknown candidate fields, and
   migrate the existing Pylint evidence without adding a concrete Generator.
5. Deferred by this sprint boundary: choose and implement the first concrete
   classic adapter with golden fixtures, then use a genuinely different
   synthetic/base-state adapter as the second contract test before extracting
   shared adapter code.

Managed LLM Generators and large-pool certification can wait for their concrete
adapter, API, and authority. A concrete interactive adapter may later implement
one narrow episode boundary; the held-out human branch-policy pilot gates
human-proxy claims. Adapter-specific named gates do not need a generic workflow
engine, and third-party interoperability does not need a plugin host.

## Generator Validity And End-To-End Estimand Decision

### Research question and verdict

The concern in `bc-r.md` is valid: current rolling-origin evidence identifies
performance on later output from a declared Task-generation and certification
process. It does not identify performance on an unspecified population of real
repository work. This is a claim-boundary problem, not a reason to remove Task
generation from Barcarolle's scope.

The final design should distinguish three research targets:

1. **Generated-pool prediction**: does a frozen Benchmark Selection predict
   later mature, scoreable `Task + Check` output from the same declared source
   protocol, Generator behavior, and certification protocol?
2. **Generator validity**: relative to one declared observable source frame,
   what does each Generator include, exclude, multiply, transform, and make
   verifiable?
3. **Field validity**: do the benchmark's Agent levels, gaps, rankings, and
   decisions predict outcomes for a declared future population of real users
   and work?

The first is the current Selection estimand. The second belongs in Task-supply
evidence and crossed Generator experiments. The third needs prospective human
or deployment evidence outside ordinary Task Pool and Result claims. No single
MAE is a golden metric for all three.

This conclusion changes how Generator support is evidenced, not the downstream
module boundary. Runner, Selection, Reporting, and Workspace should still
consume validated data rather than Generator objects. Built-ins are direct
adapter code; third-party Generators can emit the same strict package.

### Formal target and current metric

Every external-validity claim must first declare:

- the eligible repository, user/workflow cohort, channels, and time window;
- the work-event unit and deduplication rule;
- the target weighting, such as event, developer effort, value, or risk;
- the complete tested Agent policy and the user/environment regime;
- the outcome vector, observation horizon, maturity, and missingness policy;
- the Generator set, event-to-task aggregation, and any mixture weights.

Without these choices, "real work" and "utility" are not estimands. This follows
the same estimand-first discipline advocated by
[Binette and Reiter](https://arxiv.org/abs/2406.10366) and the claim/evidence
separation in
[Measurement to Meaning](https://arxiv.org/abs/2505.10573).

For a static Generator, the observable chain is:

```text
target work population
  -> observable source frame
  -> zero, one, or several generated candidates per event
  -> certified Task/Check representations
  -> frozen Benchmark Selection
  -> Agent executions
  -> Check outcomes
```

For Agent `a`, current `future_pass_rate_mae` compares the weighted Check pass
rate on the selected historical Task/Check refs with the unweighted Check pass
rate on later mature, scoreable Task/Check refs, then averages the absolute
difference across the frozen Agent set. Its precise interpretation is:

> Generator-conditional future Task/Check prediction error on one realized
> later pool.

It includes temporal forecast error, finite-pool variation, and realized
execution variation. It is not a pure structural Selector error.
`future_coverage` is the fraction of required Result-matrix cells backed by
Results; it is not source-frame or Generator coverage. `recommendation_regret`
is likewise regret on the later generated pool, not field-utility regret.

For interactive evaluation the data-generating process is different:

```text
source session -> generated episode scenario
initial context + hidden pre-interaction state
  + tested Agent policy
  + benchmark-side user policy(history)
  -> trajectory -> final workspace -> Check + interaction outcomes
```

The value being measured is conditional on both the tested Agent and the
benchmark-side user policy. The user policy stays out of `AgentRecord`, but its
exact identity, stochastic treatment, and budget must enter an episode's
execution/cache identity.

### What is and is not identifiable

Current `SourceEventRecord` evidence is a pool-local generation-outcome ledger.
Artifact validation proves that supplied events exactly cover certification
candidates, accepted Task/Check pairs, and rejected candidates. It cannot
detect an event that the source adapter never supplied. Source-window bounds
prove time bounds, not query, pagination, channel, deduplication, or capture
completeness.

The following distinction is therefore mandatory:

- an **observed source frame** is the exact finite inventory produced by a
  declared source protocol, whose design may be a census, probability sample,
  or opportunistic sample;
- a **target work population** includes the work to which the eventual claim
  should apply.

An observed frame may be complete relative to a versioned API query while
still omitting private trackers, chat, abandoned sessions, uncommitted changes,
external systems, or users who did not opt in. Do not store an
`is_complete=true` assertion. Bind the query/snapshot receipts and state the
known blind spots.

If a fraction `c` of a finite target population is known to be represented and
utility is bounded in `[0, 1]`, the represented mean `m` supports only:

```text
target mean in [c * m, c * m + (1 - c)]
```

The interval width is `1 - c`. If `c` is unknown, current records generally
support only the trivial range. Known positive sampling probabilities can
justify design weighting, but excluded events often have no executable
outcome; inverse-propensity or learned corrections must wait for an actual
sampling design and audit labels.

An error decomposition is possible only after putting every intermediate
quantity on the same event unit, Agent policy, target weight, time, and bounded
outcome scale. Let `q0` through `q6` denote, respectively, target real-work
utility, observed-frame utility, event-normalized Generator-included utility,
task-semantic success, expected Check pass, realized later-pool Check pass, and
the frozen benchmark prediction. Only under those common definitions is the
following signed telescoping identity valid:

```text
q6 - q0
  = (q6 - q5)  conditional generated-pool prediction difference
  + (q5 - q4)  finite-pool and realized-run difference
  + (q4 - q3)  Check measurement difference
  + (q3 - q2)  task-transformation difference
  + (q2 - q1)  Generator inclusion/multiplicity difference
  + (q1 - q0)  source capture and population-transport difference
```

This labels threats; it does not make the intermediate quantities observable.
In particular, `q1` through `q4` usually need audits, bridge studies, or human
labels. Absolute error has only a triangle-inequality upper bound; MSE has cross
terms. Coverage, certification yield, and MAE are not commensurate quantities
that can be added. Opposing signed errors can cancel.

Task multiplicity also matters. If one source event yields nine tasks and
another yields one, ordinary task-level averaging weights the first event nine
times. Static adapters may keep the current one-candidate SourceEvent
projection, but their sidecar must retain common upstream event IDs and
zero/one/many derivation edges. Cross-Generator studies must report an
event-normalized view and predeclare how multiple representations combine.
Synthetic stress tasks have no natural field prevalence and stay in a
separately reported stress population unless target-derived weights exist.

### Interactive trajectories are counterfactual environments

A logged trajectory observes the real user's responses only on histories
visited by the behavior Agent. A new Agent visits different histories. Many
different user policies can reproduce the logged path perfectly and disagree
on whether a real user would clarify, correct, change scope, accept an
alternative, or abandon on those new branches. A trajectory-grounded simulator
therefore extrapolates a counterfactual policy; it does not identify one from a
single path.

The timing of hidden state is critical:

- pre-existing intent, constraints, and user traits may be fixed before the
  interaction;
- a new requirement may genuinely arrive at a later turn;
- frustration, correction, and abandonment may be caused by observed Agent
  behavior;
- a post-hoc label extracted from the completed trajectory may encode the
  behavior Agent's future actions.

[Controllable User Simulation](https://arxiv.org/abs/2605.11519) formalizes
the last failure as look-ahead bias: training turn-level behavior on post-hoc
trajectory controls couples the simulator to the data-generating Agent policy.
Its proposed remedies reinforce the appropriate contract here: use only
pre-interaction controls, or update dynamic state from the observable history
at each turn. For a black-box tested Agent, the latter does not require access
to model internals.

Consequently, human indistinguishability, style similarity, intent coverage,
greater difficulty, longer trajectories, and more corrections are diagnostics,
not proof of a valid human proxy. User Correction and solve rate are outcomes
under a particular simulator treatment and are not comparable across simulator
versions without calibration.

### Primary-source evidence

| Study | Evidence that matters here | Claim limit |
| --- | --- | --- |
| [SWE-Together](https://arxiv.org/abs/2606.29957) | 109 executable tasks were obtained from 11,260 logged sessions, a deliberately high-precision 0.97% conversion. The benchmark preserves multi-turn feedback and reports final correctness, stable solving, intent coverage, and user correction. | Conversion is not target-population coverage. Filters favor public, recoverable, locally verifiable code-changing sessions and exclude substantial external-state work. The reference patch passes the paper's threshold on about 78% of the 93 tasks with extractable patches, showing that trajectory-to-oracle transformation itself is lossy. |
| [SWE-INTERACT](https://arxiv.org/abs/2606.30573) | Recasting 75 selected static tasks as progressive interaction exposes another capability axis and substantially changes cost, length, and success. | It is an interaction treatment over selected benchmark tasks, not a real-work source-frame sample. In 287 failed trajectories, about 12% of assigned semantic failure labels were missing user requirements, likely simulator-caused false negatives. Changing only the simulator model changed interaction length by roughly 1.5–2x and changed Agent success. |
| [SWE-chat](https://arxiv.org/abs/2604.20779) | Real opt-in Coding Agent sessions show understanding, collaboration, correction, and no-final-Agent-code work that patch-only benchmarks omit. | The authors limit generalization to public-repository early adopters and note that abandoned or wholly rejected outputs usually leave no committed log. It is behavioral evidence, not a source-frame census. |
| [SimulatorArena](https://arxiv.org/abs/2510.05444) and [Quantifying Simulator Utility](https://arxiv.org/abs/2605.09808) | Human-profile or human-utterance-grounded simulators can outperform simple role play in narrow domains; the latter study's simulator-trained assistant improved in a real-user study. | Positive transfer is domain- and purpose-specific. The utility study also warns that the simulator faces distribution shift as the assistant policy changes, and no single utterance-level fidelity metric reliably predicts downstream usefulness. |
| [Lost in Simulation](https://arxiv.org/abs/2601.17087) | On a retail agent benchmark, changing only the user LLM moved one Agent's success rate by up to about nine points; simulated-to-human calibration error varied by task difficulty and user group. | This is not a Coding Agent ranking study, but it directly refutes treating one simulator configuration as a neutral measurement device. |
| [Mind the Sim2Real Gap](https://arxiv.org/abs/2603.11245) | A study with 451 humans, 165 tasks, and 31 simulators found the best simulator's User-Sim Index at 76.0 versus a 92.9 human reference. Most general LLM simulators produced success above the 63.6% human baseline, up to 77.8%, by being more cooperative and informative. | The study is on a task-oriented customer-service setting, so its numbers do not transfer to coding. Its design does support the need for direct human calibration and multidimensional outcomes. |
| [PULSE](https://arxiv.org/abs/2510.09801) and [RealHumanEval](https://arxiv.org/abs/2404.02806) | Prospective human evaluation can disagree with static benchmark rankings or effect sizes. PULSE uses conversation-level randomized Agent variants; RealHumanEval found benchmark improvements associated with productivity but not proportionally. | Satisfaction and subjective preference are not complete utility. Field evidence still needs an explicit population, treatment, outcome vector, missingness rule, and time horizon. |

The literature supports three increasingly strong statements: interaction form
changes capability and failure modes; real-user grounding can improve a
simulator in a specified domain; only held-out human or field comparisons can
establish the external validity needed for real-work claims.

### Minimal architecture decision

Keep the existing eight modules and the immutable Task Pool boundary. Add
scientific evidence identities, not a Generator platform.

The provenance must separate two semantic axes:

1. **Generator behavior**: adapter family/version, implementation, stable
   behavior config, and any model, prompt, tool, learned-state, sampling,
   retry, and seed policy that can change task transformation.
2. **Source observation**: a stable source protocol plus the per-run observed
   frame: repository/channel scope, query/dataset revision, window,
   deduplication/sampling design, exact observed event inventory, observation
   time, and sanitized capture receipts.

The exact frame digest changes with inventory; its source-protocol digest is the
stable behavior compared across windows. Generator behavior, source protocol,
frame inventory, run authority, and outputs must not share one opaque digest.
The smallest implementation can use the already planned generation-provenance
manifest with independently digested sections and one Task-Pool-bound
ref/digest. It does not yet need a Generator registry, plugin lifecycle,
general `GenerationRun`, or separate service. If two concrete adapters need to
reuse and compare one frame artifact, promote that manifest section to a small
shared record without changing its semantics.

When a Task Pool binds an observed frame, its Generator outcome ledger must
cover every frame event as accepted, certification-rejected, or
pre-certification excluded. A pool without a frame can still be validated,
executed, selected, and reported, but it supports only pool-conditional claims.
The frame receipt, not a Boolean, records whether the input was a census,
probability sample, or opportunistic sample.

Reporting needs a claim lattice. Bundle consistency, Result-cell completeness,
generated-pool prospective prediction, observed-frame inclusion, Generator
bridge validity, Check/semantic calibration, and prospective field calibration
are separately supported axes. Some studies need several axes at once, but no
total ordering is valid: for example, a source-authoritative frame does not
imply a valid Check, and a calibrated Check does not imply representative
source capture. The former `task_pool_coverage` claim is now
`task_pool_bundle_internal_consistency`; it validates only supplied artifacts
and links. Generator behavior/protocol equality remains a necessary
strict-prospective gate, not evidence of temporal measurement invariance.

Do not widen current static `Task`, `Check`, or `Result` for interactive data.
When a concrete interactive source is selected, its adapter may add a narrow
episode contract:

- an episode specification binding initial solver-visible material, base state,
  hidden pre-interaction intent, step-wise user-policy state, simulator
  behavior, disclosure/termination rules, interaction budget, and final Check;
- an episode result binding exact Agent and simulator identities, stochastic
  seed/replicate, sanitized trace digest, separate Agent and simulator
  usage/cost, interaction outcomes, and the final workspace-verification
  Result.

The current one-shot subprocess invocation is not this contract. The first
episode adapter must supply a persistent turn protocol without changing the
tested Agent's ownership of model, harness, prompts, tools, and edit loop.
There is no reason to build generic event sourcing or a simulator platform.

Field outcomes do not enter `ResultRecord` unless they correspond to the exact
Task/Check execution cell. Human time, satisfaction, abandonment, code
survival, regression, and real-work completion belong in a private experiment
artifact with a sanitized report. This avoids turning Result Store into a
telemetry or online-experiment system.

### Ordered validation program

1. **Observed-frame static slice.** With the first SWE-bench adapter, freeze one
   operational frame, source receipts, common event IDs, full funnel, and
   zero/one/many derivation evidence. Randomly audit accepted, excluded, and
   certification-rejected events. This validates the evidence contract, not
   real-work coverage.
2. **Crossed Generator bridge.** On the same frame, run at least two
   Generator approaches and every frozen Agent treatment. Block analysis by
   upstream event, report task-level and event-normalized outcomes, inspect
   Generator-by-Agent rank interactions, and audit alternative correct and
   known-wrong patches to estimate task-semantic and Check error.
3. **Generator/time bridge.** Run old and new Generator behaviors on both an
   old and a later frame. This `2 x 2` design separates version drift, source
   population drift, and their interaction. Merely comparing old/old with
   new/new cannot.
4. **Interactive branch-policy pilot.** Before interpreting simulator evidence
   as human-interaction evidence, choose 10–20 scenarios and construct held-out
   correct, mistaken, clarification, partial, alternative, and abandonment
   branches. Compare trajectory-grounded, deterministic
   progressive-disclosure, and generic role-play policies against responses
   from the original user or qualified developers. Predeclare response-action
   macro-F1, hidden-fact disclosure precision/recall, correction, no-op and
   abandonment calibration, simulator-model sensitivity, and Agent-gap/rank
   agreement. Support a human-proxy claim only if the grounded policy improves
   on simple baselines on held-out branches and does not materially reverse
   predeclared Agent-gap directions relative to human responses. This is a
   claim gate, not field-validity evidence.
5. **Prospective field calibration.** Freeze the benchmark predictions first,
   then collect later eligible real work. Randomize the complete Agent treatment
   when feasible and analyze intention-to-treat, including abandonment and
   missing logs. Otherwise report prediction calibration or association, not a
   causal Agent effect. Keep completion, human effort, correction, cost,
   satisfaction, regression/security, and later patch survival as separate
   outcomes unless stakeholders predeclare a scalar utility.

Multiple Generators should be reported separately by default. Their union can
expand support and expose disagreement, but it does not identify target mixture
weights. Learn or optimize a mixture only after a target frame provides overlap,
positivity, event-level weights, and a prospective outer holdout. A
Generator-diverse but jointly biased mixture remains biased.

### Explicit non-goals

- no universal "real work" population or scalar utility in core records;
- no automatic Generator mixture or embedding-distance calibration service;
- no claim that a harder, more human-like, or lower-divergence simulator is a
  better field proxy without downstream evidence;
- no raw private trajectory store, user telemetry platform, or online
  experiment service in Barcarolle;
- no inverse-propensity, doubly robust, or learned inclusion correction before
  sampling probabilities, support, and audit outcomes exist;
- no generic interactive platform or human-proxy claim; one concrete adapter
  must establish the required turn boundary, and the branch-policy pilot must
  calibrate it before human-interaction interpretation.

## Verification Snapshot

The 2026-07-23 implementation sprint used no network, paid call, or benchmark
Agent run.

- `uv run ruff check .`: passed.
- `uv run pyright`: zero errors.
- `uv run pytest -q`: 838 passed, 2 skipped.
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
- The calibrated full-signal Cremona scan covers 34 executable first-party
  Python files and reports 115 hotspots (0 now / 37 soon / 78 monitor), nine
  `investigate_soon` files, and no dead-code candidate. No baseline exists, so
  the scan establishes routing state rather than a regression trend.

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
| RI-034 | P2 | calibrated static audit plus temporary full-suite branch coverage; active after ninety-five evidence-boundary slices | Long evidence validators and orchestrators remain navigation candidates. The maintained 34-file scan is `strained`/`investigate_soon`, with full signal health, 115 hotspots (0 now / 37 soon / 78 monitor), nine investigate-soon files, and no dead-code candidates. Earlier slices extracted characterized phase boundaries and removed placeholder, coercion, truthiness, and duplicate-validation controls without changing the public module vocabulary. No baseline exists, so the scan cannot establish trend. | Continue only from a reproduced evidence-boundary failure or measured maintenance bottleneck. Keep explicit orchestration surfaces when an extraction would create one-use forwarding objects. Do not split by file length, add a validation framework, or make Cremona a gate. |
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
| RI-046 | P1 | reproduced, resolved 2026-07-24 after audit refinement | A later Task Pool carried creation time and member digests but not the source interval it had observed, so it could not prove complete coverage of a planned future window. Treating event inventory as generator configuration would also make every later observation look like behavior drift. The first repair unnecessarily required every later pool to repeat the earlier window. | Task Pools persist canonical source-window bounds, reject accepted or certified events outside them, and bind the bounds into pool identity. Generator digest is behavior-only; SourceEvent/Task/Check digests bind inventory. Prospective replay requires the later window to cover the complete declared future interval; the pool may be incremental or cumulative, and overlapping same-ID Task/Check records cannot drift. |
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
| RI-113 | P1 | maintainer decision revised 2026-07-24 | superseded by RI-120 through RI-153; common boundary complete | The earlier stop rule treated selection of one Task Generator as a prerequisite to any Task-supply work. The final architecture is now explicit: several built-in and user Generators share one data handoff, while a user-maintained Task Pool and user-supplied Results have separate validated paths. Generator behavior, observed source frames, and field validity are separate scientific evidence axes. | The common data and trust boundaries are complete without choosing or implementing a concrete Generator. Resume only from an actual source/adapter decision; defer LLM execution and large-pool certification until that adapter and authority exist. A narrow interactive adapter may be implemented from a concrete source, but human-proxy claims require the branch-policy pilot and real-work claims require prospective field evidence. Do not build a generic Generator runtime, simulator platform, or composite storage layer. |
| RI-114 | P2 | PR-review reproduced, resolved 2026-07-23 | Multi-file paid-harness evidence retained only a sorted multiset of content hashes. Swapping the executable and helper bytes therefore kept both the harness-content digest and unchanged command paths valid, allowing paid preflight to accept different code at the executable path. | `harness_content_digest` now hashes canonical resolved-path/content-digest pairs in path order. A red preflight regression swaps two declared files and proves the endpoint/harness proof fails. The same-mode search found no other endpoint-harness content digest path. |
| RI-115 | P1 | external-review hypothesis, reproduced and resolved 2026-07-23; PR-review gap closed 2026-07-24 | `JSONValue = Any` gave Pyright no recursive payload contract. Direct validators accepted unsupported objects in Check limits, Selector validation could raise while digesting them, tuple payloads could persist as lists, and cyclic payloads could recurse indefinitely. Finite execution states were also plain strings; the first implementation checked a `Literal`'s scalar type but not membership during JSONL loading. | `JSONValue` is now recursive; shared `Literal` aliases cover finite Result, Workspace, Check, and matrix states. Latest-schema conversion enforces each Literal member set, while domain validators own valid cross-field combinations. Canonicalization rejects cycles and unsupported leaves, and the three arbitrary JSON payload boundaries reject tuples and non-finite numbers before digesting. Fourteen new or strengthened contract cases cover the counterexamples. |
| RI-116 | P1 | external-review hypothesis, reproduced and resolved 2026-07-23 | Workspace and Task Pool derived stable benchmark labels by searching exception-message substrings. A changed Git or preparation message could silently reclassify the same failure. | Missing repository binding and verifier preparation now use thin `ValueError`-compatible typed failures carrying stable labels; checkout uses one internal typed failure. Workspace and Task Pool dispatch by type and fall back to generic labels for unexpected errors. No broad exception framework or cross-module taxonomy was added. |
| RI-117 | P1 | code-confirmed, resolved 2026-07-24 | The repository had no PR workflow and Pyright used `basic` over only `src`, so local commands were documented but not continuously exercised and executable examples/migrations were outside the static contract. | The minimal `quality` workflow performs `uv sync --frozen`, Ruff, Pyright, and the full suite with pinned actions, read-only permissions, cancellation, and a timeout. Pyright now uses `standard` over `src`, `examples`, and `scripts`; target-repository hidden-check fixtures are excluded, and the optional SWE-bench adapter suppresses only unavailable local dependency reports. Formatting and coverage remain excluded. The first `main` run succeeded, and the active `main-quality` repository rule requires its stable `quality` status. |
| RI-118 | P2 | external-review example, resolved 2026-07-23 | A Runner ordering test patched `_resolved_task_pool_candidate_batch`, coupling the contract to a private helper name. | The test now supplies a nonexistent public import path and asserts malformed configs fail before that path is read or the artifact directory is created. Other private patches remain until a concrete refactor or brittle failure shows that replacing them improves a public contract. |
| RI-119 | P2 | calibrated structural audit and maintainer decision | active routing policy; no broad split | File length and Cremona hotspots identify navigation candidates but do not by themselves prove a responsibility boundary. The 34-file full-signal scan reports `strained`/`investigate_soon`, 115 hotspots (0 now / 37 soon / 78 monitor), nine investigate-soon files, and no dead-code candidates. With no baseline, it cannot establish trend. A separate `tests/test_runner.py` scan labels 18 pytest tests/helpers as high-confidence dead code because Vulture cannot see pytest discovery; that false signal alone raises the file to `investigate_now`. | Keep the current public module vocabulary. Split an internal submodule only when one coherent responsibility can move with a public characterization test or when measured change coupling/navigation cost justifies it. Default Cremona scope, exclusions, history window, and bulk-commit cutoff are stored in `pyproject.toml`; tests are scanned only for a concrete maintenance question and Vulture findings there require pytest-aware confirmation. Do not make Cremona a CI gate or initialize a baseline yet. |
| RI-120 | P0 | resolved 2026-07-24 | complete | Public `run_agents` and `fill_results` accepted a Task Pool record plus parallel Task/Check values and validated only those members. Certification and SourceEvent artifacts could be missing or damaged while Agent execution and Result writes still began. | High-level execution, fill, evaluation, scoring, and selection paths now consume or load a complete validated `TaskPoolBundle` before repository, Agent, cache, or Result side effects. Low-level member operations remain internal characterized steps. |
| RI-121 | P0 | resolved 2026-07-24 | complete | Standard Runner generator identity hashed only mode and source family, allowing behaviorally different generators to collide. The Pylint adapter included inventory-dependent evidence, causing unchanged behavior over a later window to split. | One Task-Pool-bound generation manifest independently digests stable Generator behavior, source protocol, observed frame, run authority, outputs, and optional adapter evidence. A declared frame window must exactly match its Task Pool source window. Strict prospective comparison uses behavior plus protocol, not frame/run/output inventory. Regression tests cover behavior stability and behavior drift. |
| RI-122 | P0 | resolved 2026-07-24 | complete | Adapter-specific fields could not enter the fixed generic certification schema. | The prepared package and generation manifest carry an optional content-digested adapter sidecar while certification evidence remains fixed. The full prepare/certify/publish/open path validates the sidecar. The existing Pylint pilot now stores its dependency artifact in that sidecar and reopens the complete bundle before paid stages; no adapter-specific field entered the core schema. |
| RI-123 | P1 | resolved 2026-07-24 | complete | `CandidateBatch` was in-memory-only, excluded SourceEvents could not enter through its public constructor, material mappings lived outside a portable handoff, and candidate import ignored unknown fields. | `candidate_batch` accepts candidates plus exclusions. A strict versioned prepared-candidate package carries exact candidates, exclusions, certification material refs/digests, optional generation provenance, frame inventory, and adapter evidence. Generic packages are producer-attested external input and cannot self-claim a Barcarolle-managed run or source-authoritative observation. Runner certifies and publishes them without executing Generator code; unknown candidate fields fail. |
| RI-124 | P1 | resolved 2026-07-24 | complete at programmatic boundary; binding-file CLI deferred | A complete user-maintained Task Pool lacked a named read-only open/validate path. Execution also needs machine-local repository, Check, hidden-material, and environment bindings. | `open_task_pool_bundle` reads exactly one canonical manifest, validates the complete bundle in place, and preserves bytes and timestamps; `barcarolle task-pool validate` exposes the operation. Existing Workspace context binders prove local repository, command, manifest, and hidden-material digests before Agent execution. A separate binding-file CLI is deferred until a concrete execution command needs it. |
| RI-125 | P1 | primary-source audit and maintainer decision | future-work; concrete source decision required | No core built-in Generator exists; the Pylint pilot is a fixed experiment adapter. Paper names also hide whether Barcarolle imports a dataset, wraps official code, reimplements a published paradigm, or runs a native research Generator. | When Generator work resumes, choose an actual locally/API-available source and implement one explicit adapter module, not a registry. State whether it imports a dataset, wraps official code, or reimplements a paradigm; bind revision and golden fixtures, emit the prepared package, and partition multi-repository sources into one-repository pools. Choose the second adapter to test a genuinely different material/lineage contract before extracting shared code. |
| RI-126 | P1 | SWE-smith counterexample | future-work with first concrete synthetic/base-overlay adapter | Synthetic Generators can start the solver from `upstream commit + generated bug overlay`; their published `patch` may introduce the bug rather than repair it, and combined tasks have multi-parent lineage. Treating the upstream commit as `Task.base_commit` would identify the wrong workspace. | Prefer the boring adapter-owned solution: materialize the final solver state as an immutable full Git commit and retain upstream/overlay/derivation evidence in a sidecar. Add a core commit-plus-overlay snapshot only after a concrete adapter proves materialization insufficient. Project exact lineage to the existing conservative dependency cluster for Selection. |
| RI-127 | P1 | primary-source, identifiability, and SWE-Together/SWE-Interact audit | future-work; concrete adapter and human-claim gates are separate | Current Workspace writes one static task, invokes one static Agent harness, and captures one final diff. Interactive benchmarks need a persistent user-policy environment. One logged trajectory observes human responses only on the behavior Agent's path, so a simulator's responses to a new Agent are counterfactual extrapolations. Post-hoc trajectory labels can also encode future Agent actions. Encoding the simulator inside Agent identity would mix treatments, usage, cost, and cache identity. | With a concrete source, implement at most one narrow episode specification/result contract with pre-interaction versus dynamic state, simulator behavior and seed, disclosure/termination, persistent turns, separate Agent/simulator usage and cost, sanitized trace, final Check, and final workspace Result. Treat results as simulator-treatment-conditional. Run the held-out human branch-policy pilot before claiming that policy represents human interaction. Do not add a generic stage graph, event-sourcing framework, or simulator platform. |
| RI-128 | P1 | policy-confirmed | future-work; reopen with the first managed LLM generator | Built-in SWE-smith, SWE-Bench++, or SWE-Future variants may make paid evidence-producing LLM calls. A general subprocess cannot prove endpoint, authority, prompt/model identity, retries, or spend, and external generator output cannot be upgraded to managed evidence by import. | Apply the existing paid endpoint, immutable identity, authorization, reservation, and sanitized-artifact principles inside each concrete adapter. Persist their digests in generator provenance. Do not create a generic model service; externally run generators remain producer-attested data unless separately replayed. |
| RI-129 | P2 | code-confirmed and scale hypothesis | future-work; measurement required | Task Pool certification is serial and publishes only after the full batch. Large classic pools may lose a long run's progress on interruption, but no current measured campaign establishes the need for streaming, parallelism, or a checkpoint protocol. | After a concrete adapter produces a measured long-running certification workload, add the smallest resumable single-writer checkpoint keyed by exact candidate and config identity. Reuse RI-033's bounded-concurrency gate; do not add streaming or parallel certification from anticipated scale alone. |
| RI-130 | P1 | research-design and estimand audit | future-work; reopen after the first classic built-in exposes a measured failure | Sharing an intake contract does not establish that a Barcarolle-native Generator improves on a classic paradigm. Without a frozen observed frame, common upstream event identity, event weighting, zero/one/many derivations, compute budget, and downstream outcome, better yield can mean easier, multiplied, leaked, or less representative tasks. Task-level comparisons can overweight events that produce more variants. | For each native Generator, predeclare the targeted classic failure, same-frame classic baselines, event aggregation/weights, LLM/compute budget, training cutoff when learned, ablations, funnel, later invalid rate, leakage/dependence, semantic/Check audit, diversity, difficulty mix, and generated-pool predictive error. Run crossed Generator-by-Agent analysis with event blocking and both task-level and event-normalized results. Add only the algorithm-specific training code the first Generator needs. |
| RI-131 | P0 | resolved 2026-07-24 | complete | External Results could self-declare old availability and backfill Selector history without authority or import-time evidence. | `ResultRecord` now distinguishes managed and external-attested evidence, binds source manifest/import time/source availability/policy, and includes evidence identity in Result record identity while leaving execution cache identity unchanged. Import-time floor is the default; producer-attested history is explicit and Reporting labels its claim limit. |
| RI-132 | P1 | resolved 2026-07-24 | complete | Pointing Result Store at a user JSONL risked writing into that source and provided no admission receipt. | `import_result_bundle` first validates the complete Task Pool and source manifest, then records a decision for every source row after authority, membership, Agent/config, and Task/Check admission. It normalizes admitted records into the local append-only store and writes one immutable receipt. Source, local store, and receipt roots cannot alias, including through hardlinks. Receipt replay is a read-only verification with no empty-store side effect, and the source remains byte-identical. A mounted overlay remains unjustified. |
| RI-133 | P0 | resolved 2026-07-24 | complete | Cache resolution silently used the first Result when equal cache identity had different execution evidence. | Import rejects ambiguous incoming groups and local conflicts with explicit receipt reasons before pricing or policy filtering. Cache, pre-origin resolution, and Reporting claims fail on different execution digests under one cache identity; identical executions choose the lowest canonical Result ID independent of JSONL order. Same execution may retain pricing/evidence views. Intentional replicates must carry distinct frozen stochastic/observation-slot identity. |
| RI-134 | P0 | resolved 2026-07-24 | complete | Public lazy fill accepted an in-memory Selection without proving durable upstream evidence. | `fill_results` and `prepare_evaluation_cells` validate the complete bundle, reload and deterministically replay the persisted Selection, Origin, SelectorInput, FeatureSnapshot, Selector, pre-origin Results, and Agent identities before cache access. Fill reuses the shared cell resolver, executes only selected misses, reprices exact hits, and persists an `EvaluationCellSet`. |
| RI-135 | P1 | resolved 2026-07-24 | complete | Multi-origin evaluation reloaded Result Store per origin, allowing one operation to see changing physical inventories. | `evaluate_selectors` performs one locked physical read through the maximum cutoff, releases it, and derives each origin's filtered, conflict-checked immutable view from that tuple. SelectorInputs continue to freeze exact Result IDs/digests. |
| RI-136 | P0 | resolved 2026-07-24 | complete | `task_pool_coverage` named supplied-bundle validation like a population-coverage claim. | The only latest name is `task_pool_bundle_internal_consistency`; the old name is rejected rather than aliased. It proves complete artifact and cross-record consistency only. Frame, Generator bridge, Check/semantic, and field claims remain separate lattice axes. |
| RI-137 | P0 | resolved 2026-07-24 | complete v1 | SourceEvent evidence lacked an independently frozen source protocol and frame inventory. | Optional generation provenance independently digests `generator_behavior`, `source_protocol`, `observed_frame`, `run`, and `outputs`; Task Pool binds stable behavior/protocol identities. A declared frame requires normalized authority/receipt, window, revision, blind spots, exact sorted inventory, exact SourceEvent coverage, and observations no later than pool creation. Producer attestation remains distinct from source authority; no `is_complete` assertion exists. |
| RI-138 | P1 | formal multiplicity counterexample | infrastructure complete; concrete bridge study deferred | One core SourceEvent still binds at most one candidate, while real adapters may have zero/one/many derivations and shared upstream identities. | The strict package supports an adapter evidence sidecar for common upstream IDs and derivation edges without changing downstream modules. Core v1 deliberately retains its simple zero/one projection. A concrete bridge must report task- and event-normalized outcomes; promote a shared many-to-many record only after two adapters prove it simpler. |
| RI-139 | P1 | primary-source and causal-identifiability audit | future-work; external experiment rather than core service | Current generated-pool MAE, conversion yield, distribution similarity, difficulty, and human-like language cannot establish benchmark calibration to future real work. Logged field outcomes are also policy-selected: abandonment and missing logs are informative, and stronger Agents may change which work users attempt. | Define a prospective field protocol per campaign: freeze predictions and eligible population first; randomize the complete Agent treatment where feasible; analyze intention-to-treat with user/event clusters, missingness, and future holdout; otherwise label results predictive/associational. Report completion, human effort, correction, cost, satisfaction, regression/security, and patch survival separately unless stakeholder weights are predeclared. Keep raw field evidence private and import only sanitized reports, not a telemetry platform. |
| RI-140 | P2 | mixture identifiability counterexample | future-work; no automatic mixture before outer calibration | Several biased Generators can share one blind spot. Their task counts do not reveal target mixture weights, and overlap/multiplicity can cause rank reversal or Simpson effects. Cross-Generator agreement is robustness evidence, not proof of real-work validity. | Report Generator strata separately by default. Consider a weighted union only with a declared target frame, common event IDs, overlap and positivity, event-level target weights, calibrated semantic/Check evidence, and a prospective outer holdout. Do not learn weights from the same future Agent outcomes used to evaluate the mixture. |
| RI-141 | P0 | independent-audit counterexample, resolved 2026-07-24 | complete | Result IDs were caller-controlled labels. An otherwise valid Result could retain an arbitrary or stale ID, so semantically identical evidence could fork identity and migrations could preserve IDs that no longer matched the latest schema. | Records derives and validates the canonical Result ID from execution, scoring, and evidence digests. All Result migrations recompute it, reject duplicate migrated identities, and require rebuilding FeatureSnapshots, SelectorInputs, Selections, fitted Selectors, CellSets, matrices, and metrics that bind changed Result IDs/digests. |
| RI-142 | P0 | independent-audit counterexamples, resolved 2026-07-24 | complete | Receipt replay could create an empty Result Store, import paths could alias their immutable source through hardlinks or a nested source root, and local load/query paths did not uniformly fail closed on invalid rows. | Result admission resolves file identity and source-root containment before writing, computes the implementation-owned first observation time only for a new import, verifies existing receipts against a read-only store view, and creates no store when every first-import row is rejected. Local load/append validates every Result before query or mutation. |
| RI-143 | P1 | PR-review counterexample, resolved 2026-07-24 | complete | Generation provenance ordered a run internally and validated each frame-event timestamp, but did not compare either with Task Pool creation. A fully redigested bundle could therefore claim a run completion or source observation from after the immutable pool already existed. | Complete-bundle validation now requires `run.finished_at <= TaskPoolRecord.created_at` and every `ObservedFrameEventRecord.observed_at <= TaskPoolRecord.created_at`. Public red cases rebuild every affected digest and prove both contradictions fail. |
| RI-144 | P2 | PR-review counterexample, resolved 2026-07-24 | complete | A fully redigested Task Pool with no generation manifest could retain `generator_config_digest`, while the equivalent orphaned source-protocol digest already failed at complete-bundle validation. Reporting could therefore expose an unsupported Generator-behavior identity for a user-maintained pool. | The Records contract now requires both Generator-behavior and source-protocol digests to be null when the provenance binding is absent. Task Pool construction keeps the pre-binding record neutral and attaches both identities only with the complete manifest. Fixture-only examples drop orphan identities; the fixed Pylint pilot uses a real manifest and adapter sidecar. Two public red cases cover the symmetric orphan identities. |
| RI-145 | P1 | PR-review counterexample, resolved 2026-07-24 | complete | Frame events were bounded by Task Pool creation but not by their own generation run. A fully redigested manifest could therefore claim outputs from an observation recorded after `run.finished_at`, even though the run binds the input snapshot, frame inventory, and outputs. | Both prepared-package admission and complete-bundle validation now require every frame-event `observed_at <= run.finished_at`, so invalid chronology fails before certification as well as on replay. Two public red cases rebuild the event, inventory, manifest, and Task Pool digests. |
| RI-146 | P1 | PR-review counterexample, resolved 2026-07-24 | complete | Removing the Pylint pilot's unsupported orphan Generator digest also removed its immutable dependency-evidence binding. If dependency evidence and trusted patches changed together, local replay could accept a different dependency claim before a paid cell. | The pilot now binds stable adapter behavior separately from run-specific dependency evidence and F2P/P2P summaries in a generation manifest and `adapter-evidence.jsonl`; core certification evidence remains schema-exact. Preparation validates the complete bundle. Resume opens it before other campaign work, verifies current implementation against the behavior section, and parses the dependency object from that validated snapshot. Changing dependency evidence changes run/provenance/Task Pool identity but not behavior identity. Public cases cover identity separation, paid-path routing through complete open, and sidecar drift. |
| RI-147 | P2 | PR-review counterexamples, resolved 2026-07-24 | complete | Persisted `EvaluationCellSet` identity omitted both requested scoring configuration and the benchmark-invalid reuse flag. A later lazy fill could therefore return old Result IDs, costs, pricing version, or benchmark-invalid reuse even though the caller requested a different resolution policy. | CellSet identity and reusable-set validation now bind the scoring-config digest and exact cache-policy digest. Changing either creates a new resolution view: pricing changes reuse and reprice the same paid execution without another Agent call, while a stricter benchmark-invalid policy resolves the cell again. Repeating an unchanged policy still resumes the frozen CellSet. Two public red-green cases cover both policy axes. |
| RI-148 | P1 | PR-review counterexample, resolved 2026-07-24 | complete | The fixed Pylint pilot wrote and reopened `records/task_pool.jsonl`, but the complete-bundle loader intentionally accepts only the canonical basename `task-pool.jsonl`. Preparation could succeed while preflight and every later stage failed before replay. | One shared adapter constant now drives both publication and open at `records/task-pool.jsonl`. The existing complete-open regression asserts that public filename before simulating invalid bundle content, and the same-mode search found no remaining underscore-named manifest in the Pylint adapter. |
| RI-149 | P2 | PR-review counterexample, resolved 2026-07-24 | complete | Generation provenance was attached after `freeze_task_pool` had already derived the automatic Task Pool ID. Binding changed the manifest, stable Generator identities, and Task Pool digest but preserved that pre-binding ID, so distinct immutable generated pools could share one semantic ID. | One direct binding function now clears any pre-binding ID, attaches the complete generation manifest identity, derives the final content Task Pool ID, and only then self-digests the record. Both generic prepared-package publication and the fixed Pylint adapter use this path. Public red cases prove that the final ID matches the complete bound record and that different run-specific adapter evidence yields different Task Pool IDs. |
| RI-150 | P2 | PR-review counterexample, resolved 2026-07-24 | complete | Task Pool and claim-boundary reports enumerated the generation manifest but omitted its observed-frame inventory and adapter-evidence sidecar. A report could therefore support complete-bundle consistency while its Artifact Paths section omitted evidence required to reproduce that validation. | The shared reporting path now reopens each validated generated bundle and adds the manifest-bound event inventory and adapter sidecar refs to both report surfaces. Invalid bundles retain their limitations without promoting unvalidated nested refs. One public red-green report contract covers both entry points and both optional artifacts. |
| RI-151 | P2 | PR-review concurrent-import counterexample, resolved 2026-07-24 | complete | Two workers could read the same Result Store and absent receipt before either acquired the append lock, choose different first-observation times, and then append distinct evidence views. One receipt publication could fail or be replaced after its Result was already durable, leaving a reported failed import with an unreceipted row. | External import now acquires deterministic store- and receipt-scoped POSIX coordination locks before reading either local state and holds them through Result admission and immutable receipt publication. Static source, authority, and path validation still precede local lock artifacts. A public two-worker red-green regression proves both calls return one receipt, one observation time, and one local Result. |
| RI-152 | P1 | PR-review chronology counterexample, resolved 2026-07-24 | complete | Prepared-package and complete-bundle validation ordered a frame window internally and bounded frame observations by the generation run, but did not require `observed_frame.window_end <= run.finished_at`. A run could therefore claim an exact source inventory through a date after it had already completed, and strict-prospective evaluation could treat that unsupported end as future-window coverage. | The one shared window/run check is applied at both prepared-package admission and complete-bundle replay. It requires the declared frame window to end no later than the bound generation run, while retaining the separate event-observation and Task Pool creation checks. Two public red-green contracts cover both evidence boundaries; no new provenance field or temporal framework was added. |
| RI-153 | P2 | PR-review durability counterexample, resolved 2026-07-24 | complete | Result rows were fsynced before import success, but the immutable receipt used atomic replace without syncing either the file or parent directory. Power loss could therefore leave durable admitted rows without their receipt; an all-rejected import had no local Result from which to recover its first observation time. | Receipt publication now fsyncs the receipt file and parent directory before returning, including when retrying an identical existing receipt after a prior interrupted sync. One public all-rejected red-green contract proves both durability calls occur. Generic JSONL writing remains lightweight; Task Pool publication and Result append retain their existing explicit durability boundaries. |
| RI-154 | P1 | measured and resolved 2026-07-25 | complete | The generic prepared-package boundary had no second concrete classic-source adapter or larger certified pool, so its portability and the proposed main model comparison were untested. | A thin static SWE-bench adapter freezes one exact repository slice and OCI manifests, prepares strict material/provenance/dependency evidence, and certifies through the ordinary Task Pool path. All 75 SymPy Verified candidates passed fresh base-fail/reference-pass certification and published a reopenable pool with 75 Tasks, 75 Checks, and 54 reference-patch path-overlap clusters. |
| RI-155 | P1 | reproduced, resolved 2026-07-25 | complete | Resolving a virtual-environment Python symlink before persisting a harness command replaced the environment entry point with the base interpreter. The prepared package and campaign could pass path existence checks but lose installed harness dependencies. | Static preparation, Pylint replay, and campaign launch now preserve the absolute venv entry-point path without dereferencing it. Regression coverage binds the actual command identity. |
| RI-156 | P0 | reproduced and resolved 2026-07-25 | complete | Proxy model metadata advertised OpenAI endpoint support for DeepSeek V4 Pro and Gemini 3.1 Pro, but Codex CLI could not complete their Responses streams. Treating model inventory as harness compatibility caused an Agent-invalid first cell and prevented the paired schedule from observing its second Agent. | Keep exact invalid Results as protocol evidence only and require one frozen single-Agent canary before paired calibration. Mini was scoreable and admitted; Claude, DeepSeek, and Gemini were Agent-invalid with empty usage and excluded without interpreting hidden capability. |
| RI-157 | P1 | reproduced, resolved 2026-07-25 | complete | The paired-replicate schedule was unnecessarily used as a protocol canary, authorizing 24 cells and coupling observation of the second candidate to the first candidate's scoreability. | Reuse the existing bound-input and ordered-cell record with a separate `single_agent_canary_schedule_v1`: one Agent, one Task, one Runtime slot, one replayable cell. The campaign ledger selects a matching canary schema. No registry, workflow layer, or duplicate schedule fields were added. |
| RI-158 | P0 | reproduced, resolved 2026-07-25 | complete | Immediate gateway token-balance before/after deltas did not equal individual call cost because balance updates were delayed across adjacent calls; one successful Result was already durable when the post-call balance query returned 429. Calling that delta per-call cost would misattribute evidence, while failing before the study ledger write omitted the exact Result. | Per-call accounting now selects sanitized gateway token-log rows by bound model and Result time and requires their prompt/completion totals to equal the Result exactly. Log quota is attributed cost; eventual balance is only the global guard and aggregate reconciliation. Metadata uses bounded retry, paid calls are study-serialized, Result recovery never retries a cell, and the local guard uses the larger of attributed logs and global movement. The first eight calls reconciled 1,195,672 attributed points exactly to the later global movement. |
| RI-159 | P1 | experiment-needed; active 2026-07-25 | paid study | Barcarolle lacked empirical evidence for a default model portfolio and for the stability of one cached Result per Agent×Task. | Complete the frozen Pylint calibration, select two configurations by the predeclared performance/cost/disagreement rule, run the 75-Task SymPy paired main comparison plus three-run repeats on 30% of Tasks, and report dependency-cluster and Agent×Task-cluster uncertainty. Historical Results remain retrospective and cannot support prospective Selector MAE. |
| RI-160 | P2 | measured 2026-07-25 | justified future work | Full static certification is serial and has no resumable candidate checkpoint. The first 75-candidate SymPy run completed 150 fresh checks in about 66 minutes, so an interruption near completion would impose material deterministic rerun loss. | Add one single-writer candidate checkpoint keyed by exact package, candidate, Workspace, Runtime, Check, base/ref mode, and normalized outcome before the next pool of comparable size. Replay every retained checkpoint before reuse. Do not infer a parallel certification service or workflow engine from this measurement. |
| RI-161 | P1 | reproduced, resolved 2026-07-25 | complete | Two model configurations with the same reasoning effort initially derived the same isolated Codex home path. Their credentials and harness state could therefore collide even though their Agent identities differed. | Derive each study Codex home from the exact Agent ID as well as reasoning effort, and bind the resulting path through the existing Agent harness identity. This stays an experiment-specific path rule; it does not add an Agent registry. |
| RI-162 | P0 | reproduced, resolved 2026-07-25 | complete | A campaign cell could durably append its exact Result and then fail during post-call quota metadata or the caller-side study-ledger write. The campaign correctly refused to rerun it, but the resource ledger omitted the call and its Result ID. | Reconciliation now discovers exact scheduled Results absent from the study ledger, reconstructs a token-matched sanitized receipt, and appends the missing call without executing the Agent. Persisted receipts are validated against Result tokens and remain sufficient after the gateway log retention window moves on. |
| RI-163 | P2 | reproduced 2026-07-25 | future refactor | The Pylint Generator behavior identity hashes the entire executable pilot file. A formatting-only change outside candidate generation therefore invalidated campaign resume even though the prepared Task Pool and schedule were unchanged. The fail-closed gate prevented a paid call, but the identity is broader than the claimed behavior. | After the active frozen campaign, replace the whole-file proxy with a small explicit Generator behavior/version payload plus digests of directly executed generation helpers. Preserve exact package, Task Pool, harness, and Check binding; do not relabel the current pool or weaken resume validation mid-study. |
| RI-164 | P0 | reproduced, resolved 2026-07-25 | complete | Querying the eventually consistent global token balance both before and after every cell caused repeated management-API 429 responses, including more than three minutes without `Retry-After` metadata. The post-call value could not attribute cost and its request made the next pre-call guard less available. | Keep the exact token-log receipt on every Result, remove the per-cell post-call balance request, and request one live global checkpoint every six frozen cells. Reuse a live snapshot across campaign boundaries for no more than five minutes. Between checkpoints, guard on the larger last global movement and exact attributed study quota plus the next-call ceiling. Six cells are three paired Task blocks; reconciliation remains mandatory at campaign boundaries. |
| RI-165 | P0 | code-confirmed, resolved 2026-07-25 | complete | The frozen selection rule says observed gateway cost breaks performance ties, but the first calibration summary implementation ranked on per-Agent reconstructed price estimates. Both are useful views, but substituting one for the other could change the selected portfolio. | Require one exact token-log receipt per canonical calibration Result, report both views, and use summed attributed gateway cost for selection. Repricing remains an audit and counterfactual pricing view; it no longer silently stands in for observed spend. |
| RI-166 | P1 | code-confirmed, resolved 2026-07-25 | complete | A paired campaign has one ScoringConfig, so pricing both selected Agents at the larger rate can make the campaign's estimated ledger consumption exceed its actual gateway p90 projection. Using the USD 180 actual-spend allocation as both ceilings could stop a safe frozen schedule early. | Amendment 2 separates an actual gateway p90 gate of USD 180 from a maximum USD 260 conservative ledger authority. Admission also requires spend already observed plus actual projection plus USD 30 reserve to fit the USD 300 global cap. The larger ledger number is not actual-spend authority. |
| RI-167 | P0 | reproduced, resolved 2026-07-25 | complete | One scoreable mini Result was durable before all of its successful token-log rows became visible. A single immediate receipt query could not match the Result token totals, so the caller stopped after the Result without an attributed receipt. A later reconciliation also showed that live quota and token-log management calls share rate limiting. | Keep the exact Result and zero Agent retries. Receipt acquisition waits through at most six observations with 1/2/4/8/16-second gaps for exact token equality. A reconciliation with missing receipts performs only receipt recovery and retains the last live balance checkpoint; the next receipt-complete reconciliation refreshes the global balance. |
| RI-168 | P1 | reproduced and upstream-source-confirmed, resolved 2026-07-25 | complete | Fetching a complete token-log snapshot after every Result consumed the management endpoint much faster than model calls consumed the paid endpoint. By the sixth replacement Result the proxy was in a sustained 429 window. Upstream New API routes both token usage and token logs through one IP-keyed CriticalRateLimit; its current default is 20 requests per 1,200-second fixed window, although deployments may override it. | Persist every Result immediately, but batch receipt attribution at six-cell boundaries using one token-log snapshot for all pending Results. Reserve each pending call at its own full per-call quota ceiling, and refuse to enter the next six-cell block until the prior block has exact receipts. Balance checkpoints at 0/6/12/18 and receipt checkpoints at 5/11/17/23 are naturally separated by paid work. |
| RI-169 | P1 | upstream-source-confirmed, resolved 2026-07-25 | complete | The metadata client retried a 429 five times with short exponential gaps. Under New API's fixed critical window, those requests cannot make progress and consume additional slots; the observed deployment also omitted the current upstream `Retry-After` header. | A metadata 429 now stops after one request, preserves a `Retry-After` value when present, and leaves scheduling to the research driver. Only an incomplete successful token-log snapshot uses bounded eventual-consistency observations. A focused test rejects both 429 polling and sleeping. |
| RI-170 | P0 | contract audit, resolved 2026-07-25 | complete | Calibration and main execution persisted an unexpected non-scoreable Result but did not prevent later paid cells. A model or protocol regression after its canary could therefore consume the rest of the campaign even though the frozen research contract treats scoreability drift as an exit gate. | Before every calibration or main cell, reject any non-scoreable campaign history. After a paid cell, persist and account its exact Result first, then stop immediately if it is non-scoreable. Protocol canaries retain their separate role of recording invalid compatibility evidence. |
| RI-171 | P0 | deployment-version source audit, resolved 2026-07-25 | complete | The token-log client sent the API key both in `Authorization` and in the query string. The observed gateway reports New API v1.0.0-rc.4, whose `TokenAuthReadOnly` reads only the header; the redundant URL credential could be retained by access logs or traces. | Request `/api/log/token` with the existing Bearer header only. A regression test captures the path and proves the credential is absent. The study stores only sanitized row digests and never raw gateway payloads. |
| RI-172 | P0 | reproduced, resolved 2026-07-25 | complete | The fifth mini Result's model/time window contained 23 successful rows totaling 562 input and 628 output tokens more than its exact Result usage, while the adjacent Terra Result matched exactly. A shared proxy can therefore interleave an unrelated same-model call inside a study call; selecting every model/time row is not sufficient per-call attribution. | Treat model/time rows as candidates. Accept them all when both token totals match; otherwise accept only a unique candidate-row subset matching both Result totals. Persist candidate/excluded counts and sanitized digests. No subset, multiple subsets, or more than 36 candidates fails closed. Tests cover unique exclusion and ambiguous alternatives. |

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

The first whole-worktree attempt traversed ignored virtual environments and
third-party or generated material. The maintained configuration now scans only
the 34 executable first-party Python files under `src/barcarolle`, `examples`,
and `scripts`, excluding caches, outputs, workflow state, and hidden-check
fixtures. Tests have a different complexity profile and enter only an explicit
test-maintenance scan. History uses 180 days, requires two shared commits, and
discards commits touching more than 25 in-scope files as coupling evidence.
Observed in-scope commit sizes are 35, 28, 15, 3, and 1: the cutoff retains the
package/Selection migration while preventing two broad integration PRs from
creating an almost complete coupling graph.

The current scan uses temporary full-suite branch coverage, conservative 0%
entries for non-imported scripts, and conventional 100% entries for empty
`__init__.py` files. It has full signal health and reports 115 hotspots (0
`refactor_now`, 37 `refactor_soon`, 78 `monitor`), nine
`investigate_soon` files, and no dead-code candidates. The repository verdict
remains `strained`. Coverage and hotspot counts are routing evidence, not proof
that a function is risky. No baseline is committed, so the scan does not
support a regression claim.

An explicit one-file scan of `tests/test_runner.py` was used only for the
external review's test-maintenance question. It reports 13 length/complexity
hotspots, but also calls 18 pytest-discovered tests/helpers high-confidence dead
code. That false Vulture signal supplies the scan's dead-code score and
`investigate_now` band, so neither deletion nor file splitting follows from the
headline. The one cited private-helper patch was replaced with a public
input/side-effect contract; the remaining long scenario tests stay intact until
a concrete refactor makes shared setup or file ownership observable.

The detailed figures below are historical slices retained for auditability.
The original 37-file scan had 108 hotspots, 22 `refactor_now`, and
Ruff/Lizard/Complexipy critical counts of 8/31/8. A later 38-file scope,
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
distribution, task count, and MAE on the same supplied source-event cohort.

Resolution: `RollingOriginRecord` now freezes cohorts by
`task_material_available_at`, records the maturity lag and cutoff, and separates
mature from censored history/future refs. Runner executes only mature refs;
empty mature future cohorts abstain. Training requires each training origin's
label-maturity cutoff to precede deployment. Reporting exposes the offline
arrival-versus-label-time counts, overlap, inclusion rate, and label-delay
distribution. Comparing MAE across several lags remains experiment work because
the repository does not yet contain a sufficiently large real paired history.

### RI-026: Build An Auditable Supplied-Event Ledger

Priority: P1. Evidence: code-confirmed. State: supplied-ledger contract resolved
2026-07-22; optional generic observed-frame contract resolved 2026-07-24 under
RI-137, with concrete frame evidence pending.

Before this fix, core Task supply filtered caller-provided source events but did
not collect issues, pull requests, or commits, and a frozen pool retained only
an inventory digest rather than a loadable sanitized inventory. Events that
never became candidates were therefore not auditable.

Direction: either rename the current function to describe filtering, or add
concrete source adapters. Persist a sanitized Generator-outcome ledger
containing event identity, candidate eligibility, certification decision,
rejection stage and reason, label maturity, and dependency cluster.

Do not use inverse-propensity weighting until inclusion probabilities and the
source denominator are defensible.

Resolution: Task Pool now uses `CandidateBatch` to retain pre-certification
exclusions, joins every candidate with its certification decision, and persists
the ordered `SourceEventRecord` sequence in the immutable pool bundle. The ledger
binds source identity, arrival, nullable label maturity, disposition, rejection
stage/reasons, accepted Task/Check links, dependency cluster, and sampling
stratum. Reporting validates the exact supplied ledger and summarizes
disposition, right-censoring, and label delay. It does not prove which upstream
events were never supplied. Source collection remains adapter-specific; the
core did not gain a generic ingestion framework.

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
persists a self-digested `records/adapter-evidence.jsonl` containing trusted
reference-patch digests, repository-relative changed-path footprints, exact
path-overlap edges, and deterministic connected components. A generation
manifest binds stable adapter behavior independently from this run-specific
sidecar and the Task Pool outputs. Loading validates the complete bundle,
re-derives the evidence from local trusted patches, and replays SourceEvent
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

### RI-046: Bind Task Pools To Their Declared Source Time Window

Priority: P1. Evidence: reproduced. State: time-window contract resolved
2026-07-23 and refined 2026-07-24; optional generic observed-frame contract
resolved under RI-137, with concrete capture evidence pending.

A counterexample used a later pool whose accepted inventory was internally
valid but whose records could not establish whether collection covered the
strict Origin's complete future interval. `created_at` proves observation time,
not the start and end of source coverage. Reusing the generator-config digest
for actual events would prevent later snapshots from sharing one behavior
identity. The repaired invariant proves temporal containment of supplied events,
not upstream capture completeness.

Resolution:

- generated and imported Task Pools persist canonical `source_window_start`
  and `source_window_end` values in their frozen record and bundle digest;
- the window cannot end after pool creation;
- accepted or certification-rejected SourceEvents outside it fail validation,
  while excluded outside events must record `outside_source_time_range`;
- generator configuration now describes collection mode and source family;
  SourceEvent, Task, Check, and certification digests describe supplied
  inventory;
- prospective replay requires the later source window to cover the complete
  planned future interval. It may be incremental or cumulative; if the two
  pools overlap, same-ID Task/Check records must be unchanged.

This is the minimum temporal evidence needed for two immutable snapshots. It is
not an observed-frame inventory or completeness receipt.

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
| RI-032 | P2 | code-confirmed | supplied-ledger part resolved 2026-07-22 | Task Pool summaries and documentation claimed more source, rejection, and time coverage detail than the implementation stored. | Reporting now derives only supported source disposition, censoring, rejection, validation, and label-delay summaries from the validated bundle. Continue narrowing any unsupported adapter-specific claim. |

Functionality decisions:

- Implement the validated Task Pool bundle, paid-call preflight, symmetric flaky
  certification, canonical hidden-tree digest, reserved-namespace check,
  immutable model identity handling, and resumable single-writer Result path.
  They support the target evidence boundary without adding a module.
- Preserve the sanitized supplied-event ledger because prediction bias within
  Generator input cannot be audited without events that failed to become Tasks.
  Add independent observed-frame evidence under RI-137.
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
| DOC-006 | P2 | complete 2026-07-24 | Task Pool and claim documentation now calls SourceEvents the supplied Generator-outcome ledger, treats the optional observed frame as separately bound protocol/inventory evidence, and distinguishes both from a target work population. |
| DOC-007 | P2 | complete 2026-07-22 | Coverage and invalid rate are labeled holdout-evidence diagnostics, not Selector losses. |
| DOC-008 | P1 | complete 2026-07-22 | Selection docs distinguish executable paths from deferred learned methods. |
| DOC-009 | P2 | ongoing | Keep the RI-021 checkout threshold and RI-033 bounded-parallel prerequisites current when new timing evidence replaces the 1.009 serial-pilot estimate. |
| DOC-010 | P1 | complete 2026-07-23 | The Pylint pilot report documents the frozen campaign inputs and exact `authorize`, `preflight`, and one-cell `run-next` sequence without embedding credentials or campaign-specific values. |
| DOC-011 | P1 | complete 2026-07-24 | Task Pool, Runner, data-flow, Records, and system docs distinguish strict package build from read-only complete-pool open/use, require full-bundle preflight, retain local Workspace bindings, and state managed versus producer-attested claims. |
| DOC-012 | P1 | pending with the first built-in | Document adapter fidelity names, primary-source/code revisions, independently digested Generator behavior/source protocol/observed frame/run/output provenance, sidecar evidence, single-repository partitioning, and golden-fixture expectations. |
| DOC-013 | P2 | future with RI-127 | When the first concrete episode adapter is implemented, document pre-interaction/dynamic state, persistent turns, simulator identity/seed/cost, event evidence, and metrics separately from Agent identity and static Task generation. Label its evidence simulator-treatment-conditional; add human-proxy interpretation only after the branch-policy pilot. |
| DOC-014 | P1 | complete 2026-07-24 | Result Store, Runner, data-flow, Records, and migration docs define external admission, effective availability, authority, conflicts, one-snapshot multi-origin evaluation, and persisted `history view -> Selection -> cache -> selected misses -> CellSet` order. |
| DOC-015 | P1 | complete 2026-07-24 | System, Reporting, statistical, and process docs use a claim lattice rather than a false total ladder. They name `future_pass_rate_mae` as Generator-conditional future Task/Check prediction error and separate Result cells, certification yield, observed-frame inclusion, Generator bridge, Check/semantic calibration, and field calibration. |

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
- keep downstream modules Generator-agnostic while binding Generator behavior,
  source protocol, and observed-frame inventory as separate evidence;
- keep generated-pool prediction, Generator validity, and field validity as
  distinct claims;
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
calling supplied-event integrity real-work coverage, mixing Generators by task
count, treating one user simulator as a neutral evaluator, or putting raw
verifier, Agent, trajectory, and field output into normalized reports.

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

The arrival/maturity, repeated-cell, dependency, supplied-SourceEvent,
observed-frame, and claim-boundary contracts are complete at the generic
boundary. Run adapter-specific or empirical parts only with a concrete source
and authorized evidence.

Exit criteria:

- arrival and label times have separate roles (complete);
- censored events and the supplied Generator-outcome ledger are auditable
  (complete), and deterministic dependency-edge provenance is complete for the
  concrete Pylint adapter;
- Generator behavior, source protocol, and exact observed-frame inventory have
  independent identities, and a frame-bound Task Pool accounts for every frame
  event (generic contract complete; concrete frame evidence pending);
- a larger paired history includes randomized repeated cells (paid experiment
  pending);
- all baselines share frozen origins and common future evidence (complete);
- strict-prospective generated-pool performance links a later Task Pool to the
  original frozen Origin without rewriting either snapshot (complete;
  empirical evidence pending);
- campaign estimands distinguish task-level generated-pool loss, event-level
  Generator validity, and field outcomes (research and documentation complete;
  empirical evidence pending);
- same-frame, Generator/time bridge, semantic/Check audit, interactive branch,
  and prospective field protocols are predeclared before their evidence is
  collected (research decision complete; empirical calibration pending).

The concrete Pylint campaign entry and the generic supply/admission boundary
are complete. The next Task-supply step begins only after selecting a concrete
source and adapter; observed-frame and lineage evidence then obtain real
fixtures. LLM Generator execution and large-pool certification retain their
adapter and authority gates. RI-127 permits one narrow concrete interactive
adapter while requiring a held-out human branch-policy pilot before
human-interaction claims. RI-139 field calibration remains an external
prospective study, and RI-140 forbids automatic Generator mixtures without that
outer evidence.

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
- RI-026: immutable Task Pool bundles persist and validate the complete supplied
  Generator-outcome ledger, including exclusions and right-censoring.
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
- RI-032 (bundle-ledger scope): Task Pool reports derive only claims supported
  by the validated source-event, Task, Check, and certification bundle.
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
- RI-046: Task Pools bind canonical declared source time windows separately from
  behavior-only Generator identity, so later snapshots can prove planned-window
  containment without claiming complete source capture.
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
  evidence; duplicate non-null candidate IDs cannot inflate the supplied-event
  denominator.
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
- RI-114: paid endpoint proof binds every declared harness path to its exact
  content digest; exchanging executable and helper bytes fails preflight.
- RI-115: recursive JSON payloads and finite state strings have static types,
  while direct validation rejects unsupported, cyclic, non-finite, or
  shape-changing values before persistence.
- RI-116: Workspace and Verification propagate stable preparation labels by
  typed failures rather than parsing diagnostic messages.
- RI-117: the repository owns a minimal locked quality workflow and Pyright
  standard-mode contract across library code, executable examples, and
  migrations; the active `main-quality` rule requires its successful
  default-branch status.
- RI-118: Runner's configuration-before-source contract is observed through
  public inputs and side effects rather than a private helper patch.
- RI-119: Cremona has a calibrated code scope and history policy; it remains
  routing evidence, with no automatic module split, baseline, or CI gate.

## Update Log

- 2026-07-25: opened the bounded USD 300 coding-Agent/model study and added
  RI-154 through RI-172. A thin static SWE-bench adapter froze a 75-Task SymPy
  Verified slice with 54 dependency clusters; full base/reference certification
  is active. Pylint calibration exposed three infrastructure facts before they
  could corrupt capability claims: advertised proxy inventory does not prove
  Codex Responses compatibility, immediate token-balance deltas are eventually
  consistent rather than per-call receipts, and whole-file Generator hashing
  overbinds formatting to behavior. Single-Agent protocol canaries, exact
  token-log receipts, Result-first reconciliation, Agent-specific Codex homes,
  six-cell global quota checkpoints, a global budget guard, and serialized paid
  calls now preserve the frozen evidence boundary. DeepSeek V4 Pro and Gemini
  3.1 Pro failures are retained only as protocol evidence; the scoreable
  Sol/Terra calibration is continuing.

- 2026-07-24: closed the generic pre-Generator infrastructure slice
  (RI-120–RI-124, RI-131–RI-138, and RI-141–RI-153, with concrete-adapter
  portions explicitly deferred). Runner now consumes complete Task Pool
  bundles; strict prepared packages carry candidates, exclusions,
  certification material, optional generation/frame provenance, and adapter
  evidence; user-maintained bundles open read-only and have a validation CLI.
  Generic packages cannot self-claim managed generation or source authority,
  frame windows exactly match their Task Pool windows, and neither a frame
  window end nor a frame observation can postdate generation completion; the
  run and its observations cannot postdate pool creation. Final Task Pool
  semantic identity is derived only after the complete generation manifest is
  bound. Task Pool and claim-boundary reports enumerate its observed-frame
  inventory and adapter sidecar as reproducibility artifacts. The existing fixed
  Pylint pilot binds dependency and F2P/P2P evidence through the adapter sidecar
  and publishes/opens the canonical `task-pool.jsonl` bundle before paid
  stages. External Results
  enter through authority-bound manifests and receipts with conservative
  availability, source preservation, membership/identity admission, canonical
  Result IDs, deterministic execution views, fail-closed conflict handling, and
  one import lock scope from first local observation through receipt publication.
  Receipt files and their parent directories are synced before success,
  including for all-rejected imports. Receipt replay is read-only; migrations
  recompute Result identity and require
  rebuilding every derived binding. Multi-origin Selection uses one physical
  Result snapshot, lazy fill replays persisted upstream evidence before cache
  access and freezes an EvaluationCellSet whose identity binds scoring and
  benchmark-invalid reuse policies, and strict prospective evaluation
  accepts either an incremental or cumulative later pool covering the complete
  future interval. Reporting uses
  `task_pool_bundle_internal_consistency`, labels Result evidence authority,
  and treats claims as a lattice. Added a non-destructive migration for the
  immediately preceding managed-Result schema. Three independent final audits
  found no remaining blocker before PR review; the later provenance,
  chronology, and CellSet-resolution counterexamples were reproduced and
  closed. The full suite passed 915 tests with 2 environment-dependent skips;
  Ruff, Pyright, repeated
  minimal-demo execution, and `git diff --check` passed. No concrete Generator,
  Generator registry, network call, campaign authority, or paid call was added.

- 2026-07-24: opened RI-136 through RI-140 and DOC-015 after treating
  `bc-r.md` as hypotheses rather than requirements and running independent
  formal-estimand, current-contract, and adversarial simulator audits. The
  result keeps Task generation in scientific scope while preserving a
  Generator-agnostic downstream data boundary. Current SourceEvents are now
  classified as a complete ledger for supplied Generator outcomes, not proof
  of an observed frame or real-work population; `future_pass_rate_mae` is
  classified as Generator-conditional later-Task/Check prediction error.
  Generator behavior, source protocol, exact observed-frame inventory, run,
  and outputs require separate identities. The proposed error chain is valid
  only as signed telescoping on one common estimand, not as an additive MAE.
  Primary studies of SWE-Together, SWE-INTERACT, SWE-chat, SimulatorArena,
  simulator utility, causal controls, direct Sim2Real comparisons, PULSE, and
  RealHumanEval show that interaction changes capability and real-user
  grounding can help, but one logged trajectory does not identify responses on
  a new Agent's branches. A concrete episode contract may be implemented for
  simulator-treatment-conditional evidence; a held-out human branch-policy
  pilot gates human-interaction claims, while prospective field calibration
  gates real-work claims and Generator mixtures. No source code, Task Pool,
  Result, campaign authority, private trajectory, field evidence, or paid call
  was changed.

- 2026-07-24: opened RI-131 through RI-135 and DOC-014 after the maintainer
  clarified that a user-maintained Task Pool may arrive with cached Agent
  Results, while a new Agent-by-pool combination should be selected before
  missing cells run. The decision keeps Task Pool and Result storage
  independent, preserves the existing exact cache identity without a Task Pool
  key, and treats Agent-by-pool coverage as a derived view. External Results
  are normalized into the local append-only store with an authority/import
  receipt and conservative effective availability; import cannot bypass the
  origin/query policy or directly add Selector evidence. Selection sees one
  frozen cutoff-safe history snapshot; its persisted evidence is replayed
  before the full cache resolves selected cells and Runner executes only
  misses. Conflicting executions under one exact cache identity fail closed
  instead of inheriting the current append-order winner. No source code,
  external Result, benchmark evidence, campaign authority, or paid call was
  changed.

- 2026-07-24: revised RI-113 and opened RI-120 through RI-130 after a
  three-route Task-supply sprint: current-contract audit, primary-source
  comparison of SWE-bench, SWE-Bench++, SWE-smith, SWE-Future, SWE-Together,
  and SWE-Interact, and an adversarial KISS/trust-boundary review. The decision
  keeps one-repository immutable Task Pools and separates generator-built
  candidate packages from read-only user-maintained pools. It records
  complete-bundle execution preflight, behavior/input/output provenance,
  adapter evidence, direct pool bindings, built-in fidelity, synthetic base
  state, interactive episodes, managed LLM authority, and comparative
  evaluation of native generators without a plugin host or workflow engine. A
  local schema probe also reproduced the Pylint
  `swe_bench_status` evidence conflict. The `main` quality workflow is green
  and its active repository rule is confirmed. No source code, benchmark
  evidence, campaign authority, paid call, or external pool was changed.

- 2026-07-24: closed RI-115's PR-review gap. A red public JSONL case proved
  that same-typed unknown Literal values loaded successfully; generic
  latest-schema conversion now checks membership for every Literal, while
  domain validators retain cross-field state-machine checks. The first
  `quality` run also showed that Ubuntu lacks the zsh required by the Codex
  harness contract tests, so CI installs that explicit test dependency instead
  of skipping four tests.

- 2026-07-23: closed RI-115 through RI-118 and calibrated RI-119 from the
  external review. Recursive JSON and finite state types now reach Pyright
  standard mode; unsupported, cyclic, non-finite, and tuple-shaped JSON
  counterexamples fail without exception leaks or persistence drift.
  Repository binding, checkout, and verifier preparation preserve stable
  labels through thin typed errors. The minimal quality workflow performs a
  frozen install, Ruff, Pyright standard over library code, executable
  examples, and migrations, and the full suite. One Runner test now proves
  ordering through public source and artifact effects. The full 851-test suite
  passes with 2 skipped. A full-signal 34-file Cremona scan reports 115
  hotspots (0 now / 37 soon / 78 monitor), nine investigate-soon files, and no
  dead-code candidates; no baseline means no trend claim. A separate
  `test_runner.py` scan was rejected as an automatic priority because Vulture
  misclassified 18 pytest-discovered symbols as dead code. No module-by-size
  split, generic error hierarchy, `NewType` migration, format gate, coverage
  target, Cremona baseline, network request, or paid call was added.

- 2026-07-23: closed RI-114 from PR review. Paid multi-file harness evidence
  now binds resolved path/content-digest pairs instead of an unlabelled content
  multiset. The prior implementation reproduced the swap counterexample; the
  new regression and all 838 tests pass. No new evidence record or harness
  abstraction was added.

- 2026-07-23: closed RI-112 and recorded RI-113. The Pylint replicate campaign
  now has one concrete CLI over its existing authority and executor APIs. Three
  actions keep authorization, no-call preflight, and single-cell execution
  separate; verifier images are replayed before paid execution; campaign
  artifacts are confined below one local directory and CLI summaries omit
  credentials and raw endpoint values. Five focused CLI specs
  cover explicit authority, no implicit ledger creation, exact frozen-input
  loading, image-verified preflight, and one-cell execution; the full suite
  passes 838 tests with 2
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
  inflated the supplied-event denominator. Candidate-linked events now require
  unique IDs.
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
  performance evaluation reopens only when a later Task Pool with a compatible
  declared source time window is linked without changing the original Origin. A
  second red specification
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
  supplied-ledger part of RI-032. Rolling origins now separate arrival cohorts from
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
