# Module Design: Task Pool

Status: draft, 2026-07-14.

## Responsibility

Generate or import `Task + Check` candidates, validate them by execution, and
freeze accepted records into a `Task Pool`.

Task Pool does not run Agents and does not select benchmarks.

## Inputs

- target repository reference;
- generator config or user import path;
- origin or time range;
- check construction config;
- task-validation config.

## Outputs

- `TaskPoolRecord`;
- accepted `TaskRecord` records;
- accepted `CheckRecord` records;
- rejected candidates;
- task-validation evidence.

## System Boundary

Input sources:

- user config;
- built-in generators;
- user imports;
- Workspace for checkout and replay during task validation;
- Verification for check execution during task validation.

Output consumers:

- Workspace;
- Result Store;
- Selection;
- Reporting.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Execution-Based Task Validation

The generic validation contract uses observable transitions:

- the task check fails at the base commit;
- when a reference patch is supplied, the task check passes after applying it;
- checks are repeated when repeatability or suspected flakiness needs evidence.

SWE-bench adapters preserve the standard `FAIL_TO_PASS` and `PASS_TO_PASS`
labels. `FAIL_TO_PASS` checks fail at the base and pass with the reference
patch; `PASS_TO_PASS` regression checks pass in both states. The generic Task
Pool does not introduce alternate names for them.

## Functions

### generate_history_candidates

Input:

- `repository_url_or_path: str`
- `time_range: TimeRange`
- `task_source_config: TaskSourceConfig`

Output:

- `Sequence[TaskCandidate]`

Effect:

- Produces candidates from repository history using issue, PR, commit, test, and
  release data available within the time range.

### import_task_pool

Input:

- `source_path: Path`
- `import_config: ImportConfig`

Output:

- `Sequence[TaskCandidate]`

Effect:

- Converts a user-provided pool into candidate `Task + Check` records.

### build_task_statement

Input:

- `candidate: TaskCandidate`
- `statement_config: StatementConfig`

Output:

- `task_text: str`

Effect:

- Builds solver-visible task text from allowed issue, PR, commit, release, or
  user-provided material. If LLM assistance is later used, only sanitized
  output and generation digest are stored.

### build_check_candidate

Input:

- `candidate: TaskCandidate`
- `check_config: CheckConfig`

Output:

- `CheckRecord`

Effect:

- Builds the acceptance method associated with the task. The check may be
  tests, scripts, visual evaluation, user-provided commands, or a defined
  review protocol.

### certify_task_candidate

Input:

- `candidate: TaskCandidate`
- `certification_config: CertificationConfig`

Output:

- `CertificationResult`

Effect:

- Validates checkout, dependency restoration, the base-fail and optional
  reference-patch-pass transitions, solver-visible material, hidden material
  separation, requested repeatability, and statement clarity. It may call
  Workspace and Verification, but it does not run Agents.

### freeze_task_pool

Input:

- `accepted_tasks: Sequence[TaskRecord]`
- `accepted_checks: Sequence[CheckRecord]`
- `rejected: Sequence[CertificationResult]`
- `metadata: Mapping[str, object]`

Output:

- `TaskPoolRecord`

Effect:

- Writes a frozen task pool with accepted Task/Check record references,
  rejection summaries, task-validation evidence, and source-event inventory
  digests.

### summarize_task_pool

Input:

- `task_pool: TaskPoolRecord`

Output:

- `Mapping[str, object]`

Effect:

- Reports task counts, check types, generator families, validation coverage,
  rejection reasons, and time coverage.

## Related-Work Mapping

This module is where SWE-bench-style issue/PR tasks, Verified-style quality
filters, Live-style origin freezing, large-supply generation, SWE-smith-style
environment generation, SWE-Future-style forecast-conditioned synthesis, and
user-provided pools are represented as generator or importer functions.

## Design Consistency Check

- Treats generator output as `Task + Check`.
- Reuses related-work task-generator methods instead of renaming them.
- Preserves rejected source events for supply notes.
- Leaves Agent execution to Workspace and benchmark choice to Selection.
