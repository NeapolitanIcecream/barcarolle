# Module Design: Records

Status: current core records, 2026-07-23.

## Responsibility

Define shared record shapes and validation helpers for `Task`, `Check`,
`Workspace`, `Result`, `Selector`, feature, cache identity, and
`RollingOrigin` data.

This module should not perform I/O beyond optional serialization helpers.

All evidence timestamps must be timezone-aware ISO datetimes. Records provides
the single parse/format contract: parsing rejects non-strings and naive values
and normalizes offsets to UTC; formatting rejects naive `datetime` values and emits
microsecond-precision `Z` timestamps. Record validators, rolling-origin
construction, Result queries, Runner schedules, and Reporting comparisons use
that contract.

Public persisted-record validators first replay the same latest-schema
dataclass conversion used by JSONL loading. Only a reloadable shape enters
domain semantics; malformed scalars, containers, or nested records return a
`ValidationResult` instead of reaching field operations that assume their
declared types. Valid records run this conversion once, not again after domain
checks. A Task, Check, Agent, or other evidence record accepted in memory
therefore has the same field shape as its canonical serialized form.

Canonical JSON has one floating-zero representation. `canonical_data` maps
both `-0.0` and `0.0` to positive `0.0` recursively before serialization or
digesting. This applies equally to typed fields and nested JSON values such as
measurements, features, and Selector parameters; owners do not add local
signed-zero rules merely to stabilize identity.

Records also owns `make_check_command_digest`, the canonical identity of an
exact Check argv used by Workspace and Verification. This is distinct from the
semantic Check manifest digest.

## Records

- `TaskRecord`
- `CheckRecord`
- `ResultCellRef`
- `AgentRecord`
- `WorkspaceConfig`
- `RuntimeConfig`
- `WorkspaceRunRecord`
- `ResultCacheIdentity`
- `SelectorRecord`
- `FeatureRecord`
- `FeatureSnapshotRecord`
- `SelectorInput`
- `ResultRecord`
- `ResultMatrix`
- `EvaluationCellSet`
- `TaskPoolRecord`
- `BenchmarkSelectionRecord`
- `RollingOriginRecord`
- `MetricRecord`

## Required Fields

These are minimum boundary fields. Implementations may add derived fields, but
modules should not depend on fields that are not recorded here.

### TaskCheckRef

- `task_id`
- `check_id`

`TaskCheckRef` is a compact reference to an existing `TaskRecord` and
`CheckRecord`, not a separate stored record.

### ResultCellRef

- `agent_id`
- `task_id`
- `check_id`
- `required_identity_digest`
- `result_id`
- `result_digest`
- `cell_state`
- `exclusion_reason`
- `outcome`

`ResultCellRef` is a compact cell-level reference used by result matrices and
evaluation cell sets. A `result` cell binds both Result fields as nonempty
strings, carries a normalized outcome, and has a null exclusion reason. An
`excluded` cell has a nonempty string reason; if it binds a Result, both Result
fields are nonempty strings and a normalized outcome is present, otherwise all
three are null. A `missing` cell has no Result, exclusion, or outcome payload.
Empty strings and truthy non-string values are not alternate null/binding
representations.

Records also owns the direct cross-record predicate for a bound cell. Its
Result ID/digest, Agent/Task/Check IDs, required cache-identity digest, and
outcome must all match the referenced `ResultRecord`. Result Store, Runner,
Selection, and Reporting use this same field relation.

### SourceEventRecord

- `source_event_id`
- `repository_id`
- `source_family`
- `source_ref`
- `source_resolved_at`
- `task_material_available_at`
- `check_material_available_at`
- `label_mature_at`
- `candidate_id`
- `task_id`
- `check_id`
- `disposition`
- `rejection_stage`
- `rejection_reasons`
- `dependency_cluster_id`
- `sampling_stratum`
- `source_event_digest`

This is the sanitized source denominator for a Task Pool. `disposition` is
`accepted`, `certification_rejected`, or `excluded`. Optional material times
and Task/Check links remain null when an event never reached that stage;
`label_mature_at=null` is an explicit right-censored label. The self-digest
binds the whole record. Material timestamps fail validation rather than raising
during maturity derivation. Rejected and excluded events require non-empty
reason strings in one tuple. A scalar or mapping reason container fails
validation without being iterated as a reason sequence. Raw issue bodies,
patches, and private oracle material do not belong in this record.

### TaskRecord

- `task_id`
- `repository_id`
- `base_commit`
- `source_family`
- `source_ref`
- `source_resolved_at`
- `task_material_available_at`
- `task_text`
- `solver_material_digest`
- `solver_material_refs`
- `check_ids`
- `dependency_cluster_id`
- `sampling_stratum`

`task_text` is the directly replayable solver instruction.
`solver_material_refs` optionally names supporting files already present in the
repository checkout; it does not replace or contain `task_text`.
`solver_material_digest` binds the solver-material format version, exact task
text, and ordered refs. Agent-visible rendering changes must change that
format version so old Results are not exact cache hits.

Both classification fields may be empty. `dependency_cluster_id` is reserved
for dependence-aware origin blocking and is not a Selector feature.
`sampling_stratum` is a visible coverage/stratification label. Records do not
replace an absent value with a default or `unclustered` label.

Task `known_at` is derived only from `source_resolved_at` and
`task_material_available_at`. Task/Check `known_at` also includes
`check_material_available_at`. Certification time is not part of historical
availability and is not stored on Task or Check.

### CheckRecord

- `check_id`
- `task_id`
- `check_type`
- `check_manifest_digest`
- `hidden_check_bundle_digest`
- `resource_limits`
- `oracle_source`
- `check_material_available_at`

`check_manifest_digest` binds the behavior-changing check implementation and
configuration. Machine-local executable paths and diagnostic-output paths are
runtime bindings, not Check identity. A simple adapter may use the exact
command as its manifest; an adapter with relocatable local paths should use a
structured manifest and bind the actual command separately.

`resource_limits` may be empty. `RuntimeConfig.timeout_seconds` is the default
Check timeout; a positive per-Check `resource_limits["timeout_seconds"]` only
narrows that default. Other entries have effect only when the active execution
adapter implements them.

### AgentRecord

- `agent_id`
- `agent_manifest_digest`
- `requested_model_id`
- `model_snapshot_id`
- `model_resolution_scope_id`
- `model_resolution_scope_started_at`
- `model_resolution_scope_ended_at`
- `harness_digest`
- `repository_instruction_digest`
- `prompt_digest`
- `tools_digest`
- `retrieval_digest`
- `skills_digest`
- `network_policy_digest`
- `adapter_digest`

The Workspace binder always checks `harness_digest` against the bound command
argv. Offline runs require `agent_manifest_digest` to bind the executable or
script contents, behavior-changing configuration, and other harness inputs.
Paid runs additionally hash the declared endpoint-enforcing harness paths and
bind those content digests into `network_policy_digest`. Changing any bound
input requires a new Agent identity before Result reuse.

`requested_model_id` is the exact name sent to the Agent harness.
`model_snapshot_id` is non-null only when the adapter can prove that the name
resolved to an immutable model snapshot. Otherwise the snapshot is null and
all three resolution-scope fields are required. The scope identifies one
declared campaign and a positive, timezone-aware execution window. A resolved
snapshot and a campaign scope are mutually exclusive.

### WorkspaceConfig

- `workspace_config_id`
- `repository_checkout_config_digest`
- `submodule_state_digest`
- `base_image_digest`
- `dependency_lock_digest`

Every field is a required nonempty string. `validate_workspace_config` applies
the shared latest-schema type contract before a Workspace identity is consumed.

### RuntimeConfig

- `runtime_config_id`
- `budget_digest`
- `retry_policy_digest`
- `stochastic_settings_digest`
- `timeout_seconds`
- `hardware_profile_digest`

`hardware_profile_digest` may be `null` when hardware is irrelevant to the
run; when present it must be nonempty. `timeout_seconds` is a positive integer.
`validate_runtime_config` applies those semantics after the shared
latest-schema type contract. If hardware can change scoreability or latency
claims, its digest must be present.

### ResultCacheIdentity

- `task_id`
- `check_id`
- `repository_id`
- `base_commit`
- `submodule_state_digest`
- `solver_material_digest`
- `check_digest`
- `agent_manifest_digest`
- `requested_model_id`
- `model_snapshot_id`
- `model_resolution_scope_id`
- `model_resolution_scope_started_at`
- `model_resolution_scope_ended_at`
- `harness_digest`
- `repository_instruction_digest`
- `prompt_digest`
- `tools_digest`
- `retrieval_digest`
- `skills_digest`
- `network_policy_digest`
- `budget_digest`
- `retry_policy_digest`
- `stochastic_settings_digest`
- `adapter_digest`
- `workspace_config_digest`
- `runtime_config_digest`
- `hardware_profile_digest`
- `identity_digest`

The structured fields and `identity_digest` are both stored. Cached results
missing any required identity field are isolated from reuse and may only appear
in audit reports.
An unresolved model alias is reusable only under the exact same campaign scope;
changing the scope changes `identity_digest`.

Records also owns the direct cross-record field projections used to reconstruct
evidence:

- `agent_record_from_cache_identity` projects exactly the AgentRecord fields
  frozen inside a Result cache identity;
- `cache_identity_agent_mismatches` reports the Agent fields that disagree;
- `cache_identity_task_check_mismatches` reports Task ID, Check ID, repository,
  base commit, solver material, or Check digest drift.

Result Store construction, Selection replay, Runner preflight, and Reporting
use these functions rather than maintaining separate field lists. They compare
records only; they do not load artifacts or create an identity registry.

`check_digest` is derived from the behavior-changing Check fields:
`check_type`, `check_manifest_digest`, `hidden_check_bundle_digest`,
`resource_limits`, and `oracle_source`. Check-material availability is
excluded. Verifier environment identity comes from `WorkspaceConfig` rather
than duplicate Check fields.

Pricing and scoring do not belong to paid execution identity. Changing prices
must not cause an Agent or Check to run again.

### WorkspaceRunRecord

- `workspace_run_id`
- `task_id`
- `check_id`
- `agent_id`
- `solver_workspace_digest`
- `verifier_workspace_digest`
- `terminal_status`
- `diff_digest`
- `replay_status`
- `check_outcome`
- `invalid_owner`
- `failure_label`
- `usage`
- `latency`
- `started_at`
- `finished_at`

Raw workspaces and transcripts are not stored in this record. New Workspace
runs require monotonic `workspace_seconds`, `solver_checkout_seconds`,
`verifier_checkout_seconds`, `diff_replay_seconds`, `agent_seconds`,
`verification_seconds`, and `cleanup_seconds` in `latency`. Cleanup occurs
after run-record construction and is therefore separate from
`workspace_seconds`.

### ResultRecord

- `result_id`
- `result_digest`
- `cache_identity: ResultCacheIdentity`
- `agent_id`
- `task_id`
- `check_id`
- `terminal_status`
- `scoreable_state`
- `outcome`
- `invalid_owner`
- `failure_label`
- `cost`
- `scoring_config_digest`
- `pricing_version`
- `usage`
- `latency`
- `diff_digest`
- `verifier_metadata_digest`
- `started_at`
- `finished_at`
- `result_available_at`

`invalid_owner` distinguishes Agent-attributable invalid outcomes from
benchmark infrastructure failures.
`cost.total_cost=null` means the total cost is unknown; it must not be replaced
with zero. Usage is retained so cost can be recomputed under another pricing
configuration without rerunning the Agent.

### FeatureRecord

- `feature_id`
- `feature_scope`
- `task_id`
- `check_id`
- `agent_id`
- `result_id`
- `result_cache_identity_digest`
- `feature_name`
- `value`
- `aggregation_window`
- `aggregation_method`
- `observed_at`
- `source_artifact_digest`
- `origin_snapshot_digest`
- `leakage_class`

Task, Check, Agent, Result, and cache-identity links are nullable. When a
FeatureRecord names a Result, every supplied Task, Check, Agent, and
cache-identity field must match that exact Result; `source_artifact_digest`
binds its Result digest. Origin-level pre-origin aggregates instead bind the
digest of the complete visible Result view.

### FeatureSnapshotRecord

- `feature_snapshot_id`
- `origin_id`
- `feature_record_ids`
- `feature_records_digest`
- `leakage_policy_digest`
- `leakage_lint_status`
- `feature_records`
- `result_view_digest`
- `feature_config_digest`
- `feature_snapshot_digest`

Records defines the schema. Selection builds snapshots and runs leakage
linting.

### SelectorRecord

- `selector_id`
- `selector_family`
- `selector_version`
- `training_source_digests`
- `allowed_feature_classes`
- `parameters`
- `config_digest`
- `created_at`
- `selector_digest`

### SelectorInput

- `selector_input_id`
- `origin_id`
- `task_pool_id`
- `feature_snapshot_id`
- `agent_ids`
- `agent_record_digests`
- `eligible_task_check_refs`
- `pre_origin_result_ids`
- `pre_origin_result_digests`
- `budget_digest`
- `leakage_policy_digest`
- `selector_input_digest`
- `task_pool_digest`
- `selection_budget_limit`
- `feature_records_digest`
- `feature_snapshot_lint_status`
- `origin_as_of_cutoff`
- `origin_history_refs_digest`
- `eligibility_mode`

`SelectorInput` is the leakage-checked data visible to a Selector for one
origin. Its identity and self-digest cover the full Task Pool, origin, feature,
Agent, chronological history, pre-origin Result, budget, and eligibility
bindings. The Agent-record digests align with `agent_ids` and freeze the full
Agent configurations in that order; an ID cannot silently change harness,
model, prompt, tool, or runtime-binding evidence between Selection and
evaluation. Validation also requires unique Agent IDs and eligible refs,
aligned pre-origin Result IDs/digests, a canonical UTC cutoff, and a
`budget_digest` derived from the positive `selection_budget_limit`.

### TaskPoolRecord

- `task_pool_id`
- `task_pool_digest`
- `repository_id`
- `task_ids`
- `check_ids`
- `task_records_ref`
- `task_records_digest`
- `check_records_ref`
- `check_records_digest`
- `certification_evidence_ref`
- `source_event_records_ref`
- `source_event_records_digest`
- `rejected_candidate_ids`
- `rejection_summary_digest`
- `certification_evidence_digest`
- `generator_config_digest`
- `certification_config_digest`
- `created_at`
- `source_window_start`
- `source_window_end`

`task_pool_digest` is computed from the canonical serialization of the frozen
task pool, including accepted Task/Check refs and digests, rejected candidate
IDs, rejection summary digest, certification evidence ref and digest, source
event records ref and digest, and generator/certification config digests.
Its direct validator applies the same latest-schema replay as other persisted
records before Task Pool performs cross-artifact reconciliation.
Generated pools persist a canonical source window. Its end cannot be after
`created_at`; accepted or certification-rejected events cannot fall outside it,
and an outside event must retain the normalized exclusion reason. Imported
pools may leave both window fields null, but they cannot support prospective
future-cohort claims until a source window is supplied by a later concrete
adapter.

`certification_evidence_ref` points to the exact ordered sanitized evidence
sequence whose canonical digest is `certification_evidence_digest`. The ref and
digest are one binding: a different sequence must produce a different digest.
Each evidence item includes Workspace and Runtime config digests, the exact
Check execution binding digest, and the built-in Verification adapter digest.
`source_event_records_ref` points to the exact sanitized source denominator.
Its digest covers accepted, certification-rejected, and pre-certification
excluded events, including right-censored label maturity.
`generator_config_digest` identifies generation behavior, such as generated
source events versus import mode and source family. Event inventory and local
import location are not duplicated into that digest; the frozen SourceEvent,
Task, and Check digests bind the actual data.

### RollingOriginRecord

- `origin_id`
- `task_pool_id`
- `task_pool_digest`
- `origin_time`
- `policy_digest`
- `history_task_check_refs`
- `history_censored_task_check_refs`
- `future_holdout_task_check_refs`
- `future_censored_task_check_refs`
- `as_of_cutoff`
- `eligibility_mode`
- `holdout_overlap_policy`
- `as_of_cutoff_rule`
- `history_window_start`
- `future_window_start`
- `future_window_end`
- `future_cohort_time_basis`
- `maturity_lag_seconds`
- `label_maturity_cutoff`
- `future_holdout_known`
- `allowed_dependency_cluster_ids`
- `origin_digest`

The policy digest is derived from the behavior fields. Strict prospective
origins cannot claim known future refs; counterfactual replay may persist the
predeclared holdout refs. `as_of_cutoff` must equal `origin_time` when the rule
is `origin_time`, or the explicit timestamp named by the rule. The future window
must start at or after that cutoff. Cohort membership uses
`task_material_available_at`; Check material determines label maturity.
Arrived refs whose labels are not mature by the relevant cutoff are retained in
the censored tuples and do not enter Selector training or future execution.
Future outcomes must not be available to Selection before a
`BenchmarkSelectionRecord` is frozen. Dependency-cluster constraints affect
origin membership but never authorize the Selector to observe cluster IDs.
`future_holdout_known` is an exact boolean, and
`allowed_dependency_cluster_ids` is a tuple containing only nonempty strings;
these types are part of valid persisted Origin evidence rather than truthiness
conventions.

### BenchmarkSelectionRecord

- `selection_id`
- `task_pool_id`
- `task_pool_digest`
- `origin_id`
- `selector_id`
- `selector_digest`
- `selected_task_check_refs`
- `selected_weights`
- `budget_digest`
- `selection_input_digest`
- `feature_snapshot_id`
- `eligibility_mode`
- `created_at`
- `selection_digest`

This record is the frozen benchmark selection. It must be written before future
holdout outcomes are opened for scoring. It has no publication state machine;
external publication metadata should be added only with an actual publisher.

Selection records are append-only evidence. Corrections, rescoring-policy
changes, or selector-input changes create a new `selection_id` and
`selection_digest`; existing frozen selection records are not mutated.

`selected_weights` is a keyed mapping from `TaskCheckRef` to finite positive
built-in float weights. Validators reject integer or boolean representations,
weights for unselected refs, and missing weights for selected refs. This exact
runtime shape matches latest-schema canonical reload.

### ResultMatrix

- `matrix_id`
- `matrix_role`
- `origin_id`
- `selection_id`
- `agent_ids`
- `task_check_refs`
- `cells: Sequence[ResultCellRef]`
- `join_policy_digest`
- `denominator_policy_digest`
- `abstention_reason`
- `scoreable_state`
- `matrix_digest`

`scoreable_state` is derived from the cells unless `abstention_reason` is set:
no missing/excluded cells is `complete`, any missing cell is `incomplete`, any
excluded cell without a missing cell is `complete_with_exclusions`, and an
abstention reason requires `abstained`.

### EvaluationCellSet

- `cell_set_id`
- `origin_id`
- `selection_id`
- `selected_task_check_refs`
- `future_task_check_refs`
- `future_censored_task_check_refs`
- `future_task_pool_id`
- `future_task_pool_digest`
- `cells: Sequence[ResultCellRef]`
- `abstention_reason`
- `cell_set_digest`

The CellSet is the post-selection evaluation artifact. Counterfactual replay
binds the same Task Pool as the Origin. Strict-prospective evaluation binds a
later immutable Task Pool, retains its mature and censored future refs, and
creates cells only for selected and mature future refs.

### MetricRecord

- `metric_id`
- `origin_id`
- `selection_id`
- `evaluation_cell_set_digest`
- `selected_matrix_digest`
- `future_matrix_digest`
- `join_policy_digest`
- `metric_config_digest`
- `metric_scope`
- `agent_id`
- `agent_pair`
- `aggregation_level`
- `budget_digest`
- `stratum_ref`
- `metric_name`
- `metric_value`
- `denominator_policy_digest`
- `completeness_state`
- `abstention_reason`
- `computed_at`
- `metric_digest`

Metric records are append-only evidence. Corrections, metric-config changes, or
matrix/cell-set changes create a new `metric_id` and `metric_digest`; existing
metric records are not mutated.

Metric dimension rules:

- per-Agent metrics must set `metric_scope=agent` and one nonempty string
  `agent_id`; the pair and aggregate dimensions are null;
- pairwise metrics must set `metric_scope=pair` and a two-element tuple of
  nonempty string Agent IDs; the single-Agent and aggregate dimensions are
  null;
- aggregate metrics must set `metric_scope=aggregate` and
  a nonempty string `aggregation_level`, while `agent_id` and `agent_pair` are
  null;
- budget-sensitivity metrics must set a nonempty string `budget_digest`;
- stratum metrics must set a nonempty string `stratum_ref`;
- complete states have a null abstention reason; incomplete, abstained, and
  invalid states have a nonempty string reason.

Unused optional dimensions and refs use null, not empty strings. Direct
validation and latest-schema JSONL reload therefore accept the same runtime
shape.

`metric_value` is a finite built-in float. Integer and boolean representations
are invalid even when numerically equivalent because latest-schema loading
normalizes declared float fields before checking canonical JSON.

## Serialization Rules

Canonical JSON and every digest derived from it use strict JSON numbers.
`NaN`, positive infinity, and negative infinity are invalid and must be rejected
instead of being serialized as implementation-specific tokens.
Mapping keys must be strings at every nesting level. Canonical serialization
rejects non-string keys instead of coercing them and risking key collisions.

The core JSONL reader accepts only the latest schema. Each record must use the
canonical JSON representation, contain exactly the declared dataclass fields,
and match recursive scalar, collection, optional, mapping, and nested-record
types. Blank records, unknown or missing fields, and type mismatches fail with
the input line number. Compatibility interpretation belongs only in bounded
one-off migration tools.

Final-line durability is an owning-module rule rather than a generic record
rule. Result Store requires a newline-terminated append log and exposes its own
explicit conservative tail recovery; immutable bundle readers may read a
canonical final record without adding Result Store recovery semantics.

## System Boundary

Input sources:

- Design docs;
- records produced by Task Pool, Verification, Workspace, Result Store, and
  Selection.

Output consumers:

- all modules.

## Function Boundary

Functions below define module interfaces. Each function specifies input,
output, and effect only; it does not prescribe implementation.

## Functions

### validate_task

Input:

- `task: TaskRecord`

Output:

- `ValidationResult`

Effect:

- Validates required task fields, source/material timestamp order, nonempty
  normalized task text, solver-material digest, and repository-relative solver
  material refs.

### validate_check

Input:

- `check: CheckRecord`

Output:

- `ValidationResult`

Effect:

- Validates that the Check has an execution type, a mapping for optional
  per-Check resource overrides, and no solver-visible hidden material.

### validate_agent

Input:

- `agent: AgentRecord`

Output:

- `ValidationResult`

Effect:

- Requires a requested model plus either one resolved immutable snapshot or a
  complete positive-duration campaign scope, never both.
- Validates the remaining required Agent identity fields without attempting a
  provider-specific model lookup.

### validate_workspace_config

Input:

- `config: WorkspaceConfig`

Output:

- `ValidationResult`

Effect:

- Requires the declared Workspace identity fields to be nonempty strings with
  their exact latest-schema types.

### validate_runtime_config

Input:

- `config: RuntimeConfig`

Output:

- `ValidationResult`

Effect:

- Requires nonempty runtime identity strings, a positive integer timeout, and
  a null or nonempty hardware-profile digest with exact latest-schema types.

### validate_workspace_run

Input:

- `run: WorkspaceRunRecord`

Output:

- `ValidationResult`

Effect:

- Validates normalized terminal, replay, and Check outcome values, their state
  transitions, usage and monotonic latency shape, failure attribution, and
  timestamp order without reading raw workspaces.
- `passed` requires applied replay plus a passing Check; `failed` requires
  applied replay plus a failing Check. A non-applied replay cannot carry a pass
  or fail Check outcome.

### validate_result

Input:

- `result: ResultRecord`

Output:

- `ValidationResult`

Effect:

- Validates cache identity fields, status fields, cost/latency/usage fields,
  pricing version, result availability timestamp, failure labels, and
  `result_digest` against the canonical result record.
- Accepts only normalized terminal states, scoreability states, and outcomes.
  Scoreable pass/fail results and Agent- or benchmark-invalid results must have
  consistent terminal status, outcome, and `invalid_owner` attribution.
- Requires `latency.workspace_seconds` and every known cost/latency/usage value
  to be numeric, finite, and nonnegative. `cost.total_cost` may be `null` only
  to represent an unknown total. An empty usage mapping is valid and leaves
  total cost unknown. Newly built Results copy all current Workspace phase
  timings; older preserved Results may contain only their total Workspace
  measurement.

### validate_result_cache_identity

Input:

- `identity: ResultCacheIdentity`

Output:

- `ValidationResult`

Effect:

- Validates that all required cache identity fields are present and that
  `identity_digest` matches the structured identity.
- Applies the same resolved-snapshot-or-campaign-scope model contract as
  `validate_agent`.

### validate_feature_snapshot

Input:

- `snapshot: FeatureSnapshotRecord`

Output:

- `ValidationResult`

Effect:

- Validates feature provenance fields, leakage lint status, and origin linkage.

### validate_selector_input

Input:

- `selector_input: SelectorInput`

Output:

- `ValidationResult`

Effect:

- Validates origin linkage, task-pool binding, feature snapshot digest,
  ordered Agent IDs and aligned full Agent-record digests, eligible
  `Task + Check` refs, pre-origin result IDs and digests, budget digest,
  leakage policy digest, and selector input digest.

### validate_result_matrix

Input:

- `matrix: ResultMatrix`

Output:

- `ValidationResult`

Effect:

- Validates cell-level Agent/Task/Check mapping, completeness, exclusions,
  result IDs and digests, matrix role, join policy, denominator policy,
  abstention metadata, and matrix digest.
- Rejects duplicate Agent IDs and duplicate Task/Check denominator refs.

### validate_evaluation_cell_set

Input:

- `cells: EvaluationCellSet`

Output:

- `ValidationResult`

Effect:

- Validates selected and future `Task + Check` refs, cell-level required cache
  identities, non-missing result ID and digest bindings, missing cells,
  exclusions, abstention metadata, and `cell_set_digest`.
- Rejects duplicate refs within the selected and future sequences. It does not
  infer an overlap policy between those sequences because the cell-set record
  does not carry `holdout_overlap_policy`.

### validate_selector

Input:

- `selector: SelectorRecord`

Output:

- `ValidationResult`

Effect:

- Validates selector identity, version, training source digests, allowed feature
  fields, and strict-JSON parameters. `config_digest` must equal the canonical
  digest of `selector_family` and `parameters`.

### validate_benchmark_selection

Input:

- `selection: BenchmarkSelectionRecord`

Output:

- `ValidationResult`

Effect:

- Performs local record validation: required fields, normalized exposure state,
  finite positive built-in float weights that exactly cover selected refs, timestamp
  order, and `selection_digest`.
- Rejects duplicate selected Task/Check refs before denominator weights are
  interpreted.
- Cross-record task-pool, origin, selector-input, and eligibility linkage is
  validated by Selection, Runner, and Reporting where those records are
  available together.

### validate_metric

Input:

- `metric: MetricRecord`

Output:

- `ValidationResult`

Effect:

- Performs local record validation: required provenance fields, finite built-in float
  value, normalized completeness/abstention state, timestamp shape, metric
  dimension rules, and `metric_digest`.
- Cross-record matrix, cell-set, Agent-set, and selection linkage is validated
  by Selection and Reporting where those records are available together.

### make_task_id

Input:

- `repository_id: str`
- `base_commit: str`
- `source_digest: str`

Output:

- `task_id: str`

Effect:

- Builds a stable task identifier. The function must not include future
  outcome data.

### make_solver_material_digest

Input:

- `task_text: str`
- `solver_material_refs: Sequence[str]`

Output:

- `solver_material_digest: str`

Effect:

- Digests the exact solver-visible task text and ordered supporting-file refs.
  The referenced files remain part of the repository checkout at
  `base_commit`; Workspace validates that each resolved path stays inside that
  checkout.

### make_check_id

Input:

- `task_id: str`
- `check_digest: str`

Output:

- `check_id: str`

Effect:

- Builds a stable check identifier.

### make_check_digest

Input:

- `check: CheckRecord`

Output:

- `check_digest: str`

Effect:

- Digests every Check field that can change execution or verification while
  excluding check-material availability. Workspace environment identity is
  already carried by `WorkspaceConfig`.

### make_result_cache_identity

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`

Output:

- `identity: ResultCacheIdentity`

Effect:

- Builds the structured identity for one reusable Agent-task result, including
  repository, task, Check, Agent, workspace, runtime, adapter, and optional
  hardware fields. It excludes post-execution pricing and scoring.

### make_result_cache_key

Input:

- `identity: ResultCacheIdentity`

Output:

- `cache_key: str`

Effect:

- Returns the digest key for a reusable Agent-task result. The key must not be
  computed from an incomplete identity.

### make_selector_id

Input:

- `selector: SelectorRecord`

Output:

- `selector_id: str`

Effect:

- Builds the stable semantic identifier used by Selector constructors from the
  family, version, training-source digests, allowed feature classes, and config
  digest. Observation time and the record self-digest do not enter the ID.

### load_jsonl_records

Input:

- `path: Path`
- `record_type: type`

Output:

- `list[record_type]`

Effect:

- Reads exact latest-schema records from canonical JSONL.
- Rejects blank records, noncanonical representations, unknown or missing
  dataclass fields, recursive type mismatches, and non-finite numbers with a
  line-numbered error.
- Does not implement schema migration or module-specific durable-tail recovery.

### write_jsonl_records

Input:

- `path: Path`
- `records: Sequence[object]`

Output:

- `None`

Effect:

- Writes normalized records atomically.

## Design Consistency Check

- Provides direct data contracts.
- Keeps the core vocabulary small.
- Enforces cache identity for Result reuse.
