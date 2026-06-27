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
- origin and future window;
- budget;
- selector config;
- result store;
- workspace config;
- runtime config;
- report config.

## Outputs

- references to produced records;
- run summary;
- report paths.

## System Boundary

Input sources:

- users;
- Task Pool;
- Results;
- Selection;
- Workspace;
- Reporting.

Output consumers:

- users.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### build_task_pool_run

Input:

- `config: TaskPoolRunConfig`

Output:

- `TaskPoolRecord`

Effect:

- Calls Task Pool to generate or import candidates, certify accepted tasks, and
  freeze a task pool.

### run_agent_results

Input:

- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `result_store: ResultStore`

Output:

- `Sequence[ResultRecord]`

Effect:

- Calls Workspace for requested Agent-task runs and calls Results to store the
  produced records.

### select_benchmark_run

Input:

- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `origin_time: datetime`
- `future_window: TimeRange`
- `budget: SelectionBudget`
- `selector: Selector`
- `result_store: ResultStore`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Loads allowed pre-origin results, builds the rolling origin, and calls
  Selection to produce a benchmark selection.

### run_missing_selected_results

Input:

- `selection: BenchmarkSelectionRecord`
- `task_pool: TaskPoolRecord`
- `agents: Sequence[AgentRecord]`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `result_store: ResultStore`

Output:

- `Sequence[ResultRecord]`

Effect:

- Calls Results to find selected Agent-task runs that are not reusable from the
  cache, then calls Workspace and Results to execute and store only those runs.

### evaluate_rolling_origin_run

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `result_store: ResultStore`
- `metric_config: MetricConfig`

Output:

- `Sequence[MetricRecord]`

Effect:

- Calls Results to build the result matrix and calls Selection to evaluate
  prediction metrics.

### write_report_run

Input:

- `task_pool: TaskPoolRecord`
- `selection: BenchmarkSelectionRecord`
- `results: Sequence[ResultRecord]`
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
- Implements cache reuse and lazy Agent execution by calling Results and
  Workspace, not by creating another execution mode.
- Leaves module-specific logic in the owner modules.
