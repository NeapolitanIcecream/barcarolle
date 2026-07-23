# Module Design: Task Pool

Status: current behavior and planned boundaries, 2026-07-23.

## Responsibility

Filter or import `Task + Check` candidates, retain a sanitized source-event
denominator, validate candidates by execution, and freeze the complete evidence
bundle into a `Task Pool`.

Task Pool does not run Agents and does not select benchmarks.

## Inputs

- candidates carrying a stable target `repository_id`, or a generator config
  or user import path that produces them;
- origin or time range;
- per-candidate reference patch;
- `WorkspaceConfig`, `RuntimeConfig`, certification config, and the repository
  and Check material bindings already established in Runner's immutable
  `WorkspaceRunContext`.

Generated pools persist the canonical source time range. The generator digest
describes generation behavior; the SourceEvent digest describes the observed
inventory. Keeping those identities separate lets a later pool use the same
source behavior while adding post-origin events.

## Outputs

- `TaskPoolRecord`;
- accepted `TaskRecord` records;
- accepted `CheckRecord` records;
- accepted, rejected, and excluded `SourceEventRecord` records;
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

- one aggregate Check fails at the base commit in a fresh verifier Workspace;
- the same Check passes after the reference patch is applied in another fresh
  verifier Workspace;
- `repeat_count` repeats that whole base-fail/patched-pass pair. A later base
  pass or patched failure rejects the candidate instead of treating the first
  pair as sufficient.
- `CertificationConfig` requires `repeat_count` to be an exact positive
  integer when the config is constructed. Booleans and integer-valued floats
  cannot enter certification or its evidence digest.

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
- optional `dependency_cluster_id` for dependence-aware origin blocking and
  optional `sampling_stratum` for coverage or difficulty stratification. Empty
  values stay empty rather than being replaced by a default label;
- Check type, command digest, hidden-material digest, optional
  `resource_limits`, and oracle source.

The candidate does not carry another representation of the task or a separate
Check configuration object. `task_text` is the solver-visible instruction.
History and import payloads must provide their declared string fields as
strings; Task Pool does not turn numeric or boolean source identities, task
text, dependency clusters, or sampling strata into text. Solver material refs
must be a string sequence. Resource limits must be a mapping with string keys.
These checks run before the default candidate ID is derived and also apply when
an event is excluded before certification.

## Adapter-Owned Dependence Evidence

Task Pool accepts a derived `dependency_cluster_id`; it does not own a generic
relation graph or source-ingestion service. A concrete adapter that supplies a
nonempty cluster must retain enough sanitized evidence to deterministically
reproduce it, bind that artifact through its generator config, and validate the
derived cluster against persisted SourceEvents before execution.

The Pylint SWE-bench adapter implements this with trusted reference-patch
digests and repository-relative changed-path footprints. Exact path overlap
forms relation edges and deterministic connected components. It persists no
raw patch text, and the relation paths and component IDs are not solver-visible
or Selector features. Additional issue/PR, revert, or cherry-pick relations
remain concrete-adapter work when those sources are available.

## Functions

`CandidateBatch` keeps the accepted-for-certification candidates and the source
events excluded before certification. This is a direct value object, not an
ingestion framework.

### filter_history_candidates

Input:

- `repository_id: str`
- `time_range: TimeRange`
- `task_source_config: TaskSourceConfig`

Output:

- `CandidateBatch`

Effect:

- Filters caller-provided sanitized source events by source time and required
  task/check material. Events outside the range or without usable task material
  are retained as excluded source events. Events without Check material remain
  right-censored rather than disappearing.
- The source window is later frozen into `TaskPoolRecord`; changing it changes
  Task Pool and bundle identity even when no event lies near the boundary.
- Does not collect issue-tracker or Git history. Concrete adapters own source
  collection and pass sanitized event mappings to this function.

### import_task_candidates

Input:

- `source_path: Path`
- `import_config: ImportConfig`

Output:

- `Sequence[TaskCandidate]`

Effect:

- Converts a user-provided pool into candidate `Task + Check` records.

### candidate_batch

Input:

- `candidates: Sequence[TaskCandidate]`

Output:

- `CandidateBatch`

Effect:

- Wraps already constructed candidates with no excluded events. This is the
  direct path used by import and programmatic adapters.

### finalize_source_event_records

Input:

- `batch: CandidateBatch`
- `certification_results: Sequence[CertificationResult]`

Output:

- ordered `Sequence[SourceEventRecord]`

Effect:

- Requires an exact boolean certification decision and exact certification
  coverage for every candidate, joins accepted or rejected Task/Check links and
  reasons, preserves pre-certification excluded events, validates self-digests,
  and rejects duplicate source identities or duplicate non-null candidate IDs.
- Persists source arrival, nullable label maturity, dependency cluster, and
  sampling stratum without raw patches or oracle content.
- Keeps cross-artifact Task/Check/certification reconciliation at
  `freeze_task_pool`; finalization validates only the transient decision shape
  and the SourceEvent records it creates.

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
- `run_context: WorkspaceRunContext`

Output:

- `CertificationResult`

Effect:

- Validates WorkspaceConfig and RuntimeConfig before any Check execution or
  certification-evidence digest is produced.
- For each attempt from one through `repeat_count`, requires the already-bound
  aggregate Check to fail at the base commit in one fresh Workspace, then
  applies the reference patch in a second fresh Workspace and requires the same
  Check to pass.
- Validates the direct task text and optional repository-relative solver
  material refs. It uses Workspace and Verification but does not run Agents.
- Stores normalized outcomes and the reference-patch digest, not the patch,
  workspace contents, or raw Check output.
- Rejects a bad candidate transition. Missing repository or Check bindings,
  verifier-workspace failures, check-launch failures, and unexpected
  verification failures are run-setup errors because they prevent comparable
  candidate evaluation; they stop certification instead of shrinking the
  pool.

### certification_evidence_records

Input:

- `results: Sequence[CertificationResult]`

Output:

- ordered sanitized evidence records

Effect:

- Requires an exact boolean decision, orders evidence by candidate ID, rejects
  duplicates, and verifies each evidence digest against its structured content.
  The canonical digest of this exact sequence is stored in
  `TaskPoolRecord.certification_evidence_digest`.
- Each evidence record binds the Workspace and Runtime configuration digests,
  the exact Check execution binding (command, hidden destination, and canonical
  hidden tree), and the built-in Verification adapter digest. Certification is
  invalid if any value is missing, the adapter is unsupported, or candidates
  in one Task Pool use different Workspace or Runtime digests. Check execution
  bindings remain candidate-specific.

### freeze_task_pool

Input:

- `accepted_tasks: Sequence[TaskRecord]`
- `accepted_checks: Sequence[CheckRecord]`
- `certification_results: Sequence[CertificationResult]`
- `source_events: Sequence[SourceEventRecord]`
- `metadata: Mapping[str, object]`, including the SourceEvent, Task, Check, and
  certification-evidence refs

Output:

- `TaskPoolRecord`

Effect:

- Constructs a frozen task-pool record with accepted Task/Check record refs and
  digests, rejected candidate IDs, certification evidence ref and digest, and
  the exact source-event record ref and digest. Generated pools also bind the
  canonical source-window start and end.
- Requires repository ID, artifact refs, configuration digests, and creation
  time to be nonempty strings, and an optional Task Pool ID to be a string,
  before identity construction. It does not stringify caller values.
- Validates window shape, canonical times, ordering, and creation boundary
  separately from per-event disposition and outside-range-reason alignment,
  then returns their one ordered error sequence.
- Performs no file I/O. Runner publishes the exact SourceEvent, Task, Check, and
  sanitized certification sequences as one immutable content-addressed bundle.
- Publication writes and validates a sibling staging directory, fsyncs every
  member and that directory, renames it to an absent target, and fsyncs the
  target parent. An existing target is reusable only when all members match.

### validate_task_pool_artifacts

Input:

- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Sequence[CheckRecord]`
- `certification_evidence: Sequence[Mapping[str, object]]`
- `source_events: Sequence[SourceEventRecord]`

Output:

- `ValidationResult`

Effect:

- Reuses the Records-owned required-shape, latest-schema, and self-digest
  validation for `TaskPoolRecord` itself. A malformed creation timestamp or
  other non-reloadable top-level field returns a schema error; shared timestamp
  parsing also rejects non-strings through the validation-safe `ValueError`
  contract rather than raising an attribute error during reconciliation.
- Treats the valid Task Pool record and Task/Check member layer as ordered
  prerequisites. Certification and SourceEvent reconciliation do not run when
  either layer is invalid, so downstream relations never assume a malformed
  top-level collection or member binding. Within the member layer, each Task
  and Check passes its Records validator before repository, digest, ID, or
  Task/Check linkage relations are evaluated.
- Reuses Task/Check validation and linkage rules for persisted artifacts.
- Requires exact accepted Task/Check and rejected-candidate evidence coverage,
  exactly `repeat_count` failing base checks and passing reference-patch checks
  for every accepted pair, and matching certification-config, evidence,
  source-event, and rejection-summary digests.
- Requires persisted certification evidence to retain canonical candidate-ID
  order and the rejected-candidate tuple to match that ordered evidence.
- Requires every certification record in the pool to share one WorkspaceConfig
  digest and one RuntimeConfig digest.
- Requires each normalized attempt to keep outcome state coherent: a pass has
  no failure label, a non-pass has a non-empty failure label, and a timeout is
  an invalid outcome. Non-object records and malformed nested evidence return
  validation errors instead of interrupting SourceEvent reconciliation.
- Requires source events to exactly link accepted records and certification
  decisions one-to-one while allowing excluded or right-censored events to
  remain unlinked.
- Requires a declared source window to end no later than Task Pool creation.
  Events outside it must be excluded with `outside_source_time_range`; accepted
  or certification-rejected events outside it fail validation.
- Is used by freeze and Reporting; it does not execute Checks again.

### summarize_task_pool

Input:

- `task_pool: TaskPoolRecord`

Output:

- `Mapping[str, object]`

Effect:

- Reports counts and frozen identity fields from the pool record. Reporting
  loads the bundle to derive check types, source dispositions, label delays,
  validation coverage, and rejection reasons.

## Related-Work Mapping

This module receives sanitized candidates from SWE-bench-style or repository-
specific adapters and user imports. Adapter-specific issue/PR collection,
environment construction, and forecast-conditioned synthesis remain outside
the core until a concrete adapter needs them.

## Design Consistency Check

- Treats generator output as `Task + Check`.
- Reuses related-work task-generator methods instead of renaming them.
- Preserves accepted, rejected, excluded, and right-censored source events as
  auditable bundle evidence.
- Leaves Agent execution to Workspace and benchmark choice to Selection.
