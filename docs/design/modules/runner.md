# Module Design: Runner

Status: current, 2026-07-27.

## Responsibility

Run user-facing commands by calling the owner modules in a defined order.

Runner exists because cross-module data flow needs a code owner. It does not
own task generation, Agent execution, checking, result scoring, selection, or
reporting logic.

## Inputs

- stable target `repository_id` and local `repository_path`;
- task-source config, a prepared-candidate package, or an existing complete
  `Task Pool` bundle;
- optional external Result source manifest plus an explicit accepted authority
  and availability policy;
- Agent set;
- historical window, origin, and future window;
- budget;
- specified fixed or fitted Selectors and, for fitting, explicit training
  Selection IDs;
- result store;
- workspace config;
- runtime config;
- scoring config;
- report config.

## Outputs

- references to produced records;
- persisted Selector, RollingOrigin, FeatureSnapshot, SelectorInput,
  Benchmark Selection, evaluation-cell, matrix, and metric records where the
  command produces them;
- run summary;
- report paths;
- immutable Result-import decisions and receipt when external evidence is
  admitted.

## System Boundary

Input sources:

- users;
- Task Pool;
- Result Store;
- Selection;
- Workspace;
- Reporting.

Output consumers:

- users.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

Append-only Selector evidence uses stable semantic IDs. If a resumed operation
recreates a Selector, Benchmark Selection, or Metric with identical semantics
but a later `created_at` or `computed_at`, Runner reuses and returns the first
persisted record. It first validates semantic-ID uniqueness across the complete
existing companion log, then rejects every other same-ID difference. Downstream
records therefore bind the exact persisted digest rather than a transient
regenerated timestamp.

## Public Entry Points

### build_task_pool

Input:

- `config: TaskPoolConfig`
  - stable `repository_id` stored in records;
  - local Git `repository_path` used to create workspaces;
  - the `WorkspaceConfig` and `RuntimeConfig` used to execute checks;
  - a direct `candidate_id -> CapturedDiff` mapping of trusted reference
    patches;
  - direct `candidate_id -> check command` and `candidate_id -> hidden material
    path` mappings, plus optional semantic Check manifests;
  - exactly one candidate source: an import path, a time range with task-source
    config, or a validated prepared-candidate package;
  - certification config and output refs in metadata.

Output:

- `TaskPoolRecord`

Effect:

- Validates WorkspaceConfig and RuntimeConfig before candidate or repository
  resolution. Candidate certification rechecks the same configs immediately
  before Check execution.
- Generates or imports candidates and rejects repository IDs that differ from
  `config.repository_id`; the local path is never used as record identity. It
  resolves each distinct candidate base revision to an exact commit once.
- Requires one reference patch, Check command, and hidden-material path for
  every resolved candidate before binding repository or Check material into a
  Workspace context.
- Binds `repository_path` to the Workspace config, builds each Check directly
  from its candidate, then binds the matching Check command and hidden material
  in one local immutable `WorkspaceRunContext`. When provided, the candidate's
  semantic Check manifest is passed through without replacing it with the
  machine-local command.
- Runs executable base-fail/reference-patch-pass certification as symmetric
  fresh-workspace pairs, finalizes the complete accepted/rejected/excluded
  source-event ledger, and passes both it and all certification results to
  `freeze_task_pool`.
- When the source is a prepared package, validates its candidate and exclusion
  ledgers, repository/base-commit bindings, referenced material digests, and
  optional observed-frame/provenance sidecars before certification. The
  package is a language-neutral artifact contract, not a Generator plugin API.
- After the frozen record is constructed, writes the exact accepted Task
  sequence, accepted Check sequence, ordered sanitized certification evidence,
  and ordered SourceEvent sequence as one immutable content-addressed bundle.
  Their canonical digests must match the digests stored on `TaskPoolRecord`.

### build_task_pool_from_package

Input:

- `package: PreparedCandidatePackage`
- `config: TaskPoolConfig` without another candidate source or material map.

Output:

- `TaskPoolRecord`

Effect:

- Derives the certification material maps from the validated package and calls
  the ordinary `build_task_pool` path. It adds no second certification,
  publication, or Generator execution path.

### import_result_bundle

Input:

- an immutable external Result-source manifest;
- a complete validated `TaskPoolBundle`;
- the accepted Agent set plus Workspace and Runtime configs;
- a local Result Store and receipt path;
- an explicit accepted authority digest and availability policy.

Output:

- `ResultImportReceipt`

Effect:

- Reads the source bundle without modifying it, validates its manifest and
  records, and admits only Results whose Agent, Task, Check, Workspace, and
  Runtime cache identities match the supplied local evidence.
- Rejects conflicting executions both within the source and against the local
  store. Accepted records receive external evidence provenance. The default
  policy floors effective availability at import time; preserving a
  producer-attested historical timestamp requires that explicit source policy.
- Persists per-record decisions and one immutable receipt. An exact replay
  recomputes admission against a read-only store view and returns the existing
  receipt without creating or duplicating Results. The first local observation
  time is implementation-owned, recovered from the receipt or a prior valid
  local row, and cannot predate source-manifest creation. Local write paths
  cannot alias or sit inside the read-only source root. Receipt write or replay
  returns only after the file and parent directory are fsynced.

### train_selector

Input:

- `selector_family: str`
- `deployment_origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `expert_selectors: Sequence[SelectorRecord]`
- `training_selection_ids: Sequence[str]`
- `result_store: ResultStore`
- `artifact_root: Path | None`

Output:

- `SelectorRecord`

Effect:

- Loads the exact Selections named by the caller and follows their IDs/digests
  to persisted Origins, FeatureSnapshots, SelectorInputs, selected/future
  matrices, MAE metrics, pre-origin Results, and outcome Results. Missing,
  duplicate, or ambiguous records fail closed. Matrix Result loading follows
  every present ID/digest, including bound excluded cells, so it matches
  Selection's exact training coverage.
- Loads the frozen Task Pool bundle once and supplies its ordered Task/Check
  records to Selection. Training replays all deployment/training Origins,
  Snapshot Task metadata, and pre-origin/outcome Result Task/Check cache
  projections against that bundle.
- Calls Selection's algorithm-specific fitter, persists the deployment Origin,
  expert Selectors, and fitted Selector, and reuses the first semantically
  identical persisted record on resume. It does not discover a dataset or
  choose a candidate implicitly.
- Selection requires the ordered Agent IDs and full AgentRecord digests frozen
  by every training SelectorInput to match and replays each training Result's
  Agent cache projection before its outcome can affect fitted parameters.

### select_benchmark

Input:

- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `origin_time: datetime`
- `budget: SelectionBudget`
- `selector: SelectorRecord`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`
- `result_store: ResultStore`
- `future_window: TimeRange | None`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Resolves Task/Check records from the task pool, loads allowed pre-origin
  results, and calls Selection to produce a benchmark selection frozen before
  future outcomes are opened. When supplied, `future_window` freezes the later
  evaluation interval in the Origin while strict mode keeps its future refs
  empty. Omitting it retains the point-window selection-only behavior. A
  configured as-of cutoff later than the origin is rejected before any Result
  query.
- Uses a null Result-availability lower bound for this selection-only query;
  it does not construct a malformed TimeRange as an open-bound sentinel.
- Skips Result Store access when the FeatureConfig contains only Task metadata.
  When Result features are required, strict mode applies the physical
  availability cutoff. Counterfactual mode loads exact matching Task Pool and
  Agent Results without projecting their observation timestamps; Selection
  then limits the view to mature history refs and verifies cache identity.
- Does not count repriced views as additional Agent executions; executions with
  genuinely different verifier evidence remain distinct.

## Maintainer Entry Points

### evaluate_selectors

Input:

- `selectors: Sequence[SelectorRecord]`
- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `evaluation_config: SelectorEvaluationConfig`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`
- `result_store: ResultStore`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `cache_config: ResultCacheConfig`
- `join_config: ResultJoinConfig`
- `run_context: WorkspaceRunContext`

Output:

- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`

Effect:

- Requires `counterfactual_replay` with a predeclared future holdout. The
  two-phase strict path uses `select_benchmark` followed by
  `evaluate_prospective_selection`; this batch evaluator rejects strict mode
  before writing records or invoking an Agent.
- Materializes the complete Selector batch and validates nonempty membership,
  unique IDs, record integrity, and executable algorithm parameters before
  reading Task Pool artifacts or appending any companion evidence. Agent IDs,
  evaluation mode, and the complete origin schedule are preflighted at the
  same no-side-effect boundary, so an invalid later Selector cannot leave an
  earlier Selector record behind.
- `evaluation_config.origin_times` contains ISO timestamps in strictly
  increasing UTC order. Each origin's future arrival window ends at the next
  origin; the final future window ends at `history_window.end`. Task-material
  arrival determines history/future membership. Check availability determines
  label maturity at the origin cutoff or after the configured maturity lag;
  immature refs stay in censored origin fields. Arrivals before
  `history_window.start` are excluded from that origin's history.
  Runner loads one immutable Result snapshot. Strict mode bounds it by physical
  availability. Counterfactual mode loads all exact matching pool/Agent
  Results, then derives each Origin view from mature history membership and
  cache identity regardless of physical observation time. Metadata-only
  FeatureConfigs skip this read. Runner computes every Selector/origin
  Selection in Selector-major order and appends all Selectors, Origins,
  FeatureSnapshots, SelectorInputs, and Selections before opening future
  outcomes.
- Within one Result Store, resume reuses the exact persisted FeatureSnapshot
  and SelectorInput for an Origin. Results appended by selected-cell lazy
  evaluation cannot retroactively change that frozen counterfactual input.
- Plans the first-occurrence union of each Selection's selected refs and its
  origin's mature future refs. Censored refs are never sent to Workspace. One
  locked Result Store session resolves, executes, and
  reprices that union once. Runner then reconstructs every CellSet in that
  Selection's own ref order, so overlapping or reversed ref orders do not alter
  matrix identity.
- Indexes every planned CellSet identity and rejects duplicates before reading
  the persisted CellSet log. After union resolution, Runner constructs and
  validates every pending CellSet before appending the first one; a malformed
  later plan cannot leave a partial set of new CellSet records.
- A partial execution leaves each appended Result durable but writes no new
  CellSet until union resolution succeeds. Resume reuses valid persisted
  CellSets, including explicit missing/abstained evidence, instead of rerunning
  them under the same semantic ID. Before planning the pending union, Runner
  batch-loads all Results bound by reusable CellSets and verifies their complete
  ID/digest, Agent/Task/Check, required-identity, and outcome relation. A bad
  reused binding cannot trigger an unrelated pending Agent call.
- `origin_id` is produced by `build_rolling_origin`; it is not an input config
  value.
- MAE is the primary prediction metric. Supporting metrics remain available for
  diagnosis and later algorithm decisions.

`evaluate_selector` remains a thin single-Selector wrapper over this entry
point; it has no separate execution behavior.

### evaluate_prospective_selection

Input:

- a persisted `selection_id`;
- the Selection Task Pool and a later Task Pool;
- the exact frozen Agent set;
- Result Store, Workspace, Runtime, scoring, cache, join, metric, and run
  context inputs used by ordinary evaluation.

Output:

- one `EvaluationCellSet`;
- selected and future `ResultMatrix` records;
- `MetricRecord` records.

Effect:

- Loads the persisted Selection, Origin, SelectorInput, Selector, and
  FeatureSnapshot. Selection replays deterministic inference before Task Pool
  reads. Runner then loads only the pre-origin Result IDs frozen by
  SelectorInput and replays their exact digests, Origin Agent/history/cutoff
  scope, Result-view digest, Feature provenance, and cache-identity Agent
  projection. Agent ID/order or full-record-digest drift, invalid Origins,
  missing or drifted Results, invalid provenance, and non-replayable Selections
  fail before Task Pool reads or Agent execution.
- Validates and replays the immutable selection-time Task Pool and Origin, then
  compares each pre-origin Result cache identity with the exact Task/Check
  records. Selection then replays `task_count` and every `task_stratum` record
  against that Origin and the validated TaskRecords. Metadata drift fails after
  the one required selection-pool read but before the later pool or Agent
  execution. The later pool must use the same repository, Generator behavior,
  source protocol, and certification config; cover the complete declared
  future source window; postdate the Selection; and be observed through the
  label-maturity cutoff. It may be an incremental or cumulative pool. Any
  same-ID Task or Check present in both snapshots must be unchanged.
- Replays future arrival, maturity, censoring, and dependency policy without
  mutating the strict Origin. The CellSet binds the later Task Pool identity;
  censored refs remain evidence but do not enter Agent execution.
- Uses the same shared CellSet resolver, Result Store session, complete missing-
  plan preflight, durable Result appends, matrices, and scorer as
  counterfactual evaluation. Resume requires the same future pool, cohort,
  Agent identities, and join policy.

### `barcarolle report`

Input:

- a JSON config containing paths to one selection-time `TaskPoolRecord` JSONL
  file, an optional JSONL file of later Task Pools, and the Agent, Selector,
  RollingOrigin, FeatureSnapshot, SelectorInput, Result, Benchmark Selection,
  Evaluation Cell Set, Result Matrix, and Metric JSONL files;
- an output directory.

Output:

- `report.md`;
- `report.json`.

Effect:

- Loads existing records and calls `write_report`. Later Task Pools are replayed
  only when a strict-prospective CellSet references them. The command does not
  build tasks or run Agents.

## Internal Steps

### run_agents

Input:

- `task_pool_bundle: TaskPoolBundle`
- `task_check_refs: Sequence[TaskCheckRef]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `result_store: ResultStore`
- `run_context: WorkspaceRunContext`

Output:

- `Sequence[ResultRecord]`

Effect:

- Validates the complete Task Pool bundle, including certification and
  SourceEvent evidence, before repository, Agent, or Result-store side effects.
  Calls Workspace for requested Agent-task-check cells and calls Result Store
  to store the produced records. It constructs every missing-cell identity first,
  rejects duplicate or invalid plans, applies the shared RuntimeConfig contract,
  and asks Workspace to preflight both configs plus all repository, Check,
  timeout, harness, and paid-endpoint bindings before the first Agent
  invocation.

### fill_results

Input:

- `selection: BenchmarkSelectionRecord`
- `task_pool_bundle: TaskPoolBundle`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `cache_config: ResultCacheConfig`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`
- `run_context: WorkspaceRunContext`

Output:

- `EvaluationCellSet`

Effect:

- Validates the complete Task Pool bundle, then reloads and deterministically
  replays the persisted Selection, Origin, SelectorInput, FeatureSnapshot,
  Selector, frozen pre-origin Results, and exact Agent identities before cache
  access.
- Uses the shared evaluation-cell resolver for selected refs only. It reuses
  exact cached executions, appends a current pricing view when needed, executes
  only misses, and persists the resulting `EvaluationCellSet` with the declared
  join, scoring, and benchmark-invalid reuse policies in its identity. Changing
  either resolution policy creates a new CellSet and reruns resolution;
  unchanged policy resumes the frozen cells. The complete missing plan is
  preflighted before its first call; cache-only and repricing paths do not
  require endpoint credentials.
- Holds one Result Store session across resolution, execution, repricing, and
  final lookup. Each produced Result is durable before the next Agent cell, and
  the CellSet is written only after complete resolution.

### prepare_evaluation_cells

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool_bundle: TaskPoolBundle`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `cache_config: ResultCacheConfig`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`
- `run_context: WorkspaceRunContext`

Output:

- `EvaluationCellSet`

Effect:

- Validates the complete bundle and replays the exact persisted Selection chain
  before cache access. It then acts as the single-Selection wrapper over the
  shared planner used by `evaluate_selectors`, applying the same cache identity
  and denominator policy to selected and future refs and executing their
  deduplicated union.
- Returns completeness, exclusion, and abstention metadata. A valid persisted
  CellSet with the same Selection, Origin, ref order, Agent set, execution
  identities, future Task Pool, censored cohort, and join policy is reused
  exactly.

### score_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool_bundle: TaskPoolBundle`
- `agents: Sequence[AgentRecord]`
- `evaluation_cells: EvaluationCellSet`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`

Output:

- `cell_set: EvaluationCellSet`
- `selected_matrix: ResultMatrix`
- `future_matrix: ResultMatrix`
- `metrics: Sequence[MetricRecord]`

Effect:

- Calls Result Store to build selected-benchmark and future-holdout result
  matrices from `evaluation_cells` with explicit matrix roles, then calls
  Selection with both matrices to evaluate the fixed, versioned metric
  protocol. Result Store
  receives the same `EvaluationCellSet` used for scoring so missing, excluded,
  and required-identity cells cannot be reinterpreted. Runner first requires
  every bound cell's ID/digest, Agent/Task/Check, required identity, and outcome
  to match its frozen Result; a contradiction is not converted to a missing
  cell. If genuinely required cells are incomplete under `join_config`, it
  records abstention metadata instead of scoring a partial comparison.

### write_report

Input:

- `task_pool: TaskPoolRecord`
- `selectors: Sequence[SelectorRecord]`
- `origins: Sequence[RollingOriginRecord]`
- `feature_snapshots: Sequence[FeatureSnapshotRecord]`
- `selector_inputs: Sequence[SelectorInput]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `results: Sequence[ResultRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`
- `report_config: ReportConfig`

Output:

- `Mapping[str, object]`

Effect:

- Calls Reporting to write human-readable and machine-readable summaries, then
  returns paths and record references.
- `ReportConfig` accepts one direct `.md` filename and one direct `.json`
  filename below `output_dir`; absolute paths, nested paths, traversal, and
  swapped suffixes fail when the config is constructed.
- A Selector-performance claim is supported only when Reporting can validate
  and replay the exact
  Selector→RollingOrigin→FeatureSnapshot→SelectorInput→Benchmark Selection→
  cell set→matrix→metric chain and its Agent/Result bindings. The claim name
  records whether the origin used strict prospective eligibility or explicit
  counterfactual replay.
- Uses `ReportConfig.artifact_root` to resolve Task Pool artifact refs. The
  offline command defaults it to the report-config directory.

## Design Consistency Check

- Makes cross-module data flow explicit without adding a new research object.
- Keeps `Task Pool`, `Benchmark Selection`, and `Agent Results` independent.
- Exposes Selection training, evaluation, and production benchmark selection as
  separate command flows.
- Implements cache reuse and lazy Agent execution by calling Result Store and
  Workspace, not by creating another execution mode.
- Keeps selected-benchmark and future-holdout result preparation symmetric.
- Leaves module-specific logic in the owner modules.
