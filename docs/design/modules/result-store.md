# Module Design: Result Store

Status: draft, 2026-06-27.

## Responsibility

Store, query, and join reusable `Result` records for Agent-task-check cells.

Result Store does not execute Agents and does not choose benchmark tasks.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `ResultCacheIdentity`;
- `WorkspaceRunRecord`;
- cache and scoring config.

## Outputs

- `ResultRecord`;
- result cache state;
- cached result queries;
- `ResultMatrix`;
- result completeness and exclusion metadata;
- missing Agent-task-check cells.

## System Boundary

Input sources:

- Task Pool;
- Workspace;
- Verification;
- Records.

Output consumers:

- Selection;
- Reporting;
- Runner.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### build_result_record

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_run: WorkspaceRunRecord`
- `cache_identity: ResultCacheIdentity`
- `scoring_config: ScoringConfig`

Output:

- `ResultRecord`

Effect:

- Normalizes pass/fail/invalid, cost, latency, failure label, diff digest, and
  verifier metadata, and stores the exact cache identity used for reuse.

### compute_result_cache_identity

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`

Output:

- `identity: ResultCacheIdentity`

Effect:

- Produces the structured identity used to decide whether a cached result is
  reusable.

### compute_result_cache_key

Input:

- `identity: ResultCacheIdentity`

Output:

- `cache_key: str`

Effect:

- Produces the digest key for a complete `ResultCacheIdentity`. Results with
  missing identity fields are not reusable cache hits.

### store_result

Input:

- `result: ResultRecord`
- `store: ResultStore`

Output:

- `ResultRecord`

Effect:

- Writes or updates a result record according to the store config.

### load_results

Input:

- `store: ResultStore`
- `query: ResultQuery`

Output:

- `Sequence[ResultRecord]`

Effect:

- Reads result records matching task, Agent, origin, cache, and config filters.

### find_missing_results

Input:

- `task_check_refs: Sequence[TaskCheckRef]`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `store: ResultStore`
- `cache_config: ResultCacheConfig`

Output:

- `Sequence[ResultCellRef]`

Effect:

- Builds the required `ResultCacheIdentity` for each requested
  Agent-task-check cell, isolates incomplete or stale cached results, and
  returns missing cells as `ResultCellRef` records with `cell_state=missing`
  for Runner to execute through Workspace.

### build_result_matrix

Input:

- `task_check_refs: Sequence[TaskCheckRef]`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `results: Sequence[ResultRecord]`
- `matrix_role: ResultMatrixRole`
- `join_config: ResultJoinConfig`

Output:

- `ResultMatrix`

Effect:

- Joins results into a table for Selection and Reporting. The matrix includes
  one `ResultCellRef` per Agent-task-check cell, plus completeness,
  exclusions, missing cells, join policy, abstention metadata, and whether the
  matrix is for the selected benchmark or future holdout.

## Join And Denominator Policy

`ResultJoinConfig` must explicitly define:

- required result cache identity;
- missing-cell policy;
- Agent-attributable invalid outcome policy;
- benchmark infrastructure failure policy;
- denominator policy;
- abstention policy.

Agent-attributable invalid outcomes such as timeout, no meaningful patch, or
budget exhaustion are failures. Benchmark infrastructure failures are not Agent
failures. Persistent task-level infrastructure failures should be removed from
all Agents' denominators for that matrix. If required Agent-task-check cells
are missing and cannot be filled under the configured policy, the matrix must
carry an abstention reason instead of silently scoring a partial comparison.

## Source Alignment Check

Aligned with the architecture:

- Makes paid Agent results durable and reusable.
- Enforces exact cache identity.
- Gives Selection result matrices instead of raw workspaces or transcripts.
- Matches the roadmap's invalid-outcome and cache-identity requirements.
