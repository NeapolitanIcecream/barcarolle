# Barcarolle

Barcarolle is a target-repository benchmark compiler for coding Agents.
Its north star is predictive validity: whether a benchmark selected from
repository history predicts later Agent performance on that same repository.

## Active Sources

The active design uses only two source materials:

- [System architecture](docs/architecture/v2-system-architecture-2026-06-25.md)
- [Learned selector roadmap](docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md)

Everything else from the previous codebase and prior experiments has been moved
to archive for reference only.

## Active Design

- [Design index](docs/design/README.md)
- [System design](docs/design/system-design.md)
- [Data flow](docs/design/data-flow.md)
- [Source alignment check](docs/design/source-alignment-check.md)

Module-level designs live under [docs/design/modules](docs/design/modules).

## Current Boundary

This repository is in design mode. Do not build the current system by copying
archived modules. Use archived material only as historical evidence after an
explicit review decides what to port.

Core vocabulary stays small:

- `Task`
- `Check`
- `Workspace`
- `Result`
- `Selector`
- `RollingOrigin`
- `Task Pool`
- `Benchmark Selection`
- `Agent Results`
