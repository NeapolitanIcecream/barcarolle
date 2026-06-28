# Barcarolle

Barcarolle is a target-repository benchmark compiler for coding Agents.
Its north star is predictive validity: whether a benchmark selected from
repository history predicts later Agent performance on that same repository.

## Quickstart

```bash
uv run pytest
```

## Active Code

The implementation lives in `barcarolle/`:

- `records.py`: shared record contracts, validation, canonical JSON, and
  digests.
- `task_pool.py`: Task + Check generation, import, certification, and frozen
  task-pool summaries.
- `verification.py`: hidden-oracle preparation, check execution, and normalized
  outcomes.
- `workspace.py`: solver/verifier workspaces, Agent harness invocation, diff
  capture, replay, and verification orchestration.
- `result_store.py`: append-only Result records, exact cache identity reuse,
  missing-cell queries, and result matrices.
- `selection.py`: rolling-origin construction, leakage-checked selector inputs,
  benchmark selection, and metrics.
- `reporting.py`: claim-safe reports from existing records.
- `runner.py`: command-level orchestration across the owner modules.

Tests live in `tests/` and mirror the module boundaries.

## Design

Design documents are under `docs/design/`:

- [Design index](docs/design/README.md)
- [System design](docs/design/system-design.md)
- [Data flow](docs/design/data-flow.md)
- [Source alignment check](docs/design/source-alignment-check.md)

Module-level designs live under [docs/design/modules](docs/design/modules).

The design source materials are:

- [System architecture](docs/architecture/v2-system-architecture-2026-06-25.md)
- [Learned selector roadmap](docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md)

## Vocabulary

Core data vocabulary:

- `Task`
- `Check`
- `Workspace`
- `Result`
- `Selector`
- `RollingOrigin`
- `Task Pool`
- `Benchmark Selection`
- `Agent Results`

Current modules:

- `Records`
- `Task Pool`
- `Verification`
- `Workspace`
- `Result Store`
- `Selection`
- `Reporting`
- `Runner`

## Archive

`archive/` contains historical reference material. It is not needed for normal
use of the current package, tests, or design documents.
