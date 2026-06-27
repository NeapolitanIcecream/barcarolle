# Module Design: Task Pool

Status: draft, 2026-06-27.

## Responsibility

Generate or import `Task + Check` candidates, certify them, and freeze them
into a `Task Pool`.

Task Pool does not run Agents and does not select benchmarks.

## Inputs

- target repository reference;
- generator config or user import path;
- origin or time range;
- check construction config;
- certification config.

## Outputs

- `TaskPoolRecord`;
- accepted `TaskRecord` records;
- accepted `CheckRecord` records;
- rejected candidates;
- certification evidence.

## System Boundary

Input sources:

- user config;
- built-in generators;
- user imports;
- Workspace for checkout and replay validation during certification;
- Verification for executable-check validation during certification.

Output consumers:

- Workspace;
- Result Store;
- Selection;
- Reporting.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

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

- Validates checkout, dependency restoration, check execution, solver-visible
  boundary, hidden material separation, stability, and statement clarity. It may
  call Workspace and Verification for certification, but it does not run Agents.

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
  rejection summaries, certification evidence, and source-event inventory
  digests.

### summarize_task_pool

Input:

- `task_pool: TaskPoolRecord`

Output:

- `Mapping[str, object]`

Effect:

- Reports task counts, check types, generator families, certification coverage,
  rejection reasons, and time coverage.

## Related-Work Mapping

This module is where SWE-bench-style issue/PR tasks, Verified-style quality
filters, Live-style origin freezing, large-supply generation, SWE-smith-style
environment generation, SWE-Future-style forecast-conditioned synthesis, and
user-provided pools are represented as generator or importer functions.

## Source Alignment Check

Aligned with the architecture:

- Treats generator output as `Task + Check`.
- Reuses related-work task-generator methods instead of renaming them.
- Preserves rejected source events for supply notes.
- Leaves Agent execution to Workspace and benchmark choice to Selection.
