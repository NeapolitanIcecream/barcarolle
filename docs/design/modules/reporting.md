# Module Design: Reporting

Status: current, 2026-07-27.

## Responsibility

Create claim-safe reports from existing records. Reporting does not create new
evidence and does not run experiments.

## Inputs

- `TaskPoolRecord`;
- `SelectorRecord` records;
- `RollingOriginRecord` records;
- `FeatureSnapshotRecord` records;
- `SelectorInput` records;
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
- `artifact_root: Path | None`

Output:

- `ReportSection`

Effect:

- Summarizes task count, check count, optional generation-provenance state,
  observed-frame authority, execution-based task validation, and rejection
  reasons.
- Loads the referenced SourceEvent, Task, Check, and certification-evidence
  files and compares their canonical digests and cross-record links with the
  frozen Task Pool. Missing, malformed, or mismatched artifacts make the bundle
  consistency claim unsupported. It does not re-certify tasks or infer
  population coverage.
- For a validated generated pool, enumerates the generation manifest and its
  optional observed-frame inventory and adapter sidecar in Artifact Paths.
  Invalid nested refs remain validation limitations rather than report links.
- Reports source dispositions, right-censored event count, label-delay
  distribution, and exact source-event ref/digest from evidence rather than
  inferring a source denominator from accepted Tasks.
- Reports certification yield with its candidate denominator, rejection counts
  by stage and exact reason, and pre-certification exclusions. For repeated
  certification, the flaky-quarantine diagnostic counts only rejected records
  with conflicting normalized outcomes on the same base or reference-patch
  side; it does not infer a cause for the conflict.

### build_result_report

Input:

- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`

Output:

- `ReportSection`

Effect:

- Summarizes pass/fail/invalid, cost, latency, scoreable rate, cache coverage,
  and pricing version.
- When current phase timings are present, reports count, total, and mean for
  solver checkout, verifier checkout, diff replay, and cleanup. It also reports
  checkout-plus-cleanup share against `workspace_seconds + cleanup_seconds`
  only for executions containing the complete denominator; older Results stay
  visible without fabricating missing phases.
- Counts a numeric total cost as measured. A `null` total remains separate from
  measured zero cost.
- Reports later benchmark-invalid execution rate and the fraction of observed
  Task/Check pairs affected. Pricing views are deduplicated by execution digest
  before these rates are computed; absent Result evidence produces null rates.
- Reports record and execution counts by evidence-source kind and availability
  policy, external source-manifest digests, and the number of
  producer-attested historical executions. It explicitly notes that such
  history is not a Barcarolle observation-time claim.
- Refuses result-summary claims when different executions share one cache
  identity. Repricing and evidence-source views of the same execution remain
  one execution.

### build_selector_report

Input:

- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`
- `origins: Sequence[RollingOriginRecord]`
- `feature_snapshots: Sequence[FeatureSnapshotRecord]`
- `selector_inputs: Sequence[SelectorInput]`
- `selectors: Sequence[SelectorRecord]`
- `agents: Sequence[AgentRecord]`
- `results: Sequence[ResultRecord]`

Output:

- `ReportSection`

Effect:

- Summarizes selector performance by origin, Agent set, budget, and metric using
  frozen selections, cell sets, matrices, and metrics.
- Rejects trace claims when a matrix cell changes the required identity,
  result ID, result digest, or outcome frozen in its `EvaluationCellSet`.
- Recomputes current aggregate metric values from the supplied selected and
  future matrices before supporting selector-performance claims.
- Requires every consumed Metric to bind the current implementation-owned
  metric protocol. Records remains version-neutral so an unknown protocol can
  be loaded and reported as unsupported rather than becoming a schema error.
- Only after the complete chain is valid, includes the predeclared paired MAE
  summary: macro-Origin and scoreable-future-count-weighted MAE, canonical
  pairwise differences, exact seed-bank variation, and Origin-block interval
  status. Invalid or incomplete provenance yields `mae_summary=null`; it is not
  summarized as zero.
- For each evaluated `stratified_forecast` Selector, loads the validated frozen
  TaskRecords, replays each snapshot's Task metadata provenance and the exact
  Selection, and publishes forecast/future mix, quota, TV-error, effective-
  sample-size, and cap diagnostics. The selector section binds the TaskRecords
  digest; a value/time/source mismatch, replay failure, or future-stratum
  coverage failure makes the performance summary unsupported.
- Requires exact Selector, Origin, FeatureSnapshot, SelectorInput, Agent,
  Result, cell-set, matrix, and metric links. Missing upstream evidence makes
  the summary unsupported rather than partially trusted.
- Requires unique semantic IDs for Selections, CellSets, Matrices, and Metrics
  before grouping or indexing them. Result summaries and Agent/Result identity
  claims likewise require unique Result and Agent IDs; duplicate records do not
  become extra observations or silently select one value.
- Uses Selection's Task metadata assertion to bind `task_count` to the Origin
  and Task Pool and every `task_stratum` to the exact Task value, known-at time,
  and canonical Task digest. Reporting accumulates the failure as an
  unsupported-claim reason rather than reconstructing a replacement snapshot.
- For strict-prospective rows, rejects duplicate later Task Pool identities,
  loads only referenced immutable bundles once per identity, and replays the
  mature and censored cohort refs against both validated bundles. Missing,
  unloadable, unreplayable, or drifted future evidence revokes the performance
  claim rather than producing a partial summary.
- Treats the separately supplied Agent records as an unordered evidence set.
  SelectorInput and ResultMatrix Agent order remains frozen and must still
  agree exactly. Reporting reconstructs full Agent-record digests in that
  order, so merely reordering supplied records cannot revoke a claim but
  same-ID configuration drift does.
- Uses the Records-owned Agent and Task/Check cache-identity projections when
  reconstructing Result links. It also uses Records' complete bound-cell
  predicate, so Matrix outcome evidence must match the referenced Result along
  with its ID/digest, Agent/Task/Check, and required identity. This matches
  Result Store, Selection training, and Runner scoring without duplicating
  their field lists.
- Uses Result Store's Matrix derived-state check before supporting identity or
  performance claims. Task-wide benchmark exclusions and one Matrix-wide
  agent-invalid branch must be reproducible from supplied Results; a normal
  Result cannot be removed by an invented exclusion reason, and cells cannot
  mix denominator treatment. Declared join/denominator digests, abstention, and
  scoreability must match that same replayed policy.
- Replays executable deterministic Selectors from the frozen SelectorInput and
  uses Selection's shared replay assertion to compare the resulting refs,
  weights, budget, feature snapshot, and selector binding with the recorded
  Benchmark Selection.
- Names supported summaries by eligibility mode, so
  `counterfactual_replay` evidence is not presented as prospective evidence.
- Treats a post-cutoff Result observation as a chronology violation only for
  strict-prospective evidence. In counterfactual replay, Reporting instead
  verifies mature history membership plus exact Task/Check/Agent/cache
  identity, matching Selection and Runner.

### build_claim_boundary

`ClaimConfig` contains only requested claims. They are one unique tuple drawn
from the supported claim names and are canonicalized to a stable display order.
Matrix completeness and Metric validity are fixed claim semantics, not
caller-configurable weakening axes. The config digest is derived from the
canonical requested claims, so callers cannot assign a claim label that
disagrees with the enforced boundary.

The display order is not a total evidence ladder. Task Pool bundle consistency,
source-frame authority, Generator/source-protocol continuity, Check
certification, Result availability, execution identity, rolling-origin replay,
and field outcomes are independent claim axes.

Input:

- `task_pool: TaskPoolRecord`
- `selections: Sequence[BenchmarkSelectionRecord]`
- `cell_sets: Sequence[EvaluationCellSet]`
- `result_matrices: Sequence[ResultMatrix]`
- `metrics: Sequence[MetricRecord]`
- `claim_config: ClaimConfig`
- `artifact_root: Path | None`
- `results: Sequence[ResultRecord]`
- `agents: Sequence[AgentRecord]`
- the same Selector provenance and future Task Pool records accepted by
  `build_selector_report`

Output:

- `ReportSection`

Effect:

- Separates supported claims from unsupported claims using Task Pool bundle
  consistency, rejection and task-validation evidence, cache completeness,
  abstentions, frozen Selection state, and Agent/Result identity drift.
- Evaluates only requested claim predicates while preserving the stable claim
  order.
- Supports `task_pool_bundle_internal_consistency` only when the referenced
  SourceEvent, Task, Check, and certification-evidence files are available,
  match their stored digests, pass cross-record validation, and completely
  cover accepted Task/Check and rejected candidate decisions with valid
  certification transitions. It makes no source-frame or population-coverage
  claim.
- Uses the same complete Task Pool artifact inventory as the Task Pool report,
  including manifest-bound observed-frame and adapter sidecar refs.
- Supports Selector metric claims only when the complete provenance chain also
  validates against the frozen Task Pool bundle and exact Agent/Result
  identities.
- Supports `agent_result_identity` only when every bound Result is valid,
  belongs to a supplied frozen Task/Check, and its cache identity projects to a
  supplied matching Agent. The section's source digests include the supplied
  Agent manifest digests.

### write_report

Input:

- `sections: Sequence[ReportSection]`
- `output_path: Path`
- `artifact_root: Path | None`

Output:

- `None`

Effect:

- Writes a report with source digests and artifact paths.
- Emits artifact paths under the report root or configured artifact root as
  relative refs.
- Replaces every absolute artifact path outside that root with a basename-only
  reference, so reports do not expose host directory layouts.
- Preserves caller-supplied relative artifact refs.
- Reports unknown cost separately from measured zero cost.

## Design Consistency Check

- Separates evidence from claims.
- Reports negative or weak evidence honestly.
- Keeps benchmark predictive validity distinct from tuning utility.
