# API Schema for Repository-Specific Agent Benchmarking

## 1. Scope

This document refines the stable command/query surface from `docs/architecture/interface-contracts.md` into payload-level schema guidance. It stays transport-neutral and does not define code, routes, database tables, or workflow implementation details.

Source basis:

- `docs/analysis/requirements.md`
- `docs/architecture/system-design.md`
- `docs/architecture/module-design.md`
- `docs/architecture/interface-contracts.md`
- `docs/architecture/scoring-semantics.md`
- `docs/architecture/policy-calibration.md`
- `docs/architecture/authorization-semantics.md`
- `docs/decisions/dependency-selection.md`
- `docs/decisions/module-dependencies.md`
- `docs/draft/abstract.md`
- `docs/research/**`

`Inference`: the same schema can be mapped to HTTP/OpenAPI, internal RPC, or workflow messages without changing the logical contract.

## 2. Contract Principles

- The API evaluates an `ACUT` (`Agent Configuration Under Test`), not only a base model. ACUT includes model, prompt, tools, permissions, retrieval/memory, runtime budget, control loop, run environment, adapter manifest, evaluation mode, and adapter purity.
- Barcarolle is not the default agent controller. Schema surfaces must model the Runner Integration Layer and distinguish native runner integration from `harness_native` mode, where the evaluated subject is `Agent + Harness`.
- Repository history is the source of truth for task creation and replay planning.
- Validation, runner integration, run submission, canonical verification, scoring, and policy are separate stages.
- Benchmark scorecards are first-class API resources for configuration comparison and optimization, even when callers do not request a repository License.
- Policy calibration resources are first-class API resources for threshold profiles, score-weighting factors, coverage gates, reliability-label rules, sensitivity analysis, and policy-version promotion.
- Repository and organization risk profiles are first-class API resources for explicit risk-appetite constraints consumed by calibration, scorecard policy, authorization, admission, and operating-state projection.
- Repository-agent admission APIs issue, distribute, and explain Licenses. They expose License-consumption compatibility, signed License certificates, signed status records/logs, operating-envelope coverage, status receipts, and consumer audit records for external systems, but they do not define a Barcarolle runtime enforcement plane.
- Golden/Judge remain explicit benchmark-side capabilities in the schema: Golden attaches pre-candidate discovery artifacts to `candidate_generation_run` and candidate-side reference artifacts to validation/task surfaces, while Judge attaches run-side assessment artifacts to scoring surfaces.
- Mutating commands are idempotent.
- Requests, responses, and events carry version and audit metadata.
- Unknown fields may be ignored by newer consumers when the change is additive.

`Assumption`: resource identifiers are opaque strings. Their encoding is not part of the contract.

## 3. Common Envelope

Every command or query should accept or return the following shared metadata where applicable.

### 3.1 Request metadata

| Field | Type | Stability | Notes |
| --- | --- | --- | --- |
| `contract_version` | string | Stable | Major contract family for cross-module compatibility. |
| `schema_version` | string | Stable | Resource or payload schema version. |
| `request_id` | string | Stable | Unique per request attempt. |
| `correlation_id` | string | Stable | Shared across a chain of related work. |
| `causation_id` | string | Stable | Links the request to the triggering event or command. |
| `actor_id` | string | Stable | Caller identity for audit and idempotency scope. |
| `idempotency_key` | string | Stable for writes | Required for mutating commands. |
| `requested_at` | datetime | Stable | Client-side request timestamp. |

### 3.2 Response metadata

| Field | Type | Stability | Notes |
| --- | --- | --- | --- |
| `request_id` | string | Stable | Echoed from the request. |
| `correlation_id` | string | Stable | Echoed from the request. |
| `contract_version` | string | Stable | Echoed from the request or negotiated server version. |
| `schema_version` | string | Stable | Payload version returned by the server. |
| `status` | string | Stable | `accepted`, `rejected`, `completed`, or `not_found` depending on the operation. |
| `result_ref` | string | Stable | Opaque reference to the created or retrieved resource when relevant. |
| `warnings` | array<object> | Later | Non-fatal advisory messages. |

### 3.3 Shared enums

`EvaluationMode` stable values:

- `patch_only`: external/native agent submits patch or result only; strongest non-invasiveness and often high native YOLO production fidelity, with limited process observation unless other evidence is supplied.
- `trace_submission`: external/native agent submits patch/result plus native trace, log, tool, or model summaries; traces are audit, binding, or risk evidence, not correctness root evidence.
- `observed_run`: Barcarolle does not control the agent loop but an outer wrapper observes declared workspace, process, command, network, stdout/stderr, or snapshot signals.
- `harness_native`: agent runs inside Barcarolle or a specified harness; observation/control are higher, but the ACUT must be labeled `Agent + Harness` and is not the same subject as unmodified native YOLO.

`AdapterPurityLevel` stable values:

- `A0_transport_only`: task transport, external launch, and artifact collection only.
- `A1_environment_wrapper`: workspace/container/network/budget wrapper control without changing the internal agent loop.
- `A2_tool_mediation`: tool calls are proxied or restricted, so the adapter is part of the evaluated subject.
- `A3_harness_native_controller`: Barcarolle or a specified harness controls loop, prompt, or tools; the evaluated subject is `Agent + Harness`.

`EvidenceTrustTier` stable values:

- `trusted_barcarolle_evidence`
- `adapter_observed_evidence`
- `agent_submitted_evidence`
- `third_party_evidence`

`ACUTFieldEvidenceBasis` stable values:

- `declared`: supplied by the ACUT owner or native runner without Barcarolle observation.
- `adapter_observed`: observed by a wrapper or adapter within its declared observation boundary.
- `third_party_attested`: supported by an external signed report, CI/provider usage report, deployment record, or similar third-party artifact.
- `barcarolle_trusted`: produced or verified by Barcarolle-controlled trusted execution or verification paths.

## 4. Shared Resource Shapes

### 4.1 Repository snapshot

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `snapshot_id` | string | Opaque snapshot identity. |
| `repository_id` | string | Repository identity. |
| `provider` | string | For example `github`. |
| `repository_slug` | string | Host-specific path or slug. |
| `default_branch` | string | Repository default branch. |
| `source_revision` | string | Commit or revision hash. |
| `snapshot_time` | datetime | When the snapshot was captured. |
| `import_mode` | string | Full import, incremental import, or refresh mode. |
| `provenance` | object | Source artifacts and capture trace. |
| `artifact_refs` | array<object> | Pointers to imported artifacts. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer or service identity. |

Later fields:

- `branch_tip`
- `catalog_hash`
- `retention_state`
- `labels`

`Inference`: the snapshot record should be enough to reconstruct what repository state was observed, but not necessarily the full runtime environment.

### 4.1a Repository risk profile

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `repository_risk_profile_id` | string | Opaque risk-profile identity. |
| `organization_id` | string | Organization scope when the profile is inherited across repositories. |
| `repository_id` | string | Repository scope when the profile is repository-specific. |
| `scope` | object | Repository, component/path, task-family, permission, risk-class, or high-impact path scope where the profile applies. |
| `risk_profile_version` | string | Version label for this appetite profile. |
| `predecessor_risk_profile_id` | string | Prior profile in the lineage, if any. |
| `parent_risk_profile_id` | string | Inherited parent profile, if any. |
| `risk_tolerance_class` | string | `conservative`, `balanced`, `expansive`, or `custom`. |
| `constraint_ref` | object | Full constraint artifact ref. |
| `constraint_digest` | string | Digest over the normalized constraint bundle. |
| `effective_constraint_summary` | object | Queryable summary of tier eligibility, unsafe-control budgets, coverage floors, reliability floors, evidence-basis requirements, freshness ceilings, review triggers, and calibration objective weights. |
| `tier_constraint_matrix` | object | `G0` through `G5` eligibility, floors, ceilings, and forbidden scope rules by permission/risk/task/path/target-condition slice. |
| `external_consumer_assumption_summary` | object | License-consumption assumptions downstream consumers must verify; not a Barcarolle runtime enforcement rule. |
| `lifecycle_state` | string | `draft`, `candidate`, `active`, `paused`, `superseded`, `rolled_back`, or `retired`. |
| `activated_at` | datetime | Activation timestamp when active. |
| `expires_at` | datetime | Optional expiration or review deadline. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Risk profiles are policy appetite, not benchmark evidence or calibration truth. They may tighten, forbid, or require review for future authorizations, but they cannot convert unsupported release scope into supported scope, upgrade weak evidence, or rewrite historical scorecards, decisions, admissions, or operating-state entries.

`ResolveEffectiveRiskProfile` responses should include selected source profile refs, the resolved constraint digest, inheritance or override basis, conflict handling, and whether write-capable authorization is blocked because no active or seed profile exists.

### 4.1b Candidate generation run

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `candidate_generation_run_id` | string | Opaque identity for a pre-candidate generation attempt. |
| `repository_id` | string | Owning repository. |
| `snapshot_id` | string | Source snapshot used for mining and Golden-assisted discovery. |
| `generation_strategy` | string | Mining strategy or candidate-family generation mode. |
| `signal_input_manifest_digest` | string | Canonical digest over extracted signals and repository evidence used as generation input. |
| `golden_configuration_id` | string | Governed Golden configuration used for discovery, selection, or contract synthesis, if any. |
| `golden_input_manifest_digest` | string | Digest of the Golden input package. Required when `golden_configuration_id` is present and part of the generation-run natural key. |
| `selection_policy_version` | string | Policy version used to select or rank candidate outputs. |
| `run_attempt_number` | integer | Semantic generation attempt number for the same generation basis. |
| `status` | string | `reserved`, `completed`, `failed`, or `superseded`, derived from append-only reservation/completion events. |
| `selected_output_digest` | string | Completion metadata for the selected deterministic or Golden-assisted output; required only when status is `completed`. |
| `golden_output_evidence_bundle_id` | string | Completion metadata for the exact sealed evidence bundle version containing pre-candidate Golden output, when present. |
| `golden_output_manifest_version` | integer | Completion metadata for the referenced Golden output evidence bundle manifest version. |
| `golden_output_content_digest` | string | Completion metadata for the referenced Golden output bundle or selected output. |
| `selection_ranking_identity` | object | Completion metadata for candidate-specific selection/ranking produced by deterministic or Golden-assisted selection; required only when status is `completed`. |
| `completion_event_id` | string | Append-only completion event identity when the run has been completed. |
| `completed_at` | datetime | Completion timestamp when present. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

`Inference`: this resource is the stable evidence subject for Golden discovery before any `task_candidate_id` exists. The backend allocates `candidate_generation_run_id` from the reservation natural key, which includes `golden_input_manifest_digest` when Golden is used. Output evidence-bundle refs are append-only completion metadata, not reservation-key fields. A later task candidate may reference the `candidate_generation_run_id` and exact output digest/bundle version in `generation_context_lineage`, but evidence storage must not require a candidate identity first.

### 4.2 Task candidate

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `task_candidate_id` | string | Opaque candidate identity. |
| `repository_id` | string | Owning repository. |
| `snapshot_id` | string | Source snapshot. |
| `candidate_generation_run_id` | string | Optional pre-candidate generation run that owns Golden-assisted discovery evidence before this candidate existed. |
| `generation_context_lineage` | object | Extractor lineage plus candidate-specific selection identity, and any broader candidate-build lineage that materially changes candidate semantics. When Golden assists discovery, selection, or contract synthesis before candidate creation, this includes `candidate_generation_run_id`, `golden_configuration_id`, Golden input-manifest digest, selected output digest, exact evidence-bundle version/content digest, and selection/ranking identity. |
| `task_family` | string | Issue-to-patch, PR-to-feature, commit-to-regression, CI-failure, migration, or similar. |
| `source_anchor` | object | Commit, issue, PR, CI failure, or other historical anchor. |
| `source_refs` | array<object> | Repository-native source refs that establish provenance. |
| `T_task` | datetime | Fixed task time boundary; agent-visible inputs must be at or before this time. |
| `title` | string | Human-readable candidate name. |
| `problem_statement` | string | Draft task statement. |
| `allowed_inputs` | array<object> | Inputs that may be visible to the ACUT. |
| `disallowed_inputs` | array<object> | Inputs explicitly excluded because they are post-`T_task`, answer-bearing, unsafe, or outside scope. |
| `expected_artifacts` | array<object> | Patch, config, test, doc, or other result artifacts expected from a valid solution. |
| `expected_oracle` | object | Validation or test expectation derived from repository evidence. |
| `context_refs` | array<object> | Relevant files, symbols, tests, or docs. |
| `required_permissions` | array<object> | Permission classes the task would exercise. |
| `capability_tags` | array<string> | Capability labels used for release coverage and authorization mapping. |
| `component_tags` | array<string> | Path, module, or component labels used for release coverage. |
| `risk_class` | string | Repository policy risk class for this task. |
| `high_impact_path_classes` | array<string> | High-impact path classes touched or exercised, if any. |
| `duplicate_cluster_id` | string | Similarity cluster used to cap release weight. |
| `task_admission_gate_results` | object | Provisional task-quality gate results before final validation. |
| `oracle_profile_draft` | object | Proposed oracle family, expected grade, and known limitations before validation. |
| `leakage_kind` | array<string> | Queryable leakage categories such as `future`, `answer`, `artifact_exposure`, or `provenance`. Empty when severity is `none`. |
| `leakage_severity` | string | `none`, `minor_redactable`, `suspected`, or `confirmed`. |
| `leakage_handling_decision` | string | `clear`, `redact_and_revalidate`, `requires_review`, `reject`, `quarantine`, or `retire`. |
| `leakage_review_required` | boolean | Whether leakage handling routes to governance before any exceptional path; normal approval requires objective repair/revalidation rather than human leakage truth. |
| `acut_visible_surfaces` | array<object> | ACUT-visible surfaces implicated by the report, with stable surface kind, ref or digest, and exposure summary. |
| `redaction_revalidation_lineage` | object | Redaction and follow-up validation refs when minor leakage is repaired before approval. |
| `leakage_report_ref` | object | Exact future/answer leakage report ref or summary. |
| `leakage_report_digest` | string | Digest of the exact leakage report consumed by this candidate projection. |
| `contamination_flags` | array<string> | Leakage or provenance warnings. |
| `review_required` | boolean | Whether governance review is required for annotation, pause, repair, override, rollback, or exceptional policy ownership. It is not a normal benchmark-acceptance prerequisite. |
| `review_state` | string | Candidate review projection: `not_required`, `pending`, `approved`, `rejected`, `repair_required`, `waived_warning`, or `retired`. |
| `review_reason_codes` | array<string> | Structured reason codes that explain why review is required or why the candidate cannot proceed. |
| `latest_admission_review_id` | string | Most recent append-only admission review record, if any. |
| `status` | string | Canonical candidate lifecycle state: `Draft`, `Candidate`, `Planned`, `EnvironmentReady`, `Validated`, `RepairRequired`, `Approved`, `Rejected`, `Retired`, or `Failed`. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `intent_summary`
- `leakage_review`
- `difficulty_hint`
- `retirement_reason`

`Assumption`: `source_anchor` is a tagged union, not a single fixed shape, because the contract already allows multiple repository evidence types. `generation_context_lineage` is the regeneration-safe identity axis and must capture extractor lineage plus candidate-specific selection identity at minimum; it may also include broader candidate-build lineage when that context materially changes candidate semantics. Golden-assisted discovery is part of that generation context, not a post-hoc validation note, when Golden materially influenced which candidate was created or what verifier/oracle contract was synthesized. Pre-candidate Golden output should be evidence-scoped to `candidate_generation_run`; candidate and validation evidence only take over after the candidate exists.

The candidate lifecycle is intentionally kept distinct from the downstream `task` lifecycle. Replay planning, environment build, and validation all happen against the candidate. Only after validation succeeds and `ApproveTaskCandidate` is accepted does the system materialize the canonical `task` resource.

### 4.3 Task

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `task_id` | string | Opaque approved-task identity. |
| `task_candidate_id` | string | Source candidate that was admitted. |
| `repository_id` | string | Owning repository. |
| `task_family` | string | Same family as the source candidate. |
| `status` | string | Canonical task lifecycle state: `Approved` or `Retired`. |
| `approval_validation_result_id` | string | Validation result that satisfied the approval gate. |
| `approved_environment_id` | string | Replay environment that admitted the task. |
| `approval_review_id` | string | Optional governance review record linked when approval involved annotation, warning waiver, or an exceptional policy path. |
| `approved_at` | datetime | When approval materialized the task. |
| `benchmark_scope` | object | Scope under which the task participates in benchmarking. |
| `retirement_marker` | object | Current retirement summary, if retired. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `drift_marker`
- `replacement_task_id`

`Inference`: `task` is the approved benchmark instance only. Downstream execution status belongs to `evaluation_run`, aggregate scoring belongs to `score_bundle` / `benchmark_scorecard`, and benchmark publication belongs to `benchmark_release`.

### 4.4 Replay plan

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `replay_plan_id` | string | Opaque plan identity. |
| `task_candidate_id` | string | Candidate being prepared for admission. |
| `task_id` | string | Optional approved-task reference populated after approval. |
| `base_revision` | string | Historical base commit or snapshot boundary. |
| `environment_strategy` | string | Chosen reconstruction approach. |
| `verifier_ref` | object | Selected verifier or test command reference. |
| `dependency_clues` | array<object> | Manifests, lockfiles, CI files, docs, or package metadata. |
| `fidelity_policy` | string | The replay strictness policy. |
| `feasibility_status` | string | `planned`, `needs_review`, `unreplayable`, or `ready`. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `alternate_strategies`
- `expected_cost`
- `fidelity_notes`

`Inference`: replay planning should preserve the distinction between "candidate can be reconstructed" and "candidate has already been admitted as a task."

### 4.5 Replay environment

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `environment_id` | string | Opaque environment identity. |
| `task_candidate_id` | string | Candidate whose replay environment was built. |
| `task_id` | string | Optional approved-task reference populated after approval. |
| `replay_plan_id` | string | Owning plan reference. |
| `runtime_image` | object | Image name, digest, or build recipe reference. |
| `build_artifacts` | array<object> | Image digests, build logs, or packaged outputs. |
| `build_status` | string | `pending`, `built`, `failed`, or `validated`. |
| `reproducibility_label` | string | Stable label such as `faithful`, `partial`, or `unreplayable`. |
| `environment_fingerprint` | string | Digest or fingerprint for audit. |
| `network_policy` | object | Allowed or blocked external access. |
| `tool_policy` | object | Tool and permission policy. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `package_source_snapshot`
- `seed_material`
- `resource_limits`
- `isolation_backend`

### 4.6 Validation result

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `validation_result_id` | string | Opaque validation-verdict identity. |
| `task_candidate_id` | string | Candidate that was validated. |
| `task_id` | string | Optional approved-task reference populated after approval. |
| `environment_id` | string | Environment that was validated. |
| `validation_kind` | string | Base-state, target-state, leakage, flakiness, or aggregate verdict kind. |
| `benchmark_admission_policy_version` | string | Version of the task-admission policy used for gate and oracle evaluation. |
| `oracle_profile` | object | Oracle family, grade, verifier scope, confidence, runtime, flakiness, limitations, and evidence refs. |
| `oracle_grade` | string | `A_strong_behavioral`, `B_objective_partial`, `C_auxiliary`, or `D_weak`. |
| `validation_probe_results` | array<object> | Canonical solution, no-op, known-bad, base-state, flakiness, runtime-budget, oracle-log-leakage, and optional mutation/equivalence probe results. |
| `leakage_kind` | array<string> | Queryable leakage categories detected by this validation path, such as `future`, `answer`, `artifact_exposure`, or `provenance`. |
| `leakage_severity` | string | `none`, `minor_redactable`, `suspected`, or `confirmed`. |
| `leakage_handling_decision` | string | `clear`, `redact_and_revalidate`, `requires_review`, `reject`, `quarantine`, or `retire`. |
| `leakage_review_required` | boolean | Whether this validation path routes to governance; normal approval cannot consume suspected leakage until objective repair/revalidation clears it. |
| `acut_visible_surfaces` | array<object> | ACUT-visible surfaces implicated by leakage scans, including surface kind, ref or digest, and exposure summary. |
| `redaction_revalidation_lineage` | object | Redaction refs and superseding validation refs when minor leakage was repaired. |
| `leakage_report_ref` | object | Exact leakage report used by the verdict. |
| `leakage_report_digest` | string | Digest of the exact leakage report consumed by this validation result. |
| `task_quality_gate_summary` | object | Provenance, replay, boundary, non-retrieval, complexity, duplicate, safety, and permission-map gate summary. |
| `admission_verdict` | string | `certify`, `reject`, `needs_review`, or `repair_required`. |
| `validity_decision` | string | `accepted`, `rejected`, `needs_review`, or `repair_required`. |
| `reproducibility_label` | string | `faithful`, `partial`, `flaky`, or `unreplayable`. |
| `contamination_flag` | boolean | Whether leakage or contamination was detected. |
| `failure_cause` | string | Domain failure code when validation did not pass. |
| `review_required` | boolean | Whether governance review is required before any exceptional action. Normal approval still requires automated admission gates to certify. |
| `review_reason_codes` | array<string> | Structured reasons for review, repair, rejection, or retirement. |
| `golden_artifact_refs` | array<object> | Optional candidate-side reference artifacts or summaries produced by Golden Agent or equivalent trusted validation-side logic. These refs must use the controlled assessor artifact-ref shape and default to summary-only when `blind_safe` is false. |
| `golden_configuration_id` | string | Governed Golden configuration version used to produce the attached artifacts, if any. |
| `latest_admission_review_id` | string | Most recent admission review record linked to this validation path, if any. |
| `reviewer_notes` | string | Human or policy notes for ambiguous cases. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `repeated_run_count`
- `flakiness_label`
- `validation_policy_version`

`Inference`: certified task approval requires `admission_verdict = certify`, oracle grade A or B, required validation probes passing under policy, no confirmed or suspected future or answer leakage, and an automated task-admission policy result. Golden/Judge/human C-grade evidence can support governance audit but cannot be the only pass/fail oracle or normal calibration truth.

### 4.6a Leakage report

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `leakage_report_id` | string | Opaque leakage-report identity. |
| `subject_kind` | string | `task_candidate`, `validation_result`, `task`, `task_retirement`, or `release_maintenance_finding`. |
| `task_candidate_id` | string | Candidate whose ACUT-visible boundary was scanned, when applicable. |
| `validation_result_id` | string | Validation path that consumed this report, when applicable. |
| `task_id` | string | Approved task affected by the report, when applicable. |
| `T_task` | datetime | Task-time boundary used by the scan. |
| `source_time_evidence_refs` | array<object> | Evidence refs that establish what existed at or before `T_task`. |
| `agent_visible_input_inventory` | array<object> | Prompt, workspace, retrieval, examples, memory, issue/PR, docs, logs, tool-visible files, runner package, verifier-log, and hidden-test exposure entries with refs and digests. |
| `leakage_kind` | array<string> | `future`, `answer`, `artifact_exposure`, or `provenance`. Empty only when severity is `none`. |
| `leakage_severity` | string | `none`, `minor_redactable`, `suspected`, or `confirmed`. |
| `acut_visible_surfaces` | array<object> | Machine-readable surface kind, ref or digest, visibility path, and exposure summary. |
| `scan_result_summary` | object | Future-artifact, prompt/diff overlap, identifier overlap, literal overlap, hidden-test, verifier-log, canary, and weak-baseline scan summaries. |
| `handling_decision` | string | `clear`, `redact_and_revalidate`, `requires_review`, `reject`, `quarantine`, or `retire`. |
| `review_required` | boolean | Whether the report routes to governance. Normal approval or publication can proceed only after objective repair/revalidation or automated certification clears the issue. |
| `redaction_revalidation_lineage` | object | Redaction artifact refs, superseding candidate or validation refs, and revalidation result when minor leakage is repaired. |
| `report_ref` | object | Durable artifact or evidence-bundle ref for the full report. |
| `report_digest` | string | Digest of the exact full report. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

`Inference`: `leakage_report_ref` remains the exact evidence pointer, but enforcement and query logic must use the first-class leakage fields. `confirmed` leakage must be represented directly in `leakage_severity`, and a redacted candidate must retain `redaction_revalidation_lineage` that points to the replacement validation result.

### 4.7 Benchmark definition

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `benchmark_definition_id` | string | Opaque stable benchmark identity. |
| `repository_id` | string | Owning repository. |
| `scope` | object | Repository-wide or narrower benchmark scope. |
| `benchmark_key` | string | Stable repository-local benchmark line key or slug. |
| `status` | string | `draft`, `active`, or `retired`. |
| `latest_published_release_id` | string | Current published release pointer, if any. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `retirement_marker`
- `display_name`

### 4.8 Benchmark release

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `benchmark_release_id` | string | Opaque immutable release identity. |
| `benchmark_definition_id` | string | Stable benchmark line that owns the release. |
| `release_label` | string | Human-meaningful version, sequence, or publication tag. |
| `publication_status` | string | `draft`, `published`, `superseded`, or `retired`. |
| `published_at` | datetime | Publication timestamp for the immutable release snapshot. |
| `publication_rationale` | string | Why this release was published or refreshed. |
| `source_snapshot_id` | string | Optional repository snapshot that grounded publication. |
| `membership_items` | array<object> | Immutable release-membership snapshot referencing approved tasks, weights, and roles. |
| `release_admission_policy_version` | string | Version of the release certification and coverage policy. |
| `release_coverage_profile` | object | Coverage by task family, capability, component/path, risk class, permission class, high-impact path class, oracle grade, source type, duplicate cluster, flakiness/runtime, and recency. |
| `supported_authorization_scopes` | array<object> | Authorization scopes the release has enough certified coverage to support. |
| `unsupported_authorization_scopes` | array<object> | Missing or blocked scopes with reason codes. |
| `release_certification_verdict` | string | `certified`, `diagnostic_only`, `needs_review`, or `rejected`. |
| `release_admission_review_refs` | array<object> | Governance refs when release publication involved annotation, pause, override, rollback, or exceptional policy ownership. Certified publication itself is an automated policy result. |
| `supersedes_release_id` | string | Prior release superseded by this release, if any. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `release_digest`
- `comparison_summary`

`Inference`: published certified releases must declare both supported and unsupported authorization scopes. Authorization can narrow below `supported_authorization_scopes[]`, but cannot widen beyond them.

### 4.9 Tested-agent snapshot

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `tested_agent_snapshot_id` | string | Opaque immutable tested-agent snapshot identity. |
| `snapshot_fingerprint` | string | Stable repository-scoped natural key and idempotency anchor for this snapshot's captured contents, including subject label and the ACUT field evidence-basis map. The backend recomputes the canonical value from the submitted repository-relevant digests and rejects mismatches. |
| `agent_configuration_id` | string | Optional upstream configuration/catalog identity. |
| `repository_scope` | object | Repository or narrower scope where this snapshot is meaningful. |
| `snapshot_kind` | string | `evaluated_reference`, `candidate_change`, `operating_observation`, or another explicit source kind. |
| `subject_label` | string | Evaluated subject label such as `native_agent` or `Agent + Harness`. |
| `acut_manifest_digest` | string | Canonical digest over the repository-relevant ACUT manifest. |
| `model_ref` | object | Model/provider identity. |
| `prompt_digest` | string | Digest of system prompt or governing rubric. |
| `tool_profile_digest` | string | Digest of tools and permissions. |
| `permission_profile_digest` | string | Digest of access or sandbox grants when separated from tools. |
| `memory_strategy_digest` | string | Digest of retrieval or memory policy. |
| `runtime_policy_digest` | string | Digest of runtime budget, retries, and execution posture. |
| `control_loop_digest` | string | Digest of the agent control loop or external orchestrator behavior being evaluated. |
| `run_environment_declaration` | object | Declared native runtime, wrapper, container, network, and budget environment for the ACUT. |
| `adapter_manifest` | object | Adapter identity, version, observation boundary, and purity declaration. |
| `evaluation_mode` | string | One `EvaluationMode` value. |
| `adapter_purity_level` | string | One `AdapterPurityLevel` value. |
| `acut_field_evidence_basis` | object | Map from material ACUT fields to `ACUTFieldEvidenceBasis` values, including model, prompt, tools, permissions, memory, runtime budget, control loop, run environment, adapter manifest, and network/tool posture. |
| `canonical_artifact_refs` | object | Durable refs for prompt, tool profile, permission profile, memory strategy, and runtime policy artifacts. |
| `captured_at` | datetime | When the snapshot was recorded. |
| `provenance` | object | Capture method, producer identity, and evidence summary. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `environment_digest`
- `supply_chain_attestation_ref`

`Inference`: `tested_agent_snapshot_id` remains the canonical opaque resource identity. `snapshot_fingerprint` is stable because multiple layers use it for natural-key uniqueness and idempotent registration, but the persisted fingerprint is always the backend-validated canonical digest over the submitted repository-relevant inputs rather than an unchecked caller token. Evaluation mode and adapter purity are part of the ACUT identity; callers must not compare or admit results across those axes without governed review. The field evidence-basis map prevents non-invasive `patch_only` or `trace_submission` runs from looking more verified than they are: native workspace, network, tool posture, or runtime fields can be part of the ACUT identity while still being `declared` rather than `barcarolle_trusted`. Those modes can still support high-tier native YOLO admission when correctness, production fidelity, binding/attestation, and License-consumption compatibility gates pass. If `evaluation_mode = harness_native` or `adapter_purity_level = A3_harness_native_controller`, `subject_label` must be `Agent + Harness`.

### 4.10 Benchmark evaluation

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `benchmark_evaluation_id` | string | Opaque benchmark-evaluation identity. |
| `benchmark_definition_id` | string | Stable benchmark line under evaluation. |
| `benchmark_release_id` | string | Immutable release used as the evaluation basis. |
| `tested_agent_snapshot_id` | string | Immutable evaluated-reference snapshot under test. |
| `agent_configuration_id` | string | Optional upstream configuration/catalog identity. |
| `evaluation_policy_version` | string | Policy version that determined run planning and aggregation rules. |
| `evaluation_mode` | string | One `EvaluationMode` value used for every benchmark-linked child run. Child runs must match this value; a different mode requires a separate parent benchmark evaluation and scorecard basis. |
| `adapter_purity_level` | string | One `AdapterPurityLevel` value used for comparability and admission binding. |
| `adapter_manifest` | object | Adapter identity, version, observation boundary, and purity declaration. |
| `run_environment_declaration` | object | Declared native or wrapped runtime environment. |
| `acut_field_evidence_basis_summary` | object | Field-level basis summary copied from the tested-agent snapshot for evaluation, admission, and UI display. |
| `capability_envelope_contract_id` | string | Stable identity of the benchmark-level capability-envelope contract basis. This is part of the canonical benchmark-evaluation identity so materially different execution-condition contracts do not collapse into same-basis retries. |
| `capability_envelope_contract_ref` | object | Normalized benchmark-level capability-envelope policy used to derive per-run immutable envelopes. |
| `assurance_mode` | string | `trusted_internal` in this phase, with room for stricter future modes. This is a stable benchmark-evaluation identity axis alongside release, tested-agent snapshot, evaluation policy, and attempt number. |
| `attempt_number` | integer | Caller-supplied semantic attempt ordinal. Transport retries reuse the same value; intentional reruns use a new idempotency key and the next value for the same benchmark-evaluation basis. |
| `status` | string | `requested`, `running`, `scoring`, `completed`, `failed`, or `canceled`. |
| `coverage_summary` | object | Planned membership count, completed count, failed count, and coverage gaps. |
| `benchmark_scorecard_refs[]` | array<object> | Optional immutable scorecard references produced for this evaluation, each carrying `benchmark_scorecard_id`, aggregate score, diagnostic completed score, scorecard policy, coverage policy, reliability policy, calibrated policy-profile ref when used, effective risk-profile ref/digest when appetite constraints affected the scorecard basis, evaluated capability envelope, `score_input_set_digest`, `evidence_trust_basis_digest`, denominator/missing-run summary, reliability label, and score-basis Judge lineage. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `coverage_gate`
- `comparability_summary`
- `refresh_relation`

The server must validate that `evaluation_mode`, `adapter_purity_level`, `adapter_manifest`, and `run_environment_declaration` match the referenced `tested_agent_snapshot` canonical normalized values. If they do not match, the request is not evaluating the referenced ACUT and must fail before benchmark fact creation, or return `policy_conflict` when reusing an existing basis.
`benchmark_scorecard_refs[]` is a convenience reference list, not an implicit selected-scorecard selector. When callers need a particular aggregate interpretation, they must use `GetBenchmarkScorecard` by `benchmark_scorecard_id` or `ListBenchmarkScorecards` with a complete scorecard-basis selector.

### 4.11 Evaluation run

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `run_id` | string | Opaque run identity. |
| `benchmark_evaluation_id` | string | Optional parent benchmark evaluation when the run is part of a benchmark-authoritative evaluation. |
| `benchmark_release_membership_id` | string | Optional release-membership item that this run satisfies. |
| `run_basis_type` | string | `benchmark_evaluation` or `ad_hoc`. |
| `task_id` | string | Evaluated task. |
| `environment_id` | string | Replay environment reference. |
| `tested_agent_snapshot_id` | string | Immutable tested-agent snapshot actually executed. |
| `agent_configuration_id` | string | Optional upstream configuration/catalog identity. |
| `evaluation_mode` | string | One `EvaluationMode` value for this run. |
| `adapter_purity_level` | string | One `AdapterPurityLevel` value for this run. |
| `adapter_manifest` | object | Adapter identity, version, observation boundary, and purity declaration. |
| `run_environment_declaration` | object | Declared native or wrapped runtime environment. |
| `acut_field_evidence_basis_summary` | object | Field-level ACUT identity basis copied from the tested-agent snapshot only. Run-level observation must not rewrite this value. |
| `run_observation_basis` | object | Run-scoped adapter or wrapper observations, such as observed workspace, process, network, stdout/stderr, or file-change basis. This is corroborating evidence for audit, Judge confidence, and risk analysis, not a mutation of the ACUT snapshot identity. |
| `attempt_number` | integer | Attempt ordinal within the envelope-independent `run_attempt_slot`. |
| `run_attempt_slot` | object | Derived idempotency and conflict slot. For ad hoc runs it is `task_id + tested_agent_snapshot_id + environment_id + attempt_number`; for benchmark-linked runs it is `benchmark_evaluation_id + benchmark_release_membership_id + attempt_number`. |
| `status` | string | `queued`, `invoking_runner`, `awaiting_submission`, `evidence_ingesting`, `canonically_verifying`, `completed`, `failed`, or `canceled`. |
| `started_at` | datetime | When execution began. |
| `finished_at` | datetime | When execution ended, if known. |
| `capability_envelope_id` | string | Stable identity of the immutable run contract materialized before runner invocation or harness-native launch. |
| `capability_envelope` | object | Immutable run contract covering tool policy, network or egress profile, runtime limits, and evidence destination. |
| `tool_policy` | object | Stable tool allowlist or equivalent policy ref. |
| `network_egress_profile` | object | Stable network or egress posture, allowlist, or deny profile. |
| `evidence_destination` | object | Stable evidence sink or manifest destination ref. |
| `runtime_limits` | object | Budget, timeout, or resource caps. |
| `termination_reason` | string | Why the run stopped. |
| `step_summary` | array<object> | Coarse execution steps. |
| `run_submission_id` | string | Accepted submitted patch/result/artifact manifest, if present. |
| `canonical_verification_record_id` | string | Clean-room verification record that roots correctness, if present. |
| `evidence_bundle_id` | string | Exact sealed evidence bundle version reference. |
| `evidence_bundle_manifest_version` | integer | Manifest version of the referenced evidence bundle. |
| `evidence_bundle_content_digest` | string | Content digest of the referenced evidence bundle version. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `retry_count`
- `resource_usage`
- `runner_backend`
- `trace_ref`

`Inference`: when `run_basis_type = benchmark_evaluation`, `benchmark_release_membership_id` is interpreted within the parent `benchmark_evaluation_id`. Consumers must not treat the membership identity alone as a globally unique child-run key across separate benchmark evaluations. Accepted run identity also includes evaluation mode, adapter purity, adapter manifest, and capability envelope because those axes change the evaluated boundary. Run requests must match the tested-agent snapshot and parent benchmark-evaluation canonical values for mode, purity, adapter, and run environment; mismatch is a validation failure before acceptance or `policy_conflict` for an already accepted attempt slot.

### 4.11a Run submission

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `run_submission_id` | string | Opaque submission identity. |
| `run_id` | string | Owning run. |
| `tested_agent_snapshot_id` | string | ACUT that produced the submission. |
| `evaluation_mode` | string | One `EvaluationMode` value. |
| `adapter_purity_level` | string | One `AdapterPurityLevel` value. |
| `patch_ref` | object | Submitted patch reference, when patch-shaped. |
| `result_ref` | object | Submitted non-patch result reference, when applicable. |
| `artifact_refs` | array<object> | Submitted artifacts. |
| `native_trace_refs` | array<object> | Agent-submitted traces, logs, model-call summaries, or tool-call summaries. |
| `producer_identity` | string | Agent, adapter, or harness producer identity. |
| `submission_digest` | string | Digest over submitted result metadata and artifacts. |
| `redaction_state` | string | Redaction state for submitted material. |
| `declared_completeness` | string | Whether the submitter believes required artifacts are complete. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

### 4.11b Canonical verification record

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `canonical_verification_record_id` | string | Opaque canonical verification identity. |
| `run_id` | string | Owning run. |
| `run_submission_id` | string | Submission being verified. |
| `task_id` | string | Evaluated task. |
| `environment_id` | string | Clean-room replay environment. |
| `verifier_identity` | string | Verifier identity and version. |
| `verifier_image_digest` | string | Clean-room verifier image digest. |
| `scoring_relevant_policy_version` | string | Policy basis that makes verifier outputs score-relevant and participates in canonical verification identity. |
| `clean_room_workspace_digest` | string | Workspace digest after applying the submitted result. |
| `patch_application_status` | string | `applied`, `apply_failed`, or equivalent result status. |
| `canonical_result` | string | Canonical pass/fail result used by scoring. |
| `failure_class` | string | Machine-readable failure class when not passing. |
| `verification_attempt_number` | integer | Semantic verification attempt under the same verifier basis. Idempotent retries reuse this value; intentional reverification increments it. |
| `trusted_evidence_digest` | string | Digest over trusted Barcarolle verification evidence. |
| `evidence_bundle_id` | string | Exact sealed evidence bundle version containing trusted verifier artifacts. |
| `evidence_bundle_manifest_version` | integer | Manifest version of the trusted verifier evidence bundle. |
| `evidence_bundle_content_digest` | string | Content digest of the trusted verifier evidence bundle version. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Correctness and admission root evidence must come from this record or other `trusted_barcarolle_evidence`. Agent-submitted traces and self-run tests are audit/risk evidence only unless corroborated by canonical verification. If run-level observation establishes stronger evidence basis for a material ACUT field, that observation stays in `run_observation_basis`; using it as an admission boundary requires a new tested-agent snapshot or an explicit governed change review / target-condition carry-forward.

### 4.12 Run score bundle

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `score_bundle_id` | string | Opaque score-bundle identity over the run, canonical verification record or trusted terminal outcome evidence digest, scoring policy version, score input evidence digest, and score-basis Judge lineage. |
| `run_id` | string | Source run. |
| `benchmark_evaluation_id` | string | Optional parent benchmark evaluation. |
| `benchmark_release_id` | string | Immutable release basis when the run is benchmark-linked. |
| `benchmark_release_membership_id` | string | Immutable membership item basis when the run is benchmark-linked. |
| `tested_agent_snapshot_id` | string | Immutable tested-agent snapshot used by the run. |
| `evaluated_subject_label` | string | Subject label copied from the tested-agent snapshot, such as `native_agent` or `Agent + Harness`. |
| `evaluation_mode` | string | Mode used for the source run. |
| `adapter_purity_level` | string | Adapter purity used for the source run. |
| `acut_field_evidence_basis_summary` | object | Field-level ACUT identity basis copied from the tested-agent snapshot. |
| `run_observation_basis_summary` | object | Summary of run-scoped observed basis used for audit, process scoring, Judge confidence, or risk adjustment without changing ACUT identity. |
| `run_observation_basis_digest` | string | Digest of the run-observation basis that contributed to process score, confidence, or audit-risk scoring. |
| `run_submission_id` | string | Submission scored. |
| `canonical_verification_record_id` | string | Correctness-root verification record when the run reached canonical verification. Required for positive correctness and verified pass/fail outcomes. |
| `terminal_outcome_evidence_digest` | string | Trusted Barcarolle digest used for scoreable pre-verification zeroes such as agent timeout or malformed submission when no canonical verification record exists. |
| `scoring_semantics_version` | string | Version of the run scoring semantics, such as `scoring_semantics_v1`. |
| `scoring_policy_version` | string | Policy version used to grade the run. |
| `run_outcome_class` | string | Classified terminal outcome such as `verified_pass`, `verified_fail`, `agent_timeout`, `malformed_or_empty_submission`, or `policy_invalid`. |
| `score_state` | string | `scoreable_positive`, `scoreable_zero`, `non_scoreable_missing`, `blocked`, `invalidated`, or another policy-defined score state. |
| `failure_class` | string | Machine-readable failure class when the outcome did not pass. |
| `failure_taxonomy_version` | string | Version of the failure taxonomy used by the scorer. |
| `outcome_owner` | string | `agent`, `barcarolle_infra`, `operator`, `third_party`, or `unknown`, used to distinguish scoreable agent failures from missing coverage. |
| `score_input_evidence_digest` | string | Canonical digest over exact sealed evidence bundle versions, run-observation basis digest, evidence trust-basis digest, contribution modes, and any other score-contributing or confidence-contributing evidence input. |
| `score_input_evidence_refs` | array<object> | Exact sealed evidence bundle IDs, manifest versions, content digests, and relevant artifact refs consumed by this score. |
| `raw_correctness_score` | number | Correctness before oracle/scorecard weighting. Positive values require trusted canonical verification. |
| `effective_correctness_score` | number | Per-run correctness after score-contributing caps or governed Judge reductions, before task aggregation weighting. |
| `correctness_score` | number | Main outcome score. |
| `process_score` | number | Optional process-quality score. |
| `stability_label` | string | For example `stable`, `unstable`, or `flaky`. |
| `repeated_run_group_id` | string | Stable repeated-run grouping key when this score participates in trial aggregation. |
| `trial_summary` | object | Pass-rate, trial-count, instability, and missing-trial summary when applicable. |
| `risk_flags` | array<string> | Structured risk findings from trusted checks, process evidence, or Judge assessment. |
| `authorization_blocking_risk_flags` | array<string> | Risk flags that block authorization readiness for affected scopes. |
| `authorization_eligible` | boolean | Whether this score bundle may be used as a score input for authorization-bearing scorecards. Positive or verified outcomes require a trusted canonical verification record; scoreable agent-owned zeroes may be eligible when backed by trusted terminal-outcome evidence. Critical risk flags can still make the aggregate scorecard `authorization_readiness = blocked`. |
| `metric_breakdown` | object | Supporting metrics and sub-scores. |
| `confidence` | number | Confidence or reliability signal. |
| `evidence_trust_basis` | object | Trust tiers used by the score and whether each tier was score-contributing or advisory. |
| `evidence_trust_basis_digest` | string | Canonical digest over the evidence trust basis recorded on this score bundle. This is separately exposed even though `score_input_evidence_digest` also commits to it. |
| `judge_contribution_mode` | string | `advisory`, `confidence_contributing`, `process_contributing`, or `score_contributing`. |
| `judge_artifact_refs` | array<object> | Optional run-side assessment artifacts or summaries produced by Judge Agent or equivalent trusted scoring-side logic. These refs must use the controlled assessor artifact-ref shape and default to summary-only when `blind_safe` is false. Advisory refs remain audit material and do not change canonical score identity by themselves. |
| `judge_configuration_id` | string | Governed Judge configuration version only when the active scoring policy treats that Judge output as score-contributing. When absent, the canonical score identity uses the explicit `none` Judge-lineage basis even if advisory Judge refs are attached. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `confidence_interval`
- `multi_run_summary`
- `retirement_recommendation`

### 4.13 Benchmark scorecard

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `benchmark_scorecard_id` | string | Opaque benchmark-scorecard identity over the benchmark evaluation, scorecard policy version, coverage policy version, reliability policy version, calibrated policy profile or seed basis, repository risk profile or seed basis, risk-profile digest, evaluated capability-envelope identity, evaluation mode, adapter purity, `score_input_set_digest`, `evidence_trust_basis_digest`, and score-basis Judge lineage. |
| `benchmark_evaluation_id` | string | Parent benchmark evaluation. |
| `benchmark_definition_id` | string | Stable benchmark line used for historical refresh comparison. |
| `benchmark_release_id` | string | Immutable release used as the same-benchmark comparison basis. |
| `tested_agent_snapshot_id` | string | Immutable tested-agent snapshot represented by this benchmark result. |
| `evaluated_subject_label` | string | Subject label represented by this scorecard, such as `native_agent` or `Agent + Harness`. |
| `evaluation_mode` | string | Mode covered by this scorecard. |
| `adapter_purity_level` | string | Adapter purity covered by this scorecard. |
| `acut_field_evidence_basis_summary` | object | Field-level ACUT identity basis copied from the tested-agent snapshot. |
| `run_observation_basis_summary` | object | Aggregate summary of run-scoped observations considered during scoring, kept separate from the ACUT identity basis. |
| `scoring_semantics_version` | string | Version of the scoring semantics used to interpret run outcomes, weights, missing coverage, and aggregation. |
| `scorecard_policy_version` | string | Aggregation policy version. |
| `calibrated_policy_profile_id` | string | Exact calibrated policy profile used for score weights, coverage gates, or reliability rules when the scorecard used calibrated parameters. |
| `repository_risk_profile_id` | string | Effective risk-profile identity or seed basis when scorecard policy used explicit appetite constraints. |
| `risk_profile_version` | string | Risk-profile version used for the scorecard basis. |
| `risk_profile_digest` | string | Digest of the effective risk-profile constraints used for weighting, coverage, reliability, or authorization-readiness policy. |
| `risk_profile_gate_summary` | object | Appetite constraints that affected scorecard policy inputs, such as coverage floors, reliability floors, high-impact rules, or blocked slices. |
| `aggregation_algorithm` | string | Deterministic algorithm identifier, such as `weighted_release_denominator_mean_v1`. |
| `judge_configuration_id` | string | Governed Judge configuration version only when the active scorecard basis includes score-contributing Judge output. When absent, the canonical scorecard identity uses the explicit `none` Judge-lineage basis even if advisory Judge summaries are attached. |
| `aggregate_score` | number | Benchmark-level score used for comparison and authorization. |
| `completed_score` | number | Diagnostic score over completed scoreable weight only; not a replacement for `aggregate_score` in authorization. |
| `aggregate_stability_label` | string | Aggregate stability or confidence class. |
| `reliability_label` | string | `high`, `medium`, `low`, or `blocked`, derived from coverage, sample count, verifier stability, and invalidation state. |
| `coverage_summary` | object | Coverage achieved across release membership. |
| `denominator_summary` | object | Requested/completed/verified release and score denominators, with missing weight grouped by reason. |
| `missing_run_summary` | object | Missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, or blocked run entries and their score/release weight impact. |
| `minimum_sample_summary` | object | Scoreable count, scoreable weight, covered families, critical-family/high-impact coverage, and threshold results. |
| `task_family_coverage` | object | Stable authorization-gate map keyed by task family, including completed and missing release weight, threshold status, critical-family flags, high-impact-path relevance, and whether missing coverage would require a changed benchmark basis. |
| `release_coverage_profile_ref` | object | Exact release coverage profile or digest used for authorization interpretation. |
| `release_admission_policy_version` | string | Release certification policy version attached to the supporting release coverage profile. |
| `release_certification_verdict` | string | Certification verdict of the supporting release, copied for authorization interpretation. |
| `supported_authorization_scope_summary` | object | Supported release scopes relevant to this scorecard's evaluated capability envelope. |
| `unsupported_authorization_scope_summary` | object | Unsupported or missing coverage dimensions relevant to this scorecard. |
| `canonical_verification_coverage` | object | Coverage over required canonical verification records. |
| `weighting_summary` | object | Release weight, score weight, duplicate cap, oracle multiplier/B cap, high-impact/risk multiplier, and final denominator contribution by membership or group. |
| `evidence_trust_basis` | object | Trust tiers used by aggregate scoring and authorization readiness. |
| `evidence_trust_basis_digest` | string | Canonical digest over the aggregate evidence trust basis used in scorecard identity. |
| `score_input_set_digest` | string | Canonical digest of the complete score input set, including requested release-membership entries, selected immutable score bundles and their score input evidence digests when present, repeated-run grouping, weighting factors, missing or blocked entries, and score-basis Judge lineage. |
| `contributing_score_bundle_refs` | array<object> | Exact score bundle IDs, score input evidence digests, and score-basis Judge lineage used by the aggregate. |
| `score_input_entries` | array<object> | Compact summary of all requested score input entries, including non-contributing missing or blocked entries; large detail may live behind a referenced artifact or digest. |
| `coverage_policy_version` | string | Version of the authorization-facing coverage gate policy. This is part of canonical scorecard identity because freshness on the authorization surface depends on the exact coverage gate that produced `authorization_readiness`. |
| `reliability_policy_version` | string | Version of reliability-label rules used to compute `reliability_label`; part of identity when it differs from the scorecard policy. |
| `evaluated_capability_envelope_id` | string | Stable identity of the capability envelope actually covered by the benchmark-authoritative scorecard. This is part of canonical scorecard identity because different evaluated execution postures have different authorization meaning. |
| `evaluated_capability_envelope` | object | Coverage gate over tool policy, network posture, runtime limits, and evidence destination, including minimum coverage threshold, task-family distribution requirements, and partial-evaluation policy inputs. |
| `authorization_readiness` | string | `ready`, `partial`, or `blocked` based on the evaluated coverage gate. |
| `invalidation_status` | string | `none`, `advisory`, `scorecard_invalidated`, or another policy-defined status when post-release findings affect the basis. |
| `invalidation_refs` | array<object> | `task_retirement` or `release_maintenance_finding` refs that affect this scorecard, if any. |
| `metric_breakdown` | object | Aggregate metrics and family-level summaries. |
| `policy_input_summary` | object | Explicit classification of scorecard fields consumed by authorization versus diagnostic-only fields. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `historical_comparison_summary`
- `aggregate_judge_refs`

`Inference`: authorization policy reads task-family gates from top-level `task_family_coverage`, release support from the release coverage profile, and scoring readiness from `aggregate_score`, denominator summary, missing-run summary, minimum-sample summary, reliability label, canonical-verification coverage, invalidation status, evidence trust basis, risk-profile gate summary, and score input identity. `coverage_summary` stays aggregate, `evaluated_capability_envelope` carries the partial-evaluation policy inputs, and `metric_breakdown` remains diagnostic. If fresh benchmark-authoritative interpretation is needed under a changed scoring policy, coverage policy, risk profile, weighting rule, complete score input set, or evaluated capability envelope, the system must materialize a new scorecard keyed by that full basis. Reinterpreting an older scorecard in place belongs on the governance side and must not be labeled `fresh`. Post-release task leakage or oracle invalidation writes invalidation refs instead of mutating score inputs in place.

### 4.14 Authorization decision

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `decision_id` | string | Opaque decision identity. |
| `repository_id` | string | Repository scope. |
| `scope` | object | Repository/resource boundary plus the permission action or risk class being decided. Execution posture belongs in the authorized capability envelope and downstream `target_condition_basis`. |
| `authorization_policy_version` | string | Authorization policy version used for the decision. This replaces ambiguous persisted `policy_version`; any request or response field named `policy_version` is a compatibility alias for this same value. |
| `calibrated_policy_profile_id` | string | Exact calibrated profile used for thresholds, coverage, reliability, and promotion gates when applicable. |
| `calibrated_policy_profile_digest` | string | Digest of the calibrated profile parameter bundle consumed by the decision. |
| `calibrated_profile_applicability_result` | object | Whether the promoted profile supports the requested tier/slice, including high-tier blocked, shadow-only, insufficient-control-power, or targeted-validation results. |
| `repository_risk_profile_id` | string | Effective risk-profile identity or seed basis used by the decision. |
| `risk_profile_version` | string | Risk-profile version used by the decision. |
| `risk_profile_digest` | string | Digest of effective risk-profile constraints. |
| `risk_profile_basis` | object | Source profiles, inheritance/override basis, selected constraints, and conflict handling used for the decision. |
| `risk_profile_gate_result` | object | Whether requested tier/scope satisfied tier eligibility, coverage, reliability, evidence-basis, freshness, review, and risk-budget constraints. |
| `benchmark_definition_id` | string | Stable benchmark line behind the decision. |
| `benchmark_release_id` | string | Immutable benchmark release that supplied the canonical comparison basis. |
| `benchmark_evaluation_id` | string | Benchmark evaluation that produced the supporting scorecard. |
| `benchmark_scorecard_id` | string | Supporting benchmark scorecard reference. |
| `tested_agent_snapshot_id` | string | Tested-agent snapshot the decision is about. |
| `evaluated_subject_label` | string | Subject evaluated by the supporting scorecard, such as `native_agent` or `Agent + Harness`. |
| `requested_admission_subject` | string | Subject requested for operation, such as `native_yolo`, `observed_native`, or `harness_bound`. |
| `subject_applicability` | object | Production-fidelity and applicability result comparing the evaluated subject with the requested admission subject. |
| `target_condition_basis_identity` | string | Stable identity of the target condition being decided. |
| `target_condition_basis` | object | Structured execution and interpretation/authorization boundary, including subject, mode, adapter, capability envelope, and policy basis. |
| `evaluation_mode` | string | Mode covered by the supporting scorecard. |
| `adapter_purity_level` | string | Adapter purity covered by the supporting scorecard. |
| `acut_field_evidence_basis_summary` | object | Field-level evidence basis for the ACUT fields covered by this decision. |
| `acut_binding_attestation_basis` | object | Evidence tying the submitted result and material ACUT fields to the tested-agent snapshot. |
| `license_consumption_basis` | object | Target-condition and operating-envelope assumptions external consumers need to verify compatibility with the requested repository operation surface. |
| `consumer_certificate_status_profile_basis` | object | Certificate signing, certificate validity, status freshness, status-watermark, and lifecycle-sequence assumptions required for later consumer-facing License certificate and status publication. |
| `policy_gate_results` | object | Results for correctness evidence, subject applicability, ACUT binding/attestation, License-consumption compatibility, and risk-profile constraints. |
| `score_bundle_id` | string | Optional supporting per-run score reference for drill-down or ad hoc decisions. |
| `canonical_verification_basis` | object | Summary of canonical verification records that root correctness. |
| `evidence_trust_basis` | object | Trust tiers used and whether each tier was score-contributing or advisory. |
| `release_coverage_profile_ref` | object | Release coverage profile or digest used to cap authorization scope. |
| `release_admission_policy_version` | string | Release certification and coverage policy version used as a mandatory authorization input. |
| `release_certification_verdict` | string | `certified`, `diagnostic_only`, `needs_review`, or `rejected`; write-capable grants require `certified`. |
| `release_scope_coverage_result` | object | Machine-readable result for the requested scope against `supported_authorization_scopes[]`, including covered dimensions, missing dimensions, unsupported reason codes, and coverage-profile digest. |
| `supported_authorization_scope_summary` | object | Release-supported scopes that bound this decision. |
| `unsupported_authorization_scope_summary` | object | Release-unsupported scopes and missing coverage dimensions relevant to this decision. |
| `unsupported_scope_reason_codes` | array<string> | Missing or unsupported release/scope coverage reasons when the decision narrows, downgrades, denies, or requires targeted validation. |
| `authorized_capability_envelope_id` | string | Stable identity of the capability envelope this decision actually authorizes. |
| `authorized_capability_envelope` | object | Coverage gate and bounded capability envelope used to justify the decision. |
| `authorization_readiness` | string | `ready`, `partial`, or `blocked` based on the coverage gate and partial-evaluation policy. |
| `requested_trust_tier` | string | Requested `G0` through `G5` authorization tier from `authorization_semantics_v1`, when the command asks for a tier. |
| `granted_trust_tier` | string | Granted `G0` through `G5` tier after score, coverage, correctness, subject-applicability, ACUT-binding, License-consumption compatibility, risk-profile, freshness, and review gates. |
| `policy_outcome` | string | `grant`, `deny`, `downgrade`, `needs_human_review`, `targeted_validation_required`, `full_rebenchmark_required`, `revoke`, `suspend`, or admission-lifecycle `lift_suspension`. |
| `decision_status` | string | `proposed`, `effective`, `superseded`, or `revoked`. |
| `invalidation_refs` | array<object> | Post-release `task_retirement` or `release_maintenance_finding` refs that affect this decision, if any. |
| `rationale_summary` | string | Human-readable justification. |
| `reviewer_id` | string | Human or policy engine identity. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `override_reason`
- `scope_exceptions`
- `expiry_time`

`Inference`: direct authorization decisions remain benchmark-policy outputs over an immutable benchmark scorecard and therefore represent `fresh` evidence only relative to that scorecard's exact identity, including `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, calibrated policy-profile ref, risk-profile basis, `evaluated_capability_envelope_id`, evaluated subject, requested admission subject, production-fidelity basis, evaluation mode, adapter purity, canonical verification basis, `score_input_set_digest`, and `evidence_trust_basis_digest`. If a repository later relies on `reused` or `supplemented` evidence under changed conditions, or wants to reinterpret old evidence without materializing a new scorecard, that distinction belongs on the governing change-review and admission records rather than on the benchmark fact itself. The tier and outcome semantics are defined in [authorization-semantics.md](./authorization-semantics.md).

### 4.15 Agent change review

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `agent_change_review_id` | string | Opaque append-only change-review identity. |
| `repository_id` | string | Owning repository. |
| `scope` | object | Repository, module, or task-family scope the review applies to. |
| `baseline_tested_agent_snapshot_id` | string | Previously evaluated or admitted snapshot. |
| `candidate_tested_agent_snapshot_id` | string | Later changed snapshot under review. |
| `baseline_acut_field_evidence_basis_summary` | object | Backend-derived ACUT field evidence-basis summary for the baseline snapshot. |
| `candidate_acut_field_evidence_basis_summary` | object | Backend-derived ACUT field evidence-basis summary for the candidate snapshot. |
| `acut_field_evidence_basis_delta` | object | Structured delta for ACUT field evidence-basis changes; also reflected inside `change_classification`. |
| `benchmark_evaluation_id` | string | Optional baseline benchmark fact used for the review. |
| `benchmark_scorecard_id` | string | Optional aggregate baseline fact used for the review. |
| `repository_agent_admission_id` | string | Optional prior admission carried forward or superseded by this review. |
| `change_classification` | object | Structured delta summary separating execution-condition changes from interpretation/authorization changes. |
| `target_condition_basis_identity` | string | Stable identity of the exact target condition boundary approved or rejected by this review. |
| `target_condition_basis` | object | Structured target execution and interpretation/authorization boundary for this review, including the target capability envelope and any benchmark/scorecard/policy basis needed to interpret the approval. |
| `evaluation_mode` | string | Mode covered by the reviewed basis or target condition. |
| `adapter_purity_level` | string | Adapter purity covered by the reviewed basis or target condition. |
| `canonical_verification_basis` | object | Canonical verification basis accepted, reused, supplemented, or rejected by the review. |
| `evidence_trust_basis` | object | Evidence trust tiers accepted, reused, supplemented, or rejected by the review. |
| `evidence_lineage` | string | Optional. `reused` or `supplemented` only when this review accepts non-fresh evidence for carry-forward; absent for `targeted_review_required`, `full_rebenchmark_required`, and `blocked`. |
| `review_outcome` | string | `carry_forward_acceptable`, `targeted_review_required`, `full_rebenchmark_required`, or `blocked`. |
| `applicability` | object | Explicit scope, time, and evolution boundaries for the review outcome. |
| `reviewer_id` | string | Human reviewer identity. |
| `rationale_summary` | string | Human-readable explanation. |
| `reviewed_at` | datetime | When the review was recorded. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `supersedes_agent_change_review_id`
- `change_summary`

`Inference`: `baseline_tested_agent_snapshot_id` and `candidate_tested_agent_snapshot_id` may match only when the reviewed delta is outside the ACUT identity, such as interpretation policy or a narrower authorization target condition. If evaluation mode, adapter purity, adapter manifest, run environment, or ACUT field evidence basis changes, callers must register a new candidate tested-agent snapshot before any fresh benchmark/run uses that boundary. The stored baseline/candidate field-basis summaries are derived from those snapshots; caller-supplied summaries or deltas, where accepted for readability, must match backend derivation or be rejected. In carry-forward cases, `target_condition_basis` is the explicit answer to what admission or authorization boundary the review is approving or rejecting; it does not rewrite the benchmark fact being reused.

### 4.16 Repository-agent admission

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `repository_agent_admission_id` | string | Opaque repository-agent admission or license identity. |
| `repository_id` | string | Owning repository. |
| `scope` | object | Repository/resource boundary plus the permission action or risk class being authorized. Execution posture belongs in `target_condition_basis`, not only in this field. |
| `tested_agent_snapshot_id` | string | Snapshot admitted for operation in the stated scope. |
| `admission_basis` | object | Basis references such as benchmark evaluation, scorecard, authorization decision, or change review. |
| `evidence_lineage` | string | `fresh`, `reused`, or `supplemented`, describing how the supporting evidence should be interpreted. |
| `granted_trust_tier` | string | Granted `G0` through `G5` admission tier. |
| `evaluated_subject_label` | string | Subject evaluated by the supporting evidence. |
| `admission_subject` | string | Subject this admission licenses, such as `native_yolo`, `observed_native`, or `harness_bound`. |
| `subject_applicability` | object | Production-fidelity and applicability basis for the admission. |
| `evaluation_mode` | string | Mode covered by the admission. |
| `adapter_purity_level` | string | Adapter purity covered by the admission. |
| `acut_field_evidence_basis_summary` | object | Field-level evidence basis for the admitted ACUT boundary. |
| `acut_binding_attestation_basis` | object | Evidence tying the admitted result and material ACUT fields to the tested-agent snapshot. |
| `license_consumption_basis` | object | External License-consumption and operating-envelope assumptions carried by this admission. |
| `policy_gate_results` | object | Results for the authorization gates that justified the granted tier. |
| `repository_risk_profile_id` | string | Risk-profile identity or seed basis that constrained the admission. |
| `risk_profile_version` | string | Risk-profile version used by the admission. |
| `risk_profile_digest` | string | Digest of effective risk-profile constraints. |
| `risk_profile_gate_result` | object | Appetite gate result copied from the supporting decision or change review. |
| `canonical_verification_basis` | object | Canonical verification basis that roots the admitted result. |
| `evidence_trust_basis` | object | Evidence trust tiers used by the admission and whether each tier is score-contributing or advisory. |
| `target_condition_basis_identity` | string | Stable identity of the exact target condition boundary this admission covers. |
| `target_condition_basis` | object | Structured target execution and interpretation/authorization boundary that this admission covers. |
| `covered_capability_envelope_id` | string | Stable identity of the capability envelope this admission covers. |
| `covered_capability_envelope` | object | Coverage gate and bounded capability envelope carried forward from the supporting evidence. This is the execution-posture component of `target_condition_basis`, not the whole boundary by itself. |
| `authorization_readiness` | string | `ready`, `partial`, or `blocked` based on the supporting coverage gate. |
| `status` | string | `proposed`, `effective`, `suspended`, `superseded`, `revoked`, or `expired`. |
| `effective_window` | object | Effective-from and optional expiry or freshness boundaries. |
| `freshness_deadline` | datetime | Latest time this admission can be used for its granted tier without renewal, revalidation, or rebenchmarking. |
| `admission_lifecycle_events` | array<object> | Append-only transition events, including transition kind, previous status, next status, cause, resolution summary when applicable, evidence refs, reviewer or policy identity, reviewed timestamp, and effective timestamp. |
| `admission_lifecycle_sequence` | integer | Monotonic sequence incremented by every admission lifecycle transition and copied into signed License certificates and status records so consumers can detect stale projections. |
| `consumer_certificate_status_profile` | object | Signing-key family, certificate schema version, status schema version, default certificate validity, optional certificate-expiry override or unbounded-validity setting, maximum status staleness, status-watermark requirement, and certificate availability state used to derive consumer-facing License certificates and status. |
| `latest_license_certificate_ref` | object | Optional latest materialized certificate identity, digest, signed timestamp, validity window, latest status ref, and status watermark for this admission and target-condition basis. |
| `reviewer_id` | string | Human reviewer or policy engine identity. |
| `rationale_summary` | string | Human-readable explanation. |
| `supersedes_repository_agent_admission_id` | string | Prior admission explicitly superseded when a newer effective admission takes over the same `repository_id + scope + target_condition_basis_identity`. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Later fields:

- `external_approval_requirements`

`Inference`: for any one `repository_id + scope + target_condition_basis_identity`, at most one admission may be `effective` at a time. A newer effective admission for the same tuple must explicitly point at the superseded admission rather than leaving effective-selection to UI heuristics. Multiple effective admissions may coexist for the same repository/resource scope only when their target-condition bases or authorization dimensions differ and policy explicitly allows that coexistence.
`Inference`: if the supporting decision is only partially covered, the admission must remain scope-bounded and explicitly retain the governing partial-evaluation policy rather than implying blanket authorization.
`Inference`: admissions must carry the explicit granted tier, evidence-lineage label, evaluated subject, admission subject, production-fidelity basis, evaluation mode, adapter purity, risk-profile basis, canonical verification basis, evidence trust basis, ACUT field evidence-basis summary, binding/attestation basis, and License-consumption compatibility basis so later authorization and operator reads can distinguish direct benchmark evidence from governed reuse or supplementation, native YOLO from `Agent + Harness`, and merely declared native-agent metadata from attested or enforceable metadata. A `lift_suspension` lifecycle event returns the same admission from `suspended` to `effective` only when snapshot, scope, target condition, capability envelope, tier, risk-profile basis, evidence basis, gate basis, and freshness boundary are unchanged; otherwise reinstatement must use a new superseding admission. External consumers must treat `suspended`, `revoked`, and `expired` admissions as `G0`. Signed License certificates are derived from this row and operating-state coverage, while signed status records/logs publish current lifecycle state; neither replaces the admission as the source of truth.

### 4.17 Repository-agent operating observation and state

Stable fields for the append-only operating observation:

| Field | Type | Notes |
| --- | --- | --- |
| `repository_agent_operating_observation_id` | string | Opaque append-only operating-observation identity. |
| `repository_id` | string | Owning repository. |
| `scope` | object | Repository, module, or task-family scope. |
| `tested_agent_snapshot_id` | string | Snapshot observed or declared as operating for that scope. |
| `state_source` | string | Deployment observation, operator declaration, policy sync, or another explicit source. |
| `evaluation_mode` | string | Optional mode observed or declared for this live state. Required when no linked admission/change review can supply it. |
| `adapter_purity_level` | string | Optional adapter purity observed or declared for this live state. Required when no linked admission/change review can supply it. |
| `adapter_manifest_digest` | string | Optional adapter manifest digest observed or declared for this live state. |
| `target_condition_basis_identity` | string | Optional target-condition basis identity observed, declared, or linked for this state. |
| `repository_agent_admission_id` | string | Optional admission believed to cover the observed state. |
| `agent_change_review_id` | string | Optional latest review relevant to the observation. |
| `observed_at` | datetime | When this fact was observed or declared. |
| `observer` | object | Human or system provenance for the observation. |
| `summary` | string | Short operator-facing statement of what changed or was seen. |

Stable fields for the derived operating state:

| Field | Type | Notes |
| --- | --- | --- |
| `repository_agent_operating_state_id` | string | Opaque current-state identity. |
| `repository_id` | string | Owning repository. |
| `scope` | object | Repository, module, or task-family scope. |
| `tested_agent_snapshot_id` | string | Snapshot currently selected or observed as operating. |
| `evaluation_mode` | string | Selected or primary mode for summary display. Full coverage is in `coverage_entries[]`. |
| `adapter_purity_level` | string | Selected or primary adapter purity for summary display. Full coverage is in `coverage_entries[]`. |
| `evaluated_subject_label` | string | Selected or primary evaluated subject label for summary display. Full coverage is in `coverage_entries[]`. |
| `admission_subject` | string | Selected or primary admitted subject for summary display. Full coverage is in `coverage_entries[]`. |
| `subject_applicability` | object | Selected or primary production-fidelity basis. Full coverage is in `coverage_entries[]`. |
| `adapter_manifest_digest` | string | Adapter manifest digest from the effective admission/change-review basis or selected operating observation. |
| `coverage_state` | string | `exact_match`, `carry_forward_admitted`, `pending_targeted_review`, `rebenchmark_required`, or `outside_admission`. |
| `drift_state` | string | High-level summary of divergence from the last exact benchmarked or admitted basis. |
| `evidence_lineage` | string | `fresh`, `reused`, or `supplemented`, propagated from the effective benchmark/admission basis. |
| `canonical_verification_basis` | object | Canonical verification basis currently covering this state, if any. |
| `evidence_trust_basis` | object | Evidence trust tiers currently covering this state, if any. |
| `acut_field_evidence_basis_summary` | object | Selected or primary ACUT identity field basis. Full target-condition coverage is in `coverage_entries[]`. |
| `acut_binding_attestation_basis` | object | Selected or primary binding/attestation basis. Full target-condition coverage is in `coverage_entries[]`. |
| `license_consumption_basis` | object | Selected or primary License-consumption compatibility basis. Full target-condition coverage is in `coverage_entries[]`. |
| `risk_profile_basis` | object | Selected or primary risk-profile basis and gate result. Full target-condition coverage is in `coverage_entries[]`. |
| `run_observation_basis_summary` | object | Selected or primary run-observation basis, kept separate from ACUT identity basis. |
| `target_condition_basis` | object | Selected or primary execution and interpretation/authorization boundary for summary display. Full coverage is in `coverage_entries[]`. |
| `repository_agent_admission_id` | string | Optional selected or primary admission for summary display. Full coverage is in `coverage_entries[]`. |
| `agent_change_review_id` | string | Optional selected or latest review relevant to this state. Full coverage is in `coverage_entries[]`. |
| `coverage_entries` | array<object> | Authoritative per-target-condition coverage entries for the current snapshot. Each entry includes stable coverage entry identity, target-condition basis identity, linked admission/review refs, evaluated subject, admission subject, production-fidelity basis, mode, purity, adapter manifest digest, coverage/drift state, `granted_trust_tier`, `admission_status`, `freshness_state`, `freshness_deadline`, risk-profile basis and gate result, evidence lineage, canonical verification basis, evidence trust basis, ACUT identity field basis, ACUT binding/attestation basis, License-consumption compatibility basis, run-observation basis when applicable, covered capability-envelope identity/coverage, admission lifecycle sequence, certificate profile, status-freshness profile, signed-certificate availability, latest status watermark, and next required action. |
| `operating_state_version` | integer | Monotonic projection version copied into signed License certificates, status records, receipts, and consumer audit records. |
| `latest_license_certificate_summary` | object | Optional certificate/status availability summary by coverage entry, including latest certificate digest/ref, lifecycle sequence, certificate validity window, status ref, status watermark, and status freshness deadline. |
| `latest_repository_agent_operating_observation_id` | string | Latest append-only observation fact used by the projection for this scope. |
| `state_source` | string | Deployment observation, operator selection, policy sync, or another explicit source. |
| `observed_at` | datetime | When this state was observed or declared. |
| `updated_at` | datetime | Last projection update time. |
| `summary` | string | Operator-facing explanation. |

Later fields:

- `last_exact_benchmark_evaluation_id`
- `next_required_action`

`Inference`: `repository_agent_operating_state` is a recomputable read model over benchmark facts, change reviews, repository admissions, and append-only operating observations. It is not the canonical write surface. The projection remains one row per repository scope, but `coverage_entries[]` is the authoritative representation when multiple effective target-condition admissions cover the same live snapshot. Top-level mode, purity, admission, target-condition, coverage, drift, risk-profile, and evidence fields are selected/default summaries for list views only and must not be treated as the complete authorization explanation when multiple entries exist. Each coverage entry must surface stable coverage entry identity, the relevant admission or review target-condition basis, evaluated subject, admission subject, production-fidelity basis, evaluation mode, adapter purity, `granted_trust_tier`, `admission_status`, freshness state/deadline, risk-profile basis/gate result, canonical verification basis, evidence trust basis, ACUT identity field evidence basis, ACUT binding/attestation basis, License-consumption compatibility basis, run-observation basis, admission lifecycle sequence, certificate profile, status-freshness profile, certificate availability, and latest status watermark so consumers and operators can see exactly which execution and interpretation boundary covers the live snapshot. If no admission or change review is linked, projection may use the selected operating observation's mode, purity, adapter manifest, and target-condition basis only as declared/observed live-state metadata, not as admission evidence, and must set `granted_trust_tier = G0`, `admission_status = none`, `freshness_state = not_applicable`, and signed-certificate availability to unavailable. The selected operating observation is resolved by source precedence first (`deployment_observation` over `operator_declaration` or `operator_selection` over `policy_sync`), then by latest `observed_at`, then by latest persisted observation identity as the deterministic final tie-break.

### 4.17a License certificate

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `license_certificate_id` | string | Opaque signed-certificate identity. |
| `contract_version` | string | API contract version consumed by the certificate. |
| `certificate_schema_version` | string | Version of the canonical certificate shape. |
| `certificate_digest` | string | Digest over the canonicalized certificate payload. |
| `canonicalization_algorithm` | string | Deterministic serialization rule used before signing. |
| `issuer` | object | Barcarolle issuer identity. |
| `certificate_signing_key_id` | string | Signing key used by the issuer for the certificate. |
| `issuer_key_set_version` | string | Issuer key-set version that contained the signing key at certificate issuance. |
| `issuer_key_status_ref` | string | Verifiable key-status record or event reference used at certificate issuance. |
| `issuer_key_status_digest` | string | Digest of the canonical key-status material copied into the certificate. |
| `issuer_key_status` | string | `active`, `retiring`, `retired`, or `revoked` at certificate issuance. Only `active` can sign new consumable certificates. |
| `issuer_key_valid_not_before` | datetime | Earliest accepted signing time for this key. |
| `issuer_key_valid_not_after` | datetime | Latest accepted signing time or certificate-validity boundary for this key. |
| `issuer_key_status_effective_at` | datetime | Effective timestamp for the key status copied into the certificate. |
| `issuer_key_revoked_at` | datetime | Optional hard invalidation timestamp when the key has been revoked. |
| `issuer_key_status_checked_at` | datetime | When certificate generation checked issuer-key status. |
| `signing_algorithm` | string | Signature algorithm. |
| `signature` | string | Signature over `certificate_digest` or canonical payload according to the certificate schema. |
| `signed_at` | datetime | When the certificate was signed. |
| `certificate_valid_not_before` | datetime | Earliest time the certificate can be accepted. |
| `certificate_valid_not_after` | datetime \| null | Nullable durable certificate expiry; absent means the certificate artifact is unbounded and current conformance is governed by signed status, admission freshness, and issuer-key status. |
| `renew_after` | datetime | Optional suggested renewal time before certificate expiry. |
| `status_surface_ref` | string | Pull surface for current signed status and status-log replay. |
| `status_schema_version` | string | Version of the signed status payload expected by the certificate. |
| `status_sequence_at_issuance` | integer | Status sequence used when the certificate was issued. |
| `status_watermark_at_issuance` | object | Status watermark used when the certificate was issued. |
| `max_status_staleness` | duration | Maximum age of signed status a consumer may use for current Barcarolle-conformant `allow`. |
| `next_status_poll_after` | datetime | Optional recommended status poll time. |
| `repository_id` | string | Repository covered by the certificate. |
| `scope` | object | Resource, operation, and risk-class scope covered by the certificate. |
| `repository_agent_admission_id` | string | Admission projected by the certificate. |
| `repository_agent_operating_state_id` | string | Operating-state projection used for live coverage. Required when `certificate_state = issued`; absent only for `non_consumable` admission-only diagnostics. |
| `coverage_entry_id` | string | Exact coverage entry used for target-condition coverage. Required when `certificate_state = issued`; absent only for `non_consumable` admission-only diagnostics. |
| `admission_lifecycle_sequence` | integer | Admission lifecycle sequence used to produce the certificate. |
| `operating_state_version` | integer | Operating-state projection version used to produce the certificate. |
| `event_stream_watermark` | object | Event watermark through which the certificate projection is current at issuance. |
| `target_condition_basis_identity` | string | Target condition covered by the certificate. |
| `target_condition_basis_digest` | string | Digest of the structured target-condition basis. |
| `tested_agent_snapshot_id` | string | Admitted snapshot identity. |
| `evaluated_subject_label` | string | Evaluated subject label. |
| `admission_subject` | string | Admitted subject, such as `native_yolo` or `harness_bound`. |
| `subject_applicability` | object | Production-fidelity/applicability basis. |
| `acut_field_evidence_basis_summary` | object | ACUT field evidence basis covered by the certificate. |
| `acut_binding_attestation_basis` | object | Binding/attestation basis covered by the certificate. |
| `license_consumption_basis` | object | Consumer-readable operating-envelope assumptions. |
| `covered_capability_envelope_id` | string | Covered capability envelope identity. |
| `covered_capability_envelope_digest` | string | Digest of the covered capability envelope. |
| `operation_risk_surface` | object | Operation/risk classes included, excluded, or requiring external local approval. |
| `admission_status` | string | Status at certificate issuance. Only `effective` certificates can be consumable, and only while current signed status also remains effective. |
| `granted_trust_tier` | string | Granted `G0` through `G5` tier. |
| `evidence_lineage` | string | `fresh`, `reused`, or `supplemented`. |
| `freshness_state` | string | Freshness status at certificate issuance. |
| `freshness_deadline` | datetime | Evidence freshness boundary. |
| `risk_profile_basis` | object | Risk-profile basis used by the admission. |
| `policy_gate_results` | object | Gate results copied from the supporting decision/admission. |
| `supporting_refs` | object | Authorization decision, change review, scorecard, status surface, and evidence refs/digests. |
| `supersession_refs` | object | Superseded or superseding admission refs when known. |
| `certificate_state` | string | `issued`, `non_consumable`, `expired`, `invalidated`, or `replaced`. |
| `non_consumable_reason_codes` | array<string> | Required when `certificate_state = non_consumable`, such as `missing_operating_state_coverage`, `multiple_consumer_ready_coverage_entries`, `coverage_entry_not_consumer_ready`, `uncovered_live_snapshot`, `issuer_key_unverifiable`, or `admission_not_effective`. |

`Inference`: this resource is the durable signed License artifact for external consumption. An `issued` certificate is generated from one admission plus exactly one operating-state coverage entry and may be cached until its explicit `certificate_valid_not_after` when present; when the certificate is unbounded, cacheability is governed by local retention and status lookup policy. In all cases, conforming `allow` also requires a fresh signed status record. A certificate without that binding is only an explicit `non_consumable` diagnostic projection. It is not an independent grant and is not evidence that a live agent or consumer actually respected the certificate.

### 4.17b License status record and log entry

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `license_status_id` | string | Opaque current status identity. |
| `license_status_log_entry_id` | string | Optional append-only log-entry identity when materialized separately from the current status projection. |
| `license_certificate_id` | string | Certificate whose current lifecycle state is being reported. |
| `certificate_digest` | string | Certificate digest covered by the status. |
| `repository_agent_admission_id` | string | Admission identity covered by the status. |
| `repository_agent_operating_state_id` | string | Operating-state identity covered by the status. |
| `coverage_entry_id` | string | Exact coverage entry covered by the status. |
| `target_condition_basis_identity` | string | Target condition covered by the status. |
| `status_sequence` | integer | Monotonic status sequence for this certificate/admission/coverage tuple. |
| `status_watermark` | object | Monotonic watermark consumers can acknowledge and replay from. |
| `previous_status_digest` | string | Optional previous status/log digest for replay integrity. |
| `status_log_root_digest` | string | Optional segment/root digest for log replay. |
| `event_stream_watermark` | object | Event watermark covered by this status. |
| `license_lifecycle_state` | string | `effective`, `suspended`, `revoked`, `expired`, `superseded`, `non_consumable`, or `issuer_key_invalid`. |
| `transition_kind` | string | `issue`, `suspend`, `lift_suspension`, `revoke`, `expire`, `supersede`, `issuer_key_rotate`, `issuer_key_revoke`, or another governed transition. |
| `cause_codes` | array<string> | Machine-readable cause codes. |
| `reviewer_or_policy_id` | string | Governance actor or policy engine that produced the transition. |
| `status_effective_at` | datetime | Time from which this lifecycle status applies. |
| `published_at` | datetime | Time this signed status was published. |
| `consumer_deny_after` | datetime | Optional latest timestamp after which conforming consumers must deny matching Barcarolle `allow`. |
| `admission_status` | string | Current admission status copied into the status record. |
| `admission_lifecycle_sequence` | integer | Current admission lifecycle sequence. |
| `operating_state_version` | integer | Operating-state version covered by this status. |
| `freshness_state` | string | Current freshness state. |
| `freshness_deadline` | datetime | Evidence freshness boundary. |
| `granted_trust_tier` | string | Granted tier currently projected by the status. |
| `superseding_refs` | object | Superseding admission or certificate refs when present. |
| `certificate_validity` | object | Certificate validity summary. |
| `certificate_signing_key_status` | object | Key status ref/digest/status for the certificate signing key. |
| `status_signing_key_status` | object | Key status ref/digest/status for the status signing key. |
| `max_status_staleness` | duration | Maximum age for current Barcarolle-conformant `allow`. |
| `status_fresh_until` | datetime | Latest decision time at which this status can support current Barcarolle-conformant `allow`. |
| `next_status_poll_after` | datetime | Optional recommended next status poll. |
| `status_signer` | object | Status signer identity and key id. |
| `signing_algorithm` | string | Signature algorithm. |
| `canonicalization_algorithm` | string | Deterministic serialization rule. |
| `signature` | string | Signature over the status digest or canonical payload. |
| `signed_at` | datetime | When the status was signed. |

`Inference`: status records and log entries are the independent lifecycle, revocation, supersession, expiration, and issuer-key-status authority for certificates. They are not runtime checkpoints; they let consumers prove current conformance without Barcarolle entering the agent process or run lifecycle.

### 4.17c License issuer key status

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `issuer_key_status_ref` | string | Opaque status record or event identity. |
| `issuer` | object | Barcarolle issuer identity. |
| `issuer_key_id` | string | Signing key identity. |
| `issuer_key_set_version` | string | Key-set version containing this status. |
| `public_key_digest` | string | Digest of the governed public key material. |
| `status_sequence` | integer | Monotonic sequence for key-status changes. |
| `key_status_watermark` | object | Monotonic watermark consumers can acknowledge and replay from. |
| `previous_key_status_digest` | string | Optional previous key-status digest/log pointer for replay integrity. |
| `key_status_log_root_digest` | string | Optional segment/root digest for key-status log replay. |
| `issuer_key_status` | string | `active`, `retiring`, `retired`, or `revoked`. |
| `key_purpose` | string | `certificate_signing`, `status_signing`, or both. |
| `valid_not_before` | datetime | Earliest valid signing time. |
| `valid_not_after` | datetime | Latest valid signing time or certificate/status validity boundary. |
| `status_effective_at` | datetime | Effective timestamp for this key status. |
| `retired_at` | datetime | Optional planned retirement timestamp when status is `retiring` or `retired`. |
| `emergency_retired_at` | datetime | Optional emergency-retirement timestamp that stops conforming use before normal retirement. |
| `revoked_at` | datetime | Hard invalidation timestamp when status is `revoked`. |
| `cause_codes` | array<string> | Machine-readable cause codes for non-active states. |
| `event_stream_watermark` | object | Event watermark for audit replay. |
| `published_at` | datetime | When the status was published. |
| `key_status_signer` | object | Issuer trust-anchor or accepted key-status signing authority. |
| `key_status_signing_key_id` | string | Key used to sign this key-status record. |
| `key_status_signer_key_set_version` | string | Key-set or trust-anchor version used to verify the key-status signature. |
| `signing_algorithm` | string | Signature algorithm. |
| `canonicalization_algorithm` | string | Deterministic serialization rule. |
| `status_digest` | string | Digest over the canonical key-status payload. |
| `signature` | string | Signature over `status_digest` or the canonical payload according to the key-status schema. |
| `signed_at` | datetime | When the key-status record was signed. |

`Inference`: key-status records are signed verification records for License certificate-signing and status-signing keys. They are the pull surface consumers use to verify signing-key rotation, retirement, emergency retirement, and revocation. They support offline validation and audit replay but do not authorize repository-agent operation by themselves.

### 4.17d License status receipt

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `license_status_receipt_id` | string | Opaque status receipt identity. |
| `consumer` | object | Consumer identity, version, and integration/environment id. |
| `receipt_source` | string | `pull`, `push`, or `replay`. |
| `received_at` | datetime | When the consumer received the status. |
| `acknowledged_at` | datetime | When the consumer acknowledged or rejected the status watermark. |
| `license_certificate_id` | string | Certificate covered by the receipt. |
| `certificate_digest` | string | Certificate digest covered by the receipt. |
| `license_status_id` | string | Status record covered by the receipt. |
| `status_digest` | string | Status digest covered by the receipt. |
| `status_sequence` | integer | Status sequence seen by the consumer. |
| `status_watermark` | object | Watermark acknowledged by the consumer. |
| `event_stream_watermark` | object | Event watermark seen by the consumer. |
| `certificate_signing_key_status_ref` | string | Key-status ref used to verify the certificate. |
| `status_signing_key_status_ref` | string | Key-status ref used to verify the status. |
| `verification_result` | string | `pass`, `fail`, `unsupported`, or `not_checked`. |
| `receipt_result` | string | `acknowledged`, `ignored`, `verification_failed`, or `stale`. |
| `reason_codes` | array<string> | Machine-readable reasons. |

`Inference`: receipts let Barcarolle prove which status watermark a consumer acknowledged or failed to acknowledge. They do not create runtime control over the consumer.

### 4.17e License consumption audit event

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `license_consumption_audit_event_id` | string | Opaque audit identity. |
| `consumer` | object | Consumer identity, version, and integration/environment id. |
| `operation_correlation_id` | string | Consumer-side operation or request correlation id. |
| `decided_at` | datetime | When the consumer made the local decision. |
| `repository_id` | string | Repository requested by the consumer. |
| `requested_scope` | object | Requested path/module/task-family/resource scope. |
| `requested_operation` | string | Requested operation. |
| `requested_risk_class` | string | Requested risk class. |
| `requested_target_condition_basis_identity` | string | Requested target condition. |
| `requested_capability_envelope_digest` | string | Requested capability envelope digest. |
| `requested_tested_agent_snapshot_id` | string | Snapshot the consumer believed it was operating. |
| `requested_admission_subject` | string | Requested admission subject. |
| `result` | string | `allow`, `deny`, `not_barcarolle_conformant`, `hold_for_review`, `require_targeted_validation`, or `require_full_rebenchmark`. |
| `reason_codes` | array<string> | Machine-readable reasons. |
| `local_policy_overlay_result` | object | Consumer-side policy result kept separate from Barcarolle tier semantics. |
| `license_certificate_id` | string | Certificate used by the consumer, if any. |
| `certificate_digest` | string | Certificate digest used by the consumer. |
| `certificate_signing_key_id` | string | Certificate signing key the consumer verified. |
| `certificate_signing_key_status_ref` | string | Key-status record the consumer used when verifying the certificate, if any. |
| `certificate_signing_key_status_digest` | string | Digest of the key-status material used for the certificate, if any. |
| `certificate_signature_verification_result` | string | `pass`, `fail`, `unsupported`, or `not_checked`. |
| `license_status_id` | string | Status record used by the consumer, if any. |
| `status_digest` | string | Status digest used by the consumer. |
| `status_sequence` | integer | Status sequence seen by the consumer. |
| `status_watermark` | object | Status watermark seen by the consumer. |
| `status_signing_key_id` | string | Status signing key the consumer verified. |
| `status_signing_key_status_ref` | string | Key-status record used when verifying the signed status, if any. |
| `status_signing_key_status_digest` | string | Digest of the status-key material used, if any. |
| `status_signature_verification_result` | string | `pass`, `fail`, `unsupported`, or `not_checked`. |
| `repository_agent_admission_id` | string | Admission identity used, if any. |
| `repository_agent_operating_state_id` | string | Operating-state identity used, if any. |
| `coverage_entry_id` | string | Coverage entry used, if any. |
| `admission_lifecycle_sequence` | integer | Lifecycle sequence seen by the consumer. |
| `operating_state_version` | integer | Operating-state version seen by the consumer. |
| `event_stream_watermark` | object | Watermark seen by the consumer. |
| `granted_trust_tier` | string | Granted tier used in the consumer decision, nullable when no certificate/status or coverage entry was available. |
| `admission_status` | string | Admission status used in the consumer decision, nullable when unknown. |
| `freshness_state` | string | Freshness state used in the consumer decision, nullable when unknown. |
| `freshness_deadline` | datetime | Freshness deadline used in the consumer decision, nullable when unknown. |
| `certificate_validity` | object | `certificate_valid_not_before`, nullable `certificate_valid_not_after`, optional `renew_after`, and validity-profile basis used by the consumer. |
| `status_freshness` | object | `max_status_staleness`, `status_fresh_until`, and optional `next_status_poll_after` used by the consumer. |
| `evidence_lineage` | string | `fresh`, `reused`, or `supplemented` basis used in the consumer decision, nullable when no certificate or entry was available. |
| `risk_profile_basis` | object | Risk-profile basis copied from the certificate/status or matched coverage entry. |
| `policy_gate_basis` | object | Policy gate basis/results copied from the certificate/status or matched coverage entry. |
| `failure_mode` | string | Stale cache, read failure, certificate signature failure, status signature failure, lifecycle mismatch, status-watermark mismatch, scope mismatch, target-condition mismatch, capability mismatch, or another explicit cause. |

`Inference`: audit events explain consumer behavior and support conformance review. They do not make Barcarolle a runtime enforcement plane and must not mutate admissions, scorecards, or operating state.

### 4.18 Evidence bundle and artifact

Stable fields for the bundle:

| Field | Type | Notes |
| --- | --- | --- |
| `evidence_bundle_id` | string | Opaque identity for one immutable sealed bundle version. |
| `subject_type` | string | Bundle subject class, such as `candidate_generation_run`, `task_candidate`, `validation_result`, `leakage_report`, `task`, `task_retirement`, `release_maintenance_finding`, `environment`, `evaluation_run`, `run_submission`, or `canonical_verification_record`. |
| `subject_id` | string | Opaque identity of the subject resource. |
| `candidate_generation_run_id` | string | Pre-candidate generation-run subject, when applicable. |
| `task_candidate_id` | string | Candidate subject, when applicable. |
| `validation_result_id` | string | Validation result subject, when applicable. |
| `task_id` | string | Task subject, when applicable. |
| `run_id` | string | Evaluation-run subject, when applicable. |
| `environment_id` | string | Replay-environment subject, when applicable. |
| `run_submission_id` | string | Submission linked to this bundle, if applicable. |
| `canonical_verification_record_id` | string | Canonical verification linked to this bundle, if applicable. |
| `bundle_kind` | string | Logical evidence bundle series type, such as runner, submission, canonical verification, judge, or aggregate. |
| `bundle_series_key` | string | Stable series key, normally `subject_type + subject_id + bundle_kind`; this is not the immutable row identity. |
| `manifest_version` | integer | Monotonic sealed manifest version inside the bundle series. Backfill or repair writes a new version. |
| `manifest_ref` | object | Bundle manifest or index. |
| `content_digest` | string | Digest of this sealed manifest version. |
| `supersedes_evidence_bundle_id` | string | Optional earlier sealed bundle version this version supersedes for current/latest views. |
| `artifact_refs` | array<object> | Logs, patches, transcripts, verifier outputs, and environment captures. |
| `evidence_trust_tier_summary` | object | Counts and digests grouped by evidence trust tier. |
| `score_contribution_summary` | object | Which artifacts can contribute to scoring versus audit only. |
| `retention_state` | string | Retained, archived, or tombstoned state. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Stable fields for an artifact:

| Field | Type | Notes |
| --- | --- | --- |
| `artifact_id` | string | Opaque artifact identity. |
| `artifact_type` | string | Log, patch, transcript, verifier output, image digest, or similar. |
| `evidence_producer` | object | Barcarolle component, adapter, agent, or third-party producer identity. |
| `evidence_trust_tier` | string | One `EvidenceTrustTier` value. |
| `source_class` | string | Source class such as task digest, canonical verifier log, wrapper observation, native trace, CI result, provider report, or artifact signature. |
| `content_ref` | object | Blob location or inline content reference. |
| `checksum` | string | Integrity checksum. |
| `provenance` | object | Source and capture metadata. |
| `summary_ref` | object | Summary-safe metadata or summary artifact returned by default when the full artifact is not blind-safe. |
| `contribution_mode` | string | Optional contribution classification. Judge-side scoring artifacts should use stable values such as `advisory` or `score_contributing`; Golden-side refs may omit it when not relevant. |
| `score_contributing` | boolean | Whether this artifact can affect score under the active policy. Agent-submitted traces default to false for correctness. |
| `redaction_state` | string | `none`, `summary_only`, or `redacted`. |
| `sensitivity_label` | string | Stable sensitivity class such as blind-safe summary, restricted review, or answer-bearing reference. |
| `audience_scope` | array<string> | Allowed audiences for full artifact reads, such as validation reviewers, scoring reviewers, governance reviewers, or sensitive-evidence readers. |
| `blind_safe` | boolean | Whether the artifact is safe to expose beyond summary form without compromising blind evaluation. |
| `default_access` | string | `summary_only` by default for non-blind-safe artifacts; `full` only when the artifact is blind-safe and audience policy allows. |
| `created_at` | datetime | Audit field. |

Later fields:

- `expiration_time`

`golden_artifact_refs` and `judge_artifact_refs` should reuse this controlled artifact-ref shape rather than an unconstrained object.

For a given `subject_type + subject_id + bundle_kind`, `manifest_version` forms an append-only version sequence. `GetEvidenceBundle` may resolve current/latest for browsing by selecting the highest sealed version in the series, but scoring, Judge assessment, canonical verification, scorecards, and authorization explanations must store and read exact `evidence_bundle_id`, `manifest_version`, and `content_digest` values. They must not reinterpret an old score against the latest bundle version. Pre-candidate Golden discovery artifacts must use `candidate_generation_run` as the subject so evidence storage does not depend on a not-yet-created `task_candidate_id`. After the candidate exists, Golden validation artifacts may use `task_candidate` or `validation_result` subjects so pre-approval evidence does not need a nonexistent `task_id`.

For Judge-produced refs, callers should be able to tell whether the attachment is advisory or score-contributing. Advisory refs do not split canonical score or scorecard identity unless the enclosing score record also carries a score-basis `judge_configuration_id`. Agent-submitted traces can inform Judge audit findings and confidence, but they cannot be score-contributing correctness evidence without a Barcarolle trusted canonical verification record.

### 4.19 Admission review record

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `admission_review_id` | string | Opaque admission-review identity. |
| `review_subject_kind` | string | `task_candidate`, `validation_result`, `benchmark_release`, `task_retirement`, `release_maintenance_finding`, or another governed review subject. |
| `task_candidate_id` | string | Optional candidate under review. Required when `review_subject_kind = task_candidate`. |
| `validation_result_id` | string | Optional validation record that informed the review. |
| `benchmark_release_id` | string | Optional release under certification or maintenance review. |
| `task_retirement_id` | string | Optional retirement/quarantine finding under review. |
| `release_maintenance_finding_id` | string | Optional release-maintenance or post-release invalidation finding under review. |
| `review_required` | boolean | Whether governance review was routed for this candidate state. |
| `review_state` | string | `pending`, `approved`, `rejected`, `repair_required`, `waived_warning`, or `retired`. `not_required` is valid only on candidate projections, not on append-only review records. |
| `compliance_state` | string | `compliant`, `missing_required_review`, or another stable compliance label. |
| `deterministic_gate_summary` | object | Benchmark-admission gate, oracle, leakage, release-coverage, or invalidation summary that triggered review. |
| `review_reason_codes` | array<string> | Structured reason codes such as suspected leakage, high-risk permission, B-oracle high-impact scope, duplicate pressure, flakiness near threshold, or release unsupported-scope review. |
| `required_fixes` | array<object> | Fixes required before approval or publication can proceed. |
| `waived_warning_codes` | array<string> | Non-hard warnings accepted with rationale. Hard failures are not valid waiver targets. |
| `reviewer_id` | string | Human reviewer identity. |
| `reviewed_at` | datetime | When the review action was recorded. |
| `rationale_summary` | string | Human-readable justification. |
| `notes` | string | Optional longer reviewer notes. |
| `supersedes_review_id` | string | Prior review record superseded by this one, if any. |

Hard failures such as confirmed future/answer leakage, no faithful replay, and D-grade sole oracle cannot be waived into certified task status.

`repair_required` review records must populate `required_fixes[]` and block approval until a repair creates a new validation or release-certification basis. `waived_warning` review records must populate `waived_warning_codes[]` and may only waive non-hard warnings under a bounded scope and rationale.

### 4.19a Task retirement

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `task_retirement_id` | string | Opaque retirement or quarantine identity. |
| `task_id` | string | Approved task affected by the finding. |
| `task_candidate_id` | string | Optional source candidate when the finding applies before approval or to candidate provenance. |
| `retirement_reason` | string | `leakage_confirmed`, `oracle_invalid`, `oracle_weakened`, `flaky_over_threshold`, `environment_unreplayable`, `duplicate_overweight`, `source_provenance_invalid`, `policy_retired`, or another policy-defined reason. |
| `invalidation_severity` | string | `advisory`, `quarantine`, `scorecard_invalidating`, or `admission_invalidating`. |
| `leakage_kind` | array<string> | Leakage categories when retirement is leakage-related. |
| `leakage_severity` | string | `none`, `minor_redactable`, `suspected`, or `confirmed` when retirement is leakage-related. |
| `leakage_handling_decision` | string | `quarantine` or `retire` for leakage-related retirement; absent for non-leakage causes. |
| `acut_visible_surfaces` | array<object> | Machine-readable surfaces affected by leakage, when applicable. |
| `leakage_report_ref` | object | Exact leakage report ref when retirement is leakage-related. |
| `leakage_report_digest` | string | Digest of the exact leakage report. |
| `finding_source` | object | Human review, automated scan, Judge escalation, verifier repair, or incident source. |
| `evidence_refs` | array<object> | Evidence bundle, validation, release, scorecard, or review refs supporting the finding. |
| `affected_release_membership_refs` | array<object> | Release-membership rows affected by this finding. |
| `affected_scorecard_refs` | array<object> | Scorecards requiring warning, replacement, or invalidation. |
| `affected_authorization_decision_refs` | array<object> | Decisions whose basis is narrowed, blocked, or invalidated. |
| `affected_repository_agent_admission_refs` | array<object> | Admissions requiring review, suspension, revocation, renewal, targeted validation, or rebenchmark. |
| `replacement_task_id` | string | Optional replacement task that supersedes this task in a later release. |
| `repair_ticket_ref` | object | Optional repair workflow or manual ticket reference. |
| `reviewer_notes` | string | Reviewer or operator notes. |
| `retired_at` | datetime | When the finding became effective. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Retirement and quarantine do not edit historical benchmark releases. They prevent future certified membership, drive new scorecards or releases when needed, and route admission-impacting findings to suspension or revocation on repository-agent admissions.

### 4.19b Release maintenance finding

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `release_maintenance_finding_id` | string | Opaque post-release maintenance or invalidation finding identity. |
| `subject_kind` | string | `benchmark_release`, `benchmark_release_membership`, `benchmark_scorecard`, `authorization_decision`, `repository_agent_admission`, or `release_coverage_profile`. |
| `subject_ref` | object | Exact subject identity and digest or version where applicable. |
| `benchmark_release_id` | string | Release affected by the finding. |
| `finding_type` | string | `post_release_leakage`, `oracle_invalidation`, `coverage_drift`, `evidence_corruption`, `policy_change`, or `scope_unsupported`. |
| `cause_code` | string | Policy-defined cause, aligned with task-retirement reasons where a task-level cause exists. |
| `invalidation_severity` | string | `advisory`, `quarantine`, `scorecard_invalidating`, or `admission_invalidating`. |
| `leakage_kind` | array<string> | Leakage categories when the finding is leakage-related. |
| `leakage_severity` | string | `none`, `minor_redactable`, `suspected`, or `confirmed` when leakage-related. |
| `leakage_handling_decision` | string | `requires_review`, `quarantine`, or `retire` for leakage-related post-release handling. |
| `acut_visible_surfaces` | array<object> | Machine-readable surfaces affected by leakage, when applicable. |
| `leakage_report_ref` | object | Exact leakage report ref when the finding is leakage-related. |
| `leakage_report_digest` | string | Digest of the exact leakage report. |
| `evidence_refs` | array<object> | Evidence bundle, validation, release, scorecard, review, or incident refs supporting the finding. |
| `affected_release_membership_refs` | array<object> | Release-membership rows affected by this finding. |
| `affected_scorecard_refs` | array<object> | Scorecards requiring warning, replacement, or invalidation. |
| `affected_authorization_decision_refs` | array<object> | Decisions whose basis is narrowed, blocked, or invalidated. |
| `affected_repository_agent_admission_refs` | array<object> | Admissions requiring review, suspension, revocation, renewal, targeted validation, or rebenchmark. |
| `required_next_actions` | array<object> | Required actions such as targeted validation, new scorecard, full rebenchmark, suspension, revocation, or superseding release. |
| `finding_status` | string | `open`, `under_review`, `applied`, `superseded`, or `closed`. |
| `review_required` | boolean | Whether governance review is required for this finding. |
| `latest_admission_review_id` | string | Latest admission-review record governing this finding, if any. |
| `effective_at` | datetime | When the finding affects authorization interpretation. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

`Inference`: task-specific quarantine and retirement use `task_retirement`. Release-wide, scorecard-wide, authorization-decision, repository-admission, or release-coverage invalidation uses `release_maintenance_finding` with an explicit `subject_kind`. Scorecards, authorization decisions, admissions, and operating-state projections may reference either resource in `invalidation_refs`.

### 4.20 Governed assessor configuration

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `assessor_configuration_id` | string | Opaque governed configuration identity. |
| `configuration_fingerprint` | string | Backend-recomputed natural key digest over material assessor configuration fields. |
| `assessor_kind` | string | `golden` or `judge`. |
| `repository_scope` | object | Repository or narrower scope where this version is governed. |
| `model_ref` | object | Model/provider identity. |
| `prompt_digest` | string | Digest of system prompt or rubric content. |
| `tool_profile_digest` | string | Digest of tool and permission profile. |
| `memory_strategy_digest` | string | Digest of retrieval or memory configuration when relevant. |
| `runtime_policy_digest` | string | Digest of runtime budget and retry posture. |
| `output_schema_version` | string | Output contract version expected from this configuration. |
| `governance_state` | string | `candidate`, `shadow`, `advisory`, `active`, `superseded`, or `rolled_back`. |
| `predecessor_configuration_id` | string | Prior governed version in the lineage, if any. |
| `comparison_baseline_id` | string | Baseline version used for current comparison or promotion review, if any. |
| `promotion_review_id` | string | Admission or governance review record that promoted or rolled back the version, if any. |
| `comparison_summary_ref` | object | Summary artifact describing offline or shadow comparison outcome. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

`Inference`: `configuration_fingerprint` is derived by the backend from the governed model, prompt, tool profile, memory strategy, runtime policy, output schema, and assessor-role descriptors. Callers may supply an expected fingerprint for idempotency, but a mismatch with backend recomputation must be rejected. Any material configuration change creates a new `assessor_configuration_id`; lifecycle transitions only move the registered configuration through governance states.

### 4.21 Policy calibration run

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `policy_calibration_run_id` | string | Opaque calibration attempt identity. |
| `repository_scope` | object | Repository or narrower scope being calibrated. |
| `target_policy_families` | array<string> | Policy families or surfaces being calibrated, such as authorization thresholds, scorecard weights, coverage gates, or reliability labels. |
| `trigger_kind` | string | `scheduled`, `release_published`, `scorecard_volume`, `variance_drift`, `maintenance_finding`, `profile_expiring`, or `operator_requested`. |
| `run_attempt_number` | integer | Semantic calibration attempt for the same manifest basis. |
| `predecessor_profile_refs` | array<object> | Active or shadow profiles used as the comparison baseline. |
| `repository_risk_profile_id` | string | Effective risk-profile identity or seed basis consumed by this calibration run. |
| `risk_profile_version` | string | Risk-profile version used for the run. |
| `risk_profile_digest` | string | Digest of the effective risk-profile constraints. |
| `risk_constraint_summary` | object | Queryable constraints used as hard bounds and objective weights for calibration. |
| `calibration_input_manifest_ref` | object | Exact manifest of releases, scorecards, canonical verification records, controls, baselines, and slices consumed. |
| `calibration_input_manifest_digest` | string | Digest of the exact calibration input manifest. |
| `calibration_truth_contract_version` | string | Version of the observation semantics used to classify positive controls, negative controls, safety controls, unsupported-scope controls, and invalidation controls. |
| `truth_observation_manifest_ref` | object | Manifest or query handle for `calibration_truth_observation` entries consumed by the run. |
| `truth_observation_manifest_digest` | string | Digest over normalized truth observations, expected policy effects, semantic slices, source refs, and exclusions. |
| `truth_observation_summary` | object | Counts and coverage by observation kind, truth basis kind, semantic slice, split, and exclusion reason. |
| `evidence_slice_coverage_summary` | object | Coverage by release, task family, component/path, risk class, permission class, high-impact path class, oracle grade, mode, purity, and evidence trust basis. |
| `excluded_slice_summary` | object | Slices excluded because objective evidence was insufficient or human truth would be required. |
| `control_baseline_summary` | object | No-op, mutation, known pre-fix, retrieval-only, rule-based, weak baseline, and prior-agent control coverage. |
| `high_tier_authorization_control_summary` | object | Positive, negative, safety, stability, and coverage-control power for claimed `G4`/`G5` applicability slices, including blocked or shadow-only slices. |
| `repeated_run_variance_summary` | object | Variance and confidence summaries used for reliability calibration. |
| `unsafe_false_positive_summary` | object | Observed unsafe false-positive counts, weighted rates, confidence upper bounds, severity classes, and budget keys by tier/slice. |
| `positive_control_false_negative_summary` | object | Positive-control misses and overly restrictive outcomes used for usefulness/cost optimization. |
| `risk_budget_consumption_summary` | object | Unsafe-control promotion rates, separation margins, forbidden-tier checks, and constrained-slice status. |
| `sensitivity_analysis_refs` | array<object> | Parameter perturbation and outcome-flip analysis refs. |
| `candidate_profile_refs` | array<object> | Candidate calibrated policy profiles produced by the run. |
| `selected_profile_ref` | object | Profile selected for promotion or shadowing when gates pass. |
| `promotion_gate_summary` | object | Machine-checkable gate results and blockers. |
| `status` | string | `requested`, `gathering_evidence`, `generating_controls`, `running_baselines`, `fitting_profiles`, `validating_profiles`, `completed`, `failed`, `blocked`, or `canceled`. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Calibration runs are automatic. They must not accept human baselines, human labels, risk-profile edits, or manual benchmark acceptance as normal calibration truth. The risk profile constrains optimization and false-positive budgets; it does not supply objective observation labels.

### 4.21a Calibration truth observation

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `calibration_truth_observation_id` | string | Opaque observation identity, or a manifest-local stable key when returned through a manifest page. |
| `policy_calibration_run_id` | string | Calibration run that consumed the observation. |
| `observation_kind` | string | `positive_control`, `negative_control`, `safety_control`, `baseline_result`, `prior_agent_result`, `variance_sample`, `coverage_gap`, or `maintenance_invalidation`. |
| `truth_basis_kind` | string | Objective basis such as `post_fix_canonical_positive`, `known_pre_fix_negative`, `trusted_policy_violation_negative`, `unsupported_scope_negative`, or `invalidation_control`. |
| `source_refs` | array<object> | Task, release, run, scorecard, canonical verification, maintenance finding, evidence bundle, or generated-control refs. |
| `expected_policy_effect` | string | `should_score_positive`, `should_not_score_positive`, `must_not_authorize_above_tier`, `must_block_authorization`, `must_require_targeted_validation`, `must_require_full_rebenchmark`, or `diagnostic_only`. |
| `expected_maximum_safe_tier` | string | Highest tier allowed by the objective control, when applicable. |
| `semantic_slice` | object | Task family, component/path, risk class, permission class, high-impact path class, mode, purity, capability envelope, evidence basis, and target condition. |
| `truth_confidence_basis` | object | Verifier, canonical verification, certified release, trusted policy evidence, maintenance finding, variance, or baseline/control-run lineage. |
| `split` | string | `fit`, `validation`, `held_out`, or `diagnostic`. |
| `exclusion_status` | string | `included`, `excluded`, or `blocked`. |
| `exclusion_reason_codes` | array<string> | Reasons such as `requires_human_truth`, `undercovered_slice`, `unresolved_leakage`, or `insufficient_control_power`. |
| `unsafe_false_positive_result` | object | Candidate-policy replay result, severity, budget key, and unsafe false-positive boolean when applicable. |

Truth observations are calibration measurement records. They are not risk-profile appetite records, human review labels, or runtime enforcement state.

### 4.22 Calibrated policy profile

Stable fields:

| Field | Type | Notes |
| --- | --- | --- |
| `calibrated_policy_profile_id` | string | Opaque calibrated profile identity. |
| `semantic_policy_family` | string | Semantic family such as `authorization_semantics_v1`. |
| `repository_scope` | object | Repository or narrower scope where the profile applies. |
| `applicability_slices` | object | Slices covered by the profile. Under-covered slices must remain excluded or blocked. |
| `predecessor_profile_id` | string | Prior active or shadow profile in the lineage. |
| `policy_calibration_run_id` | string | Calibration run that produced the profile. |
| `repository_risk_profile_id` | string | Effective risk-profile identity or seed basis under which this profile is valid. |
| `risk_profile_version` | string | Risk-profile version used by the profile. |
| `risk_profile_digest` | string | Digest of effective risk-profile constraints. |
| `risk_constraint_summary` | object | Hard constraints and objective weights that bounded optimization. |
| `authorization_policy_version` | string | Exact authorization policy version governed by this profile. |
| `scorecard_policy_version` | string | Exact scorecard policy version governed by this profile. |
| `coverage_policy_version` | string | Exact coverage policy version governed by this profile. |
| `release_admission_policy_version` | string | Exact release-admission policy version governed by this profile, when applicable. |
| `reliability_policy_version` | string | Exact reliability-label policy version governed by this profile. |
| `parameter_ref` | object | Full parameter artifact ref. |
| `parameter_digest` | string | Digest over threshold, weighting, coverage, reliability, and promotion parameters. |
| `evidence_manifest_digest` | string | Digest of the calibration manifest used to fit the profile. |
| `calibration_truth_contract_version` | string | Observation semantics used by the producing run. |
| `truth_basis_digest` | string | Digest over the truth-observation manifest and exclusion decisions used for fitting and promotion. |
| `truth_observation_summary` | object | Observation coverage and exclusion summary inherited from the producing run. |
| `validation_summary` | object | Objective-control, held-out, variance, and non-regression metrics. |
| `unsafe_false_positive_metrics` | object | Tier/slice unsafe false-positive rates, confidence upper bounds, severities, and budget pass/fail results. |
| `high_tier_authorization_applicability_summary` | object | `G4`/`G5` applicability, blocked slices, shadow-only slices, and targeted-validation requirements. |
| `parameter_authority_summary` | object | Marks each parameter as `seed_default`, `evidence_fit`, `constraint_bound`, `shadow_only`, or `blocked`. |
| `risk_budget_consumption_summary` | object | How candidate thresholds/weights consume the effective risk profile's risk budgets. |
| `sensitivity_summary_refs` | array<object> | Sensitivity analysis refs. |
| `impact_preview_refs` | array<object> | Scorecard, decision, admission, and operating-state impact previews. |
| `promotion_gate_results` | object | Machine-checkable gates used for profile lifecycle. |
| `lifecycle_state` | string | `candidate`, `shadow`, `active`, `paused`, `superseded`, `rolled_back`, or `blocked`. |
| `activated_at` | datetime | Activation timestamp when profile becomes active. |
| `created_at` | datetime | Audit field. |
| `created_by` | string | Producer identity. |

Profiles are append-only parameter bundles. Scorecards and decisions copy exact profile refs or policy versions; later profile changes do not reinterpret old facts.

## 5. Command and Query Payloads

### 5.1 Repository intake

#### `RegisterRepositorySnapshot`

Request:

- `repository_id`
- `provider`
- `repository_slug`
- `source_revision`
- `snapshot_time`
- `import_mode`
- `artifact_refs`
- `provenance`

Response:

- `snapshot_id`
- `status`
- `snapshot`

#### `GetRepositorySnapshot`

Request:

- `repository_id`
- one of `snapshot_id`, `source_revision`, or another selector accepted by the read model

Response:

- `snapshot`

#### `ListRepositorySnapshots`

Request:

- `repository_id`
- optional filters: `source_revision`, `snapshot_time_from`, `snapshot_time_to`, `import_mode`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`
- `total_count` when available

### 5.2 Task candidate creation

#### `ReserveCandidateGenerationRun`

Request:

- `repository_id`
- `snapshot_id`
- `generation_strategy`
- `signal_input_manifest_digest`
- optional `golden_configuration_id`
- required `golden_input_manifest_digest` when `golden_configuration_id` is present
- `selection_policy_version`
- `run_attempt_number`

Response:

- `candidate_generation_run_id`
- `candidate_generation_run`

This command reserves the pre-candidate generation attempt and gives Golden discovery/selection artifacts a stable evidence subject before any `task_candidate` exists. Its natural key is `repository_id + snapshot_id + generation_strategy + signal_input_manifest_digest + selection_policy_version + optional golden_configuration_id + optional golden_input_manifest_digest + run_attempt_number`.

#### `CompleteCandidateGenerationRun`

Request:

- `candidate_generation_run_id`
- optional `golden_output_evidence_bundle_id`
- optional `golden_output_manifest_version`
- optional `golden_output_content_digest`
- completion status such as `completed`, `failed`, or `superseded`
- optional completion summary and failure cause
- `selected_output_digest` and `selection_ranking_identity` when completion status is `completed`

Response:

- `candidate_generation_run_id`
- `completion_event_id`
- `candidate_generation_run`

This command appends completion metadata after deterministic or Golden-assisted discovery finishes and any Golden evidence bundle is sealed. It does not change the reservation natural key. `selected_output_digest` and `selection_ranking_identity` are required only for `completed` status. `failed` or `superseded` completions may omit selected-output fields, but must carry a failure cause or completion summary and may attach evidence-bundle refs for audit. A replay of the same completion metadata is idempotent; a different selected output digest, selection identity, or evidence-bundle ref for the same reserved run is `policy_conflict` unless the caller creates a new semantic attempt number. If Golden materially influenced discovery, selection, or contract synthesis, later `CreateTaskCandidate` requests must reference this run and the exact selected output digest or evidence bundle version in `generation_context_lineage`.

#### `CreateTaskCandidate`

Request:

- `snapshot_id`
- optional `candidate_generation_run_id`
- `generation_context_lineage`
- optional Golden-assisted discovery/selection/contract-synthesis refs, including `candidate_generation_run_id`, `golden_configuration_id`, input-manifest digest, selected output digest, exact evidence-bundle version/content digest, and selection/ranking identity when Golden materially contributed
- `signal_refs`
- `task_family`
- `source_anchor`
- `problem_statement` or candidate draft text
- `context_refs`
- `expected_oracle`
- `contamination_hints`
- optional preliminary leakage summary fields: `leakage_kind`, `leakage_severity`, `leakage_handling_decision`, `leakage_review_required`, `acut_visible_surfaces`, `leakage_report_ref`, and `leakage_report_digest`

Response:

- `task_candidate_id`
- `status`
- `task_candidate`

Pre-candidate Golden refs must come through a completed `candidate_generation_run`; `task_candidate` or `validation_result` evidence subjects are only valid after the candidate exists.

#### `GetCandidateGenerationRun`

Request:

- `candidate_generation_run_id`

Response:

- `candidate_generation_run`
- exact output evidence-bundle refs when completed
- candidate refs created from this generation run, when any exist

#### `ListCandidateGenerationRuns`

Request:

- `repository_id`
- optional `snapshot_id`
- optional `golden_configuration_id`
- optional `status`
- optional created-at range
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

This query must include generation runs that never produced a task candidate, so Golden-assisted discovery and rejected/weak selection attempts remain independently auditable.

#### `GetTaskCandidate`

Request:

- `task_candidate_id`

Response:

- `task_candidate`

#### `ListTaskCandidates`

Request:

- `repository_id`
- optional filters: `snapshot_id`, `status`, `task_family`, `review_state`, `review_required`, `compliance_state`, `leakage_severity`, `leakage_kind`, `leakage_handling_decision`, `leakage_review_required`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`
- `total_count` when available

#### `ApproveTaskCandidate`

Request:

- `task_candidate_id`
- `validation_result_id`
- `task_admission_policy_result_ref` or `task_admission_policy_result_digest`
- optional `admission_review_id` when approval carries a governance annotation, warning waiver, override, or exceptional policy path
- `decision_note`
- optional `reviewer_override`

Normal approval requires an automated policy result that certifies the candidate. `review_required` is governance routing metadata, not a normal benchmark-acceptance prerequisite. `repair_required`, `pending`, `rejected`, and `retired` governance states block normal approval until repair and revalidation produce a new certifying policy result. An exceptional governance override may be recorded, but that path is excluded from normal calibration evidence unless a later objective validation basis certifies it.

Response:

- `task_id`
- `status`
- `task`
- `approval_record` using the stable admission-review-record shape

#### `CreateAdmissionReviewRecord`

Request:

- `review_subject_kind`
- one subject identity such as `task_candidate_id`, `validation_result_id`, `benchmark_release_id`, `task_retirement_id`, or `release_maintenance_finding_id`
- `reviewer_id`
- `review_state`
- `compliance_state`
- optional `deterministic_gate_summary`
- optional `review_reason_codes`
- optional `required_fixes`
- optional `waived_warning_codes`
- `rationale`
- optional `supersedes_admission_review_id`

Response:

- `admission_review_id`
- `admission_review`

`review_state = repair_required` requires non-empty `required_fixes[]`. `review_state = waived_warning` requires non-empty `waived_warning_codes[]` and cannot target hard failures such as confirmed leakage, no faithful replay, or D-grade sole oracle.

#### `RetireTaskCandidate`

Request:

- `task_candidate_id`
- `retirement_cause`
- `evidence_refs`

Response:

- `status`
- `retirement_record`

#### `RetireTask`

Request:

- `task_id`
- `retirement_cause`
- `invalidation_severity`
- optional leakage summary fields: `leakage_kind`, `leakage_severity`, `leakage_handling_decision`, `acut_visible_surfaces`, `leakage_report_ref`, and `leakage_report_digest`
- `finding_source`
- `evidence_refs`
- optional `affected_release_membership_refs`
- optional `affected_scorecard_refs`
- optional `affected_authorization_decision_refs`
- optional `affected_repository_agent_admission_refs`
- optional `replacement_task_id`
- optional `repair_ticket_ref`
- `reviewer_id`
- `rationale`

Response:

- `task_retirement_id`
- `task_retirement`
- `invalidation_impact_summary`

#### `CreateReleaseMaintenanceFinding`

Request:

- `subject_kind`
- `subject_ref`
- `benchmark_release_id`
- `finding_type`
- `cause_code`
- `invalidation_severity`
- optional leakage summary fields: `leakage_kind`, `leakage_severity`, `leakage_handling_decision`, `acut_visible_surfaces`, `leakage_report_ref`, and `leakage_report_digest`
- `evidence_refs`
- optional `affected_release_membership_refs`
- optional `affected_scorecard_refs`
- optional `affected_authorization_decision_refs`
- optional `affected_repository_agent_admission_refs`
- optional `required_next_actions`
- `finding_status`
- `review_required`
- optional `latest_admission_review_id`
- `effective_at`
- `reviewer_id`
- `rationale`

Response:

- `release_maintenance_finding_id`
- `release_maintenance_finding`
- `invalidation_impact_summary`

#### `GetReleaseMaintenanceFinding`

Request:

- `release_maintenance_finding_id`

Response:

- `release_maintenance_finding`

#### `ListReleaseMaintenanceFindings`

Request:

- one of `benchmark_release_id`, `benchmark_scorecard_id`, `authorization_decision_id`, `repository_agent_admission_id`, or `repository_id`
- optional filters: `subject_kind`, `finding_type`, `cause_code`, `invalidation_severity`, `finding_status`, `leakage_severity`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetAdmissionReviewRecord`

Request:

- `admission_review_id`

Response:

- `admission_review`

#### `ListAdmissionReviewRecords`

Request:

- one of `task_candidate_id`, `validation_result_id`, `release_maintenance_finding_id`, or `repository_id`
- optional filters: `review_state`, `review_required`, `compliance_state`, `reviewer_id`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.3 Replay planning

#### `PlanReplayEnvironment`

Request:

- `task_candidate_id`
- `base_revision`
- `dependency_clues`
- optional `verifier_preference`
- optional `fidelity_policy`

Response:

- `replay_plan_id`
- `feasibility_status`
- `replay_plan`

#### `GetReplayPlan`

Request:

- `replay_plan_id`

Response:

- `replay_plan`

#### `ListReplayPlans`

Request:

- one of `task_candidate_id` or `task_id`
- optional filters: `feasibility_status`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `BuildReplayEnvironment`

Request:

- `replay_plan_id`
- `build_policy`
- optional `resource_limits`

Response:

- `environment_id`
- `build_status`
- `build_artifacts`

#### `GetReplayEnvironment`

Request:

- `environment_id`

Response:

- `environment`

#### `ListReplayEnvironments`

Request:

- one of `task_candidate_id`, `task_id`, or `replay_plan_id`
- optional filters: `build_status`, `reproducibility_label`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `ValidateReplayEnvironment`

Request:

- `environment_id`
- `task_candidate_id`
- optional `validation_policy`

Response:

- `validation_result_id`
- `validity_decision`
- `reproducibility_label`
- `failure_cause` when rejected
- optional `golden_artifact_refs`
- `validation_result`

`golden_artifact_refs` should default to summary-only expansions when the referenced artifacts are not blind-safe for the caller's audience.

#### `GetValidationResult`

Request:

- `validation_result_id`

Response:

- `validation_result`

#### `ListValidationResults`

Request:

- one of `task_candidate_id`, `task_id`, or `environment_id`
- optional filters: `validity_decision`, `validation_kind`, `leakage_severity`, `leakage_kind`, `leakage_handling_decision`, `leakage_review_required`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetLeakageReport`

Request:

- `leakage_report_id`

Response:

- `leakage_report`

#### `ListLeakageReports`

Request:

- one of `task_candidate_id`, `validation_result_id`, `task_id`, `release_maintenance_finding_id`, or `repository_id`
- optional filters: `subject_kind`, `leakage_severity`, `leakage_kind`, `handling_decision`, `review_required`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.4 Approved task registry

#### `GetTask`

Request:

- `task_id`

Response:

- `task`

#### `ListTasks`

Request:

- `repository_id`
- optional filters: `task_candidate_id`, `status`, `task_family`, `retirement_marker`, `approved_at_from`, `approved_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`
- `total_count` when available

### 5.5 Benchmark registry and release publication

#### `GetBenchmarkDefinition`

Request:

- `benchmark_definition_id`

Response:

- `benchmark_definition`

#### `ListBenchmarkDefinitions`

Request:

- `repository_id`
- optional filters: `scope`, `status`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `PublishBenchmarkRelease`

Request:

- `benchmark_definition_id`
- one of `task_ids[]` or `publication_rule`
- `release_label`
- `publication_rationale`
- optional `source_snapshot_id`
- optional `publication_policy`

Response:

- `benchmark_release_id`
- `publication_status`
- `benchmark_release`

#### `GetBenchmarkRelease`

Request:

- `benchmark_release_id`

Response:

- `benchmark_release`

#### `ListBenchmarkReleases`

Request:

- `benchmark_definition_id`
- optional filters: `publication_status`, `published_at_from`, `published_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.6 Tested-agent snapshots and evolution governance

#### `RegisterTestedAgentSnapshot`

Request:

- `repository_scope`
- `snapshot_fingerprint`
- optional `agent_configuration_id`
- `snapshot_kind`
- `subject_label`
- `model_ref`
- `prompt_digest`
- `tool_profile_digest`
- `permission_profile_digest`
- `memory_strategy_digest`
- `runtime_policy_digest`
- `control_loop_digest`
- `run_environment_declaration`
- `adapter_manifest`
- `evaluation_mode`
- `adapter_purity_level`
- `acut_field_evidence_basis`
- `canonical_artifact_refs`
- `provenance`

Rules:

- `acut_field_evidence_basis` must cover every material ACUT field required by the contract and use only `ACUTFieldEvidenceBasis` values.
- The backend must reject non-`declared` field-basis values that lack matching provenance, adapter-observation, third-party attestation, or Barcarolle-trusted evidence refs.
- The backend recomputes the canonical `snapshot_fingerprint` from the submitted repository-relevant digests, descriptors, subject label, and `acut_field_evidence_basis` before persistence.
- If the caller-supplied `snapshot_fingerprint` does not match the recomputed canonical value, reject the request instead of persisting a mismatched tested-agent snapshot identity.
- Because `acut_field_evidence_basis` participates in `snapshot_fingerprint`, upgrading a field from `declared` to `third_party_attested` or `barcarolle_trusted` creates a new tested-agent snapshot rather than mutating an existing one.
- If `evaluation_mode = harness_native` or `adapter_purity_level = A3_harness_native_controller`, `subject_label` must be `Agent + Harness`; native YOLO snapshots use a native subject label such as `native_agent`.

Response:

- `tested_agent_snapshot_id`
- `status`
- `tested_agent_snapshot`

#### `GetTestedAgentSnapshot`

Request:

- `tested_agent_snapshot_id`

Response:

- `tested_agent_snapshot`

#### `ListTestedAgentSnapshots`

Request:

- optional filters: `repository_id`, `scope`, `tested_agent_snapshot_id`, `snapshot_fingerprint`, `agent_configuration_id`, `snapshot_kind`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `RecordAgentChangeReview`

Request:

- `repository_id`
- `scope`
- `baseline_tested_agent_snapshot_id`
- `candidate_tested_agent_snapshot_id`
- optional `benchmark_evaluation_id`
- optional `benchmark_scorecard_id`
- optional `repository_agent_admission_id`
- `change_classification`
- optional `acut_field_evidence_basis_delta`; when omitted, the backend derives it from baseline and candidate snapshots
- optional baseline/candidate ACUT field evidence-basis summaries for readability; supplied values must match backend-derived snapshot summaries
- `target_condition_basis_identity`
- `target_condition_basis`
- optional `evidence_lineage`
- `review_outcome`
- `applicability`
- `reviewer_id`
- `rationale_summary`

Response:

- `agent_change_review_id`
- `agent_change_review`

#### `GetAgentChangeReview`

Request:

- `agent_change_review_id`

Response:

- `agent_change_review`

#### `ListAgentChangeReviews`

Request:

- optional filters: `repository_id`, `scope`, `baseline_tested_agent_snapshot_id`, `candidate_tested_agent_snapshot_id`, `review_outcome`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `RecordRepositoryAgentAdmission`

Request:

- `repository_id`
- `scope`
- `tested_agent_snapshot_id`
- `admission_basis`
- `evidence_lineage`
- `granted_trust_tier`
- `evaluated_subject_label`
- `admission_subject`
- `subject_applicability`
- `evaluation_mode`
- `adapter_purity_level`
- `acut_binding_attestation_basis`
- `license_consumption_basis`
- `policy_gate_results`
- `canonical_verification_basis`
- `evidence_trust_basis`
- `target_condition_basis_identity`
- `target_condition_basis`
- `status`
- `effective_window`
- `freshness_deadline`
- optional `admission_lifecycle_events`
- optional `consumer_certificate_status_profile`
- optional `supersedes_repository_agent_admission_id`
- `reviewer_id`
- `rationale_summary`

Response:

- `repository_agent_admission_id`
- `repository_agent_admission`

#### `RecordRepositoryAgentAdmissionTransition`

Request:

- `repository_agent_admission_id`
- `transition_kind` (`suspend`, `lift_suspension`, `supersede`, `revoke`, or `expire`)
- `previous_status`
- `next_status`
- `cause`
- optional `resolution_summary`
- optional `evidence_refs`
- `reviewer_id`
- `reviewed_at`
- `effective_at`

Response:

- `repository_agent_admission_id`
- `repository_agent_admission`
- `admission_lifecycle_event`
- `admission_lifecycle_sequence`

#### `GetRepositoryAgentAdmission`

Request:

- `repository_agent_admission_id`

Response:

- `repository_agent_admission`

#### `ListRepositoryAgentAdmissions`

Request:

- optional filters: `repository_id`, `scope`, `tested_agent_snapshot_id`, `status`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `RecordRepositoryAgentOperatingObservation`

Request:

- `repository_id`
- `scope`
- `tested_agent_snapshot_id`
- `state_source`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- optional `adapter_manifest_digest`
- optional `target_condition_basis_identity`
- optional `repository_agent_admission_id`
- optional `agent_change_review_id`
- `observed_at`
- optional `summary`

Response:

- `repository_agent_operating_observation_id`
- `repository_agent_operating_observation`
- `repository_agent_operating_state_id`
- `repository_agent_operating_state`
- `coverage_entries`

#### `GetRepositoryAgentOperatingState`

Request:

- `repository_id`
- `scope`

Response:

- `repository_agent_operating_state`
- `coverage_entries`
- `operating_state_version`
- `latest_license_certificate_summary`

#### `GetLicenseCertificate`

Request:

- `repository_id`
- `scope`
- optional `repository_agent_admission_id`
- nullable `repository_agent_operating_state_id` selection hint
- nullable `coverage_entry_id` selection hint
- `target_condition_basis_identity`
- `tested_agent_snapshot_id`
- `admission_subject`
- optional requested operation, risk class, and capability-envelope digest for server-side certificate selection
- optional `if_none_match_certificate_digest`

Response:

- `license_certificate` when a consumable certificate bound to one coverage entry or an explicitly non-consumable diagnostic projection can be produced
- `certificate_state`
- `non_consumable_reason_codes` when no certificate can be used for Barcarolle `allow` decisions
- `latest_license_status`
- `next_status_poll_after`

The query signs or returns a signed certificate over the selected admission and exactly one operating-state coverage entry when `certificate_state = issued`. If the server cannot select a unique consumer-ready coverage entry, it must return `certificate_state = non_consumable` with reason codes rather than signing an allow-capable admission-only certificate. It may pre-compute matching diagnostics, but consumers remain responsible for checking current signed status and local policy overlays.

#### `ListLicenseCertificates`

Request:

- optional filters: `repository_id`, `repository_agent_admission_id`, `repository_agent_operating_state_id`, `coverage_entry_id`, `target_condition_basis_identity`, `issuer_key_id`, `certificate_state`, `signed_at_from`, `signed_at_to`, `valid_after`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetLicenseStatus`

Request:

- optional `license_certificate_id`
- optional `repository_agent_admission_id`
- optional `repository_agent_operating_state_id`
- optional `coverage_entry_id`
- optional `target_condition_basis_identity`
- optional `status_watermark`
- optional `at_time`

Response:

- `license_status_record`
- `status_fresh_until`
- `status_watermark`
- `next_status_poll_after`

#### `ListLicenseStatusLog`

Request:

- optional filters: `license_certificate_id`, `repository_agent_admission_id`, `coverage_entry_id`, `target_condition_basis_identity`, `status_sequence_from`, `status_watermark_from`, `published_at_from`, `published_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetLicenseIssuerKeyStatus`

Request:

- `issuer_key_id`
- optional `issuer_key_set_version`
- optional `at_time`

Response:

- signed `license_issuer_key_status`

#### `RecordLicenseStatusReceipt`

Request:

- `consumer`
- `receipt_source`
- `received_at`
- `acknowledged_at`
- `license_certificate_id`
- `certificate_digest`
- `license_status_id`
- `status_digest`
- `status_sequence`
- `status_watermark`
- `event_stream_watermark`
- optional certificate signing-key status ref/digest
- optional status signing-key status ref/digest
- `verification_result`
- `receipt_result`
- `reason_codes`

Response:

- `license_status_receipt_id`
- `license_status_receipt`

#### `ListLicenseStatusReceipts`

Request:

- optional filters: `consumer`, `license_certificate_id`, `license_status_id`, `status_watermark`, `receipt_result`, `acknowledged_at_from`, `acknowledged_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `RecordLicenseConsumptionAuditEvent`

Request:

- `consumer`
- `operation_correlation_id`
- `decided_at`
- `repository_id`
- `requested_scope`
- `requested_operation`
- `requested_risk_class`
- `requested_target_condition_basis_identity`
- `requested_capability_envelope_digest`
- `requested_tested_agent_snapshot_id`
- `requested_admission_subject`
- `result`
- `reason_codes`
- optional `local_policy_overlay_result`
- optional `license_certificate_id`
- optional `certificate_digest`
- optional `certificate_signing_key_id`
- nullable `certificate_signing_key_status_ref`
- nullable `certificate_signing_key_status_digest`
- optional `certificate_signature_verification_result`
- optional `license_status_id`
- optional `status_digest`
- optional `status_sequence`
- optional `status_watermark`
- optional `status_signing_key_id`
- nullable `status_signing_key_status_ref`
- nullable `status_signing_key_status_digest`
- optional `status_signature_verification_result`
- optional `repository_agent_admission_id`
- nullable `repository_agent_operating_state_id`
- nullable `coverage_entry_id`
- optional `admission_lifecycle_sequence`
- optional `operating_state_version`
- optional `event_stream_watermark`
- nullable `granted_trust_tier`
- nullable `admission_status`
- nullable `freshness_state`
- nullable `freshness_deadline`
- nullable `certificate_validity`
- nullable `status_freshness`
- nullable `evidence_lineage`
- nullable `risk_profile_basis`
- nullable `policy_gate_basis`
- optional `failure_mode`

Response:

- `license_consumption_audit_event_id`
- `license_consumption_audit_event`

#### `GetLicenseConsumptionAuditEvent`

Request:

- `license_consumption_audit_event_id`

Response:

- `license_consumption_audit_event`

#### `ListLicenseConsumptionAuditEvents`

Request:

- optional filters: `repository_id`, `consumer`, `repository_agent_admission_id`, `license_certificate_id`, `license_status_id`, `status_watermark`, `result`, `reason_codes`, `decided_at_from`, `decided_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.7 Benchmark evaluation, runner integration, and submission

#### `StartBenchmarkEvaluation`

Request:

- `benchmark_release_id`
- `tested_agent_snapshot_id`
- optional `agent_configuration_id`
- `evaluation_policy_version`
- `evaluation_mode`
- `adapter_purity_level`
- `adapter_manifest`
- `run_environment_declaration`
- `assurance_mode`
- `attempt_number`
- optional `requested_capability_envelope`
- `runtime_limits`
- optional `seed`
- optional `run_policy`

Response:

- `benchmark_evaluation_id`
- `status`
- `benchmark_evaluation`

`attempt_number` is supplied by the caller before workflow ID derivation. The first semantic attempt for the same benchmark-evaluation basis should use `1`; a transport retry must reuse the same idempotency key and `attempt_number`; an intentional rerun must use a new idempotency key and the next `attempt_number`. The benchmark-evaluation basis includes evaluation mode and adapter purity, so `patch_only`, `trace_submission`, `observed_run`, and `harness_native` results do not collide.
The supplied `evaluation_mode`, `adapter_purity_level`, `adapter_manifest`, and `run_environment_declaration` must match the referenced `tested_agent_snapshot` canonical values. The request may assert those values for readability and idempotency, but it may not override the ACUT snapshot. To run a fresh benchmark evaluation under a different mode, adapter, or run environment, callers must first register a new tested-agent snapshot. Governed change review and target-condition basis records are for admission carry-forward, reused/supplemented evidence, and authorization interpretation; they do not let a benchmark evaluation execute under a different ACUT boundary while pointing at the old snapshot.

#### `GetBenchmarkEvaluation`

Request:

- `benchmark_evaluation_id`

Response:

- `benchmark_evaluation`
- `coverage_summary`
- `coverage_gate`
- `evaluation_mode`
- `adapter_purity_level`
- `adapter_manifest`
- `benchmark_scorecard_refs[]`

#### `ListBenchmarkEvaluations`

Request:

- optional filters: `repository_id`, `benchmark_definition_id`, `benchmark_release_id`, `tested_agent_snapshot_id`, `agent_configuration_id`, `status`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetBenchmarkScorecard`

Request:

- `benchmark_scorecard_id`

Response:

- `benchmark_scorecard`

`GetBenchmarkScorecard` is an exact immutable-resource lookup. It returns the scoring semantics version, aggregation algorithm, aggregate score, diagnostic completed score, denominator summary, weighting summary, missing-run summary, minimum-sample summary, reliability label, complete score input set digest, risk-profile basis when used, and policy-input summary as part of the scorecard resource. It must not use `benchmark_evaluation_id` alone, because one benchmark evaluation can legitimately produce multiple scorecards under different scorecard policies, coverage policies, risk profiles, evaluated capability envelopes, score input sets, evidence trust bases, or score-basis Judge lineages. Missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, or blocked entries must remain visible in the score input set and missing-run summary rather than being inferred from absent score-bundle refs.

#### `ListBenchmarkScorecards`

Request:

- optional filters: `benchmark_evaluation_id`, `benchmark_definition_id`, `benchmark_release_id`, `tested_agent_snapshot_id`, `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, `calibrated_policy_profile_id`, `repository_risk_profile_id`, `risk_profile_digest`, `evaluated_capability_envelope_id`, `evaluation_mode`, `adapter_purity_level`, `score_input_set_digest`, `evidence_trust_basis_digest`, optional `judge_configuration_id`, `computed_at_from`, `computed_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

Callers that need to resolve a scorecard by semantic basis rather than `benchmark_scorecard_id` must use `ListBenchmarkScorecards` with the complete scorecard-basis selector. If the selector is incomplete or matches multiple immutable scorecards, the API returns a list and clients must not collapse it to a single "current" scorecard unless an explicit read-model policy says which one is being displayed.

#### `StartRunnerInvocation`

Request:

- `task_id`
- `environment_id`
- `tested_agent_snapshot_id`
- optional `agent_configuration_id`
- `evaluation_mode`
- `adapter_purity_level`
- `adapter_manifest`
- `run_environment_declaration`
- `attempt_number`
- optional `requested_capability_envelope`
- `runtime_limits`
- optional `benchmark_evaluation_id`
- optional `benchmark_release_membership_id`
- optional `seed`
- optional `run_policy`

Response:

- `run_id`
- `status`
- `run`
- `expected_run_submission_contract`

The command first derives an envelope-independent `run_attempt_slot`. For benchmark-linked child runs the slot is `benchmark_evaluation_id + benchmark_release_membership_id + attempt_number`; for ad hoc runs it is `task_id + tested_agent_snapshot_id + environment_id + attempt_number`. For ad hoc runs the direct caller supplies `attempt_number`; for benchmark-linked child runs the parent `BenchmarkEvaluationWorkflow` or an explicit child-rerun operator command supplies it. Accepted run identity is `run_attempt_slot + capability_envelope_id + evaluation_mode + adapter_purity_level + adapter_manifest_digest`.
The server must first verify that supplied evaluation mode, adapter purity, adapter manifest, and run environment declaration match the referenced `tested_agent_snapshot` and, for benchmark-linked runs, the parent benchmark evaluation. It must then normalize `requested_capability_envelope`, evaluation mode, adapter purity, and adapter manifest before deciding replay vs conflict. If the same `run_attempt_slot` resolves to the same normalized values, it should return the original accepted run or `idempotency_conflict`. If the same slot resolves to a different normalized value on any of those axes, it must return `policy_conflict` because the caller is attempting to change the immutable run contract rather than replay the same run fact. A run-environment mismatch against the snapshot or parent benchmark evaluation is likewise `policy_conflict` for an existing slot and validation failure before acceptance. A different `run_attempt_slot` creates a new run identity.
Transport retries must reuse the same idempotency key and `attempt_number`; semantic reruns use a new idempotency key and the next attempt number.

#### `SubmitRunResult`

Request:

- `run_id`
- optional `patch_ref`
- optional `result_ref`
- optional `artifact_refs`
- optional `native_trace_refs`
- `producer_identity`
- `submission_digest`
- `redaction_state`
- `declared_completeness`

Response:

- `run_submission_id`
- `run_submission`
- `evidence_ingestion_status`

This records what the external/native agent or harness-backed runner produced. It does not by itself establish correctness.

#### `RecordCanonicalVerification`

Request:

- `run_id`
- `run_submission_id`
- `verifier_identity`
- `verifier_image_digest`
- `scoring_relevant_policy_version`
- `clean_room_workspace_digest`
- `patch_application_status`
- `canonical_result`
- optional `failure_class`
- `verification_attempt_number`
- `trusted_evidence_digest`
- `evidence_bundle_id`
- `evidence_bundle_manifest_version`
- `evidence_bundle_content_digest`

Response:

- `canonical_verification_record_id`
- `canonical_verification_record`

This command is normally workflow-owned. It records `trusted_barcarolle_evidence` and is the correctness/admission root for the run. The evidence bundle fields must identify the exact sealed verifier-evidence version consumed by canonical verification, not the current/latest bundle pointer. Idempotent retries reuse `verification_attempt_number` and must resolve to the same trusted evidence digest and verifier evidence bundle content digest; semantic reverification under the same verifier image and policy uses a new attempt number.

#### `CancelRunnerInvocation`

Request:

- `run_id`
- `cancellation_reason`

Response:

- `status`
- `termination_reason`

#### `GetEvaluationRun`

Request:

- `run_id`

Response:

- `run`
- `step_summary`
- `run_submission`
- `canonical_verification_record`
- `score_bundle_refs[]`
- `evidence_refs`
- `evidence_trust_basis`
- `acut_field_evidence_basis_summary`
- `run_observation_basis`

`score_bundle_refs[]` is a convenience list of immutable score bundles attached to the run, not a selected score. Each ref should include `score_bundle_id`, scoring policy, run outcome class, score state, `canonical_verification_record_id` or terminal outcome evidence digest, `score_input_evidence_digest`, `evidence_trust_basis_digest`, `authorization_eligible`, and score-basis Judge lineage. Clients that need one score must call `GetRunScore` by `score_bundle_id` or `ListRunScores` with a complete score-basis selector.

#### `ListEvaluationRuns`

Request:

- optional filters: `benchmark_evaluation_id`, `benchmark_release_membership_id`, `task_id`, `tested_agent_snapshot_id`, `agent_configuration_id`, `repository_id`, `evaluation_mode`, `adapter_purity_level`, `status`, `started_at_from`, `started_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.8 Scoring

#### `ComputeRunScore`

Request:

- `run_id`
- optional `canonical_verification_record_id`
- optional `terminal_outcome_evidence_digest` for scoreable pre-verification zeroes
- `scoring_policy_version`
- optional `multi_run_context`

Response:

- `score_bundle_id`
- `scoring_semantics_version`
- `run_outcome_class`
- `score_state`
- `failure_class`
- `failure_taxonomy_version`
- `outcome_owner`
- `raw_correctness_score`
- `effective_correctness_score`
- `correctness_score`
- `process_score`
- `stability_label`
- `repeated_run_group_id`
- `trial_summary`
- `risk_flags`
- `authorization_blocking_risk_flags`
- `authorization_eligible`
- `metric_breakdown`
- `score_input_evidence_digest`
- `score_input_evidence_refs`
- `evidence_trust_basis`
- `evidence_trust_basis_digest`
- `acut_field_evidence_basis_summary`
- `run_observation_basis_summary`
- `judge_contribution_mode`
- optional `judge_configuration_id`
- optional `judge_artifact_refs`

`judge_artifact_refs` should default to summary-only expansions when the referenced artifacts are not blind-safe for the caller's audience.
Correctness scoring must be rooted in the supplied `canonical_verification_record_id` or equivalent `trusted_barcarolle_evidence`. `agent_submitted_evidence` can affect audit findings, process score, or confidence adjustment, but cannot independently determine pass/fail.
Scoreable agent-owned failures such as verified failure, agent timeout, malformed agent submission, or trusted policy violation produce immutable score bundles with `correctness_score = 0`. Platform-owned infra failures, operator cancellations, unresolved verifier flakiness, and missing canonical verification are represented as missing or blocked scorecard input entries rather than as hidden positive or negative score bundles. `authorization_eligible = true` means the bundle can be selected into an authorization-bearing scorecard; it does not mean the aggregate decision will be ready or granted.
The backend must derive `evidence_trust_basis_digest` from the normalized trust-basis object and must derive `score_input_evidence_digest` from the exact sealed evidence bundle versions and other score- or confidence-contributing evidence inputs, including that trust-basis digest. If evidence repair or backfill changes any score-contributing or confidence-contributing input under the same scoring policy, the system must write a new immutable score bundle with a different `score_input_evidence_digest` rather than overwriting the old score.
When `judge_configuration_id` is present, it means the active scoring policy treated that governed Judge lineage as score-contributing. Advisory Judge refs may still be present without a `judge_configuration_id`, in which case canonical score identity remains on the explicit `none` Judge-lineage basis.

#### `GetRunScore`

Request:

- `score_bundle_id`

Response:

- `score_bundle`

`GetRunScore` is an exact immutable-resource lookup. It must not use `run_id` alone, because one run can have multiple score bundles under different scoring policies, score input evidence digests after repair/backfill, or score-basis Judge lineages.

#### `ListRunScores`

Request:

- optional filters: `run_id`, `benchmark_evaluation_id`, `canonical_verification_record_id`, `terminal_outcome_evidence_digest`, `scoring_policy_version`, `score_input_evidence_digest`, `evidence_trust_basis_digest`, `authorization_eligible`, optional `judge_configuration_id`, `computed_at_from`, `computed_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

Callers that need to resolve a score bundle by semantic basis rather than `score_bundle_id` must use `ListRunScores` with the complete score-basis selector. If evidence backfill or Judge lineage creates parallel immutable scores for one run, the API returns multiple score bundles rather than selecting one implicitly.

### 5.9 Authorization

#### `DecideAuthorization`

Request:

- `benchmark_scorecard_id`
- `benchmark_release_id`
- `scope`
- `authorization_policy_version`
- optional `policy_version` only as a deprecated alias for `authorization_policy_version`
- optional `calibrated_policy_profile_id`
- optional `expected_calibrated_policy_profile_digest`
- optional `repository_risk_profile_id` or `resolve_active_risk_profile = true`
- optional `expected_risk_profile_digest`
- optional `expected_release_coverage_profile_digest`
- optional `requested_admission_subject`
- optional `requested_trust_tier`
- optional `requested_operation`
- optional `requested_capability_envelope_id`
- optional `requested_consumer_certificate_status_profile`
- optional `target_condition_basis_identity`
- optional `target_condition_basis`
- optional `review_override`

Response:

- `decision_id`
- `requested_trust_tier`
- `granted_trust_tier`
- `authorization_policy_version`
- `policy_outcome`
- `decision_status`
- `rationale_summary`
- `calibrated_policy_profile_id`
- `calibrated_policy_profile_digest`
- `calibrated_profile_applicability_result`
- `repository_risk_profile_id`
- `risk_profile_version`
- `risk_profile_digest`
- `risk_profile_gate_result`
- `evaluated_subject_label`
- `requested_admission_subject`
- `subject_applicability`
- `target_condition_basis_identity`
- `target_condition_basis`
- `evaluation_mode`
- `adapter_purity_level`
- `acut_field_evidence_basis_summary`
- `acut_binding_attestation_basis`
- `license_consumption_basis`
- `consumer_certificate_status_profile_basis`
- `policy_gate_results`
- `canonical_verification_basis`
- `evidence_trust_basis`
- `release_admission_policy_version`
- `release_certification_verdict`
- `release_coverage_profile_ref`
- `release_scope_coverage_result`
- `supported_authorization_scope_summary`
- `unsupported_authorization_scope_summary`
- `unsupported_scope_reason_codes`
- `invalidation_refs`

#### `GetAuthorizationDecision`

Request:

- `decision_id` or `repository_id` plus optional `scope`

Response:

- `decision`

### 5.10 Evidence

#### `AppendEvidenceArtifact`

Request:

- one subject selector: `subject_type + subject_id`, or one of `candidate_generation_run_id`, `task_candidate_id`, `validation_result_id`, `leakage_report_id`, `task_id`, `task_retirement_id`, `release_maintenance_finding_id`, `run_id`, `environment_id`, `run_submission_id`, `canonical_verification_record_id`, or `evidence_bundle_id`
- optional `bundle_kind`
- optional `base_evidence_bundle_id` for a backfill or repair version
- optional `manifest_version` assertion; when absent, the backend allocates the next version for the bundle series
- `artifact_type`
- `content_ref`
- `provenance`
- optional `checksum`

Response:

- `artifact_id`
- `evidence_bundle_id`
- `manifest_version`
- `content_digest`

#### `GetEvidenceBundle`

Request:

- one subject selector: `subject_type + subject_id`, or one of `candidate_generation_run_id`, `task_candidate_id`, `validation_result_id`, `leakage_report_id`, `task_id`, `task_retirement_id`, `release_maintenance_finding_id`, `run_id`, `environment_id`, `run_submission_id`, `canonical_verification_record_id`, or `evidence_bundle_id`
- optional `bundle_kind`
- optional `manifest_version`; absent means resolve the current/latest sealed version for browsing

Response:

- `evidence_bundle_id`
- `manifest_version`
- `content_digest`
- `manifest`
- `artifact_refs`
- `retention_state`

### 5.11 Governed assessor configuration

#### `RegisterGovernedAssessorConfiguration`

Request:

- `assessor_kind`
- `repository_scope`
- `model_ref`
- `prompt_digest`
- `tool_profile_digest`
- `memory_strategy_digest`
- `runtime_policy_digest`
- `output_schema_version`
- optional assessor-role descriptors or policy refs
- optional `configuration_fingerprint` assertion
- optional `predecessor_configuration_id`
- optional `comparison_baseline_id`
- `created_by`

Response:

- `assessor_configuration_id`
- `configuration_fingerprint`
- `assessor_configuration`

The backend must recompute `configuration_fingerprint` from normalized configuration fields before persistence. Re-registering the same `repository_scope + assessor_kind + configuration_fingerprint` is idempotent; changing any material field creates a new governed assessor configuration rather than mutating the old one.

#### `GetGovernedAssessorConfiguration`

Request:

- `assessor_configuration_id`

Response:

- `assessor_configuration`

#### `ListGovernedAssessorConfigurations`

Request:

- optional filters: `assessor_kind`, `repository_id` or `scope`, `governance_state`, `comparison_baseline_id`, `created_at_from`, `created_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

### 5.12 Governed assessor lifecycle writes

#### `ApplyGovernedAssessorTransition`

Request:

- `assessor_configuration_id`
- `transition_type` such as `promote`, `demote`, or `rollback`
- `reviewer_id`
- `rationale`
- optional `comparison_baseline_id`
- optional `supersedes_assessor_configuration_id`

Response:

- `assessor_configuration`
- `transition_record`

### 5.12a Risk profile governance

#### `RegisterRepositoryRiskProfile`

Request:

- `organization_id` or `repository_id`
- `scope`
- optional `parent_risk_profile_id`
- `risk_profile_version`
- `risk_tolerance_class`
- `constraint_ref` or inline `constraint_summary`
- optional `expected_constraint_digest`
- lifecycle target such as `draft` or `candidate`

Response:

- `repository_risk_profile_id`
- `repository_risk_profile`
- `effective_profile_preview`
- `status`

The backend normalizes constraints, recomputes the digest, and rejects malformed or contradictory tier/scope matrices. Registering the same normalized profile is idempotent. A risk profile may declare License-consumption assumptions for external consumers, but it must not define a Barcarolle runtime enforcement plane.

#### `ResolveEffectiveRiskProfile`

Request:

- `organization_id` or `repository_id`
- `scope`
- optional `requested_trust_tier`
- optional `permission_class`
- optional `risk_class`
- optional `high_impact_path_class`
- optional `target_condition_basis`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- optional `evidence_trust_basis`

Response:

- `effective_risk_profile_basis`
- `repository_risk_profile_id` or seed basis
- `risk_profile_version`
- `risk_profile_digest`
- `source_profile_refs[]`
- `constraint_summary`
- `conflict_handling`
- `blocked_without_profile`

#### `GetRepositoryRiskProfile`

Request:

- `repository_risk_profile_id` or exact organization/repository/scope/version selector

Response:

- `repository_risk_profile`

#### `ListRepositoryRiskProfiles`

Request:

- optional filters: `organization_id`, `repository_id`, `scope`, `lifecycle_state`, `risk_tolerance_class`, `predecessor_risk_profile_id`, `constraint_digest`, `activated_at_from`, `activated_at_to`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `ApplyRepositoryRiskProfileTransition`

Request:

- `repository_risk_profile_id`
- `transition_type` such as `activate`, `pause`, `resume`, `supersede`, `rollback`, or `retire`
- actor identity
- governance `rationale`
- optional `transition_gate_refs`
- optional `supersedes_repository_risk_profile_id`

Response:

- `repository_risk_profile`
- `transition_record`
- `effective_selection_effect`
- optional triggered `policy_calibration_run_refs`
- optional `impact_preview_refs`

Risk-profile transitions affect future policy selection only. They can trigger recalibration, reauthorization, suspension, revocation, targeted validation, or full rebenchmarking, but they do not rewrite historical scorecards, authorization decisions, admissions, or operating-state coverage entries.

### 5.13 Policy calibration

#### `StartPolicyCalibration`

Request:

- `repository_scope`
- `target_policy_families`
- optional `repository_risk_profile_id` or `resolve_active_risk_profile = true`
- optional `predecessor_profile_refs`
- `trigger_kind`
- optional `requested_evidence_window`
- optional `requested_release_refs`
- optional `requested_scorecard_refs`
- `run_attempt_number`

Response:

- `policy_calibration_run_id`
- `policy_calibration_run`
- `truth_observation_manifest_ref` when the manifest has already been sealed or partially built
- `status`

This command starts the automated calibration workflow. It may cause the backend to run automatic controls or baselines through normal benchmark workflows, but it must not accept human baselines, human labels, risk-profile edits, or manual benchmark acceptance as calibration truth. The effective risk profile constrains optimization and false-positive budgets and is copied to the calibration run; objective truth observations are derived only from verifier, release, trusted policy, control, baseline, variance, or maintenance-invalidation evidence.

#### `GetPolicyCalibrationRun`

Request:

- `policy_calibration_run_id`

Response:

- `policy_calibration_run`

The run response must include the truth-observation manifest digest/ref, truth-observation summary, unsafe false-positive summary, high-tier authorization control summary, parameter authority blockers when known, and promotion gate summary. Large per-observation payloads may be paged through `ListCalibrationTruthObservations`.

#### `ListCalibrationTruthObservations`

Request:

- `policy_calibration_run_id`
- optional filters: `observation_kind`, `truth_basis_kind`, `semantic_slice`, `split`, `exclusion_status`, `unsafe_false_positive_result`, `candidate_profile_id`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

This query is for traceability and reviewer/auditor inspection. It must not provide a write path for labels.

#### `ListPolicyCalibrationRuns`

Request:

- optional filters: `repository_id` or `scope`, `target_policy_family`, `status`, `trigger_kind`, `predecessor_profile_id`, `selected_profile_id`, `created_at_from`, `created_at_to`
- optional `repository_risk_profile_id` or `risk_profile_digest`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `GetCalibratedPolicyProfile`

Request:

- `calibrated_policy_profile_id` or exact policy-version selector

Response:

- `calibrated_policy_profile`

The profile response must expose truth basis digest, unsafe false-positive metrics, high-tier authorization applicability summary, parameter authority summary, promotion gate results, and impact-preview refs so callers can distinguish evidence-fit parameters from risk-profile-bound constraints.

#### `ListCalibratedPolicyProfiles`

Request:

- optional filters: `semantic_policy_family`, `repository_id` or `scope`, `lifecycle_state`, `predecessor_profile_id`, `authorization_policy_version`, `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, `activated_at_from`, `activated_at_to`
- optional `repository_risk_profile_id` or `risk_profile_digest`
- pagination: `limit`, `cursor`, `sort`, `order`

Response:

- `items[]`
- `next_cursor`

#### `ApplyCalibratedPolicyProfileTransition`

Request:

- `calibrated_policy_profile_id`
- `transition_type` such as `promote`, `shadow`, `pause`, `resume`, `rollback`, or `supersede`
- actor identity
- automated `transition_gate_refs` for workflow-owned `promote`, `shadow`, `resume`, or `supersede`, including truth-observation completeness, unsafe false-positive, high-tier applicability, sensitivity, and parameter-authority gate refs; governance `rationale` for `pause`, `rollback`, or annotation
- optional `supersedes_calibrated_policy_profile_id`

Response:

- `calibrated_policy_profile`
- `transition_record`

Normal promotion, activation, resume, and supersession transitions are workflow-owned and require machine-checkable gate refs. Human-initiated transitions are governance pause, annotation, rollback, or exceptional policy actions, not calibration labels. `pause` removes the profile from active selection for new scorecards and decisions, falls back to the latest eligible non-paused active predecessor for the same policy surface, and leaves existing facts that reference the paused profile intact. If no predecessor is eligible, new materialization for that slice is blocked until automated `resume` or `supersede` succeeds.

## 6. Event Families

Cross-module events should use the common envelope and publish benchmark lifecycle changes as first-class events rather than requiring consumers to infer benchmark state only from child-run traffic.

### 6.1 Common event envelope

| Field | Type | Notes |
| --- | --- | --- |
| `event_id` | string | Opaque event identity. |
| `event_type` | string | Stable event family and action name. |
| `contract_version` | string | Contract family for cross-module compatibility. |
| `schema_version` | string | Event payload schema version. |
| `occurred_at` | datetime | Producer timestamp. |
| `producer` | string | Module or worker that emitted the event. |
| `request_id` | string | Request lineage reference when applicable. |
| `correlation_id` | string | Shared operation lineage. |
| `causation_id` | string | Triggering command or prior event. |
| `subject` | object | Primary resource identifiers for routing and audit. |
| `payload` | object | Event-specific data. |

### 6.2 Benchmark lifecycle event payloads

#### `TaskRetired` / `TaskQuarantined`

Stable payload fields:

- `task_retirement_id`
- `task_id`
- optional `task_candidate_id`
- `retirement_reason`
- `invalidation_severity`
- `finding_source`
- affected release, scorecard, authorization decision, and repository-agent admission refs when known
- optional `replacement_task_id`
- `retired_at`

#### `ReleaseMaintenanceFindingRecorded`

Stable payload fields:

- `release_maintenance_finding_id`
- `subject_kind`
- `subject_ref`
- `benchmark_release_id`
- `finding_type`
- `cause_code`
- `invalidation_severity`
- optional leakage summary fields: `leakage_kind`, `leakage_severity`, `leakage_handling_decision`, `leakage_report_digest`
- affected release membership, scorecard, authorization decision, and repository-agent admission refs when known
- `finding_status`
- `effective_at`

#### `BenchmarkReleasePublished`

Stable payload fields:

- `benchmark_definition_id`
- `benchmark_release_id`
- `release_label`
- `publication_status`
- `published_at`
- `membership_count`
- optional `release_coverage_profile_digest`
- optional `supported_authorization_scopes`
- optional `unsupported_authorization_scopes`
- optional `release_certification_verdict`
- optional `source_snapshot_id`

#### `BenchmarkReleaseCoverageProfileComputed`

Stable payload fields:

- `benchmark_definition_id`
- `benchmark_release_id`
- `release_admission_policy_version`
- `release_coverage_profile_digest`
- `supported_authorization_scopes`
- `unsupported_authorization_scopes`
- `release_certification_verdict`

#### `RepositoryRiskProfileRegistered` / `RepositoryRiskProfileTransitioned`

Stable payload fields:

- `repository_risk_profile_id`
- optional `organization_id`
- optional `repository_id`
- `scope`
- `risk_profile_version`
- `risk_profile_digest`
- `risk_tolerance_class`
- `transition_type` when transitioned
- `from_lifecycle_state` when transitioned
- `to_lifecycle_state`
- `effective_selection_effect`
- optional `supersedes_repository_risk_profile_id`
- optional `policy_calibration_run_refs`
- optional `impact_preview_refs`
- `occurred_at`

#### `BenchmarkEvaluationRequested`, `BenchmarkEvaluationStarted`, `BenchmarkEvaluationCompleted`, `BenchmarkEvaluationFailed`, `BenchmarkEvaluationCanceled`

Stable payload fields:

- `benchmark_evaluation_id`
- `benchmark_definition_id`
- `benchmark_release_id`
- `tested_agent_snapshot_id`
- `agent_configuration_id`
- `evaluation_policy_version`
- `evaluation_mode`
- `adapter_purity_level`
- `adapter_manifest_digest`
- `capability_envelope_contract_id`
- `attempt_number`
- `status`
- `coverage_summary`
- optional `failure_cause`
- optional `benchmark_scorecard_id` once available

#### `BenchmarkScorecardPublished`

Stable payload fields:

- `benchmark_scorecard_id`
- `benchmark_evaluation_id`
- `benchmark_definition_id`
- `benchmark_release_id`
- `tested_agent_snapshot_id`
- `scoring_semantics_version`
- `scorecard_policy_version`
- optional `calibrated_policy_profile_id`
- optional `repository_risk_profile_id`
- optional `risk_profile_version`
- optional `risk_profile_digest`
- `aggregation_algorithm`
- `coverage_policy_version`
- optional `reliability_policy_version`
- optional `judge_configuration_id`
- `aggregate_score`
- optional `completed_score`
- `aggregate_stability_label`
- `reliability_label`
- `coverage_summary`
- `denominator_summary`
- `missing_run_summary`
- `minimum_sample_summary`
- `task_family_coverage`
- optional `release_coverage_profile_digest`
- optional `release_admission_policy_version`
- optional `release_certification_verdict`
- optional `unsupported_authorization_scope_summary`
- `canonical_verification_coverage`
- `evidence_trust_basis`
- `evidence_trust_basis_digest`
- `score_input_set_digest`
- optional compact `score_input_entries_summary`
- `acut_field_evidence_basis_summary`
- `evaluated_capability_envelope`
- `authorization_readiness`
- optional `invalidation_status`
- optional `invalidation_refs`
- `created_at`

`BenchmarkScorecardPublished` is the benchmark-level completion surface for aggregate results. It should be emitted once the immutable scorecard record is durable and available for authorization or historical comparison.

#### `PolicyCalibrationRunCompleted`

Stable payload fields:

- `policy_calibration_run_id`
- `repository_scope`
- `target_policy_families`
- `repository_risk_profile_id`
- `risk_profile_version`
- `risk_profile_digest`
- `risk_constraint_summary`
- `calibration_input_manifest_digest`
- `truth_observation_manifest_digest`
- `truth_observation_summary`
- `evidence_slice_coverage_summary`
- `control_baseline_summary`
- `unsafe_false_positive_summary`
- `high_tier_authorization_control_summary`
- `candidate_profile_refs`
- optional `selected_profile_ref`
- `promotion_gate_summary`
- `status`
- `completed_at`

#### `CalibratedPolicyProfileTransitioned`

Stable payload fields:

- `calibrated_policy_profile_id`
- `semantic_policy_family`
- `repository_scope`
- `repository_risk_profile_id`
- `risk_profile_version`
- `risk_profile_digest`
- `transition_type`
- `from_lifecycle_state`
- `to_lifecycle_state`
- `authorization_policy_version`
- `scorecard_policy_version`
- `coverage_policy_version`
- optional `reliability_policy_version`
- optional `calibrated_policy_profile_id_or_seed`
- optional `transition_gate_refs`
- optional `governance_rationale_ref`
- `active_selection_effect` such as `unchanged`, `activated`, `fallback_to_predecessor`, or `blocked_until_successor`
- `parameter_digest`
- `truth_basis_digest`
- optional `unsafe_false_positive_summary`
- optional `high_tier_authorization_applicability_summary`
- optional `parameter_authority_summary`
- `policy_calibration_run_id`
- `occurred_at`

#### `TestedAgentSnapshotRegistered`

Stable payload fields:

- `tested_agent_snapshot_id`
- optional `agent_configuration_id`
- `repository_scope`
- `snapshot_kind`
- `snapshot_fingerprint`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- optional `adapter_manifest_digest`
- `acut_field_evidence_basis`
- optional `canonical_artifact_refs`
- `created_at`

#### `AgentChangeReviewRecorded`

Stable payload fields:

- `agent_change_review_id`
- `repository_id`
- `scope`
- `baseline_tested_agent_snapshot_id`
- `candidate_tested_agent_snapshot_id`
- optional `benchmark_evaluation_id`
- optional `benchmark_scorecard_id`
- `baseline_acut_field_evidence_basis_summary`
- `candidate_acut_field_evidence_basis_summary`
- `acut_field_evidence_basis_delta`
- `review_outcome`
- `applicability`
- `reviewer_id`
- `reviewed_at`

#### `RepositoryAgentAdmissionRecorded`

Stable payload fields:

- `repository_agent_admission_id`
- `repository_id`
- `scope`
- `tested_agent_snapshot_id`
- `admission_basis`
- optional `granted_trust_tier`
- optional `evaluated_capability_envelope`
- optional `authorization_readiness`
- optional `repository_risk_profile_id`
- optional `risk_profile_digest`
- optional `risk_profile_gate_result`
- `status`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- optional `canonical_verification_basis`
- optional `evidence_trust_basis`
- `effective_window`
- optional `freshness_deadline`
- optional `admission_lifecycle_events`
- optional `admission_lifecycle_sequence`
- optional `consumer_certificate_status_profile`
- optional `latest_license_certificate_ref`
- optional `latest_license_status_ref`
- optional `supersedes_repository_agent_admission_id`
- `created_at`

#### `RepositoryAgentAdmissionTransitionRecorded`

Stable payload fields:

- `repository_agent_admission_id`
- `transition_kind`
- `previous_status`
- `next_status`
- `cause`
- optional `resolution_summary`
- optional `evidence_refs`
- `reviewer_id`
- `reviewed_at`
- `effective_at`
- `admission_lifecycle_sequence`
- optional `invalidates_license_certificate_refs`
- optional `status_watermark`
- optional `consumer_deny_after`

#### `LicenseCertificateIssued`

Stable payload fields:

- `license_certificate_id`
- `certificate_digest`
- `repository_id`
- `scope`
- `repository_agent_admission_id`
- `repository_agent_operating_state_id`
- `coverage_entry_id`
- `target_condition_basis_identity`
- `admission_lifecycle_sequence`
- optional `operating_state_version`
- `event_stream_watermark`
- `certificate_signing_key_id`
- `issuer_key_set_version`
- `issuer_key_status_ref`
- `issuer_key_status_digest`
- `issuer_key_status`
- `issuer_key_valid_not_before`
- `issuer_key_valid_not_after`
- `issuer_key_status_effective_at`
- optional `issuer_key_revoked_at`
- `issuer_key_status_checked_at`
- `signed_at`
- `certificate_valid_not_before`
- nullable `certificate_valid_not_after`
- optional `renew_after`
- `status_surface_ref`
- `status_sequence_at_issuance`
- `status_watermark_at_issuance`
- `max_status_staleness`
- `certificate_state`

#### `LicenseStatusChanged`

Stable payload fields:

- `license_status_id`
- `license_certificate_id`
- `certificate_digest`
- `repository_agent_admission_id`
- optional `repository_agent_operating_state_id`
- optional `coverage_entry_id`
- `target_condition_basis_identity`
- `status_sequence`
- `status_watermark`
- `license_lifecycle_state`
- `transition_kind`
- optional `cause_codes`
- optional `invalidating_event_id`
- `admission_lifecycle_sequence`
- optional `operating_state_version`
- optional `certificate_signing_key_status_ref`
- optional `status_signing_key_status_ref`
- `status_effective_at`
- `published_at`
- `status_fresh_until`
- `consumer_deny_after`

#### `LicenseIssuerKeyStatusChanged`

Stable payload fields:

- `issuer_key_status_ref`
- `issuer_key_id`
- `issuer_key_set_version`
- `status_sequence`
- `issuer_key_status`
- `key_purpose`
- `valid_not_before`
- `valid_not_after`
- `status_effective_at`
- optional `revoked_at`
- `status_digest`
- `event_stream_watermark`
- `published_at`

#### `LicenseStatusReceiptRecorded`

Stable payload fields:

- `license_status_receipt_id`
- `consumer`
- `receipt_source`
- `license_certificate_id`
- `certificate_digest`
- `license_status_id`
- `status_digest`
- `status_sequence`
- `status_watermark`
- `event_stream_watermark`
- `verification_result`
- `receipt_result`
- `reason_codes`
- `acknowledged_at`
- `created_at`

#### `RepositoryAgentOperatingObservationRecorded`

Stable payload fields:

- `repository_agent_operating_observation_id`
- `repository_id`
- `scope`
- `tested_agent_snapshot_id`
- `state_source`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- optional `repository_agent_admission_id`
- optional `agent_change_review_id`
- `observed_at`
- `created_at`

#### `RepositoryAgentOperatingStateUpdated`

Stable payload fields:

- `repository_agent_operating_state_id`
- `repository_id`
- `scope`
- `tested_agent_snapshot_id`
- optional `evaluation_mode`
- optional `adapter_purity_level`
- `coverage_state`
- `drift_state`
- `coverage_entries`
- optional `operating_state_version`
- optional `latest_license_certificate_summary`
- optional `repository_risk_profile_id`
- optional `risk_profile_digest`
- optional `acut_field_evidence_basis_summary`
- optional `run_observation_basis_summary`
- optional `canonical_verification_basis`
- optional `evidence_trust_basis`
- optional `repository_agent_admission_id`
- optional `agent_change_review_id`
- optional `latest_repository_agent_operating_observation_id`
- `observed_at`
- `updated_at`

#### `LicenseConsumptionAuditEventRecorded`

Stable payload fields:

- `license_consumption_audit_event_id`
- `consumer`
- `operation_correlation_id`
- `repository_id`
- `result`
- `reason_codes`
- optional `license_certificate_id`
- optional `certificate_digest`
- optional `license_status_id`
- optional `status_digest`
- optional `status_watermark`
- optional `certificate_signing_key_id`
- optional `certificate_signing_key_status_ref`
- optional `certificate_signing_key_status_digest`
- optional `certificate_signature_verification_result`
- optional `status_signing_key_id`
- optional `status_signing_key_status_ref`
- optional `status_signing_key_status_digest`
- optional `status_signature_verification_result`
- optional `repository_agent_admission_id`
- nullable `repository_agent_operating_state_id`
- nullable `coverage_entry_id`
- optional `admission_lifecycle_sequence`
- optional `operating_state_version`
- optional `event_stream_watermark`
- nullable `granted_trust_tier`
- nullable `admission_status`
- nullable `freshness_state`
- nullable `freshness_deadline`
- nullable `certificate_validity`
- nullable `status_freshness`
- nullable `evidence_lineage`
- nullable `risk_profile_basis`
- nullable `policy_gate_basis`
- optional `local_policy_overlay_result`
- optional `failure_mode`
- `decided_at`
- `created_at`

## 7. Filters and Pagination

List endpoints should use the same pagination contract.

| Field | Type | Notes |
| --- | --- | --- |
| `limit` | integer | Maximum records to return. |
| `cursor` | string | Opaque continuation token. |
| `sort` | string | Sort key for the list view. |
| `order` | string | `asc` or `desc`. |
| `status` | string | Common filter for lifecycle views. |
| `created_at_from` / `created_at_to` | datetime | Time window filters. |
| `repository_id` | string | Repository-scoped filter. |
| `benchmark_definition_id` | string | Benchmark-line-scoped filter. |
| `benchmark_release_id` | string | Immutable release-scoped filter. |
| `benchmark_evaluation_id` | string | Benchmark-evaluation-scoped filter. |
| `benchmark_release_membership_id` | string | Benchmark-release-membership-scoped filter, interpreted with `benchmark_evaluation_id` for child-run drill-downs. |
| `benchmark_scorecard_id` | string | Exact scorecard-scoped filter where supported. |
| `task_candidate_id` | string | Candidate-scoped filter. |
| `task_id` | string | Task-scoped filter. |
| `run_id` | string | Run-scoped filter. |
| `score_bundle_id` | string | Exact score-bundle-scoped filter where supported. |
| `tested_agent_snapshot_id` | string | Evaluated or operating snapshot-scoped filter. |
| `agent_configuration_id` | string | Configuration-scoped filter. |
| `evaluation_mode` | string | Evaluation mode filter. |
| `adapter_purity_level` | string | Adapter-purity filter. |
| `evidence_trust_tier` | string | Evidence trust-tier filter. |
| `score_input_evidence_digest` | string | Score-input evidence basis filter for immutable run scores. |
| `score_input_set_digest` | string | Score-input set basis filter for immutable benchmark scorecards. |
| `evidence_trust_basis_digest` | string | Aggregate evidence trust-basis filter for immutable benchmark scorecards. |
| `policy_calibration_run_id` | string | Exact calibration-run filter. |
| `calibration_truth_observation_id` | string | Exact calibration truth-observation filter where supported. |
| `truth_basis_kind` | string | Calibration truth basis filter for observation and calibration audit reads. |
| `calibrated_policy_profile_id` | string | Exact calibrated profile filter where supported. |
| `repository_risk_profile_id` | string | Exact risk-profile filter where supported. |
| `risk_profile_digest` | string | Effective risk-profile basis filter for calibration, scorecard, authorization, admission, and operating-state views. |
| `repository_agent_admission_id` | string | Admission-scoped filter for License certificates, status, audit events, and operating-state coverage reads. |
| `license_certificate_id` | string | Signed License-certificate filter where supported. |
| `license_status_id` | string | Signed License-status filter where supported. |
| `license_consumption_audit_event_id` | string | Exact consumer-audit filter where supported. |

`Assumption`: filter names can vary slightly by transport, but the semantic set should stay the same.

## 8. Error Model

All synchronous operations should return structured domain errors with:

- `code`
- `message`
- `retryable`
- `subject_id`
- optional `remediation_hint`

Recommended error codes:

- `not_found`
- `invalid_state`
- `validation_failed`
- `environment_unreplayable`
- `environment_build_failed`
- `task_rejected`
- `contaminated_or_leaked`
- `flaky_or_unstable`
- `verification_failed`
- `idempotency_conflict`
- `permission_denied`
- `policy_conflict`
- `resource_exhausted`
- `internal_error`

Rules:

- Deterministic rejections such as `validation_failed` or `task_rejected` should usually be non-retryable.
- Infrastructure failures such as `environment_build_failed` may be retryable.
- `idempotency_conflict` should point to the original accepted resource when possible, including when a mutating request replays the same normalized immutable capability envelope.
- `policy_conflict` should be used when `StartRunnerInvocation` reuses an already accepted `run_attempt_slot` while changing the normalized capability envelope, evaluation mode, adapter purity, adapter manifest, or any run-environment value that must match the referenced ACUT snapshot.
- `internal_error` should not be the only persisted outcome for a business decision.

`Inference`: exact retry classification can be refined later, but the contract should already separate business rejection from transient failure.

## 9. Idempotency

All write-like commands must accept an idempotency key.

Attempt-bearing start commands must receive `attempt_number` as part of the request before deriving workflow IDs. Reusing an idempotency key with a different `attempt_number` or different natural basis should return `idempotency_conflict`; using a different idempotency key with the next `attempt_number` is the explicit semantic new-attempt signal.

Recommended natural keys:

| Command family | Natural key |
| --- | --- |
| Repository snapshot | `repository_id + source_revision + import_mode` |
| Repository risk profile | `organization_id_or_repository_id + scope + risk_profile_version`; equivalent definitions may be idempotent by `organization_id_or_repository_id + scope + constraint_digest` |
| Candidate generation run | `repository_id + snapshot_id + generation_strategy + signal_input_manifest_digest + selection_policy_version + optional golden_configuration_id + optional golden_input_manifest_digest + run_attempt_number` |
| Task candidate | `repository_id + snapshot_id + generation_context_lineage + task_family + contract_version`, where `generation_context_lineage` includes candidate-specific selection identity and Golden-assisted discovery/selection lineage when applicable |
| Replay environment | `task_candidate_id + plan_version` |
| Leakage report | `subject_kind + subject_id + report_digest` |
| Benchmark release | `benchmark_definition_id + release_label` |
| Release maintenance finding | `subject_kind + subject_ref + finding_type + cause_code + evidence_digest` |
| Tested-agent snapshot | `repository_scope + snapshot_fingerprint` |
| Agent change review | `repository_id + scope + baseline_tested_agent_snapshot_id + candidate_tested_agent_snapshot_id + review_sequence` |
| Repository-agent admission | row identity: `repository_id + scope + tested_agent_snapshot_id + admission_basis_identity + target_condition_basis_identity`; effective-selection key: `repository_id + scope + target_condition_basis_identity` |
| Repository-agent operating observation | `repository_id + scope + observed_at + state_source + tested_agent_snapshot_id` |
| License certificate | `repository_agent_admission_id + repository_agent_operating_state_id + coverage_entry_id + target_condition_basis_identity + operating_state_version + admission_lifecycle_sequence + certificate_schema_version + certificate_digest` |
| License status record | `license_certificate_id + status_sequence + status_watermark` |
| License status receipt | `consumer + license_status_id + status_watermark + acknowledged_at` |
| License consumption audit event | `consumer + operation_correlation_id + decided_at + certificate_digest + status_watermark` |
| Benchmark evaluation | `benchmark_release_id + tested_agent_snapshot_id + evaluation_policy_version + evaluation_mode + adapter_purity_level + capability_envelope_contract_id + assurance_mode + attempt_number` |
| Evaluation run | accepted run identity is `run_attempt_slot + capability_envelope_id + evaluation_mode + adapter_purity_level + adapter_manifest_digest`; `ad_hoc.run_attempt_slot = task_id + tested_agent_snapshot_id + environment_id + attempt_number`; `benchmark_linked.run_attempt_slot = benchmark_evaluation_id + benchmark_release_membership_id + attempt_number` |
| Run submission | one accepted submission per `run_id` |
| Canonical verification record | `run_submission_id + verifier_identity + verifier_image_digest + scoring_relevant_policy_version + verification_attempt_number` |
| Evidence bundle | immutable version key: `subject_type + subject_id + bundle_kind + manifest_version`; current/latest read-model series: `subject_type + subject_id + bundle_kind` |
| Run score bundle | `run_id + canonical_verification_record_id_or_terminal_outcome_evidence_digest + scoring_policy_version + score_input_evidence_digest + score-basis Judge lineage`, where the lineage axis is score-contributing `judge_configuration_id` or explicit `none` |
| Benchmark scorecard | `benchmark_evaluation_id + scorecard_policy_version + coverage_policy_version + reliability_policy_version + calibrated_policy_profile_id_or_seed + repository_risk_profile_id_or_seed + risk_profile_digest_or_seed + evaluated_capability_envelope_id + evaluation_mode + adapter_purity_level + score_input_set_digest + evidence_trust_basis_digest + score-basis Judge lineage`, where `score_input_set_digest` covers scoreable and missing entries and the lineage axis is score-contributing `judge_configuration_id` or explicit `none` |
| Authorization decision | `repository_id + scope + authorization_policy_version + calibrated_policy_profile_id_or_seed + repository_risk_profile_id_or_seed + risk_profile_digest_or_seed + benchmark_scorecard_id + authorized_capability_envelope_id + target_condition_basis_identity` |
| Policy calibration run | `repository_scope + target_policy_families + repository_risk_profile_id_or_seed + risk_profile_digest_or_seed + calibration_input_manifest_digest + trigger_kind + run_attempt_number` |
| Calibration truth observation | `policy_calibration_run_id + manifest_local_observation_key`, with source refs plus truth basis digest idempotent for repeated manifest construction |
| Calibrated policy profile | `semantic_policy_family + repository_scope + repository_risk_profile_id_or_seed + risk_profile_digest_or_seed + parameter_digest + applicability_slice_digest` |
| Governed assessor configuration | `repository_scope + assessor_kind + configuration_fingerprint` |

Rules:

- Replays of the same idempotent command should return the original outcome or a stable conflict response.
- Queries must be safe to retry without side effects.

`Inference`: `source_anchor` stays as historical source lineage, while `snapshot_id + generation_context_lineage` is the generation-instance identity for `task_candidate`. The generation-context lineage must include extractor lineage plus candidate-specific selection identity at minimum and can absorb broader candidate-build context, including `candidate_generation_run_id`, selected Golden output digest, exact evidence-bundle version/content digest, and Golden-assisted discovery/selection/contract-synthesis lineage, when that context materially changes candidate semantics.

## 10. Versioning

### 10.1 Contract versioning

- Every request, response, and event should carry `contract_version`.
- Additive changes should not change the major contract version.
- Breaking changes should introduce a new major version or a new event family.

### 10.2 Resource schema versioning

The following schemas should evolve independently:

- repository snapshot
- repository risk profile
- candidate generation run
- task candidate
- task
- replay plan
- replay environment
- validation result
- leakage report
- release maintenance finding
- tested-agent snapshot
- agent change review
- repository-agent admission
- repository-agent operating state
- license certificate
- license status
- license status receipt
- license consumption audit event
- evaluation run
- run submission
- canonical verification record
- run score bundle
- policy calibration run
- calibrated policy profile
- authorization decision
- evidence bundle

### 10.3 Evolution rules

- New optional fields may be added without breaking older consumers.
- Required field removal is breaking.
- Field renames are breaking unless the old field remains during a deprecation window.
- Consumers should ignore unknown fields when possible.

`Assumption`: additive evolution is the default because replay and audit artifacts must remain readable over time.

## 10. Audit Fields

Every persisted record that can affect a score or authorization decision should include:

- `created_at`
- `created_by`
- `request_id`
- `correlation_id`
- `causation_id`
- `contract_version`
- `schema_version`
- upstream artifact or snapshot reference
- provenance summary
- ACUT field evidence-basis summary when the record interprets a tested-agent snapshot
- `admission_review_id` when required admission review governed the outcome
- `benchmark_admission_policy_version` or `release_admission_policy_version` where rubric gates or release coverage affected the outcome
- `tested_agent_snapshot_id` where applicable
- `repository_agent_admission_id` where applicable
- `agent_change_review_id` where applicable
- `license_certificate_id`, certificate digest, `license_status_id`, and status watermark where a signed License certificate/status affected the record
- `license_consumption_audit_event_id` where applicable
- `golden_configuration_id` when Golden materially contributed
- score-basis `judge_configuration_id` when Judge materially contributed to canonical scoring; advisory Judge refs may still be attached separately

For runs and decisions, also include:

- `agent_configuration_id`
- `tested_agent_snapshot_id`
- `evaluation_mode`
- `adapter_purity_level`
- `acut_field_evidence_basis_summary`
- `run_submission_id`
- `canonical_verification_record_id`
- `terminal_outcome_evidence_digest` when scoring a trusted pre-verification terminal zero
- evidence trust-tier basis
- `environment_id`
- `scoring_policy_version` or `authorization_policy_version` when the record is an authorization decision
- `policy_calibration_run_id`, `calibrated_policy_profile_id`, and calibrated policy-profile digest where calibrated parameters affected the record
- `repository_risk_profile_id`, risk-profile version, risk-profile digest, and effective-profile basis where appetite constraints affected the record
- `verifier_ref`
- `stability_label`
- `run_outcome_class`, `score_state`, `failure_taxonomy_version`, and `score_input_set_digest` where applicable
- retirement or rejection reason where relevant

## 11. Required Scope and Later Scope

### 11.1 Required

- repository snapshot registration and lookup
- candidate generation-run reservation, completion, and lookup
- task candidate creation, lookup, approval, and retirement
- task-level benchmark-admission fields for gates, oracle grading, validation probes, leakage reports, and review reason codes
- approved task lookup
- replay plan lookup plus candidate-scoped planning
- replay environment lookup plus candidate-scoped build
- validation-result lookup plus candidate-scoped validation
- admission-review lookup and compliance query surfaces
- admission-review writes for explicit approval lineage
- tested-agent snapshot registration and lookup
- change-review writes and reads for post-evaluation agent evolution
- repository-agent admission writes and reads
- current operating-state write and read surfaces
- signed License-certificate query/list surfaces derived from admissions and operating-state coverage
- signed License-status query/log surfaces plus status-receipt ingest and lookup surfaces
- License-consumption audit-event ingest and lookup surfaces for conforming consumers
- runner invocation, run-submission, status, and cancellation
- canonical verification record writes
- evidence capture with producer, trust tier, source class, digest, redaction, and score-contribution metadata
- score computation
- policy calibration run and calibrated policy profile recording
- authorization decision recording
- governed assessor configuration lineage reads for promotion and comparison auditability
- governed assessor lifecycle writes for append-only promotion, demotion, and rollback
- optional Golden/Judge artifact references on validation and score resources
- persisted task retirement records and release maintenance findings
- first-class leakage reports plus queryable leakage summary fields on candidates, validations, retirements, and maintenance findings
- benchmark release coverage profiles with supported and unsupported authorization scopes
- idempotency, versioning, and audit fields
- structured domain errors

### 11.2 Later scope

- richer composed dashboard read models built from the canonical resources
- multi-repository federation
- stronger policy tiers
- multiple verifier families per task
- repeated-run statistical summaries
- external audit export formats
- richer replay diff visualizations

`Inference`: later scope should extend the same resource model rather than replace it.

## 12. Coverage Check

The schema above covers the required chain:

- snapshot intake: `RegisterRepositorySnapshot`, `GetRepositorySnapshot`, `ListRepositorySnapshots`
- candidate generation run: `ReserveCandidateGenerationRun`, `CompleteCandidateGenerationRun`, `GetCandidateGenerationRun`, `ListCandidateGenerationRuns`
- task candidate: `CreateTaskCandidate`, `GetTaskCandidate`, `ListTaskCandidates`, `ApproveTaskCandidate`, `RetireTaskCandidate`
- task: `GetTask`, `ListTasks`, `RetireTask`
- replay plan: `PlanReplayEnvironment`, `GetReplayPlan`, `ListReplayPlans`
- environment: `BuildReplayEnvironment`, `GetReplayEnvironment`, `ListReplayEnvironments`
- validation and leakage: `ValidateReplayEnvironment`, `GetValidationResult`, `ListValidationResults`, `GetLeakageReport`, `ListLeakageReports`
- admission review and post-release findings: `CreateAdmissionReviewRecord`, `GetAdmissionReviewRecord`, `ListAdmissionReviewRecords`, `CreateReleaseMaintenanceFinding`, `GetReleaseMaintenanceFinding`, `ListReleaseMaintenanceFindings`
- benchmark definition/release: `GetBenchmarkDefinition`, `ListBenchmarkDefinitions`, `PublishBenchmarkRelease`, `GetBenchmarkRelease`, `ListBenchmarkReleases`
- tested-agent evolution: `RegisterTestedAgentSnapshot`, `GetTestedAgentSnapshot`, `ListTestedAgentSnapshots`, `RecordAgentChangeReview`, `GetAgentChangeReview`, `ListAgentChangeReviews`, `RecordRepositoryAgentAdmission`, `RecordRepositoryAgentAdmissionTransition`, `GetRepositoryAgentAdmission`, `ListRepositoryAgentAdmissions`, `RecordRepositoryAgentOperatingObservation`, `GetRepositoryAgentOperatingState`
- benchmark evaluation/scorecard: `StartBenchmarkEvaluation`, `GetBenchmarkEvaluation`, `ListBenchmarkEvaluations`, `GetBenchmarkScorecard`, `ListBenchmarkScorecards`
- risk profile governance: `RegisterRepositoryRiskProfile`, `ResolveEffectiveRiskProfile`, `GetRepositoryRiskProfile`, `ListRepositoryRiskProfiles`, `ApplyRepositoryRiskProfileTransition`
- policy calibration: `StartPolicyCalibration`, `GetPolicyCalibrationRun`, `ListPolicyCalibrationRuns`, `ListCalibrationTruthObservations`, `GetCalibratedPolicyProfile`, `ListCalibratedPolicyProfiles`, `ApplyCalibratedPolicyProfileTransition`
- run: `StartRunnerInvocation`, `SubmitRunResult`, `RecordCanonicalVerification`, `CancelRunnerInvocation`, `GetEvaluationRun`, `ListEvaluationRuns`
- score: `ComputeRunScore`, `GetRunScore`, `ListRunScores`
- decision: `DecideAuthorization`, `GetAuthorizationDecision`
- governed assessor lifecycle: `RegisterGovernedAssessorConfiguration`, `ApplyGovernedAssessorTransition`
- evidence: `AppendEvidenceArtifact`, `GetEvidenceBundle`

The contract stays aligned with `docs/architecture/interface-contracts.md` by keeping benchmark definition, immutable release, benchmark evaluation, runner integration, canonical verification, scorecard, admission, authorization, and operating-state surfaces explicit.
