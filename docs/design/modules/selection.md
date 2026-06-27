# Module Design: Selection

Status: draft, 2026-06-27.

## Responsibility

Train Selectors from historical data, evaluate a specified Selector on
historical data, select production benchmarks for a frozen origin, and update
Selector choice from new evaluation feedback.

Selection is the core research module.

## Inputs

- frozen `Task Pool`;
- cached `Agent Results`;
- origin or historical window definition;
- candidate Agents;
- budget;
- selector config or specified Selector;
- leakage rules.

## Outputs

- `BenchmarkSelectionRecord`;
- `SelectorRecord`;
- prediction metrics;
- selector notes.

## System Boundary

Input sources:

- Task Pool;
- Result Store;
- user or experiment config;
- selector roadmap.

Output consumers:

- Reporting;
- Runner.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Selection Entry Points

These are module-level entry points. Runner calls them as needed.

### train_selector

Input:

- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `candidate_selectors: Sequence[SelectorRecord]`
- `training_config: SelectorTrainingConfig`

Output:

- `SelectorRecord`

Effect:

- Trains or chooses a persistent Selector using only historical data allowed by
  the training config. Rolling-origin splitting is internal to this function.

### evaluate_selector

Input:

- `selector: SelectorRecord`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `evaluation_config: SelectorEvaluationConfig`

Output:

- `Sequence[MetricRecord]`

Effect:

- Tests the specified Selector on historical data and returns metrics across
  the origins defined by the evaluation config.

### select_benchmark

Input:

- `selector: SelectorRecord`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `origin_time: datetime`
- `budget: SelectionBudget`
- `selection_config: SelectionConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Uses the specified Selector at the origin to choose a production benchmark.
  It does not run missing Agent-task results; Runner handles lazy Agent
  execution after this record is produced.

### update_selector

Input:

- `selector: SelectorRecord`
- `selection: BenchmarkSelectionRecord`
- `metrics: Sequence[MetricRecord]`
- `feedback_config: SelectorFeedbackConfig`

Output:

- `SelectorRecord`

Effect:

- Updates the persistent Selector or its trust metadata after new evaluation
  metrics are available. It does not inspect raw workspaces or hidden checks.

## Functions

### build_rolling_origin

Input:

- `task_pool: TaskPoolRecord`
- `origin_time: datetime`
- `future_window: TimeRange`

Output:

- `RollingOriginRecord`

Effect:

- Defines history pool and future holdout without exposing future outcomes to
  selectors.

### build_selector_input

Input:

- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `budget: SelectionBudget`
- `leakage_rules: LeakageRules`

Output:

- `SelectorInput`

Effect:

- Builds the pre-origin data visible to a selector.

### select_random

Input:

- `selector_input: SelectorInput`
- `seed: int`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects a count-matched random benchmark from the history pool.

### select_recency

Input:

- `selector_input: SelectorInput`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects recent tasks under budget.

### select_coverage

Input:

- `selector_input: SelectorInput`
- `coverage_config: CoverageConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects tasks to cover modules, task types, generator families, or check
  types.

### select_rule_mixture

Input:

- `selector_input: SelectorInput`
- `expert_weights: Mapping[str, float]`
- `selection_config: SelectionConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Combines rule-based selector scores and solves for one common selected task
  set.

### fit_learned_mixture

Input:

- `training_origins: Sequence[RollingOriginRecord]`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `baseline_selectors: Sequence[SelectorRecord]`
- `fit_config: FitConfig`

Output:

- `SelectorRecord`

Effect:

- Learns mixture weights over rule-based selectors using only out-of-origin
  training data.

### fit_calibrated_weighting

Input:

- `training_origins: Sequence[RollingOriginRecord]`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `selection_config: SelectionConfig`

Output:

- `SelectorRecord`

Effect:

- Fits a low-dimensional weighting layer for calibrated, constrained coreset
  selection.

### select_with_learned_model

Input:

- `selector_input: SelectorInput`
- `selector: SelectorRecord`
- `selection_config: SelectionConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects one common task set and weight vector for all Agents in the
  comparison.

### evaluate_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `result_matrix: ResultMatrix`
- `metric_config: MetricConfig`

Output:

- `Sequence[MetricRecord]`

Effect:

- Computes future pass-rate MAE, pairwise gap error, rank agreement,
  recommendation regret, invalid rate, cost, latency, and coverage. It emits
  metric records and selector notes, not a human-facing report.

### choose_selector_for_origin

Input:

- `registered_selectors: Sequence[SelectorRecord]`
- `prior_metrics: Sequence[MetricRecord]`
- `origin: RollingOriginRecord`
- `controller_config: ControllerConfig`

Output:

- `SelectorRecord`

Effect:

- Chooses a selector using only prior-origin evidence, with fallback to
  rule-based selectors under uncertainty or drift.

## Algorithm Roadmap

Initial order:

1. random, recency, and coverage baselines;
2. strong baseline envelope;
3. learned mixture over rule selectors;
4. calibrated constrained weighting;
5. future-stratum matching;
6. outcome-aware selectors only under explicit available-before-origin rules;
7. pairwise and hierarchical models only when data volume supports them;
8. adaptive controller after selectors have enough prior-origin evidence.

## Source Alignment Check

Aligned with the architecture and roadmap:

- Selectors use common task sets for Agent comparisons.
- Future outcomes are not visible at selection time.
- Primary metric is future pass-rate MAE.
- Learned selectors start with data-efficient methods.
- Adaptive behavior is based on prior-origin metrics and later feedback
  supplied through Metric records.
- Reporting, not Selection, owns human-readable reports.
