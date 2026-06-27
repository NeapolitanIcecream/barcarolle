# Module Design: Selection

Status: draft, 2026-06-27.

## Responsibility

Train Selectors from historical data, freeze benchmark selections for a
specified Selector, score already-frozen selections, and update Selector choice
from new evaluation feedback.

Selection is the core research module.

## Inputs

- frozen `Task Pool`;
- pre-origin `Agent Results`;
- origin or historical window definition;
- candidate Agents;
- budget;
- selector config or specified Selector;
- rolling-origin policy;
- feature config and leakage policy.

## Outputs

- `BenchmarkSelectionRecord`;
- `SelectorRecord`;
- `FeatureSnapshotRecord`;
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

## Policy Records

`RollingOriginPolicy` must define:

- as-of cutoff rule;
- embargo interval;
- task cluster constraints;
- eligibility mode, such as strict historical evaluation or explicit
  counterfactual replay;
- holdout overlap rule;
- whether future holdout `Task + Check` refs may be known before scoring.

`BenchmarkSelectionRecord` is the frozen benchmark selection. Selection must
write it before future holdout outcomes are opened. Selection functions must not
accept future-result paths, verifier workspaces, raw hidden-check material, or
raw Agent transcripts.

## Selection Entry Points

These are module-level entry points. Runner calls them as needed.

### train_selector

Input:

- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `candidate_selectors: Sequence[SelectorRecord]`
- `training_config: SelectorTrainingConfig`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`

Output:

- `SelectorRecord`

Effect:

- Trains or chooses a persistent Selector using only historical data allowed by
  the training config and rolling-origin policy. Rolling-origin splitting is
  internal to this function.

### freeze_evaluation_selections

Input:

- `selector: SelectorRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `selector_inputs: Mapping[str, SelectorInput]`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `evaluation_config: SelectorEvaluationConfig`
- `rolling_policy: RollingOriginPolicy`

Output:

- `selections: Sequence[BenchmarkSelectionRecord]`

Effect:

- Freezes one `BenchmarkSelectionRecord` per origin for a specified Selector.
  It does not score selections, does not accept raw result sets, and does not
  open future outcomes.

### select_benchmark

Input:

- `selector: SelectorRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `pre_origin_results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `origin_time: datetime`
- `budget: SelectionBudget`
- `selection_config: SelectionConfig`
- `rolling_policy: RollingOriginPolicy`
- `feature_config: FeatureConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Uses the specified Selector at the origin to choose a production benchmark
  and write a frozen `BenchmarkSelectionRecord` before future outcomes are
  opened. It does not run missing Agent-task-check cells; Runner handles lazy
  Agent execution after this record is produced.

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
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `origin_time: datetime`
- `future_window: TimeRange`
- `policy: RollingOriginPolicy`

Output:

- `RollingOriginRecord`

Effect:

- Defines history pool and future holdout without exposing future outcomes to
  selectors. It uses Task and Check timestamps to build eligible `Task + Check`
  refs. The policy defines as-of cutoff, embargo, cluster constraints,
  eligibility mode, and holdout overlap rules.

### build_feature_snapshot

Input:

- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `pre_origin_results: Sequence[ResultRecord]`
- `feature_config: FeatureConfig`

Output:

- `FeatureSnapshotRecord`

Effect:

- Builds pre-origin feature records with scope, optional Agent/result linkage,
  aggregation method, `observed_at`, `source_artifact_digest`,
  `origin_snapshot_digest`, and `leakage_class`. The function does not read
  future result paths.

### lint_feature_snapshot

Input:

- `snapshot: FeatureSnapshotRecord`
- `policy: LeakagePolicy`

Output:

- `ValidationResult`

Effect:

- Rejects features whose `observed_at`, source, or leakage class is not allowed
  for the origin and eligibility mode.

### build_selector_input

Input:

- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `feature_snapshot: FeatureSnapshotRecord`
- `pre_origin_results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- `budget: SelectionBudget`
- `leakage_policy: LeakagePolicy`

Output:

- `SelectorInput`

Effect:

- Runs leakage linting and builds the pre-origin data visible to a selector.
  The output digest binds origin, task pool, feature snapshot, Agent set,
  eligible `Task + Check` refs, pre-origin result view, budget, and leakage
  policy.

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
  and check set.

### fit_learned_mixture

Input:

- `training_origins: Sequence[RollingOriginRecord]`
- `training_selector_inputs: Mapping[str, SelectorInput]`
- `baseline_selectors: Sequence[SelectorRecord]`
- `fit_config: FitConfig`

Output:

- `SelectorRecord`

Effect:

- Learns mixture weights over rule-based selectors using only leakage-checked,
  out-of-origin selector inputs.

### fit_calibrated_weighting

Input:

- `training_origins: Sequence[RollingOriginRecord]`
- `training_selector_inputs: Mapping[str, SelectorInput]`
- `selection_config: SelectionConfig`

Output:

- `SelectorRecord`

Effect:

- Fits a low-dimensional weighting layer for calibrated, constrained coreset
  selection using leakage-checked selector inputs.

### select_with_selector

Input:

- `selector_input: SelectorInput`
- `selector: SelectorRecord`
- `selection_config: SelectionConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Selects one common task set and weight vector for all Agents in the
  comparison, then returns a frozen `BenchmarkSelectionRecord` with selected
  `Task + Check` refs, weights, selector input digest, and feature snapshot ID.

### evaluate_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `evaluation_cells: EvaluationCellSet`
- `selected_matrix: ResultMatrix`
- `future_matrix: ResultMatrix`
- `metric_config: MetricConfig`

Output:

- `Sequence[MetricRecord]`

Effect:

- Computes future pass-rate MAE, pairwise gap error, rank agreement,
  recommendation regret, invalid rate, cost, latency, and coverage by comparing
  selected-benchmark estimates against future-holdout outcomes. It emits metric
  records with selected/future matrix, cell-set, and metric-config digests, not
  a human-facing report. Before computing MAE, it verifies matrix roles,
  origin, selection, Agent set, join policy, and denominator policy alignment.
  If these checks fail, it emits abstention or invalid metric records instead
  of scoring the comparison.

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
- Historical evaluation freezes benchmark selections before any scoring step.
- Rolling-origin leakage controls are represented in function inputs, not only
  prose.
- Feature provenance is recorded before selector input is built.
- Primary metric is future pass-rate MAE.
- Learned selectors start with data-efficient methods.
- Adaptive behavior is based on prior-origin metrics and later feedback
  supplied through Metric records.
- Reporting, not Selection, owns human-readable reports.
