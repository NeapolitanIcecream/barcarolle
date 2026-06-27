# Barcarolle V2 Design Index

Status: draft design set for the clean v2 rewrite, 2026-06-27.

## Source Materials

This design set uses only:

- `docs/architecture/v2-system-architecture-2026-06-25.md`
- `docs/design-inputs/learned-selector-roadmap-gpt-5-5-pro-2026-06-25.md`

The architecture document is authoritative for system boundary and vocabulary.
The roadmap is authoritative only for Selector algorithm design.

## Documents

- [System design](system-design.md): module boundaries and responsibilities.
- [Data flow](data-flow.md): how data moves between modules.
- [Source alignment check](source-alignment-check.md): drift check against the
  architecture document.

Module-level design:

- [Records](modules/records.md)
- [Task Pool](modules/task-pool.md)
- [Checks](modules/checks.md)
- [Workspace](modules/workspace.md)
- [Results](modules/results.md)
- [Selection](modules/selection.md)
- [Reporting](modules/reporting.md)

## Update Rule

These documents are not append-only. When a module-level design clarifies a
field, function, or boundary, update the system and data-flow documents in the
same change.
