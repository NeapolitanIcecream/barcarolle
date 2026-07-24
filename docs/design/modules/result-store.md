# Module Design: Result Store

Status: current behavior and planned scale boundary, 2026-07-24.

## Responsibility

Store, admit, query, and join reusable `Result` records for exact
Agent-task-check execution cells.

Result Store does not execute Agents and does not choose benchmark tasks.

## Inputs

- `TaskRecord`;
- `CheckRecord`;
- `AgentRecord`;
- `ResultCacheIdentity`;
- `WorkspaceRunRecord`;
- cache and scoring config.
- optional external Result source manifest plus explicit import authority and
  availability policy.

## Outputs

- `ResultRecord`;
- result cache state;
- cached result queries;
- `ResultMatrix`;
- result completeness and exclusion metadata;
- missing Agent-task-check cells;
- normalized external Result evidence and an immutable import receipt.

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
caller-supplied identifier. Construction validates both fields, normalizes
finite nonnegative integer or float rates to sorted built-in floats, maps signed
zero to positive `0.0`, and stores a read-only snapshot. Numeric representations
with identical pricing behavior therefore have one stable digest, and later
mutation of the source mapping cannot create a second pricing view identity.

`ResultCacheConfig` exposes only `reuse_benchmark_invalid`, which must be an
exact boolean. Exact full-identity reuse is a fixed Result Store invariant,
not a caller-selectable cache policy.

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

- Validates the supplied Task, Check, Agent, and WorkspaceRun records before
  evaluating linkage or cache projections. A schema-invalid upstream record
  cannot be converted into a valid-looking Result merely because the malformed
  field is absent from cache identity.
- Normalizes pass/fail/invalid, cost, latency, failure label, diff digest, and
  verifier metadata, and stores the exact cache identity used for reuse.
- Reuses the Records-owned Agent and Task/Check projection contract to require
  that the supplied cache identity matches the exact construction inputs.
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
- Marks locally executed evidence as `barcarolle_managed`, with source and
  effective availability equal and no external manifest or import-observation
  timestamp.
- Derives `result_id` from execution evidence, scoring configuration, and
  evidence provenance/availability. Repricing the same execution through any
  prior price view therefore produces the same ID for the same target price
  table and evidence view; importing it through another authority or
  availability policy does not overwrite that view.

### result_execution_digest

Input:

- `result: ResultRecord`

Output:

- `execution_digest: str`

Effect:

- Digests the Result fields that describe one execution while excluding cost,
  pricing provenance, evidence source, Result availability, and Result record
  identity.
- Gives all pricing and evidence views of the same execution one stable key
  without adding another record type.

### load_result_source_bundle

Input:

- canonical `result-source-manifest.jsonl`.

Output:

- read-only source manifest, Result tuple, and resolved source path.

Effect:

- Requires one latest-schema, self-digested manifest with producer, authority
  digest, availability semantics, canonical creation time, and one relative
  `results.jsonl` ref.
- Loads strict canonical Result records, rejects duplicate source Result IDs,
  and checks the tuple digest. Per-row semantic admission remains Runner's
  responsibility. It never opens the source for writing.

### normalize_external_result

Input:

- source `ResultRecord`;
- source-manifest digest;
- implementation-owned local import-observation time;
- `import_time_floor_v1` or
  `producer_attested_historical_v1`.

Output:

- normalized local `ResultRecord`.

Effect:

- Preserves execution and cache identity, labels the evidence
  `external_attested`, and binds source manifest and import time.
- Under the default policy sets effective availability to
  `max(source_result_available_at, evidence_imported_at)`. The historical policy
  preserves source time only as an explicit producer attestation.
- Recomputes Result identity/digest for the evidence view. It does not change
  or authenticate the source record.

### load_result_import_receipt / write_result_import_receipt

Input:

- receipt path and, for writes, one `ResultImportReceipt`.

Output:

- zero or one immutable receipt.

Effect:

- Requires exactly one self-digested record when present and refuses a
  different record at the same path.
- The receipt binds source/target digests, authority, the first local
  import-observation time,
  availability policy, admitted Agent/config identities, and each source row's
  admitted/idempotent/rejected local binding and reason.
- Runner requires exact replay to use the same canonical observation time and
  rejects an observation before source-manifest creation.

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

- Validates the supplied Task, Check, Agent, WorkspaceConfig, and RuntimeConfig
  before Task/Check linkage or identity construction. Missing-cell and
  cache-reuse planning therefore cannot derive a valid-looking identity from a
  schema-invalid upstream record or configuration. Runtime timeout and optional
  hardware identity are also checked at this boundary.
- Produces the structured identity used to decide whether a cached execution is
  reusable. A single `check_digest` binds all behavior-changing Check fields.
  Pricing and scoring are excluded. Rejects an invalid identity instead of
  returning a runnable missing cell.

### compute_cost

Input:

- `usage: Mapping[str, JSONValue]`
- `scoring_config: ScoringConfig`

Output:

- `Mapping[str, JSONValue]`

Effect:

- Computes a pricing view from retained usage without executing an Agent or a
  Check. Returns `total_cost=null` when usage is absent, no rates are
  configured, or a configured priced key is missing. Rejects an absent pricing
  version and nonnumeric, negative, or non-finite rates.

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

- Delegates to the same locked writer used for batches. Writes a result record
  append-only. Records validation requires the canonical Result ID derived
  from execution, scoring, and evidence identity. Corrections or rescoring
  create a new `result_id` and
  `result_digest`; existing frozen records are not mutated.

### open_result_store_session

Input:

- `store: ResultStore`

Output:

- one context-managed `ResultStoreSession`.

Effect:

- Takes an exclusive advisory lock, loads and indexes the JSONL file once, and
  rejects a repeated `result_id` before building the live index. Identical and
  conflicting duplicates are both invalid persisted histories.
- Keeps the index current as Results are appended. Each `append` writes one
  complete canonical line, flushes it, and fsyncs it before returning; first
  creation also fsyncs the directory. `append_many` validates the entire batch,
  writes it once, and fsyncs once. Runner holds one session across cell
  resolution, execution, repricing, and final resolution.

### load_results

Input:

- `store: ResultStore`
- `query: ResultQuery`

Output:

- `Sequence[ResultRecord]`

Effect:

- Validates every ID/digest filter as a tuple of nonempty strings before store
  access. Availability bounds are explicitly null or nonempty timezone-aware
  timestamps, and the lower bound cannot follow the upper bound. Malformed
  queries therefore behave the same whether the store is absent, empty, or
  populated.
- Reads result records matching task, check, Agent, result ID, exact cache
  identity, scoring config, and result-availability time filters.
- Compares availability bounds as UTC instants, so equivalent timestamps with
  different offsets have the same ordering.
- Takes a shared advisory lock and rejects an unterminated final line instead of
  treating a partial append as a record.
- Validates every complete Result row, including its canonical Result ID,
  before applying query filters; invalid durable evidence fails closed rather
  than disappearing from a cache view.
- Rejects the second occurrence of any `result_id`, with its line number, before
  applying query filters. This is the same rule used by a locked session.

### recover_result_store_tail

Input:

- `store: ResultStore`

Output:

- `not_needed`, `completed`, or `truncated`.

Effect:

- Under the exclusive lock, explicitly repairs only a final line lacking its
  newline. A parseable JSON value receives the missing newline and remains
  subject to normal schema validation. An unparseable byte tail is truncated to
  the last complete newline. Complete invalid lines are never changed; normal
  loading reports their line number.

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
- Separates the requested model name from an immutable snapshot. When no
  snapshot is proven, exact reuse is limited to the identical model-resolution
  campaign scope stored in the identity.
- Without `scoring_config`, resolves execution reuse independently of pricing.
  With it, resolves only the exact derived scoring-config digest so evaluation
  cells cannot bind a stale price view.
- Validates every stored Result before indexing it for reuse. By default it
  does not reuse benchmark-invalid infrastructure results; callers may opt in
  with `reuse_benchmark_invalid` without allowing malformed records. Agent-
  invalid results remain reusable.
- If the same exact cache identity has different execution digests, fails as
  ambiguous instead of choosing by append order. Equal execution digests may
  have several pricing or evidence views; pricing selection remains
  deterministic.
- Loads and indexes matching stored results once per resolution operation.
- When Runner supplies its active Result Store session, reuses the same live
  index instead of parsing JSONL again.

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
- Inherits the same ambiguity check. A conflicting cache cannot be disguised as
  a missing cell and rerun implicitly.

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
  handled as missing under the join policy. Resolution uses Records' complete
  ResultCell-to-Result predicate, including Agent/Task/Check and outcome.
- Validates persisted Matrix cell states against the same Results. A
  benchmark-invalid Result produces the canonical task-wide exclusion; an
  agent-invalid Result follows one supported policy for the complete Matrix.
  Normal Results cannot invent exclusions, cell-local policy mixtures are
  rejected, and unbound exclusions require a benchmark-invalid Result on the
  same Task/Check denominator. The same replay binds the declared join and
  denominator policy digests, abstention reason, and scoreable state to one of
  the four currently executable missing-cell/agent-invalid combinations.

## Join And Denominator Policy

`ResultJoinConfig` explicitly defines:

- missing-cell policy;
- Agent-attributable invalid outcome policy;
- benchmark infrastructure failure policy;
- abstention policy.

Construction rejects unsupported policy values, so a misspelled policy cannot
silently change a matrix denominator. `join_policy_digest` is derived from all
four values. `denominator_policy_digest` is derived from the two invalid-outcome
policies that determine whether Agent or benchmark failures enter the common
denominator. Neither digest is caller-supplied. Required Result identity comes
from each frozen evaluation cell, not from this policy config.

Agent-attributable invalid outcomes such as timeout, no meaningful patch, or
budget exhaustion are failures. Benchmark infrastructure failures are not Agent
failures. Persistent task-level infrastructure failures should be removed from
all Agents' denominators for that matrix. If required Agent-task-check cells
are missing and cannot be filled under the configured policy, the matrix must
carry an abstention reason instead of silently scoring a partial comparison.
Selection also abstains when exclusions leave any Agent with no result cells in
the selected or future matrix.

## Design Consistency Check

- Makes paid Agent results durable and reusable.
- Enforces exact cache identity.
- Gives Selection result matrices instead of raw workspaces or transcripts.
- Applies the invalid-outcome and cache-identity rules used by selection and
  reporting.
