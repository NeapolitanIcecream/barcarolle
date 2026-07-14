# Module Design: Records

Status: draft, 2026-07-14.

## Responsibility

Define shared record shapes and validation helpers for `Task`, `Check`,
`Workspace`, `Result`, `Selector`, feature, cache identity, and
`RollingOrigin` data.

This module should not perform I/O beyond optional serialization helpers.

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

`ResultCellRef` is a compact cell-level reference used by result matrices and
evaluation cell sets. `result_id`, `result_digest`, and `exclusion_reason` may
be null depending on `cell_state`.

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
- `cluster_id`

`task_text` is the directly replayable solver instruction.
`solver_material_refs` optionally names supporting files already present in the
repository checkout; it does not replace or contain `task_text`.
`solver_material_digest` binds the solver-material format version, exact task
text, and ordered refs. Agent-visible rendering changes must change that
format version so old Results are not exact cache hits.

`cluster_id` may be empty. Records do not replace an absent cluster with a
default or `unclustered` label.

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

`resource_limits` may be empty. `RuntimeConfig.timeout_seconds` is the default
Check timeout; a positive per-Check `resource_limits["timeout_seconds"]` only
narrows that default. Other entries have effect only when the active execution
adapter implements them.

### AgentRecord

- `agent_id`
- `agent_manifest_digest`
- `model_snapshot_id`
- `harness_digest`
- `repository_instruction_digest`
- `prompt_digest`
- `tools_digest`
- `retrieval_digest`
- `skills_digest`
- `network_policy_digest`
- `adapter_digest`

The current Workspace binder checks `harness_digest` against the bound command
argv. It does not hash files named by that argv. For scoreable runs,
`agent_manifest_digest` must therefore bind the executable or script contents,
their behavior-changing configuration, and other harness inputs. Changing any
of them requires a new Agent identity before Result reuse.

### WorkspaceConfig

- `workspace_config_id`
- `repository_checkout_config_digest`
- `submodule_state_digest`
- `base_image_digest`
- `dependency_lock_digest`

### RuntimeConfig

- `runtime_config_id`
- `budget_digest`
- `retry_policy_digest`
- `stochastic_settings_digest`
- `timeout_seconds`
- `hardware_profile_digest`

`hardware_profile_digest` may be `null` when hardware is irrelevant to the
run. If hardware can change scoreability or latency claims, it must be present.

### ResultCacheIdentity

- `task_id`
- `check_id`
- `repository_id`
- `base_commit`
- `submodule_state_digest`
- `solver_material_digest`
- `check_digest`
- `agent_manifest_digest`
- `model_snapshot_id`
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
- `started_at`
- `finished_at`

Raw workspaces and transcripts are not stored in this record.

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

### FeatureSnapshotRecord

- `feature_snapshot_id`
- `origin_id`
- `feature_record_ids`
- `feature_records_digest`
- `leakage_policy_digest`
- `leakage_lint_status`

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

### SelectorInput

- `selector_input_id`
- `origin_id`
- `task_pool_id`
- `feature_snapshot_id`
- `agent_ids`
- `eligible_task_check_refs`
- `pre_origin_result_ids`
- `pre_origin_result_digests`
- `budget_digest`
- `leakage_policy_digest`
- `selector_input_digest`

`SelectorInput` is the leakage-checked data visible to a Selector for one
origin. Its digest covers the listed fields and the referenced feature snapshot.

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
- `rejected_candidate_ids`
- `rejection_summary_digest`
- `certification_evidence_digest`
- `source_event_inventory_digest`
- `generator_config_digest`
- `certification_config_digest`
- `created_at`

`task_pool_digest` is computed from the canonical serialization of the frozen
task pool, including accepted Task/Check refs and digests, rejected candidate
IDs, rejection summary digest, certification evidence ref and digest, source
event inventory digest, and generator/certification config digests.

`certification_evidence_ref` points to the exact ordered sanitized evidence
sequence whose canonical digest is `certification_evidence_digest`. The ref and
digest are one binding: a different sequence must produce a different digest.

### RollingOriginRecord

- `origin_id`
- `task_pool_id`
- `task_pool_digest`
- `origin_time`
- `policy_digest`
- `history_task_check_refs`
- `future_holdout_task_check_refs`
- `as_of_cutoff`
- `cluster_constraints_digest`
- `eligibility_mode`
- `holdout_overlap_policy`

Future holdout `Task + Check` refs may be recorded before scoring, but future
outcomes must not be available to Selection before a `BenchmarkSelectionRecord`
is frozen.

### BenchmarkSelectionRecord

- `selection_id`
- `task_pool_id`
- `task_pool_digest`
- `origin_id`
- `selector_id`
- `selected_task_check_refs`
- `selected_weights`
- `budget_digest`
- `selection_input_digest`
- `feature_snapshot_id`
- `eligibility_mode`
- `exposure_state`
- `exposed_at`
- `exposure_scope_digest`
- `created_at`
- `selection_digest`

This record is the frozen benchmark selection. It must be written before future
holdout outcomes are opened for scoring.

Selection records are append-only evidence. Corrections, rescoring-policy
changes, or selector-input changes create a new `selection_id` and
`selection_digest`; existing frozen selection records are not mutated.

`selected_weights` is a keyed mapping from `TaskCheckRef` to numeric weight.
Validators must reject weights for unselected refs and missing weights for
selected refs.

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

### EvaluationCellSet

- `cell_set_id`
- `origin_id`
- `selection_id`
- `selected_task_check_refs`
- `future_task_check_refs`
- `cells: Sequence[ResultCellRef]`
- `abstention_reason`
- `cell_set_digest`

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

- per-Agent metrics must set `metric_scope=agent` and `agent_id`;
- pairwise metrics must set `metric_scope=pair` and `agent_pair`;
- aggregate metrics must set `metric_scope=aggregate` and
  `aggregation_level`, and must not set `agent_id` or `agent_pair`;
- budget-sensitivity metrics must set `budget_digest`;
- stratum metrics must set `stratum_ref`.

## Serialization Rules

Canonical JSON and every digest derived from it use strict JSON numbers.
`NaN`, positive infinity, and negative infinity are invalid and must be rejected
instead of being serialized as implementation-specific tokens.
Mapping keys must be strings at every nesting level. Canonical serialization
rejects non-string keys instead of coercing them and risking key collisions.

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

### validate_workspace_run

Input:

- `run: WorkspaceRunRecord`

Output:

- `ValidationResult`

Effect:

- Validates normalized terminal, replay, and Check outcome values, their state
  transitions, usage shape, failure attribution, and timestamp order without
  reading raw workspaces.
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
  total cost unknown.

### validate_result_cache_identity

Input:

- `identity: ResultCacheIdentity`

Output:

- `ValidationResult`

Effect:

- Validates that all required cache identity fields are present and that
  `identity_digest` matches the structured identity.

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
  eligible `Task + Check` refs, pre-origin result IDs and digests, budget
  digest, leakage policy digest, and selector input digest.

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
  finite positive keyed weights that exactly cover selected refs, timestamp
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

- Performs local record validation: required provenance fields, finite numeric
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

- `selector_digest: str`

Output:

- `selector_id: str`

Effect:

- Builds a stable identifier for a persistent Selector.

### load_jsonl_records

Input:

- `path: Path`
- `record_type: type`

Output:

- `list[record_type]`

Effect:

- Reads normalized records. It should not infer module-specific behavior from
  unrelated file formats.

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
