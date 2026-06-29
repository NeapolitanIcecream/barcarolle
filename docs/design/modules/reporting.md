# Module Design: Reporting

Status: draft, 2026-06-27.

## Responsibility

Create claim-safe reports from existing records. Reporting does not create new
evidence and does not run experiments.

## Inputs

- `TaskPoolRecord`;
- `BenchmarkSelectionRecord`;
- `EvaluationCellSet` records;
- `ResultMatrix` records;
- `ResultRecord` records;
- `MetricRecord` records;
- source and cache digests.

## Outputs

- human-readable reports;
- machine-readable summaries;
- claim-boundary sections.

## System Boundary

Input sources:

- Task Pool;
- Result Store;
- Selection;
- Records.

Output consumers:

- users.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### build_task_pool_report

Input:

- `task_pool: TaskPoolRecord`

Output:

- `ReportSection`

Effect:

- Summarizes task count, check count, generator families, certification
  coverage, and rejection reasons.

### build_result_report

Input:

- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`

Output:

- `ReportSection`

Effect:

- Summarizes pass/fail/invalid, cost, latency, scoreable rate, and cache
  coverage, including pricing version and usage coverage.

### build_selector_report

Input:

- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`

Output:

- `ReportSection`

Effect:

- Summarizes selector performance by origin, Agent set, budget, metric, and
  benchmark exposure state using selections, cell sets, matrices, and metrics.

### build_claim_boundary

Input:

- `task_pool: TaskPoolRecord`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`
- `claim_config: ClaimConfig`

Output:

- `ReportSection`

Effect:

- Separates supported claims from unsupported claims using task-pool coverage,
  rejection and certification evidence, cache completeness, abstentions,
  benchmark exposure state, and Agent/result identity drift.

### write_report

Input:

- `sections: Sequence[ReportSection]`
- `output_path: Path`

Output:

- `None`

Effect:

- Writes a report with source digests and artifact paths.

## Design Consistency Check

- Separates evidence from claims.
- Reports negative or weak evidence honestly.
- Keeps benchmark predictive validity distinct from tuning utility.
