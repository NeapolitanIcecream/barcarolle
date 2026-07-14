# Module Design: Selection

Status: current behavior and planned boundaries, 2026-07-14.

## Responsibility

Configure executable rule-based Selectors from historical inputs, freeze
benchmark selections for a specified Selector, score already-frozen selections,
and choose among evaluated Selectors from prepared historical MAE rows. Learned
methods remain planned; their training contract will be defined with the first
concrete algorithm.

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
- user config;
- selector config;
- feature config.

Output consumers:

- Reporting;
- Runner.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Capability Status

- Implemented and executable: random, recency, coverage, and rule-mixture
  selection.
- Implemented evaluation metrics: future pass-rate MAE, future coverage, future
  invalid rate, pairwise gap MAE, pairwise rank agreement, and recommendation
  regret.
- Implemented mean-MAE selector choice: `choose_selector_from_metrics` validates
  complete, paired rolling-origin metrics and chooses the rule Selector with the
  lowest mean MAE. It uses a rule Selector fallback only when no prior metrics
  exist.
- Implemented weight fitting for the existing executable `rule_mixture`:
  `fit_rule_mixture_from_metrics` uses paired rolling-origin MAE from the
  coverage, random, and recency Selectors. It does not introduce another
  Selector family.

## Policy Records

`RollingOriginPolicy` must define:

- as-of cutoff rule;
- task cluster constraints;
- eligibility mode, such as strict historical evaluation or explicit
  counterfactual replay;
- holdout overlap rule;
- whether future holdout `Task + Check` refs may be known before scoring.

An explicit as-of cutoff may be earlier than the origin, but never later. The
runtime rejects a later cutoff before constructing history or loading Result
evidence.

`BenchmarkSelectionRecord` is the frozen benchmark selection. Selection must
write it append-only before future holdout outcomes are opened. Selection
functions must not accept future-result paths, verifier workspaces, raw
hidden-check material, or raw Agent transcripts.

Rule-based `SelectorRecord.parameters` contains every value that changes
selection behavior:

- recency: `{}`;
- random: `{"seed": int}`;
- coverage: `{"group_by_ref_key": {task_check_ref_key: group}}`;
- rule mixture: `{"expert_weights": {...}, "random_seed": int,
  "group_by_ref_key": {...}}`.

`SelectorRecord.config_digest` covers the family and these parameters.
`SelectionConfig` contains per-freeze bindings and metadata; changing its digest
does not change a Selector's algorithm.

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

- Chooses a supplied executable Selector or creates a persistent rule-based
  Selector using only historical data allowed by the training config and
  rolling-origin policy.
- Copies the rule parameters from `SelectorTrainingConfig` into the resulting
  `SelectorRecord`, so the record is directly executable and replayable.
- Rejects planned learned or calibrated families instead of creating a
  `SelectorRecord` that `select_with_selector` cannot execute.

### freeze_evaluation_selections

Input:

- `selector: SelectorRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `selector_inputs: Sequence[SelectorInput]`
- `agents: Sequence[AgentRecord]`
- `history_window: TimeRange`
- `selection_config: SelectionConfig`
- `rolling_policy: RollingOriginPolicy`

Output:

- `selections: Sequence[BenchmarkSelectionRecord]`

Effect:

- Freezes one `BenchmarkSelectionRecord` per already-built `SelectorInput`, in
  input order, for a specified Selector.
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
  refs. The policy defines as-of cutoff, cluster constraints, eligibility mode,
  and holdout overlap rules.

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
- Allows an explicit empty pre-origin result view for metadata-only cold-start
  selector inputs.

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

- Selects the latest eligible task/check refs under budget. Rolling-origin
  construction orders refs by their UTC known-at instant, then task ID and
  check ID, so caller input order cannot change recency behavior.

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
- `selector_parameters: Mapping[str, JSONValue]`
- `selection_config: SelectionConfig`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Combines normalized recency, deterministic-random, and coverage round-robin
  ranks with nonnegative expert weights, then selects one common task and check
  set.
- Rejects unknown expert names and negative or non-finite weights instead of
  silently changing their meaning.
- Uses the persisted random seed and coverage groups from
  `selector_parameters`; `SelectionConfig` does not supply algorithm parameters.

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

- Computes future pass-rate MAE, future coverage, future invalid rate, pairwise
  gap MAE, pairwise rank agreement, and recommendation regret by comparing
  selected-benchmark estimates against future-holdout outcomes.
- Pairwise rank agreement is the fraction of Agent pairs whose selected and
  future signed ordering agrees, including tie state. With fewer than two Agents
  it is `1.0`.
- Recommendation regret is the future best pass rate minus the future pass rate
  of the selected-benchmark recommendation. Selected-rate ties use the lowest
  Agent ID.
- Emits metric records with selected/future matrix, cell-set, metric-config, and
  metric digests, not a human-facing report. Before computing metrics, it
  verifies matrix roles, origin, selection, Agent set, join policy, and
  denominator policy alignment. Matrix cells must preserve each frozen cell's
  required identity, result ID, result digest, and outcome. If these checks
  fail, it emits abstention or invalid metric records instead of scoring the
  comparison.
- Every emitted metric binds `budget_digest` to the frozen selection budget. A
  non-null, conflicting `MetricConfig.budget_digest` produces an invalid metric
  instead of a cross-budget comparison.
- Metric completeness is `complete_with_exclusions` when either the selected or
  future matrix has exclusions; it is `complete` only when both are complete.

### choose_selector_by_mean_mae

Input:

- `registered_selectors: Sequence[SelectorRecord]`
- `mae_by_origin: Sequence[Mapping[str, float]]`
- `fallback_selector_id: str`

Output:

- `SelectorRecord`

Effect:

- Each row contains one comparable MAE value for every registered Selector at
  one prior origin.
- Averages each Selector's rows and returns the lowest mean MAE, breaking ties by
  Selector ID.
- Uses the registered fallback only when `mae_by_origin` is empty. Incomplete
  rows and non-finite or out-of-range MAE values are input errors.

### choose_selector_from_metrics

Input:

- `registered_selectors: Sequence[SelectorRecord]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `mae_metrics: Sequence[MetricRecord]`
- `future_matrices: Sequence[ResultMatrix]`
- `fallback_selector_id: str`

Output:

- `SelectorRecord`

Effect:

- Validates frozen Selections and `future_pass_rate_mae` Metric records, then
  pairs one metric with every registered Selector at every supplied origin.
- Requires one Task Pool and budget across the comparison and one frozen
  selection input per origin. Metric configuration, join policy, and
  denominator policy must match globally; completeness state must match within
  an origin but may differ across origins. Each Metric must bind its supplied
  future matrix, and every Selector at one origin must use the same future
  Result cells. Missing Selectors, metrics, matrices, duplicate records, and
  mismatched fields are input errors.
- Calls `choose_selector_by_mean_mae` with the paired rows. When Selection,
  Metric, and future-matrix inputs are all empty, it returns the registered
  fallback.

### fit_rule_mixture_from_metrics

Input:

- `expert_selectors: Sequence[SelectorRecord]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `mae_metrics: Sequence[MetricRecord]`
- `future_matrices: Sequence[ResultMatrix]`

Output:

- executable `SelectorRecord` with `selector_family="rule_mixture"`

Effect:

- Requires exactly one executable coverage, random, and recency Selector and
  reuses the same complete paired-MAE checks as
  `choose_selector_from_metrics`. Missing paired evidence is an input error;
  there is no fallback.
- Sets each expert's weight to one minus its mean `future_pass_rate_mae` across
  origins. If all three values are zero, it uses equal positive weights.
- Inherits the random seed and coverage grouping directly from their expert
  Selectors. The mixture's random component uses the same seeded ordering as
  the standalone random Selector. The fitted record binds the expert Selector
  records, Selections, and Metric records through `training_source_digests`;
  each Metric already binds its future matrix digest.

## Selector Development Order

Development order, with the first three steps implemented:

1. random, recency, and coverage baselines;
2. strong baseline envelope;
3. fit the existing rule-mixture weights from paired MAE;
4. calibrated constrained weighting;
5. future-stratum matching;
6. outcome-aware selectors only under explicit available-before-origin rules;
7. pairwise and hierarchical models only when data volume supports them;
8. stronger learned or drift-aware adaptive control after selectors have enough
   prior-origin evidence; mean-MAE Selector choice remains the baseline.

## Design Consistency Check

- Selectors use common task sets for Agent comparisons.
- Future outcomes are not visible at selection time.
- Historical evaluation freezes benchmark selections before any scoring step.
- Rolling-origin leakage controls are represented in function inputs, not only
  prose.
- Feature provenance is recorded before selector input is built.
- Primary metric is future pass-rate MAE.
- Learned selectors start with data-efficient methods.
- `choose_selector_from_metrics` rejects incomplete or incomparable
  rolling-origin MAE rows before comparing Selectors.
- Reporting, not Selection, owns human-readable reports.
