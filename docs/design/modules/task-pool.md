# Module Design: Task Pool

Status: draft, 2026-07-14.

## Responsibility

Generate or import `Task + Check` candidates, validate them by execution, and
freeze accepted records into a `Task Pool`.

Task Pool does not run Agents and does not select benchmarks.

## Inputs

- candidates carrying a stable target `repository_id`, or a generator config
  or user import path that produces them;
- origin or time range;
- per-candidate reference patch;
- `WorkspaceConfig`, `RuntimeConfig`, certification config, and the repository
  and Check material bindings already established by Runner.

## Outputs

- `TaskPoolRecord`;
- accepted `TaskRecord` records;
- accepted `CheckRecord` records;
- rejected candidates;
- sanitized certification evidence.

## System Boundary

Input sources:

- user config;
- built-in generators;
- user imports;
- Workspace for checkout and replay during task validation;
- Verification for check execution during task validation.

Output consumers:

- Runner, which writes the referenced frozen files;
- Workspace;
- Result Store;
- Selection;
- Reporting.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Execution-Based Task Validation

The generic validation contract uses observable transitions:

- one aggregate Check fails at the base commit;
- the same Check passes after the reference patch is applied in a fresh
  verifier Workspace;
- the patched Check may be repeated in fresh verifier Workspaces.

This proves the aggregate fail-to-pass transition. It does not separately
certify SWE-bench `FAIL_TO_PASS` and `PASS_TO_PASS` sets. A SWE-bench adapter
that needs both must make its Check wrapper execute and distinguish both sets;
the generic Task Pool does not add another outcome vocabulary.

## Candidate Contract

`TaskCandidate` carries the fields needed to construct one `TaskRecord` and one
`CheckRecord`:

- stable repository and source identity;
- `base_commit` and source, task-material, and check-material availability
  timestamps;
- direct `task_text` plus optional `solver_material_refs` to files already in
  the repository checkout;
- optional `cluster_id`; an empty value means no cluster is recorded and is not
  replaced by a default label;
- Check type, command digest, hidden-material digest, optional
  `resource_limits`, and oracle source.

The candidate does not carry another representation of the task or a separate
Check configuration object. `task_text` is the solver-visible instruction.

## Functions

### generate_history_candidates

Input:

- `repository_id: str`
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

### build_check_candidate

Input:

- `candidate: TaskCandidate`

Output:

- `CheckRecord`

Effect:

- Builds the Check directly from the candidate fields. The executable command
  and hidden material are bound separately by Workspace and must match the
  candidate digests.

### certify_task_candidate

Input:

- `candidate: TaskCandidate`
- `certification_config: CertificationConfig`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `reference_patch: CapturedDiff`

Output:

- `CertificationResult`

Effect:

- Requires the already-bound aggregate Check to fail once at the base commit.
- Applies the reference patch in a fresh verifier Workspace and requires the
  same Check to pass. `repeat_count` repeats this patched Check in a new
  verifier Workspace each time.
- Validates the direct task text and optional repository-relative solver
  material refs. It uses Workspace and Verification but does not run Agents.
- Stores normalized outcomes and the reference-patch digest, not the patch,
  workspace contents, or raw Check output.
- Rejects a bad candidate transition. Missing repository or Check bindings are
  run-setup errors because they prevent all candidates from being evaluated.

### certification_evidence_records

Input:

- `results: Sequence[CertificationResult]`

Output:

- ordered sanitized evidence records

Effect:

- Orders evidence by candidate ID, rejects duplicates, and verifies each
  evidence digest against its structured content. The canonical digest of this
  exact sequence is stored in `TaskPoolRecord.certification_evidence_digest`.

### freeze_task_pool

Input:

- `accepted_tasks: Sequence[TaskRecord]`
- `accepted_checks: Sequence[CheckRecord]`
- `rejected: Sequence[CertificationResult]`
- `metadata: Mapping[str, object]`, including accepted certification results
  and the Task, Check, and certification-evidence refs

Output:

- `TaskPoolRecord`

Effect:

- Constructs a frozen task-pool record with accepted Task/Check record refs and
  digests, rejected candidate IDs, certification evidence ref and digest, and
  source-event inventory digests.
- Performs no file I/O. Runner writes the exact accepted Task records, accepted
  Check records, and sanitized certification evidence referenced by the frozen
  record.

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
