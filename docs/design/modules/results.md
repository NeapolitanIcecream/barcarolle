# Module Design: Results

Status: draft, 2026-06-27.

## Responsibility

Store, query, and join reusable `Result` rows for `Agent x Task` cells.

Results does not execute Agents and does not choose benchmark tasks.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `WorkspaceRunRecord`;
- cache and scoring policy.

## Outputs

- `ResultRecord`;
- result-cache snapshot;
- cached result queries;
- `ResultMatrix`;
- missing Agent-task cells.

## System Boundary

Input sources:

- Task Pool;
- Workspace;
- Checks;
- Records.

Output consumers:

- Selection;
- Reporting;
- Workspace, for missing-cell execution.

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
- `scoring_policy: ScoringPolicy`

Output:

- `ResultRecord`

Effect:

- Normalizes pass/fail/invalid, cost, latency, failure label, diff digest, and
  verifier metadata.

### compute_result_cache_key

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_policy: WorkspacePolicy`
- `runtime_policy: RuntimePolicy`
- `scoring_policy: ScoringPolicy`

Output:

- `cache_key: str`

Effect:

- Produces the identity used to decide whether a cached result is reusable.

### store_result

Input:

- `result: ResultRecord`
- `store: ResultStore`

Output:

- `StoredResultRef`

Effect:

- Writes or updates a result row according to the store policy.

### load_results

Input:

- `store: ResultStore`
- `query: ResultQuery`

Output:

- `Sequence[ResultRecord]`

Effect:

- Reads result rows matching task, Agent, origin, cache, and policy filters.

### find_missing_results

Input:

- `task_ids: Sequence[str]`
- `agents: Sequence[AgentRecord]`
- `store: ResultStore`
- `identity_policy: ResultIdentityPolicy`

Output:

- `Sequence[MissingResultCell]`

Effect:

- Identifies selected `Agent x Task` cells that need execution by Workspace.

### build_result_matrix

Input:

- `tasks: Sequence[TaskRecord]`
- `agents: Sequence[AgentRecord]`
- `results: Sequence[ResultRecord]`
- `join_policy: ResultJoinPolicy`

Output:

- `ResultMatrix`

Effect:

- Joins results into a table for Selection and Reporting.

## Invalid Policy

Agent-attributable invalid outcomes such as timeout, no meaningful patch, or
budget exhaustion are failures. Benchmark infrastructure failures are not Agent
failures and should be handled consistently across Agents.

## Source Alignment Check

Aligned with the architecture:

- Makes paid Agent results durable and reusable.
- Enforces exact cache identity.
- Gives Selection result matrices instead of raw workspaces or transcripts.
- Matches the roadmap's invalid-cell and cache-identity requirements.
