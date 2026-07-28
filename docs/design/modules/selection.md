# Module Design: Selection

Status: current behavior and planned boundaries, 2026-07-27.

## Responsibility

Construct executable fixed-rule Selectors, fit the existing rule mixture from
frozen rolling-origin evidence, freeze benchmark selections, score frozen
selections, and choose among evaluated Selectors from paired historical MAE.
Model-based methods remain planned; the current fitting boundary is concrete
and algorithm-specific rather than a training platform.

Selection is the core research module.

## Inputs

- frozen `Task Pool`;
- pre-origin `Agent Results`;
- origin or historical window definition;
- candidate Agents;
- budget;
- fixed-rule parameters or specified Selector;
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

- Implemented and executable: random, recency, coverage, stratified-forecast,
  and rule-mixture selection.
- Implemented evaluation metrics: future pass-rate MAE, future coverage, future
  invalid rate, pairwise gap MAE, pairwise rank agreement, and recommendation
  regret.
- Implemented mean-MAE selector choice: `choose_selector_from_metrics` validates
  internally complete, paired rolling-origin Metric/future-matrix inputs and
  chooses the rule Selector with the lowest mean MAE. It uses a rule Selector
  fallback only when no prior metrics exist. This offline analysis API does not
  receive selected matrices or Results and is not a deployment evidence gate.
- Implemented offline shrinkage safe-switch choice:
  `choose_selector_with_safe_switch` reuses the same paired evidence validation
  and returns the fallback unless a candidate clears explicit history, margin,
  shrinkage, and uncertainty gates. It is not the Runner default.
- Implemented offline drift-aware guarded choice:
  `choose_selector_with_ewma_guard` rejects training evidence not mature before
  its explicit deployment Origin, orders validated paired rows by Origin cutoff,
  ranks candidates by a declared EWMA half-life, and then applies the unweighted
  full-history safe-switch to the one ranked candidate.
- Implemented paired MAE summary: `summarize_selector_mae` reports macro-Origin
  and scoreable-future-count-weighted MAE, canonical pairwise loss differences,
  exact seed-bank variation, and deterministic Origin-block intervals only when
  at least eight complete Origins exist.
- Implemented weight fitting for the existing executable `rule_mixture`:
  `train_selector` replays coverage, random, and recency Selections, recomputes
  their paired rolling-origin MAE from exact matrices and Results, and binds a
  deployment origin. It does not introduce another Selector family.
- Implemented offline thirds-simplex comparison: `build_rule_mixture_grid`
  freezes ten executable candidate mixtures, and
  `choose_rule_mixture_from_grid` applies a minimum-history and
  one-standard-error rule to their actual paired MAE, preferring the point
  closest to equal weights within the accepted band.

## Policy Records

`RollingOriginPolicy` defines:

- as-of cutoff rule;
- optional dependency-cluster constraints;
- eligibility mode: `strict_prospective` or `counterfactual_replay`;
- holdout overlap rule;
- whether future holdout `Task + Check` refs may be known before scoring;
- a nonnegative label-maturity lag.

Its digest is derived from these behavior fields; callers cannot supply an
unrelated policy digest. `future_holdout_known` must be an exact boolean, and
the optional dependency filter must be a tuple of nonempty string cluster IDs;
the persisted Origin validator enforces the same shapes. An explicit as-of cutoff may be earlier than the
origin, but never later. The runtime rejects a later cutoff before constructing
history or loading Result evidence. `strict_prospective` treats a ref as known
no earlier than Task Pool creation and forbids predeclared future refs.
`counterfactual_replay` reconstructs availability from Task and Check material
timestamps and may expose the predeclared future cohort for historical scoring.
Future cohort membership is always based on `task_material_available_at`; Check
availability determines whether the arrived label is mature by the fixed
cutoff. Immature refs remain in explicit history/future censored tuples and do
not become executable Results. `disjoint_clusters` rejects history/future
dependency-cluster overlap; it does not silently drop either side. Dependency
clusters are protocol metadata, not Selector features. A separately named
`sampling_stratum` may be exposed as `task_stratum`.

The caller supplies the future `TimeRange`; core does not impose a task-count
horizon. Offline studies may use the next `H` Tasks to control target sample
size, but that is an experiment protocol and must report the realized calendar
span. Imported historical availability may be used in
`counterfactual_replay` with its lineage. `strict_prospective` is required only
for the stronger real-time evidence claim.

Result visibility follows the same mode. Strict-prospective inputs reject a
Result observed after the Origin cutoff. Counterfactual inputs may use a
persisted Result observed later only when its exact Task/Check ref is mature
history and its Agent and cache identity match. The Result timestamp is not
projected. The exact Result view is frozen in `FeatureSnapshotRecord` and
`SelectorInput`; a Result appended by later lazy evaluation cannot alter an
already persisted or resumed Selection.

`SelectionBudget` accepts only `max_task_checks`, which must be a positive
integer; `budget_digest` is derived from that limit. `FeatureConfig` accepts
only feature names. It rejects empty, duplicate, non-string, and unsupported
inputs, normalizes supported names to the builder's execution order, derives
their leakage classes from the implementation, and then derives
`feature_config_digest`. For each origin it constructs a `LeakagePolicy` from
those classes and the cutoff; `leakage_policy_digest` is derived from both
values. Callers cannot attach unrelated labels to any of these behavior-only
configurations.

`BenchmarkSelectionRecord` is the frozen benchmark selection. Selection must
write it append-only before future holdout outcomes are opened. Selection
functions must not accept future-result paths, verifier workspaces, raw
hidden-check material, or raw Agent transcripts.

The stable Selector, Benchmark Selection, and Metric IDs identify semantic
outputs rather than repeated observations. Runner retains the first persisted
observation timestamp on resume when the remaining record is identical; a
same-ID semantic difference is invalid.

Rule-based `SelectorRecord.parameters` contains every value that changes
selection behavior:

- recency: `{}`;
- random: `{"seed": int}`;
- coverage: `{"group_by_ref_key": {task_check_ref_key: group}}`;
- stratified forecast: `{"dirichlet_alpha": positive number,
  "trailing_ref_count": positive int, "seed": int,
  "weight_cap": null or number >= 1}`;
- rule mixture: `{"expert_weights": {...}, "random_seed": int,
  "group_by_ref_key": {...}}`.

Construction validates these family-specific shapes, normalizes accepted
continuous integer/float forms to built-in floats, and snapshots nested string
mappings in stable key order before deriving identity. An externally supplied
record is executable only when its parameters already have that canonical
shape; validation does not silently rescale or add omitted weights. The shared
canonical JSON boundary treats floating `-0.0` as `0.0`, so that spelling is an
identity-equivalent zero rather than a Selector-specific rejection rule.
Because rule-mixture inference divides by total expert weight, its canonical
shape contains all three experts as positive-zero-normalized floats on a unit
simplex. Overall scaling and omitted zero-weight experts cannot create another
identity for the same ranking behavior; normalization is idempotent under
`fsum` even for highly imbalanced weights.
Inference also uses `fsum` across the weighted expert scores. Mathematical ties
therefore reach the documented Task/Check ID tie-break instead of depending on
binary64 operand order.
`SelectorRecord.config_digest` covers the family and these canonical parameters.
`SelectorInput` already binds the feature snapshot and budget, while
`SelectorRecord` binds the algorithm identity. Selection therefore needs no
second per-freeze configuration object.

## Selection Entry Points

These are module-level entry points. Runner calls them as needed.

### train_selector

Input:

- `selector_family: str`
- `deployment_origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `training_origins: Sequence[RollingOriginRecord]`
- `feature_snapshots: Sequence[FeatureSnapshotRecord]`
- `selector_inputs: Sequence[SelectorInput]`
- `expert_selectors: Sequence[SelectorRecord]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`
- `pre_origin_results: Sequence[ResultRecord]`
- `training_results: Sequence[ResultRecord]`

Output:

- `SelectorRecord`

Effect:

- Supports only the current concrete fitted family, `rule_mixture`; fixed rules
  use `build_rule_selector` and choosing evaluated records remains separate.
- Requires exactly one executable coverage, random, and recency expert at every
  training origin. It validates each Origin/Snapshot/Input chain, resolves the
  exact pre-origin Results, verifies Selector digests, and deterministically
  replays each frozen Selection.
- Requires every training SelectorInput to carry the same ordered Agent IDs and
  complete AgentRecord digests. Each bound training Result cache identity is
  projected through the Records-owned Agent contract and must match that frozen
  digest; a stable ID alone is not a comparable treatment.
- Requires the deployment and all training Origins to validate against one
  frozen Task Pool and its exact ordered Task/Check record digests. It replays
  each FeatureSnapshot's Task metadata provenance and every pre-origin/outcome
  Result's Task/Check cache projection before fitting.
- Requires selected and future matrices plus one complete aggregate
  `future_pass_rate_mae` metric per Selection. It resolves every matrix Result,
  applies Records' complete cell-to-Result identity and outcome predicate,
  requires common future evidence within an origin, and recomputes MAE instead
  of trusting the stored value. Every cell carrying a Result ID/digest is
  covered, including bound exclusions; only genuinely unbound excluded or
  missing cells omit Result evidence. It also calls Result Store's derived-state
  check, so a bound exclusion must follow benchmark-invalid or agent-invalid
  evidence rather than merely carrying a valid Result binding, and the complete
  Matrix must follow its one declared join/denominator policy, including derived
  abstention and scoreability.
- Every training origin's label-maturity cutoff precedes the deployment cutoff. A
  strict-prospective deployment additionally requires each bound outcome Result
  to have been available strictly before that cutoff; counterfactual replay may
  use evidence collected later while retaining the historical logical windows.
- Stores compact weights and inherited coverage/random parameters directly in
  an executable `SelectorRecord`. Category-specific source digests bind the
  trainer protocol, deployment and training origins, snapshots, inputs,
  experts, Selections, matrices, metrics, pre-origin Results, and outcome
  Results.

### build_rule_selector

Input:

- `selector_family: str`
- `parameters: Mapping[str, JSONValue] | None`
- `allowed_feature_classes: tuple[str, ...]`

Output:

- executable fixed-rule `SelectorRecord`

Effect:

- Constructs coverage, random, recency, or stratified-forecast Selectors. It
  validates the family's exact parameter shape, normalizes allowed feature
  classes, records no fake training sources, and includes those classes in
  Selector identity. Stratified forecast requires `task_stratum` features at
  inference; `weight_cap=null` is the exact unweighted stratified baseline.

### build_rule_mixture_grid

Input:

- `random_seed: int`
- `group_by_ref_key: Mapping[str, str]`
- `allowed_feature_classes: tuple[str, ...]`

Output:

- ten executable `rule_mixture` Selector records

Effect:

- Enumerates every nonnegative coverage/random/recency weight triple in thirds
  that sums to one, including equal weights and each individual expert.
- Binds all points to one grid-protocol digest, random seed, coverage mapping,
  Selector version, and feature-class contract. It opens no Result evidence and
  does not claim the candidates were outcome-fitted.

### select_with_selector

Input:

- `selector_input: SelectorInput`
- `feature_snapshot: FeatureSnapshotRecord`
- `selector: SelectorRecord`

Output:

- `BenchmarkSelectionRecord`

Effect:

- Validates the executable Selector and the materialized snapshot, not only its
  ID. Snapshot origin, records digest, leakage policy, lint status, cutoff, and
  leakage classes must match the frozen SelectorInput and Selector contract.
- Runs inference only over the input's eligible refs and budget, returns one
  frozen `BenchmarkSelectionRecord`, and cannot open training or future Result
  sources. Runner owns Task/Check/origin construction and persists all
  Selections before future resolution.
- For `stratified_forecast`, counts only the declared trailing eligible refs,
  applies symmetric Dirichlet smoothing over all eligible strata, allocates a
  capacity-constrained largest-remainder quota, and uses a digest-ranked seed
  within each stratum. Optional post-stratification weights are capped before
  being stored in the existing `selected_weights` mapping.

### ensure_selection_replay

Input:

- `selector_input: SelectorInput`
- `feature_snapshot: FeatureSnapshotRecord`
- `selector: SelectorRecord`
- `selection: BenchmarkSelectionRecord`

Output:

- none; raises on invalid or non-replayable evidence.

Effect:

- Calls the ordinary deterministic inference path and compares every semantic
  Selection field: IDs and digests for the pool, Origin, Selector, input and
  snapshot; selected refs and weights; budget; and eligibility mode.
- Ignores only `created_at` and the resulting self-digest because replay occurs
  after the original observation.
- Is the single replay assertion used by prospective Runner preflight,
  Reporting, Selector training, and stratified diagnostics.

### ensure_selector_input_result_evidence

Input:

- `selector_input: SelectorInput`
- `origin: RollingOriginRecord`
- `feature_snapshot: FeatureSnapshotRecord`
- `pre_origin_results: Sequence[ResultRecord]`

Output:

- the exact resolved Results in frozen SelectorInput order; raises on
  incomplete or inconsistent evidence.

Effect:

- Resolves every frozen Result ID/digest in SelectorInput order. The supplied
  Result collection may be unordered, but duplicate records, duplicate frozen
  bindings, missing IDs, and digest drift fail closed.
- Requires the Input's history, cutoff, eligibility mode, Agent membership,
  and each Result's availability to match the exact Origin.
- Projects each Result cache identity back to an AgentRecord and requires its
  canonical digest to match the full Agent digest frozen by SelectorInput.
- Replays the FeatureSnapshot Result-view digest and every aggregate or
  Result-linked provenance record against the resolved view.
- Is the shared construction, training, and prospective-execution assertion.
  Reporting keeps a separate multi-error adapter because reports accumulate
  all unsupported-claim reasons instead of failing on the first error.

### ensure_feature_snapshot_task_metadata_provenance

Input:

- `snapshot: FeatureSnapshotRecord`
- `origin: RollingOriginRecord`
- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`

Output:

- `None`; raises on incomplete or inconsistent provenance.

Effect:

- Requires the snapshot, Origin, and Task Pool identities to agree and every
  FeatureRecord to carry the canonical Origin/config provenance digest.
- For `task_count`, requires one origin-scoped record with the exact history
  count, cutoff observation time, and Task Pool digest.
- For `task_stratum`, requires exactly one record for every Origin history ref,
  with the exact Task value, Task-known time, and canonical Task digest.
- Rejects an unknown feature using the `task_metadata` leakage class. Adding a
  Task metadata feature therefore requires its builder and replay rule in the
  same change rather than a registry or permissive fallback.
- Is shared by snapshot construction, strict prospective execution, and
  Reporting. A future trainer must call it when that trainer first consumes
  Task metadata values; the current metric-only rule-mixture fitter does not.

### summarize_stratified_forecast

Input:

- `selector_input: SelectorInput`
- `feature_snapshot: FeatureSnapshotRecord`
- `selector: SelectorRecord`
- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `future_stratum_by_ref_key: Mapping[str, str]`

Output:

- deterministic diagnostic mapping

Effect:

- Replays the exact Selection and rejects Origin, snapshot, Selector, or future
  stratum coverage drift.
- Reports forecast/future proportions, realized quotas, forecast TV error,
  unweighted and post-stratified TV error, effective sample size/fraction,
  configured and realized maximum weight, and the fraction of selected refs
  whose raw post-stratification weight was capped.
- Reads future stratum labels only after Selection freeze and never reads
  future Agent outcomes. Reporting publishes the mapping only after the same
  complete provenance chain passes and binds the TaskRecords digest used for
  future stratum labels.

## Functions

### build_rolling_origin

Input:

- `task_pool: TaskPoolRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`
- `origin_time: datetime`
- `future_window: TimeRange`
- `policy: RollingOriginPolicy`
- `history_window: TimeRange | None`

Output:

- `RollingOriginRecord`

Effect:

- Defines history and future cohorts without exposing future outcomes to
  selectors. Task-material arrival determines cohort membership. Task/Check
  availability determines label maturity at the history cutoff or at
  `future_window.end + maturity_lag_seconds`.
- Binds the materialized as-of cutoff to `as_of_cutoff_rule` and requires the
  future window to start at or after that cutoff.
- Stores mature and censored refs separately. Only mature history refs are
  eligible Selector inputs; only mature future refs enter execution and
  scoring. An empty mature future cohort is valid and produces abstention rather
  than synthetic evidence.
- Applies optional dependency-cluster constraints and disjointness to the union
  of mature and censored refs. When supplied, `history_window` bounds arrivals
  at both its start and the origin's as-of cutoff; omitting it means all arrived
  history through that cutoff.
- Requires every Task and Check named by the Task Pool to be present and each
  Check to link back to its owning Task before deriving cohorts. Extra records
  may be supplied but do not enter the Task Pool denominator.

### materialize_prospective_future_cohort

Input:

- a persisted strict-prospective `BenchmarkSelectionRecord` and its
  `RollingOriginRecord`;
- the Selection Task Pool and a later Task Pool;
- both pools' validated Task and Check records.

Output:

- mature future `TaskCheckRef` records;
- censored future `TaskCheckRef` records.

Effect:

- Requires the Selection to predate its declared future window and the later
  Task Pool. The later pool must be observed through the label-maturity cutoff,
  use the same repository, stable Generator behavior, source protocol, and
  certification config, and cover the complete planned future source window.
  The later pool may contain only that incremental interval or a wider
  cumulative interval. Run, observed-frame, and output identities may change.
- Rejects changed same-ID Task or Check records across snapshots and replays
  dependency-cluster filtering and overlap policy.
- Derives arrival and maturity from the later pool without changing the frozen
  Origin. It does not open Results, execute Agents, or create a second Origin.

### compare_arrival_and_label_time_cohorts

Input:

- `origin: RollingOriginRecord`
- `tasks: Sequence[TaskRecord]`
- `checks: Mapping[str, CheckRecord]`

Output:

- cohort and label-delay diagnostic mapping

Effect:

- For a counterfactual origin with known future refs, compares the frozen
  task-arrival cohort with the legacy label-time cohort. Reports mature and
  censored counts, inclusion rate, overlap/difference counts, maturity cutoff,
  and a label-delay distribution. It does not compute or claim MAE.

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
  future result paths. The returned snapshot stores the feature-config digest,
  a self-digest, the exact pre-origin Result-view digest, and a persisted
  `passed` leakage-lint status.
- Validates that every present Task, Check, Agent, and cache-identity field on a
  Result-linked feature matches the exact visible Result. Origin-level result
  aggregates retain the complete-view digest and exact count contract.
- Derives the exact per-origin leakage policy from `FeatureConfig` and the
  origin cutoff before writing or linting the snapshot. Leakage classes are
  implementation-owned properties of the canonical feature names, not a
  second caller-supplied list.
- Exposes `TaskRecord.sampling_stratum` only when `task_stratum` is requested.
  `dependency_cluster_id` is intentionally absent from the feature vocabulary.
- Calls the Task metadata provenance assertion before returning, so constructed
  `task_count` and `task_stratum` records use the same replay contract as
  strict execution and Reporting.

### lint_feature_snapshot

Input:

- `snapshot: FeatureSnapshotRecord`
- `policy: LeakagePolicy`

Output:

- `ValidationResult`

Effect:

- Rejects a snapshot whose policy digest, records digest, observation cutoff,
  or leakage classes disagree with the supplied policy. Exact Result and Task
  source provenance is replayed by the two dedicated assertions above.

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
  The output digest binds origin, task pool, feature snapshot, ordered Agent
  IDs and full Agent-record digests,
  eligible `Task + Check` refs, pre-origin result view, budget, and leakage
  policy, the origin eligibility mode, and the complete chronological history
  denominator.
- Uses the Records-owned SelectorInput contract: Agent IDs and eligible refs
  are unique, Agent IDs and record digests align, the cutoff is canonical UTC,
  and the budget digest is derived from the positive selection limit.
  Inference does not maintain a second copy of these checks.
- Calls `ensure_selector_input_result_evidence` before returning, so the
  persisted IDs/digests, Origin scope, and Feature provenance replay through
  the same contract used by training and strict prospective execution.
- Allows an explicit empty pre-origin result view for metadata-only cold-start
  selector inputs.

Random, recency, coverage, stratified-forecast, and rule-mixture behavior is
reachable only through the `SelectorRecord`-based `select_with_selector` entry
point above. There are no parallel public helpers that can bypass
FeatureSnapshot validation.

### evaluate_selection

Input:

- `selection: BenchmarkSelectionRecord`
- `origin: RollingOriginRecord`
- `evaluation_cells: EvaluationCellSet`
- `selected_matrix: ResultMatrix`
- `future_matrix: ResultMatrix`

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
- Emits metric records with selected/future matrix, cell-set, metric-protocol,
  and metric digests, not a human-facing report. The metric-protocol digest is
  derived by Selection from a versioned declaration of the implemented metric
  names and aggregation level; callers cannot relabel identical scoring
  behavior. Before computing metrics, the function verifies the
  Selection/Origin eligibility mode, matrix roles, origin, selection, Agent
  set, join policy, and denominator policy alignment. Matrix cells must
  preserve each frozen cell's required identity, result ID, result digest, and
  outcome. If these checks fail, it emits abstention or invalid metric records
  instead of scoring the comparison.
- Every emitted metric binds `budget_digest` to the frozen Selection budget.
  Add a caller-visible metric configuration only when a concrete scoring
  behavior can vary; include that behavior in the implementation-derived
  protocol identity.
- Metric completeness is `complete_with_exclusions` when either matrix has
  exclusions and every Agent still has result cells in both matrices. If
  exclusions empty any Agent's selected or future denominator, evaluation
  abstains instead of assigning a zero pass rate. Metrics are `complete` only
  when both matrices are complete.

This function scores materialized evidence; it does not discover later task
supply. Counterfactual evidence takes its future denominator from the Origin.
Strict-prospective evidence takes mature future refs from an EvaluationCellSet
whose later Task Pool has already been replayed by Runner and Reporting. The
frozen strict Origin remains unchanged and empty of future refs.

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
  future matrix, its Selection must bind the registered Selector digest, and
  every Selector at one origin must use the same future Result cells. Missing
  Selectors, metrics, matrices, duplicate records, and mismatched fields are
  input errors.
- Averages each Selector's comparable rows and returns the lowest mean MAE,
  breaking ties by Selector ID. When Selection, Metric, and future-matrix inputs
  are all empty, it returns the registered fallback.
- Does not recompute MAE from selected matrices or replay exact Results. Before
  promotion into Runner or a deployed adaptive policy, a caller must add the
  complete training-style evidence replay and persist choice provenance; this
  offline function alone cannot support an evidence claim.

### choose_selector_with_safe_switch

Input:

- the same registered Selector, Selection, Metric, future-matrix, and fallback
  inputs as `choose_selector_from_metrics`;
- `config: SafeSwitchConfig`.

Output:

- `SelectorRecord`

Effect:

- Reuses the complete paired-evidence checks from mean-MAE choice.
- Computes each candidate's per-Origin improvement over the frozen fallback,
  shrinks the mean improvement toward zero, and subtracts a configurable
  multiple of its sample standard error.
- Returns the strongest candidate only when the configured minimum Origin count
  is met and the conservative improvement strictly exceeds the configured
  margin. Otherwise it returns the fallback. Ties are deterministic by Selector
  ID.
- This is an offline choice rule. Hyperparameter choice belongs inside prior
  nested rolling origins; outer-origin evidence remains reserved for evaluation.

### choose_selector_with_ewma_guard

Input:

- the same registered Selector, Selection, Metric, future-matrix, and fallback
  inputs as `choose_selector_from_metrics`;
- `training_origins: Sequence[RollingOriginRecord]`;
- `deployment_origin: RollingOriginRecord`;
- `config: EWMASwitchConfig`.

Output:

- `SelectorRecord`

Effect:

- Reuses the complete paired-evidence checks and requires the supplied training
  Origins to exactly cover those rows. Training and deployment Origins validate
  and bind the same Task Pool. Every training origin and cutoff precedes
  deployment, its label-maturity cutoff is available by deployment, and the
  training set uses one comparable policy and distinct `as_of_cutoff` instants.
- Orders rows by cutoff, ranks Selectors by normalized exponentially weighted
  mean MAE, and uses the configured half-life in units of Origins. Input order
  and lexical Origin IDs do not determine recency.
- Returns the fallback when it ranks first or history is shorter than the
  embedded safe-switch minimum. Any other ranked candidate must then clear
  `choose_selector_with_safe_switch` against the fallback on the ordinary
  unweighted full history. The EWMA is not treated as a confidence interval.
- Half-life and safe-switch configuration belong inside prior nested rolling
  origins. Outer-origin evidence remains reserved for comparison.

### choose_rule_mixture_from_grid

Input:

- `registered_selectors: Sequence[SelectorRecord]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `mae_metrics: Sequence[MetricRecord]`
- `future_matrices: Sequence[ResultMatrix]`
- `config: SimplexChoiceConfig`

Output:

- one registered grid `SelectorRecord`

Effect:

- Requires the complete ten-point thirds grid with identical non-weight
  behavior and reuses the same complete paired-evidence validation as other
  Selector choices. It never derives a mixture loss from individual-expert
  losses.
- With fewer than the configured prior Origins, returns equal weights.
  Otherwise it finds the point with lowest mean MAE, adds that point's sample
  standard error, and chooses the eligible point closest to equal weights;
  lower mean and Selector ID break remaining ties.
- Grid evaluation and this choice occur only inside prior rolling-origin
  history. Outer Origins compare the frozen chosen point against equal weights,
  individual experts, and the current inverse-MAE fitted mixture.

### summarize_selector_mae

Input:

- `registered_selectors: Sequence[SelectorRecord]`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `mae_metrics: Sequence[MetricRecord]`
- `future_matrices: Sequence[ResultMatrix]`

Output:

- deterministic summary mapping

Effect:

- Reuses the same complete paired-origin validation as Selector choice: one
  Task Pool, budget, current implementation-owned metric protocol,
  join/denominator policy, and exact future Result evidence per Origin across
  every registered Selector. An internally consistent unknown protocol is not
  treated as comparable evidence.
- Weights an Origin by its distinct future Task/Check refs with Result cells,
  after common exclusions. Reports macro-Origin MAE, weighted MAE, and
  canonical A-minus-B paired differences. It rejects empty or non-scoreable
  evidence rather than reporting zero loss.
- Groups `random.seed`, `stratified_forecast.seed`, or
  `rule_mixture.random_seed` variants only when every non-seed behavior and
  training-source field matches, then reports the mean and population standard
  deviation of per-seed macro MAE.
- With at least eight Origins, reports a deterministic 10,000-resample 95%
  paired Origin-block percentile interval using seed `20260722`; otherwise the
  interval state is `insufficient_origin_blocks` with null bounds.
- This function aggregates already validated Metric evidence. Reporting
  publishes the summary only after it also validates and recomputes the full
  selected/future matrix provenance chain.

## Selector Development Order

Development order, with the first five steps implemented offline:

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
- Aggregate MAE weighting, pairing, seed-bank, and interval rules match
  `docs/statistical-protocol.md`.
- Learned selectors start with data-efficient methods.
- `choose_selector_from_metrics` rejects incomplete or incomparable
  rolling-origin MAE rows before comparing Selectors.
- `choose_selector_with_safe_switch` uses the same paired rows and never treats
  missing history as evidence to leave the fallback.
- `choose_selector_with_ewma_guard` derives chronology from validated Origin
  cutoffs and cannot bypass the unweighted full-history safe-switch.
- Reporting, not Selection, owns human-readable reports.
