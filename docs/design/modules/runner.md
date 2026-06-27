# Module Design: Runner

Status: draft, 2026-06-27.

## Responsibility

Run user-facing commands by calling the owner modules in a defined order.

Runner exists because cross-module data flow needs a code owner. It does not
own task generation, Agent execution, checking, result scoring, selection, or
reporting logic.

## Inputs

- target repository reference;
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

Output:

- `TaskPoolRecord`

Effect:

- Calls Task Pool to generate or import candidates, certify accepted tasks, and
  freeze a task pool.

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
  future outcomes are opened.

### update_selector

Input:

- `selector: SelectorRecord`
- `selection: BenchmarkSelectionRecord`
- `metrics: Sequence[MetricRecord]`
- `feedback_config: SelectorFeedbackConfig`

Output:

- `SelectorRecord`

Effect:

- Calls Selection to update the persistent Selector or its trust metadata after
  new metrics are available.

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

Output:

- `selections: Sequence[BenchmarkSelectionRecord]`
- `metrics: Sequence[MetricRecord]`

Effect:

- For each origin defined by the evaluation config and rolling-origin policy,
  resolves Task/Check records, builds pre-origin selector input, calls Selection
  `freeze_evaluation_selections` to freeze `BenchmarkSelectionRecord`s, then
  calls `prepare_evaluation_cells` and `score_selection`. It returns both
  frozen selections and metrics.

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
- `result_store: ResultStore`

Output:

- `Sequence[ResultRecord]`

Effect:

- Calls Result Store to find selected Agent-task-check cells that are not
  reusable from the cache, then calls Workspace and Result Store to execute and
  store only those cells.

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
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`

Output:

- `EvaluationCellSet`

Effect:

- Applies the same cache identity and denominator policy to selected benchmark
  `Task + Check` refs and future holdout `Task + Check` refs. It asks Result
  Store for missing cells, runs allowed missing cells through Workspace, stores
  new results, and returns completeness, exclusion, and abstention metadata for
  scoring.

### score_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `evaluation_cells: EvaluationCellSet`
- `result_store: ResultStore`
- `join_config: ResultJoinConfig`
- `metric_config: MetricConfig`

Output:

- `Sequence[MetricRecord]`

Effect:

- Calls Result Store to build selected-benchmark and future-holdout result
  matrices from `evaluation_cells` with explicit matrix roles, then calls
  Selection with both matrices to evaluate prediction metrics. If the required
  cells are incomplete under `join_config`, it records abstention metadata
  instead of scoring a partial comparison.

### write_report

Input:

- `task_pool: TaskPoolRecord`
- `selection: BenchmarkSelectionRecord`
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

## Source Alignment Check

Aligned with the architecture:

- Makes cross-module data flow explicit without adding a new research object.
- Keeps `Task Pool`, `Benchmark Selection`, and `Agent Results` independent.
- Exposes Selection training, evaluation, and production benchmark selection as
  separate command flows.
- Implements cache reuse and lazy Agent execution by calling Result Store and
  Workspace, not by creating another execution mode.
- Keeps selected-benchmark and future-holdout result preparation symmetric.
- Leaves module-specific logic in the owner modules.
