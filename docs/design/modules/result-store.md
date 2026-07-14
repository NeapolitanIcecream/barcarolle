# Module Design: Result Store

Status: draft, 2026-07-14.

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

`ScoringConfig` accepts only `pricing_version` and `cost_rates`. Its
`scoring_config_digest` is the canonical digest of those values, not a
caller-supplied identifier.

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
- Treats `error` and `timeout` terminal states as Agent-attributable invalid
  results even if a Check also reported `fail`; only terminal `failed` is a
  scoreable failure.
- Carries harness-provided usage mappings into the `ResultRecord` and computes
  cost from numeric usage keys in `ScoringConfig.cost_rates`. Present priced
  values must be finite and nonnegative. If usage is absent, the rate mapping
  is empty, or any configured priced key is missing, total cost is stored as
  `null`, never zero. A zero total is measured only when at least one explicit
  rate is configured and all priced keys are present.
- Stores pricing provenance on the Result, outside `ResultCacheIdentity`, so a
  new price table can reprice retained usage without rerunning paid work.
- Derives `result_id` from the execution evidence digest and the derived
  scoring-config digest. Repricing the same execution through any prior price
  view therefore produces the same ID for the same target price table.

### result_execution_digest

Input:

- `result: ResultRecord`

Output:

- `execution_digest: str`

Effect:

- Digests the Result fields that describe one execution while excluding cost,
  pricing provenance, Result availability, and Result record identity.
- Gives all pricing views of the same execution one stable key without adding
  another record type.

### compute_result_cache_identity

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`

Output:

- `identity: ResultCacheIdentity`

Effect:

- Produces the structured identity used to decide whether a cached execution is
  reusable. A single `check_digest` binds all behavior-changing Check fields.
  Pricing and scoring are excluded.

### compute_cost

Input:

- `usage: Mapping[str, JSONValue]`
- `scoring_config: ScoringConfig`

Output:

- `Mapping[str, JSONValue]`

Effect:

- Computes a pricing view from retained usage without executing an Agent or a
  Check. Returns `total_cost=null` when usage is absent, no rates are
  configured, or a configured priced key is missing.

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

- Writes a result record append-only. Corrections or rescoring create a new
  `result_id` and `result_digest`; existing frozen records are not mutated.

### load_results

Input:

- `store: ResultStore`
- `query: ResultQuery`

Output:

- `Sequence[ResultRecord]`

Effect:

- Reads result records matching task, check, Agent, result ID, exact cache
  identity, scoring config, and result-availability time filters.
- Compares availability bounds as UTC instants, so equivalent timestamps with
  different offsets have the same ordering.

### resolve_result_cells

Input:

- `task_check_refs: Sequence[TaskCheckRef]`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `store: ResultStore`
- `cache_config: ResultCacheConfig`
- `scoring_config: ScoringConfig | None`

Output:

- `Sequence[ResultCellRef]`

Effect:

- Returns one result-or-missing cell for every requested Agent-task-check cell.
- Reuses only a valid, fully equal `ResultCacheIdentity` under
  `exact_identity`; a digest match alone is insufficient.
- Without `scoring_config`, resolves execution reuse independently of pricing.
  With it, resolves only the exact derived scoring-config digest so evaluation
  cells cannot bind a stale price view.
- Under the default valid-result policy, does not reuse benchmark-invalid
  infrastructure results. Agent-invalid results retain the existing reuse
  policy.
- If duplicate eligible records have the same exact identity, chooses the first
  record in append order.
- Loads and indexes matching stored results once per resolution operation.

### reprice_cached_results

Input:

- the same Task/Check/Agent, workspace, runtime, store, and cache inputs used
  for exact cell resolution;
- `scoring_config: ScoringConfig`.

Output:

- newly appended `Sequence[ResultRecord]` pricing views.

Effect:

- Finds reusable executions by exact `ResultCacheIdentity`.
- When the current derived scoring digest is missing, recomputes cost from the
  retained usage and appends a new Result without running the Agent or Check.
- Preserves the source Result and its `result_available_at`; a pricing view is
  not a new execution and cannot move old evidence into a later history window.
- Does nothing when that execution already has the requested pricing view.

### find_missing_results

Input:

- `task_check_refs: Sequence[TaskCheckRef]`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `store: ResultStore`
- `cache_config: ResultCacheConfig`

Output:

- `Sequence[ResultCellRef]`

Effect:

- Filters `resolve_result_cells` to return only `ResultCellRef` records with
  `cell_state=missing` for Runner to execute through Workspace.
- Uses pricing-independent resolution: a price-table change is never a reason
  to rerun the Agent.

### build_result_matrix

Input:

- `evaluation_cells: EvaluationCellSet`
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
  one `ResultCellRef` per Agent-task-check cell from `evaluation_cells`,
  filtered by matrix role, plus completeness, exclusions, missing cells, join
  policy, abstention metadata, and whether the matrix is for the selected
  benchmark or future holdout. The relevant `Task + Check` refs are derived
  from `evaluation_cells`; the `task_check_refs` input is a caller assertion
  that must exactly match the selected or future subset for `matrix_role`.
- Resolves only the exact `result_id`, `result_digest`, required identity, and
  outcome frozen in each `EvaluationCellSet` cell. A later result with the same
  cache identity cannot replace the frozen result; an absent frozen binding is
  handled as missing under the join policy.

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

## Design Consistency Check

- Makes paid Agent results durable and reusable.
- Enforces exact cache identity.
- Gives Selection result matrices instead of raw workspaces or transcripts.
- Applies the invalid-outcome and cache-identity rules used by selection and
  reporting.
