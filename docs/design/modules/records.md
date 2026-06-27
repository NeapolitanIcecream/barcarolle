# Module Design: Records

Status: draft, 2026-06-27.

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
- `certified_at`
- `solver_material_digest`
- `solver_material_refs`
- `check_ids`
- `cluster_id`

`known_at` is a derived value computed from source, material, check, and
certification timestamps. It should not replace those source timestamps.

### CheckRecord

- `check_id`
- `task_id`
- `check_type`
- `check_manifest_digest`
- `hidden_check_bundle_digest`
- `verifier_image_digest`
- `verifier_deps_digest`
- `resource_limits`
- `oracle_source`
- `check_material_available_at`
- `certified_at`

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
- `check_manifest_digest`
- `hidden_check_bundle_digest`
- `verifier_image_digest`
- `verifier_deps_digest`
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
- `scoring_config_digest`
- `identity_digest`

The structured fields and `identity_digest` are both stored. Cached results
missing any required identity field are isolated from reuse and may only appear
in audit reports.

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
- `pricing_version`
- `usage`
- `usage_coverage`
- `latency`
- `diff_digest`
- `verifier_metadata_digest`
- `started_at`
- `finished_at`
- `result_available_at`

`invalid_owner` distinguishes Agent-attributable invalid outcomes from
benchmark infrastructure failures.

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
- `rejected_candidate_ids`
- `rejection_summary_digest`
- `certification_evidence_digest`
- `source_event_inventory_digest`
- `generator_config_digest`
- `certification_config_digest`
- `created_at`

`task_pool_digest` is computed from the canonical serialization of the frozen
task pool, including accepted Task/Check refs and digests, rejected candidate
IDs, rejection summary digest, certification evidence digest, source event
inventory digest, and generator/certification config digests.

### RollingOriginRecord

- `origin_id`
- `task_pool_id`
- `task_pool_digest`
- `origin_time`
- `policy_digest`
- `history_task_check_refs`
- `future_holdout_task_check_refs`
- `as_of_cutoff`
- `embargo`
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

This record is the frozen benchmark selection. It must be written before future
holdout outcomes are opened for scoring.

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

Metric dimension rules:

- per-Agent metrics must set `metric_scope=agent` and `agent_id`;
- pairwise metrics must set `metric_scope=pair` and `agent_pair`;
- aggregate metrics must set `metric_scope=aggregate` and
  `aggregation_level`, and must not set `agent_id` or `agent_pair`;
- budget-sensitivity metrics must set `budget_digest`;
- stratum metrics must set `stratum_ref`.

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

- Validates required task fields, timestamp order, solver-visible material, and
  absence of hidden check material.

### validate_check

Input:

- `check: CheckRecord`

Output:

- `ValidationResult`

Effect:

- Validates that the check has an execution type, bounded resource limits, and no
  solver-visible hidden material.

### validate_workspace_run

Input:

- `run: WorkspaceRunRecord`

Output:

- `ValidationResult`

Effect:

- Validates task, check, and Agent linkage, diff digest, replay status, usage
  fields, and failure attribution without reading raw workspaces.

### validate_result

Input:

- `result: ResultRecord`

Output:

- `ValidationResult`

Effect:

- Validates cache identity fields, status fields, cost/latency fields, usage
  coverage, pricing version, result availability timestamp, and failure labels.

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

### validate_evaluation_cell_set

Input:

- `cells: EvaluationCellSet`

Output:

- `ValidationResult`

Effect:

- Validates selected and future `Task + Check` refs, cell-level required cache
  identities, missing cells, exclusions, and abstention metadata.

### validate_selector

Input:

- `selector: SelectorRecord`

Output:

- `ValidationResult`

Effect:

- Validates selector identity, version, training source digests, allowed feature
  fields, and leakage boundary metadata.

### validate_benchmark_selection

Input:

- `selection: BenchmarkSelectionRecord`

Output:

- `ValidationResult`

Effect:

- Validates frozen origin linkage, selected `Task + Check` refs, keyed weight
  coverage, task-pool binding, budget digest, feature snapshot linkage, and
  exposure metadata.

### validate_metric

Input:

- `metric: MetricRecord`

Output:

- `ValidationResult`

Effect:

- Validates metric provenance digests, denominator policy, completeness state,
  and metric dimension rules.

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

### make_check_id

Input:

- `task_id: str`
- `check_digest: str`

Output:

- `check_id: str`

Effect:

- Builds a stable check identifier.

### make_result_cache_identity

Input:

- `task: TaskRecord`
- `check: CheckRecord`
- `agent: AgentRecord`
- `workspace_config: WorkspaceConfig`
- `runtime_config: RuntimeConfig`
- `scoring_config_digest: str`

Output:

- `identity: ResultCacheIdentity`

Effect:

- Builds the structured identity for one reusable Agent-task result, including
  repository, task, check, Agent, workspace, runtime, scoring, adapter, and
  optional hardware fields.

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

- Reads normalized records. It should not interpret archived experiment
  formats.

### write_jsonl_records

Input:

- `path: Path`
- `records: Sequence[object]`

Output:

- `None`

Effect:

- Writes normalized records atomically.

## Source Alignment Check

Aligned with the architecture:

- Provides direct data contracts.
- Keeps the core vocabulary small.
- Enforces cache identity for Result reuse.
