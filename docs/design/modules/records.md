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
- `AgentRecord`
- `WorkspaceConfig`
- `RuntimeConfig`
- `ResultCacheIdentity`
- `SelectorRecord`
- `FeatureRecord`
- `FeatureSnapshotRecord`
- `ResultRecord`
- `TaskPoolRecord`
- `BenchmarkSelectionRecord`
- `RollingOriginRecord`
- `MetricRecord`

## Required Fields

These are minimum boundary fields. Implementations may add derived fields, but
modules should not depend on fields that are not recorded here.

### TaskRecord

- `task_id`
- `repository_id`
- `base_commit`
- `source_family`
- `source_ref`
- `available_at`
- `known_at`
- `solver_material_digest`
- `solver_material_refs`
- `check_ids`
- `cluster_id`

### CheckRecord

- `check_id`
- `task_id`
- `check_type`
- `hidden_check_bundle_digest`
- `verifier_image_digest`
- `verifier_deps_digest`
- `resource_limits`
- `oracle_source`
- `available_at`

### AgentRecord

- `agent_id`
- `agent_manifest_digest`
- `model_snapshot_id`
- `harness_digest`
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
- `hidden_check_bundle_digest`
- `verifier_image_digest`
- `verifier_deps_digest`
- `agent_manifest_digest`
- `model_snapshot_id`
- `harness_digest`
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

### ResultRecord

- `result_id`
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
- `latency`
- `diff_digest`
- `verifier_metadata_digest`
- `started_at`
- `finished_at`

`invalid_owner` distinguishes Agent-attributable invalid outcomes from
benchmark infrastructure failures.

### FeatureRecord

- `feature_id`
- `task_id`
- `feature_name`
- `value`
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

### TaskPoolRecord

- `task_pool_id`
- `repository_id`
- `task_ids`
- `check_ids`
- `generator_config_digest`
- `certification_config_digest`
- `created_at`

### RollingOriginRecord

- `origin_id`
- `origin_time`
- `policy_digest`
- `history_task_ids`
- `future_holdout_task_ids`
- `known_at_cutoff`
- `embargo`
- `cluster_constraints_digest`
- `eligibility_mode`
- `holdout_overlap_policy`

Future holdout task IDs may be recorded before scoring, but future outcomes
must not be available to Selection before a `BenchmarkSelectionRecord` is
frozen.

### BenchmarkSelectionRecord

- `selection_id`
- `origin_id`
- `selector_id`
- `selected_task_ids`
- `selected_weights`
- `budget_digest`
- `selection_input_digest`
- `feature_snapshot_id`
- `eligibility_mode`
- `created_at`

This record is the frozen benchmark selection. It must be written before future
holdout outcomes are opened for scoring.

### MetricRecord

- `metric_id`
- `origin_id`
- `selection_id`
- `result_matrix_digest`
- `metric_name`
- `metric_value`
- `denominator_policy_digest`
- `computed_at`

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

### validate_result

Input:

- `result: ResultRecord`

Output:

- `ValidationResult`

Effect:

- Validates cache identity fields, status fields, cost/latency fields, and failure
  labels.

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

### validate_selector

Input:

- `selector: SelectorRecord`

Output:

- `ValidationResult`

Effect:

- Validates selector identity, version, training source digests, allowed feature
  fields, and leakage boundary metadata.

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
