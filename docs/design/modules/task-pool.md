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
- certification policy;
- check construction config.

## Outputs

- `TaskPoolRecord`;
- accepted `TaskRecord` rows;
- accepted `CheckRecord` rows;
- rejection summaries.

## Functions

### generate_history_candidates

Input:

- `repository: RepositoryRef`
- `time_range: TimeRange`
- `generator_config: GeneratorConfig`

Output:

- `Sequence[TaskCandidate]`

Effect:

- Produces candidates from repository history using issue, PR, commit, test, and
  release data available within the time range.

### import_task_pool

Input:

- `source_path: Path`
- `import_policy: ImportPolicy`

Output:

- `Sequence[TaskCandidate]`

Effect:

- Converts a user-provided pool into candidate `Task + Check` records.

### build_task_statement

Input:

- `candidate_source: CandidateSource`
- `statement_policy: StatementPolicy`

Output:

- `TaskStatement`

Effect:

- Builds solver-visible task text from allowed issue, PR, commit, release, or
  user-provided material. If LLM assistance is later used, only sanitized
  output and generation digest are stored.

### build_check_candidate

Input:

- `candidate_source: CandidateSource`
- `check_policy: CheckPolicy`

Output:

- `CheckCandidate`

Effect:

- Builds the acceptance method associated with the task. The check may be
  tests, scripts, visual evaluation, user-provided commands, or a defined
  review protocol.

### certify_task_candidate

Input:

- `candidate: TaskCandidate`
- `certification_policy: CertificationPolicy`

Output:

- `CertificationResult`

Effect:

- Validates checkout, dependency restoration, check execution, solver-visible
  boundary, hidden material separation, stability, and statement clarity.

### freeze_task_pool

Input:

- `accepted: Sequence[CertifiedTask]`
- `rejected: Sequence[CertificationResult]`
- `pool_metadata: TaskPoolMetadata`

Output:

- `TaskPoolRecord`

Effect:

- Writes a frozen task pool with accepted records and rejection summaries.

### summarize_task_pool

Input:

- `task_pool: TaskPoolRecord`

Output:

- `TaskPoolSummary`

Effect:

- Reports task counts, check types, generator families, certification coverage,
  rejection reasons, and time coverage.

## Related-Work Mapping

This module is where SWE-bench-style issue/PR tasks, Verified-style quality
filters, Live-style origin freezing, large-supply generation, SWE-smith-style
environment generation, SWE-Future-style forecast-conditioned synthesis, and
user-provided pools are represented as generator or importer functions.

## Source Alignment Check

Aligned with the V2 architecture:

- Treats generator output as `Task + Check`.
- Reuses related-work task-generator methods instead of renaming them.
- Preserves rejected source events for supply diagnostics.
- Leaves Agent execution to Workspace and benchmark choice to Selection.
