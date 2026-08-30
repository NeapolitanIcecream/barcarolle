# Barcarolle System Design

Status: current implementation design, 2026-08-30.

## Scope

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain. A self-evolving agent retains behavior-changing updates across tasks,
including changes to its model, harness, prompts, memory, skills, tools, or
other persistent state. The evolving subject is the core context; changing the
evaluator in response is an optional method.

Reliability is bounded by a declared task population, outcome definition, agent
lineage and optimizer, feedback interface, optimization budget, threat model,
time horizon, and decision. The three primary empirical objectives are
pass-rate MAE on future real-world tasks, pass-rate-difference MAE between
agents, and retention of both errors under repeated evaluator-guided
optimization. See [`../research-program.md`](../research-program.md).

Evaluation and method selection have four stages, in order:

1. Evidence validity determines whether the tasks, outcomes, and information
   boundaries can support the claim.
2. Absolute error limits determine whether both errors, coverage, and uncertainty
   meet predeclared deployment requirements.
3. Degradation under optimization measures change from the same evaluation
   method's no-optimization baseline (`b=0`).
4. Method comparison chooses among methods under matched conditions.

A reliability claim must pass the first two stages and the third when it covers
evaluator-guided optimization. The fourth stage cannot repair an earlier
failure.
Neither stability from an inaccurate baseline nor improvement over an
inaccurate comparator establishes reliable evaluation.

The current implementation accepts direct candidate sources, prepared output
from arbitrary task generators, or an existing user-maintained `Task Pool`;
validates `Task + Check` by execution; runs agents in fresh `Workspace`s;
admits managed or explicitly attested external `Result`s; and evaluates
`Selector`s with `RollingOrigin`.

The agent optimizer remains external to the current execution boundary, but its
version, parent links, behavior-changing persistent state, evaluator feedback,
candidate archive, and optimization budget must become experiment evidence for
repeated-optimization claims. A higher evaluator score is not evidence of
capability improvement until the result is checked against an independent
reference standard on prospective future tasks.

## Research Layer Versus Implemented Modules

The research architecture has three information flows:

1. **Agent optimization:** the current evaluator version exposes only the
   feedback interface declared by the frozen evaluation method. The agent
   optimizer produces a complete lineage of every candidate it considered,
   including each candidate's identity, parent links, update, and disposition.
   Expensive prospective outcome measurement may use a predeclared probability
   sample with recorded inclusion probabilities; lineage retention may not.
2. **Optional evaluator update:** an evaluator builder may use development
   evidence, consumed prospective cohorts, and red-team results to produce the
   next evaluator version under a frozen update rule. A static evaluator is a
   valid control and may itself be sufficient.
3. **Independent prospective evidence:** the evaluation method, predictions,
   and applicable agent and evaluator versions are frozen before a future
   real-world cohort and its outcomes open. That cohort remains unavailable to
   both preceding flows until scoring; once used for development or selection
   it is retired from independent-test use.

The eight modules below implement only part of those flows. They are the current
static execution and evidence boundary; they do not limit research to the
`Selection` module. An experiment-level evaluation method may compose task supply or
generation, admission, selection or weighting, statistical outcome models,
evaluator feedback, updating, and uncertainty policies. Parent links and
persistent state between agent versions, feedback records, optimization rounds,
complete reliability-claim evidence, prospective-cohort lifecycle, evidence that
separates behavior from capability, and adversarial stress tests still need durable
implementation contracts.

Do not describe those concepts as existing modules until code and replay tests
enforce their boundaries. Conversely, do not reject a concrete task-generation or
meta-evaluation experiment merely because the current module table predates
it.

## Module Boundary Overview

The system has eight modules. The table below is the module boundary contract:
for each module, it states what crosses the boundary, where inputs come from,
and who consumes the outputs.

| Module | Owns | Inputs | Input Source | Outputs | Output Consumers |
| --- | --- | --- | --- | --- | --- |
| Records | Shared record schemas, identity rules, validation errors, and JSON/JSONL serialization contracts. | Record definitions; record payloads produced by other modules. | Design docs; Task Pool; Verification; Workspace; Result Store; Selection; Reporting; Runner. | Validated source-frame, generation-provenance, prepared-package, `Task`, `Check`, `Feature`, managed/external `Result`, import-receipt, cache-identity, `Selector`, `Benchmark Selection`, metric, and report records; validation errors; stable IDs. | All modules. |
| Task Pool | Source-event filtering, prepared-candidate admission, task import, execution-based task validation, rejection provenance, and frozen task-pool records. | Stable repository ID; sanitized source events or candidates; a language-neutral prepared package; direct task text; Check fields; certification config; bound Workspace and Verification inputs. | User config; arbitrary task-generator outputs; repository-specific adapters; user imports; Verification for check execution; Workspace for checkout/replay. | Frozen `Task Pool`; accepted `Task + Check` records; sanitized accepted/rejected/excluded SourceEvents; optional generation provenance and observed-frame binding; certification evidence. | Workspace; Result Store; Selection; Reporting. |
| Verification | Check execution interface and normalized check outcomes. | `Check`; verifier workspace path; candidate diff already applied; verification runtime config. | Task Pool provides `Check`; Workspace provides verifier workspace and applied diff. | Normalized check outcome: pass, fail, invalid, failure label, sanitized evidence summary. | Workspace; Result Store; Reporting. |
| Workspace | Solver workspace creation, Agent invocation, diff capture, verifier workspace creation, diff replay, and verification orchestration. | `Task`; `Check`; Agent config; workspace config; runtime config. | Task Pool provides `Task + Check`; user or run config provides Agent and configs; Verification provides verification runner. | Captured diff digest; execution metadata; check outcome; workspace-level failure classification. | Result Store. |
| Result Store | Result cache identity, managed-result storage, external-source normalization, ambiguity detection, missing-cell queries, and result matrices. | `Task`; `Check`; Agent config; exact result identity; workspace output; check outcome; or an immutable external Result source with authority and availability semantics. | Task Pool; Workspace; Verification; users; Records. | Reusable evidence-provenance-aware `Result` records; import decisions and receipts; result cache state; cell-level result matrix; completeness, exclusion, and abstention metadata; missing Agent-task-check cells. | Selection; Reporting; Runner. |
| Selection | Current Selector training, evaluation, benchmark selection, rolling-origin construction, feature snapshotting, and static pass-rate and pass-rate-difference scoring. | Frozen `Task Pool`; `Agent Results`; historical window or origin; budget; candidate Agents; selector config or specified Selector; rolling-origin policy; feature config. | Task Pool; Result Store; user config; selector config; feature config. | `Selector`; `Benchmark Selection`; selected `Task + Check` refs and weights; rolling-origin metrics; feature snapshots; selector notes. | Reporting; Runner. |
| Reporting | Summaries with explicit evidence limits, audit reports, and machine-readable summaries. | Selection `Task Pool`; any later prospective `Task Pool`; Selector; RollingOrigin; FeatureSnapshot; SelectorInput; `Benchmark Selection`; `EvaluationCellSet`; result matrices; `Agent Results`; rolling-origin metrics; artifact digests. | Task Pool; Result Store; Selection; Records. | Human-readable report; machine-readable summary; mode-specific claim-boundary statement. | Users. |
| Runner | Command-level orchestration across modules, including complete-bundle validation, external Result admission, cache reuse, persisted-selection replay, and lazy Agent execution. | Run config; target repository; task-source config or prepared package; Agent set; historical window or origin; budget; selector config or specified Selector; result source/store; workspace config; runtime config; scoring config; report config. | Users; Task Pool; Result Store; Selection; Workspace; Reporting. | Run summary; references to records produced by owner modules; Result-import receipt; report paths. | Users. |

## Canonical Data Flow

The intended research-level information flow is:

```text
agent optimization (core context)
  frozen evaluation method M
  evaluator version E(k) --permitted feedback--> agent optimizer
  agent optimizer --versioned candidates + lineage--> agent archive

optional evaluator update
  development evidence + consumed cohorts + held-out-family stress tests
  --frozen evaluator-update rule U--> evaluator version E(k+1)

independent prospective evidence
  frozen method M + agent/evaluator-version/budget checkpoints
  + sealed future real-world tasks + independent outcomes
  --> evidence validity
  --> absolute error limits
  --> degradation curves under optimization
  --> method comparison and bounded report
```

The prospective evidence flow must not feed the first two flows before the
corresponding predictions and protocol are frozen. An opened cohort may inform a
later version, but then a new sealed cohort is required for its independent
test.

The current module graph implements a primarily static slice. It has two
durable stores: `Task Pool` and `Agent Results`. `Benchmark Selection` is a
durable output of Selection that joins them under a frozen origin and budget.

Runner receives user config and calls the owner modules:

```text
User config, task source, or prepared-candidate package
  -> Task Pool
  -> frozen Task + Check records

Runner + Task Pool + Agent config + workspace config
  -> Workspace
  -> Verification
  -> Result Store
  -> Agent Results

External Result manifest + authority + Task Pool + local identities
  -> Result admission
  -> normalized Agent Results + immutable import receipt

Task Pool + pre-origin Agent Results + origin + budget + Selector
  -> `RollingOrigin` -> `FeatureSnapshot` -> `SelectorInput`
  -> frozen Benchmark Selection
  -> Evaluation Cell Set -> Result Matrices -> rolling-origin metrics

Task Pool + complete Selector provenance + Agent Results + metrics
  -> Reporting
  -> report + machine-readable summary
```

Records is used by every arrow in the graph. It validates data at module
boundaries and assigns stable identities; it does not own system behavior.
Runner owns the arrows between modules. It does not own the records produced by
those modules.

## Core Data Objects

### Task

Direct solver-visible task text, optional refs to supporting files in the
repository checkout, and repository metadata. A `Task` never contains hidden
check material or future outcome data. `dependency_cluster_id` is protocol-only
blocking metadata; `sampling_stratum` may be used for Selector-visible
stratification. Empty values remain empty.

### Check

Acceptance method for a `Task`. A `Check` may be a test command, script,
visual check, user-supplied check, human-reviewed result, or LLM-judged check
when the judgment process is explicitly represented. Its optional resource
mapping overrides only limits implemented by the active execution path;
Workspace and Runtime records own environment identity and the default
timeout.

### Workspace

A fresh checkout for solving or verification. Solver workspaces receive only
solver-visible material. Verifier workspaces receive hidden check material
after the Agent diff is captured. This separates benchmark data but does not
contain a cooperative Agent from the host. A hardened adapter is optional
defense in depth for cooperative runs and mandatory when the evidence claim
deliberately includes test/scorer/grader/host attacks or mutually untrusted
same-host execution.

### Result

One Agent on one Task under one environment and runtime config. A `Result`
contains status, pass/fail/invalid, usage, cost, pricing version, latency,
failure label, captured diff digest, verifier metadata, and the time
the result became available for selector use.

A reusable `Result` is matched by `ResultCacheIdentity`, which stores the
structured task, check, Agent, workspace, runtime, adapter, and optional
hardware identity plus a digest. Pricing and scoring are stored on the Result,
not in execution identity. Agent identity stores the requested model separately
from a proven immutable snapshot; an unresolved alias instead binds exact reuse
to a declared campaign and execution window. Results with incomplete identity
are not cache hits.

The Result also identifies whether Barcarolle observed the execution or an
external producer attested it, the source manifest, import time, source
availability time, and policy used to derive effective availability. The
default external policy prevents evidence imported today from appearing in
yesterday's Selector history. A producer-attested historical policy is allowed
only as an explicit weaker provenance claim. Multiple different executions
sharing one cache identity are ambiguous and cannot be selected or reported as
one cache hit.

### Selector

A function that chooses benchmark tasks from a pre-origin history pool under a
budget. A selector may use task metadata and past outcomes available at the
origin, but never future holdout outcomes. A persistent Selector is stored as a
`SelectorRecord` with version, training source digests, and allowed feature
metadata. Static Selection currently computes pass-rate MAE and aggregate
pass-rate-difference MAE, although only pass-rate MAE drives the implemented
fitter and claim summary. The research program makes both primary metrics and
treats Selection as
one possible evaluator component. A learned or adaptive method defines its data
and parameter contract with its concrete algorithm.

### RollingOrigin

Evaluation protocol that freezes an origin time, selects from pre-origin
history, and compares selected-benchmark performance with later holdout
performance. Task-material arrival fixes cohort membership; Check availability
and a fixed lag determine label maturity, with unresolved refs retained as
censored provenance. The policy records as-of cutoffs, dependency-cluster
constraints, eligibility mode, and holdout overlap rules. The current modes are
strict prospective eligibility, which treats refs as known no earlier than Task
Pool creation, and explicit counterfactual replay from historical
material-availability times. The complete `RollingOrigin`, `FeatureSnapshot`,
`SelectorInput`, `Selector`, and
`BenchmarkSelection` chain is persisted before future results are opened. A
later strict-prospective Task Pool must preserve the bound task-generator
behavior, source protocol, repository, and certification configuration while
covering the planned future source interval; it may be incremental or
cumulative. A changed run or output inventory alone does not break continuity,
while overlapping same-ID Task/Check records cannot
change.

### Research Evidence Not Yet Represented By Core Records

The research design also needs agent lineage and persistent-state transitions,
agent-optimizer identity, evaluator-policy versions and feedback events,
optimization-budget checkpoints, candidate disposition, prospective-cohort
consumption, and independent reference-standard evidence. These are evidence
concepts, not claims that corresponding core records already exist.

The evidence must distinguish a general capability change from behavior that is
specific to the evaluator, an ability-preserving change, and an integrity
violation. Pass/fail outcomes alone do not identify that distinction.

## Result Reuse And Lazy Execution

The normal flow is: build a `Task Pool`, obtain `Agent Results`, then let
Selection choose a `Benchmark Selection` for a frozen origin. Two optimizations
keep this affordable.

### Cache Reuse

When `Agent Results` already exist for some Agent-task-check cells, selectors
reuse those results instead of re-running paid Agent runs. This is what makes
repeated selector research possible. Reuse requires an exact
`ResultCacheIdentity` match; incomplete or stale identities are isolated from
scoring.

### Lazy Agent Execution

When Agent execution is expensive and results are sparse, Selection can choose
a benchmark first. Workspace then runs only selected Agent-task-check cells
whose results are missing from the cache. Runner is the module that calls
Result Store to find missing results, Workspace to execute them, and Result
Store again to store them. The same completeness and denominator policy is
applied when scoring the selected benchmark against the future holdout.

Before cache access, Runner validates the complete Task Pool bundle and reloads
the persisted Origin, FeatureSnapshot, SelectorInput, Selector, Selection,
frozen pre-origin Results, and Agent identities. It deterministically replays
selection and then stores the resolved selected cells as an
`EvaluationCellSet`; an unpersisted in-memory choice cannot silently become paid
benchmark evidence.

## Evidence Claim Lattice

Evidence strength is not one total ladder. Independent axes include supplied
bundle consistency, observed source-frame authority, task-generator behavior and
source-protocol continuity, executable Check certification, Result execution
identity, Result availability provenance, rolling-origin chronology, and
field/tuning outcomes. Reports support only claims whose required axes replay;
for example, an internally consistent user pool does not imply population
coverage, and producer-attested historical availability is not a Barcarolle
observation-time claim.

For a self-evolving-agent reliability claim, the lattice also includes agent
lineage and persistent state, optimizer and feedback identity, optimization
budget, prospective-cohort independence, reference-standard validity, both
primary errors, coverage, and uncertainty. Evidence validity is a prerequisite;
absolute error limits, degradation under optimization, and method comparison are
separate stages. They must not be collapsed into one scalar score.

## Module Boundary Rules

- Task Pool does not run Agents.
- Workspace does not select benchmark tasks.
- Result Store does not inspect unsanitized Agent run logs for selector
  features.
- Selection does not read solver workspaces, verifier logs, hidden check text,
  raw reference patches, or future outcomes.
- Agent optimization and optional evaluator updating do not read sealed
  prospective tasks or outcomes before the applicable predictions and protocol
  are frozen.
- Reporting does not create new evidence; it only summarizes existing records.
- Runner does not implement task generation, selection, Agent execution,
  verification, result scoring, or reporting logic. It only calls the owner
  modules in a defined order.

## Schema Changes

Core modules read and write only the latest schema. A small one-off migration
may preserve valuable paid results after a schema change. The core does not
maintain compatibility branches or a general migration framework.

## Design Consistency Check

- Keeps `Task`, `Check`, `Workspace`, `Result`, `Selector`, and
  `RollingOrigin` as first-class objects.
- Keeps `Task Pool`, `Benchmark Selection`, and `Agent Results` decoupled.
- Treats the implemented Selector path as one replayable evaluator mechanism,
  not the core research claim.
- Keeps pass-rate and pass-rate-difference prediction distinct.
- Does not claim robustness under repeated optimization without agent-version
  history, evaluator-feedback, optimization-budget, and independent temporal
  evidence.
- Keeps agent optimization outside the predictive-validity claim.
- Prevents selectors from accessing future outcomes, hidden checks, solver
  workspaces, and verifier logs.
