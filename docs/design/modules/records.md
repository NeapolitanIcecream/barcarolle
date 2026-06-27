# Module Design: Records

Status: draft, 2026-06-27.

## Responsibility

Define shared record shapes and validation helpers for `Task`, `Check`,
`Workspace`, `Result`, `Selector`, and `RollingOrigin` data.

This module should not perform I/O beyond optional serialization helpers.

## Records

- `TaskRecord`
- `CheckRecord`
- `AgentRecord`
- `WorkspaceConfig`
- `RuntimeConfig`
- `SelectorRecord`
- `ResultRecord`
- `TaskPoolRecord`
- `BenchmarkSelectionRecord`
- `RollingOriginRecord`
- `MetricRecord`

## System Boundary

Input sources:

- Design docs;
- records produced by Task Pool, Verification, Workspace, Results, and
  Selection.

Output consumers:

- all modules.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### validate_task

Input:

- `task: TaskRecord`

Output:

- `ValidationResult`

Effect:

- Validates required task fields, timestamp order, solver-visible material, and
  absence of hidden check material.

### validate_check

Input:

- `check: CheckRecord`

Output:

- `ValidationResult`

Effect:

- Validates that the check has an execution type, bounded resource limits, and no
  solver-visible hidden material.

### validate_result

Input:

- `result: ResultRecord`

Output:

- `ValidationResult`

Effect:

- Validates cache identity fields, status fields, cost/latency fields, and failure
  labels.

### validate_selector

Input:

- `selector: SelectorRecord`

Output:

- `ValidationResult`

Effect:

- Validates selector identity, version, training source digests, allowed feature
  fields, and leakage boundary metadata.

### make_task_id

Input:

- `repository_id: str`
- `base_commit: str`
- `source_digest: str`

Output:

- `task_id: str`

Effect:

- Builds a stable task identifier. The function must not include future
  outcome data.

### make_check_id

Input:

- `task_id: str`
- `check_digest: str`

Output:

- `check_id: str`

Effect:

- Builds a stable check identifier.

### make_result_cache_key

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config_digest: str`

Output:

- `cache_key: str`

Effect:

- Returns the exact identity for a reusable Agent-task result.

### make_selector_id

Input:

- `selector_digest: str`

Output:

- `selector_id: str`

Effect:

- Builds a stable identifier for a persistent Selector.

### load_jsonl_records

Input:

- `path: Path`
- `record_type: type`

Output:

- `list[record_type]`

Effect:

- Reads normalized records. It should not interpret archived experiment
  formats.

### write_jsonl_records

Input:

- `path: Path`
- `records: Sequence[object]`

Output:

- `None`

Effect:

- Writes normalized records atomically.

## Source Alignment Check

Aligned with the architecture:

- Provides direct data contracts.
- Keeps the core vocabulary small.
- Enforces cache identity for Result reuse.
