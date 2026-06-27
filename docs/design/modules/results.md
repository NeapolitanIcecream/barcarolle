# Module Design: Results

Status: draft, 2026-06-27.

## Responsibility

Store, query, and join reusable `Result` records for Agent-task runs.

Results does not execute Agents and does not choose benchmark tasks.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `WorkspaceRunRecord`;
- cache and scoring config.

## Outputs

- `ResultRecord`;
- result cache state;
- cached result queries;
- `ResultMatrix`;
- missing Agent-task runs.

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
- `scoring_config: ScoringConfig`

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
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`

Output:

- `cache_key: str`

Effect:

- Produces the identity used to decide whether a cached result is reusable.

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

- `task_ids: Sequence[str]`
- `agents: Sequence[AgentRecord]`
- `store: ResultStore`
- `cache_config: ResultCacheConfig`

Output:

- `Sequence[MissingAgentTaskRun]`

Effect:

- Identifies selected Agent-task runs that need execution by Workspace.

### build_result_matrix

Input:

- `tasks: Sequence[TaskRecord]`
- `agents: Sequence[AgentRecord]`
- `results: Sequence[ResultRecord]`
- `join_config: ResultJoinConfig`

Output:

- `ResultMatrix`

Effect:

- Joins results into a table for Selection and Reporting.

## Invalid Outcomes

Agent-attributable invalid outcomes such as timeout, no meaningful patch, or
budget exhaustion are failures. Benchmark infrastructure failures are not Agent
failures and should be handled consistently across Agents.

## Source Alignment Check

Aligned with the architecture:

- Makes paid Agent results durable and reusable.
- Enforces exact cache identity.
- Gives Selection result matrices instead of raw workspaces or transcripts.
- Matches the roadmap's invalid-outcome and cache-identity requirements.
