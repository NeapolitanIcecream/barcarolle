# Barcarolle Design Reference

Status: active design authority, 2026-07-14.

These documents describe the intended Barcarolle module boundaries, data
contracts, and cross-module behavior. Use them when implementation details need
the benchmark boundary rather than an incidental code path.

The design assumes cooperative Agents unless an execution adapter states a
stronger threat model. Fresh solver/verifier workspaces and hidden-check
separation are core behavior; host-level isolation is optional.

The core follows only the latest schema. Small one-off migrations may preserve
valuable paid results after a schema change, but compatibility layers are not a
design goal. See [Implementation status](../implementation-status.md) for gaps
between these documents and the alpha runtime.

## Documents

- [System design](system-design.md): module boundaries and responsibilities.
- [Data flow](data-flow.md): how data moves between modules.
- [Design consistency check](source-alignment-check.md): consistency checks for
  vocabulary, module boundaries, and evidence flow.

Module-level design:

- [Records](modules/records.md)
- [Task Pool](modules/task-pool.md)
- [Verification](modules/verification.md)
- [Workspace](modules/workspace.md)
- [Result Store](modules/result-store.md)
- [Selection](modules/selection.md)
- [Reporting](modules/reporting.md)
- [Runner](modules/runner.md)

Each module-level document defines function boundaries. Functions specify
inputs, outputs, and effects only; they do not include implementation bodies.
The `System Boundary` section in each module document must stay consistent with
the module boundary table in [System design](system-design.md).
Names ending in `Config` are ordinary parameter groups, not first-class system
concepts or modules.

## Update Rule

These documents are not append-only. When a module-level design clarifies a
field, function, or boundary, update the system and data-flow documents in the
same change.
