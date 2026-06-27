# Module Design: Selection

Status: draft, 2026-06-27.

## Responsibility

Define rolling-origin windows, run Selectors, compare selected benchmarks with
future holdouts, and record prediction metrics.

Selection is the core research module.

## Inputs

- frozen `Task Pool`;
- cached `Agent Results`;
- origin definition;
- candidate Agents;
- budget;
- selector version;
- leakage policy.

## Outputs

- `BenchmarkSelectionRecord`;
- prediction metrics;
- selector comparison reports.

## Functions

### build_rolling_origin

Input:

- `task_pool: TaskPoolRecord`
- `origin_time: datetime`
- `future_window_policy: FutureWindowPolicy`

Output:

- `RollingOriginRecord`

Effect:

- Defines history pool and future holdout without exposing future outcomes to
  selectors.

### build_selector_context

Input:

- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `budget: SelectionBudget`
- `leakage_policy: LeakagePolicy`

Output:

- `SelectionContext`

Effect:

- Builds the pre-origin data visible to a selector.

### select_random

Input:

- `context: SelectionContext`
- `seed: int`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects a count-matched random benchmark from the history pool.

### select_recency

Input:

- `context: SelectionContext`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects recent tasks under budget.

### select_coverage

Input:

- `context: SelectionContext`
- `coverage_policy: CoveragePolicy`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects tasks to cover modules, task types, generator families, or check
  types.

### select_rule_mixture

Input:

- `context: SelectionContext`
- `expert_weights: Mapping[str, float]`
- `constraint_policy: SelectionConstraintPolicy`

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
- `baseline_selectors: Sequence[SelectorSpec]`
- `fit_policy: LearnedFitPolicy`

Output:

- `LearnedSelectorModel`

Effect:

- Learns mixture weights over rule-based selectors using only out-of-origin
  training data.

### fit_calibrated_weighting

Input:

- `training_origins: Sequence[RollingOriginRecord]`
- `feature_table: FeatureTable`
- `results: Sequence[ResultRecord]`
- `constraint_policy: SelectionConstraintPolicy`

Output:

- `LearnedSelectorModel`

Effect:

- Fits a low-dimensional weighting layer for calibrated, constrained coreset
  selection.

### select_with_learned_model

Input:

- `context: SelectionContext`
- `model: LearnedSelectorModel`
- `constraint_policy: SelectionConstraintPolicy`

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
- `metric_policy: MetricPolicy`

Output:

- `Sequence[MetricRecord]`

Effect:

- Computes future pass-rate MAE, pairwise gap error, rank agreement,
  recommendation regret, invalid rate, cost, latency, and coverage.

### choose_selector_for_origin

Input:

- `registered_selectors: Sequence[SelectorSpec]`
- `prior_metrics: Sequence[MetricRecord]`
- `origin: RollingOriginRecord`
- `controller_policy: ControllerPolicy`

Output:

- `SelectorSpec`

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

Aligned with the V2 architecture and roadmap:

- Selectors use common task sets for Agent comparisons.
- Future outcomes are not visible at selection time.
- Primary metric is future pass-rate MAE.
- Learned selectors start with data-efficient methods.
- Adaptive behavior is conservative and based on prior origins.
