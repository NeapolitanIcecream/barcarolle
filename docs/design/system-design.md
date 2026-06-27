# Barcarolle System Design

Status: draft, 2026-06-27.

## Scope

Barcarolle compiles target-repository benchmarks for coding Agents. It
generates or imports `Task + Check`, stores them in a `Task Pool`, runs Agents
in isolated `Workspace`s, stores reusable `Result`s, and evaluates `Selector`s
with `RollingOrigin`.

Agent tuning is outside this system design. A predictive benchmark may later be
used by a tuner, but tuning utility is not the same claim as predictive
validity.

## Source Materials

- `docs/architecture/v2-system-architecture-2026-06-25.md`
- `docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md`

No archived code or experiment document is an active source for this design.

## Module Boundary Overview

The system has eight modules. The table below is the module boundary contract:
for each module, it states what crosses the boundary, where inputs come from,
and who consumes the outputs.

| Module | Owns | Inputs | Input Source | Outputs | Output Consumers |
| --- | --- | --- | --- | --- | --- |
| Records | Shared record schemas, identity rules, validation errors, and JSON/JSONL serialization contracts. | Record definitions; record payloads produced by other modules. | Design docs; Task Pool; Verification; Workspace; Result Store; Selection; Reporting; Runner. | Validated `Task`, `Check`, `Feature`, `Result`, `ResultCacheIdentity`, `Selector`, `Benchmark Selection`, metric, and report records; validation errors; stable IDs. | All modules. |
| Task Pool | Task generation, task import, task certification, rejected-task summaries, and frozen task-pool files. | Target repository reference; task-source config; user-provided tasks; check construction config; certification config. | User config; built-in generators; user imports; Verification for executable-check validation; Workspace for checkout/replay validation. | Frozen `Task Pool`; accepted `Task + Check` records; rejected candidates; certification evidence; source-event inventory. | Workspace; Result Store; Selection; Reporting. |
| Verification | Check execution interface and normalized check outcomes. | `Check`; verifier workspace path; candidate diff already applied; verification runtime config. | Task Pool provides `Check`; Workspace provides verifier workspace and applied diff. | Normalized check outcome: pass, fail, invalid, failure label, sanitized evidence summary. | Workspace; Result Store; Reporting. |
| Workspace | Solver workspace creation, Agent invocation, diff capture, verifier workspace creation, diff replay, and verification orchestration. | `Task`; `Check`; Agent config; workspace config; runtime config. | Task Pool provides `Task + Check`; user or run config provides Agent and configs; Verification provides verification runner. | Captured diff digest; execution metadata; check outcome; workspace-level failure classification. | Result Store. |
| Result Store | Result cache identity, result storage, missing-cell queries, and result matrices. | `Task`; `Check`; Agent config; exact result identity; workspace output; check outcome. | Task Pool; Workspace; Verification; Records. | Reusable `Result` records; result cache state; cell-level result matrix; completeness, exclusion, and abstention metadata; missing Agent-task-check cells. | Selection; Reporting; Runner. |
| Selection | Selector training, Selector evaluation, production benchmark selection, rolling-origin construction, feature snapshotting, and feedback-based Selector updates. | Frozen `Task Pool`; `Agent Results`; historical window or origin; budget; candidate Agents; selector config or specified Selector; rolling-origin policy; feature config. | Task Pool; Result Store; user or experiment config; selector roadmap. | `Selector`; `Benchmark Selection`; selected `Task + Check` refs and weights; rolling-origin metrics; feature snapshots; selector notes. | Reporting; Runner. |
| Reporting | Claim-safe summaries, audit reports, and machine-readable summaries. | `Task Pool`; `Benchmark Selection`; `Agent Results`; rolling-origin metrics; artifact digests. | Task Pool; Result Store; Selection; Records. | Human-readable report; machine-readable summary; claim-boundary statement. | Users. |
| Runner | Command-level orchestration across modules, including cache reuse and lazy Agent execution. | Run config; target repository; task-source config; Agent set; historical window or origin; budget; selector config or specified Selector; result store; workspace config; runtime config; result identity config; report config. | Users; Task Pool; Result Store; Selection; Workspace; Reporting. | Run summary; references to records produced by owner modules; report paths. | Users. |

## Canonical Data Flow

The module graph has two durable stores: `Task Pool` and `Agent Results`.
`Benchmark Selection` is a durable output of Selection that joins them under a
frozen origin and budget.

Runner receives user config and calls the owner modules:

```text
User config or task source
  -> Task Pool
  -> frozen Task + Check records

Runner + Task Pool + Agent config + workspace config
  -> Workspace
  -> Verification
  -> Result Store
  -> Agent Results

Task Pool + Agent Results + origin + budget + selector config
  -> RollingOrigin + Feature Snapshot
  -> Selection
  -> frozen Benchmark Selection + rolling-origin metrics

Task Pool + Agent Results + Benchmark Selection + metrics
  -> Reporting
  -> report + machine-readable summary
```

Records is used by every arrow in the graph. It validates data at module
boundaries and assigns stable identities; it does not own system behavior.
Runner owns the arrows between modules. It does not own the records produced by
those modules.

## Core Data Objects

### Task

Solver-visible problem material plus repository metadata. A `Task` never
contains hidden check material or future outcome data.

### Check

Acceptance method for a `Task`. A `Check` may be a test command, script,
visual check, user-supplied check, human-reviewed result, or LLM-judged check
when the judgment process is explicitly represented.

### Workspace

Isolated checkout for solving or verification. Solver workspaces receive only
solver-visible material. Verifier workspaces receive hidden check material
after the Agent diff is captured.

### Result

One Agent on one Task under one environment and runtime config. A `Result`
contains status, pass/fail/invalid, cost, pricing version, usage coverage,
latency, failure label, captured diff digest, verifier metadata, and the time
the result became available for selector use.

A reusable `Result` is matched by `ResultCacheIdentity`, which stores the
structured task, check, Agent, workspace, runtime, scoring, adapter, and
optional hardware identity plus a digest. Results with incomplete identity are
not cache hits.

### Selector

A function that chooses benchmark tasks from a pre-origin history pool under a
budget. A selector may use task metadata and past outcomes available at the
origin, but never future holdout outcomes. A persistent Selector is stored as a
`SelectorRecord` with version, training source digests, and allowed feature
metadata.

### RollingOrigin

Evaluation protocol that freezes an origin time, selects from pre-origin
history, and compares selected-benchmark performance with later holdout
performance. The policy records as-of cutoffs, embargo, cluster constraints,
eligibility mode, and holdout overlap rules.

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

## Module Boundary Rules

- Task Pool does not run Agents.
- Workspace does not select benchmark tasks.
- Result Store does not inspect raw Agent transcripts for selector features.
- Selection does not read solver workspaces, verifier logs, hidden check text,
  raw reference patches, or future outcomes.
- Reporting does not create new evidence; it only summarizes existing records.
- Runner does not implement task generation, selection, Agent execution,
  verification, result scoring, or reporting logic. It only calls the owner
  modules in a defined order.

## Source Alignment Check

Aligned with the architecture:

- Keeps `Task`, `Check`, `Workspace`, `Result`, `Selector`, and
  `RollingOrigin` as first-class objects.
- Keeps `Task Pool`, `Benchmark Selection`, and `Agent Results` decoupled.
- Treats Selector as the core research claim.
- Keeps Agent tuning outside the predictive-validity claim.
- Does not import archived experiment abstractions.
