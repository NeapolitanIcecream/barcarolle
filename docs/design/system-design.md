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

## Modules

| Module | Owns | Inputs | Outputs | Sends Output To |
| --- | --- | --- | --- | --- |
| Records | Shared data shapes and validation contracts. | Design-level field definitions. | Typed records and validation errors. | All modules. |
| Task Pool | Generation, import, certification, and frozen task pools. | Target repository, generator config, user imports, Check definitions. | `Task Pool` containing `Task`, `Check`, metadata, and certification records. | Workspace, Results, Selection, Reporting. |
| Checks | Check execution contract and check outcome normalization. | `Check`, verifier `Workspace`, candidate diff. | Check outcome: pass, fail, invalid, evidence summary. | Workspace, Results. |
| Workspace | Solver/verifier workspace lifecycle and Agent execution boundary. | `Task`, `Check`, Agent config, workspace policy. | Captured diff, check outcome, execution metadata. | Results. |
| Results | Cache identity, result storage, and result joins. | `Task`, `Check`, Agent config, workspace output, check outcome. | Reusable `Result` rows and query results. | Selection, Reporting. |
| Selection | Rolling-origin windows, selectors, metrics, and selector comparison. | `Task Pool`, `Agent Results`, origin, budget, candidate Agents. | `Benchmark Selection`, prediction metrics, selector diagnostics. | Results, Reporting. |
| Reporting | Claim-safe reports and audit summaries. | `Task Pool`, `Benchmark Selection`, `Agent Results`, metrics. | Human-readable reports and machine-readable summaries. | Users. |

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

One Agent on one Task under one environment and runtime policy. A `Result`
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

## Execution Modes

### Cached Pool Mode

Use when `Agent Results` already exist for many `Agent x Task` cells.
Selectors choose virtual benchmarks and compute prediction error from cached
rows without re-running paid Agent cells.

### Select-Then-Run Mode

Use when Agent execution is expensive and results are sparse. The selector
chooses a benchmark first, then the system runs only missing Agent-task cells.

### Incremental Cache Fill Mode

Use when selector uncertainty is dominated by missing result cells. Selection
identifies which cells would reduce uncertainty, and Results records newly run
cells for later reuse.

## Module Boundary Rules

- Task Pool does not run Agents.
- Workspace does not select benchmark tasks.
- Results does not inspect raw Agent transcripts for selector features.
- Selection does not read solver workspaces, verifier logs, hidden check text,
  raw reference patches, or future outcomes.
- Reporting does not create new evidence; it only summarizes existing records.

## Source Alignment Check

Aligned with the architecture:

- Keeps `Task`, `Check`, `Workspace`, `Result`, `Selector`, and
  `RollingOrigin` as first-class objects.
- Keeps `Task Pool`, `Benchmark Selection`, and `Agent Results` decoupled.
- Treats Selector as the core research claim.
- Keeps Agent tuning outside the predictive-validity claim.
- Does not import archived experiment abstractions.
