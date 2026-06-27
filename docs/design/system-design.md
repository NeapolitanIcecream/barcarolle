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
| Records | Shared record schemas, identity rules, validation errors, and JSON/JSONL serialization contracts. | Record definitions; record payloads produced by other modules. | Design docs; Task Pool; Checks; Workspace; Results; Selection; Reporting; Runner. | Validated `Task`, `Check`, `Result`, `Benchmark Selection`, metric, and report records; validation errors; stable IDs. | All modules. |
| Task Pool | Task generation, task import, task certification, rejected-task summaries, and frozen task-pool files. | Target repository reference; task-source config; user-provided tasks; check construction config; certification config. | User config; built-in generators; user imports; Checks for executable-check validation; Workspace for checkout/replay validation. | Frozen `Task Pool`; accepted `Task + Check` records; rejected candidates; certification evidence. | Workspace; Results; Selection; Reporting. |
| Checks | Check execution interface and normalized check outcomes. | `Check`; verifier workspace path; candidate diff already applied; check runtime config. | Task Pool provides `Check`; Workspace provides verifier workspace and applied diff. | Normalized check outcome: pass, fail, invalid, failure label, sanitized evidence summary. | Workspace; Results; Reporting. |
| Workspace | Solver workspace creation, Agent invocation, diff capture, verifier workspace creation, diff replay, and check orchestration. | `Task`; `Check`; Agent config; workspace config; runtime config. | Task Pool provides `Task + Check`; user or run config provides Agent and configs; Checks provides check runner. | Captured diff digest; execution metadata; check outcome; workspace-level failure classification. | Results. |
| Results | Result cache identity, result storage, missing-run queries, and result matrices. | `Task`; `Check`; Agent config; workspace output; check outcome. | Task Pool; Workspace; Checks; Records. | Reusable `Result` records; result cache state; result matrix; missing Agent-task runs. | Selection; Reporting; Runner. |
| Selection | Rolling-origin construction, selector execution, selector training/evaluation, and `Benchmark Selection` records. | Frozen `Task Pool`; `Agent Results`; origin; budget; candidate Agents; selector config. | Task Pool; Results; user or experiment config; selector roadmap. | `Benchmark Selection`; selected task IDs and weights; rolling-origin metrics; selector notes. | Reporting; Runner. |
| Reporting | Claim-safe summaries, audit reports, and machine-readable closeouts. | `Task Pool`; `Benchmark Selection`; `Agent Results`; rolling-origin metrics; artifact digests. | Task Pool; Results; Selection; Records. | Human-readable report; machine-readable summary; claim-boundary statement. | Users. |
| Runner | Command-level orchestration across modules, including cache reuse and lazy Agent execution. | Run config; target repository; task-source config; Agent set; origin; budget; selector config; result store; workspace config; runtime config; report config. | Users; Task Pool; Results; Selection; Workspace; Reporting. | Run summary; references to records produced by owner modules; report paths. | Users. |

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
  -> Checks
  -> Results
  -> Agent Results

Task Pool + Agent Results + origin + budget + selector config
  -> Selection
  -> Benchmark Selection + rolling-origin metrics

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
contains status, pass/fail/invalid, cost, latency, failure label, captured diff
digest, and verifier metadata.

### Selector

A function that chooses benchmark tasks from a pre-origin history pool under a
budget. A selector may use task metadata and past outcomes available at the
origin, but never future holdout outcomes.

### RollingOrigin

Evaluation protocol that freezes an origin time, selects from pre-origin
history, and compares selected-benchmark performance with later holdout
performance.

## Result Reuse And Lazy Execution

The normal flow is: build a `Task Pool`, obtain `Agent Results`, then let
Selection choose a `Benchmark Selection` for a frozen origin. Two optimizations
keep this affordable.

### Cache Reuse

When `Agent Results` already exist for some Agent-task runs, selectors reuse
those results instead of re-running paid Agent runs. This is what makes repeated
selector research possible.

### Lazy Agent Execution

When Agent execution is expensive and results are sparse, Selection can choose
a benchmark first. Workspace then runs only selected Agent-task runs whose
results are missing from the cache. Runner is the module that calls Results to
find missing results, Workspace to execute them, and Results again to store
them.

## Module Boundary Rules

- Task Pool does not run Agents.
- Workspace does not select benchmark tasks.
- Results does not inspect raw Agent transcripts for selector features.
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
