# Module Design: Runner

Status: draft, 2026-07-14.

## Responsibility

Run user-facing commands by calling the owner modules in a defined order.

Runner exists because cross-module data flow needs a code owner. It does not
own task generation, Agent execution, checking, result scoring, selection, or
reporting logic.

## Inputs

- stable target `repository_id` and local `repository_path`;
- task-source config or existing `Task Pool`;
- Agent set;
- historical window, origin, and future window;
- budget;
- selector config or specified Selector;
- result store;
- workspace config;
- runtime config;
- scoring config;
- report config.

## Outputs

- references to produced records;
- run summary;
- report paths.

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
    path` mappings;
  - either an import path or a time range with task-source config;
  - certification config and output refs in metadata.

Output:

- `TaskPoolRecord`

Effect:

- Generates or imports candidates and rejects repository IDs that differ from
  `config.repository_id`; the local path is never used as record identity.
- Binds `repository_path` to the Workspace config, builds each Check directly
  from its candidate, then binds the matching check command and hidden
  material before certification.
- Requires one reference patch, check command, and hidden-material path for
  every candidate. It runs executable base-fail/reference-patch-pass
  certification and passes the accepted records and complete certification
  results to `freeze_task_pool`.
- After the frozen record is constructed, writes the exact accepted Task
  sequence, accepted Check sequence, and ordered sanitized certification
  evidence to their refs. Their canonical digests must match the digests stored
  on `TaskPoolRecord`.

### train_selector

Input:

- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `candidate_selectors: Sequence[SelectorRecord]`
- `training_config: SelectorTrainingConfig`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`
- `result_store: ResultStore`

Output:

- `SelectorRecord`

Effect:

- Resolves Task/Check records from the task pool, loads historical results, and
  calls Selection to train or choose a persistent Selector under the requested
  rolling-origin and feature policies.
- Treats append-only pricing views with the same `result_execution_digest` as
  one pre-origin execution, preserving the first record in append order.

### select_benchmark

Input:

- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `origin_time: datetime`
- `budget: SelectionBudget`
- `selector: SelectorRecord`
- `selection_config: SelectionConfig`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`
- `result_store: ResultStore`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Resolves Task/Check records from the task pool, loads allowed pre-origin
  results, and calls Selection to produce a benchmark selection frozen before
  future outcomes are opened. A configured as-of cutoff later than the origin
  is rejected before any Result query.
- Does not count repriced views as additional Agent executions; executions with
  genuinely different verifier evidence remain distinct.

## Maintainer Entry Points

### evaluate_selector

Input:

- `selector: SelectorRecord`
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
- `metric_config: MetricConfig`

Output:

- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`

Effect:

- `evaluation_config.origin_times` contains ISO timestamps in strictly
  increasing UTC order. Each origin's future window ends at the next origin;
  the final future window ends at `history_window.end`. A Task/Check known at
  an origin boundary is in the preceding future holdout and the following
  history, while Task/Check refs before `history_window.start` are excluded.
  For each timestamp,
  resolves Task/Check records, builds pre-origin selector input, calls Selection
  `freeze_evaluation_selections` to freeze `BenchmarkSelectionRecord`s, then
  calls `prepare_evaluation_cells` and `score_selection`. It returns frozen
  selections, cell sets, result matrices, and metrics.
- `origin_id` is produced by `build_rolling_origin`; it is not an input config
  value.
- MAE is the primary prediction metric. Supporting metrics remain available for
  diagnosis and later algorithm decisions.

### `barcarolle report`

Input:

- a JSON config containing paths to one `TaskPoolRecord` JSONL file and the
  Agent, Result, Benchmark Selection, Evaluation Cell Set, Result Matrix, and
  Metric JSONL files;
- an output directory.

Output:

- `report.md`;
- `report.json`.

Effect:

- Loads existing records and calls `write_report`. It does not build tasks or
  run Agents.

## Internal Steps

### run_agents

Input:

- `task_pool: TaskPoolRecord`
- `task_check_refs: Sequence[TaskCheckRef]`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `result_store: ResultStore`

Output:

- `Sequence[ResultRecord]`

Effect:

- Calls Workspace for requested Agent-task-check cells and calls Result Store to
  store the produced records.

### fill_results

Input:

- `selection: BenchmarkSelectionRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `cache_config: ResultCacheConfig`
- `result_store: ResultStore`

Output:

- `Sequence[ResultRecord]`

Effect:

- Calls Result Store to find selected Agent-task-check cells that are not
  reusable from the cache, then calls Workspace and Result Store to execute and
  store only those cells. If an exact execution exists only under older
  pricing, appends and returns the current pricing view without running the
  Agent. An already-present current pricing view is not duplicated.

### prepare_evaluation_cells

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config: ScoringConfig`
- `cache_config: ResultCacheConfig`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`

Output:

- `EvaluationCellSet`

Effect:

- Applies the same cache identity and denominator policy to selected benchmark
  `Task + Check` refs and future holdout `Task + Check` refs. It asks Result
  Store for missing cells using `cache_config`, runs allowed missing cells
  through Workspace, stores new results, reprices reusable old-price
  executions, then resolves cells against the exact current derived scoring
  digest. Runner does not implement a separate cache lookup policy. It returns
  completeness, exclusion, and abstention metadata for scoring.

### score_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `agents: Sequence[AgentRecord]`
- `evaluation_cells: EvaluationCellSet`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`
- `metric_config: MetricConfig`

Output:

- `cell_set: EvaluationCellSet`
- `selected_matrix: ResultMatrix`
- `future_matrix: ResultMatrix`
- `metrics: Sequence[MetricRecord]`

Effect:

- Calls Result Store to build selected-benchmark and future-holdout result
  matrices from `evaluation_cells` with explicit matrix roles, then calls
  Selection with both matrices to evaluate prediction metrics. Result Store
  receives the same `EvaluationCellSet` used for scoring so missing, excluded,
  and required-identity cells cannot be reinterpreted. If the required cells are
  incomplete under `join_config`, it records abstention metadata instead of
  scoring a partial comparison.

### write_report

Input:

- `task_pool: TaskPoolRecord`
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
