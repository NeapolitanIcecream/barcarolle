# Interface Contracts for Repository-Specific Agent Benchmarking

## 1. Purpose

This document defines the module-to-module contracts for the repository-specific agent benchmarking system described in [docs/architecture/system-design.md](./system-design.md), with support from [docs/architecture/benchmark-admission-rubric.md](./benchmark-admission-rubric.md), [docs/architecture/scoring-semantics.md](./scoring-semantics.md), [docs/architecture/policy-calibration.md](./policy-calibration.md), [docs/analysis/requirements.md](../analysis/requirements.md), [docs/decisions/dependency-selection.md](../decisions/dependency-selection.md), [docs/draft/abstract.md](../draft/abstract.md), and the research notes under `docs/research/**`.

The contract is intentionally implementation-agnostic. It focuses on boundaries, commands, queries, events, state transitions, error semantics, idempotency, versioning, and audit fields. It does not define business code or low-level storage schemas.

## 2. Contracting Principles

- The system evaluates a whole agent configuration, not only a base model. This follows the system design and research corpus.
- The evaluated subject is the `ACUT` (`Agent Configuration Under Test`): model, prompt, tools, permissions, retrieval/memory, runtime budget, control loop, run environment, adapter manifest, evaluation mode, and adapter purity.
- Task generation, environment replay, validation, runner integration, canonical verification, scoring, and authorization are separate responsibilities. Do not merge them into one opaque service.
- Barcarolle is not the default agent controller. It must not silently replace the tested agent's prompt, tool loop, memory, model proxy, shell/edit interface, or controller. If the mode is `harness_native`, the evaluated subject is `Agent + Harness`.
- Benchmark identity, benchmark release publication, benchmark evaluation, and benchmark scorecards are first-class responsibilities. Do not infer them indirectly from whichever approved tasks or runs happen to exist.
- Policy calibration is a first-class responsibility. Do not hard-code score weights, coverage gates, reliability labels, or authorization thresholds as permanent assumptions when objective calibration evidence exists.
- Repository and organization risk appetite is a first-class policy input. Calibration and authorization must consume an explicit effective risk profile instead of inferring tolerance from benchmark outcomes.
- Benchmark admission is executable policy over existing task, validation, release, review, retirement, scorecard, authorization, admission, and operating-state resources. Do not create a parallel approval lane that bypasses those records.
- Scorecards are useful without a License: callers may use benchmark evidence for configuration comparison and optimization without invoking admission.
- Repository-agent admission contracts issue and explain Licenses for external consumers. They carry operating-envelope compatibility, signed License certificates, signed status records/logs, status receipts, and consumer audit records but do not implement runtime enforcement.
- `Golden Agent` and `Judge Agent` are explicit benchmark-side capabilities: Golden produces pre-candidate discovery artifacts and candidate-side reference artifacts for validation and review, while Judge produces run-side assessment outputs from sealed evidence for scoring and governance review.
- Repository-native evidence is the primary truth source for task validity. When a task cannot be replayed faithfully, the contract must allow rejection rather than silent approximation.
- All cross-module interactions must carry correlation and audit identifiers.
- Deterministic validation, scoring, and authorization remain primary; Golden/Judge outputs are additive evidence and review signals rather than silent overrides.
- `Inference`: the public transport can be HTTP, workflow activities, or internal jobs; the contract below is transport-neutral so the implementation can choose the best runtime fit later.

## 3. Module Boundaries

| Module | Owns | Exposes |
| --- | --- | --- |
| Repository Intake and Catalog | Repository metadata, history snapshots, source artifacts, and provenance. | Snapshot registration commands and snapshot lookup queries. |
| Signal Extraction | Structured signals derived from repository history. | Derived-signal queries and extraction completion events. |
| Candidate Task Miner | Candidate-generation runs and task candidates derived from repository signals, including pre-candidate Golden discovery evidence when used. | Candidate-generation-run commands, task-candidate creation commands, and candidate lookup queries. |
| Replay Planner | Base revision choice, verifier selection, and environment reconstruction plan for a task candidate. | Replay-plan commands and plan lookup queries. |
| Environment Reconstruction | Historical environment build inputs and build artifacts for a task candidate. | Build commands and environment lookup queries. |
| Task Validator | Candidate admissibility, replayability, contamination checks, approval gating, and any candidate-side Golden/reference artifacts attached during validation. | Validation commands, approval commands, validation lookup queries, and decision events. |
| Benchmark Registry and Release Publication | Stable benchmark definitions, immutable benchmark releases, release-membership snapshots, release coverage profiles, and supported/unsupported authorization scopes. | Benchmark-definition lookup queries, release-publication commands, benchmark-release queries. |
| Benchmark Evaluation | One ACUT evaluated against one benchmark release under one benchmark-level capability-envelope contract basis, evaluation mode, adapter purity, child-run coordination, and benchmark scorecards. | Benchmark-evaluation commands, evaluation-status queries, and scorecard queries. |
| Runner Integration Layer | Task package delivery, native-runner invocation, run-submission intake, adapter observation, and mode/purity recording. | Runner-invocation commands, run-submission commands, run-status queries, and coarse step events. |
| Evidence Store and Canonical Verification | Immutable traces, logs, diffs, run submissions, evidence trust tiers, and clean-room verification records. | Artifact append commands, canonical-verification commands, and evidence lookup queries. |
| Scoring and Stability Layer | Correctness score, process score, run stability assessment, and any run-side Judge outputs attached during scoring. | Score computation commands and score queries. |
| Policy Calibration | Automatic calibration manifests, objective controls, baseline runs, sensitivity analyses, calibrated policy profiles, and promotion/rollback lifecycle. | Calibration commands, profile queries, and calibration lifecycle events. |
| Risk Profile Governance | Organization, repository, and component/path risk-appetite profiles, inheritance, lifecycle transitions, and impact triggers. | Risk-profile registration, transition, lookup, and effective-profile resolution queries. |
| Authorization Policy | Trust tier and access decision. | Decision commands and decision queries. |
| Agent Governance and License Distribution | Repository-agent admissions, operating observations, operating-state coverage projections, signed License certificates, signed License status publication, lifecycle transition propagation, status receipt ingest, and consumer audit ingest. | Admission/change-review commands, operating-state queries, signed certificate/status queries, status lifecycle events, receipt commands, and consumption-audit commands. |

`Assumption`: module names may map to services, workers, or workflow activities, but ownership should remain stable even if deployment topology changes.

## 4. Core Data Contracts

### 4.1 Common identifiers

Every request, event, and stored record should carry the following minimum identifiers where applicable:

- `contract_version`
- `request_id`
- `correlation_id`
- `causation_id`
- `repository_id`
- `benchmark_definition_id`
- `benchmark_release_id`
- `benchmark_release_membership_id`
- `tested_agent_snapshot_id`
- `benchmark_evaluation_id`
- `benchmark_scorecard_id`
- `repository_agent_admission_id`
- `agent_change_review_id`
- `repository_agent_operating_state_id`
- `license_certificate_id`
- `license_status_id`
- `license_status_receipt_id`
- `license_consumption_audit_event_id`
- `target_condition_basis_identity`
- optional `task_candidate_id`, required when the review subject is a task candidate
- `task_id`
- `replay_plan_id`
- `run_id`
- `run_submission_id`
- `canonical_verification_record_id`
- `capability_envelope_id`
- `candidate_generation_run_id`
- `environment_id`
- `validation_result_id`
- `admission_review_id`
- `evidence_bundle_id`
- `assessor_configuration_id`
- `policy_calibration_run_id`
- `calibrated_policy_profile_id`
- `repository_risk_profile_id`
- `risk_profile_version`
- `source_revision` or `snapshot_id`
- `generation_context_lineage`
- `evaluation_mode`
- `adapter_purity_level`
- `evidence_trust_tier`
- `benchmark_admission_policy_version`
- `release_admission_policy_version`
- `scorecard_policy_version`
- `coverage_policy_version`
- `reliability_policy_version`
- `authorization_policy_version`

### 4.2 Repository snapshot

Minimum fields:

- repository provider and repository slug
- default branch
- source revision hash
- snapshot time or extraction time
- artifact provenance references

### 4.2a Candidate generation run

Minimum fields:

- `candidate_generation_run_id`
- repository and snapshot identity
- generation strategy and signal/input manifest digest
- optional governed `golden_configuration_id`
- optional Golden input-manifest digest, required and identity-forming when Golden is used
- selection policy version
- optional exact Golden output evidence-bundle version/content digest and selection/ranking identity from the append-only completion event
- semantic generation attempt number
- status and audit fields

This is the stable pre-candidate subject for Golden-assisted discovery, selection, and contract synthesis. It breaks the identity loop where a candidate's identity would otherwise need to reference evidence that could only be stored after the candidate existed.

### 4.3 Task specification

Minimum fields:

- approved task identity and source `task_candidate_id`
- task family
- source anchor, such as commit, issue, PR, or CI failure, as historical lineage only
- `source_refs[]`, source type, and fixed `T_task`
- source snapshot identity, optional `candidate_generation_run_id`, and generation-context lineage for regeneration-safe candidate identity; that lineage must include candidate-specific selection identity and Golden-assisted discovery/selection/contract-synthesis lineage when Golden materially contributed
- The rejected critique that `source_anchor` should join the natural key is not adopted; `generation_context_lineage` remains the identity axis.
- base revision
- target revision or expected transition
- allowed inputs, disallowed inputs, expected artifact shape, required permissions, component/path tags, capability tags, risk class, high-impact path classes, duplicate-cluster identity, and benchmark-admission gate summary
- approved verifier, environment, and validation-result references
- certified oracle grade and oracle-profile summary
- leakage clearance or contamination summary with queryable `leakage_kind[]`, `leakage_severity`, `leakage_handling_decision`, `leakage_review_required`, `acut_visible_surfaces[]`, `redaction_revalidation_lineage`, exact `leakage_report_ref`, and `leakage_report_digest`
- optional Golden/reference artifact references and confidence markers recorded during admission
- task status
- contamination or retirement flags

### 4.4 Benchmark definition and release

Minimum fields:

- stable benchmark identity
- repository identity and benchmark scope
- release identity and publication timestamp
- release provenance such as source snapshot or publication rationale
- immutable release-membership snapshot referencing the approved tasks included in the release
- release-admission policy version
- release coverage profile over task family, component/path, capability, risk, permission class, high-impact path class, oracle grade, duplicate cluster, flakiness/runtime, and source type
- supported authorization scopes and unsupported authorization scopes with missing-coverage reason codes
- release status such as draft, published, superseded, or retired

### 4.5 Benchmark evaluation and scorecard

Minimum fields:

- benchmark-evaluation identity
- benchmark-release identity used as the evaluation basis
- tested-agent snapshot identity
- optional upstream agent-configuration identity
- ACUT manifest identity and comparability axes: `evaluation_mode`, `adapter_purity_level`, adapter manifest identity, and run environment declaration
- ACUT field evidence-basis summary for declared, observed, attested, and trusted fields
- evaluation status and coverage summary
- stable `task_family_coverage` for task-family authorization gates, plus evaluated capability-envelope coverage summary, including minimum coverage thresholds and partial-evaluation policy
- authorization-readiness state derived from the coverage gate and partial-evaluation policy
- child-run references or release-membership references used by the evaluation
- benchmark-scorecard reference list for scorecards produced from the evaluation; each immutable scorecard still has its own `benchmark_scorecard_id`, aggregate metrics, `task_family_coverage`, complete `score_input_set_digest`, `evidence_trust_basis_digest`, scorecard policy, coverage policy, reliability policy, calibrated policy-profile ref when used, effective risk-profile ref/digest when appetite constraints affected the scorecard policy basis, aggregation algorithm, denominator summary, missing-run summary, weighting summary, reliability label, evaluated capability envelope, and comparability labels
- explicit flag when a result is ad hoc and not a full benchmark evaluation

Evaluation mode values are `patch_only`, `trace_submission`, `observed_run`, and `harness_native`. Adapter purity values are `A0_transport_only`, `A1_environment_wrapper`, `A2_tool_mediation`, and `A3_harness_native_controller`. Results from different values on either axis must not be mixed in scorecards or admission decisions without an explicit governed comparison rule. These values identify the evaluated subject and applicability boundary; they are not simple maximum-tier caps.

`evaluation_mode`, `adapter_purity_level`, adapter manifest identity, and run environment declaration on evaluation and run commands are consistency assertions against the referenced `tested_agent_snapshot`, not caller-controlled overrides. A mismatch with the snapshot's canonical values must be rejected as `policy_conflict` when the caller is trying to reuse an existing benchmark/run basis, or as validation error when the submitted value is malformed or unsupported. A fresh benchmark evaluation or run under different mode, adapter, or run-environment values requires a new tested-agent snapshot. Governed change review and target-condition basis records may justify admission carry-forward, reuse, or supplemented evidence, but they must not change the ACUT boundary of an executing benchmark fact.

### 4.5a Policy calibration and calibrated profile

### 4.5a.1 Repository risk profile

Minimum fields for `repository_risk_profile`:

- risk-profile identity
- optional organization identity and optional repository identity
- scope descriptor and deterministic inheritance/override basis
- risk-profile version, predecessor profile ref, and optional parent profile ref
- risk tolerance class, such as `conservative`, `balanced`, `expansive`, or `custom`
- constraint artifact ref and constraint digest
- tier eligibility or forbidden-tier matrix by `G0` through `G5`, permission class, risk class, task family, component/path, high-impact path class, target condition, evaluation mode, adapter purity, and evidence trust basis
- unsafe-control budget, minimum control-separation margins, coverage/reliability floors, evidence-basis requirements, ACUT-binding requirements, freshness ceilings, required review triggers, and calibration objective weights
- external-consumer assumption summary for License consumption, without defining a Barcarolle runtime enforcement plane
- lifecycle state: `draft`, `candidate`, `active`, `paused`, `superseded`, `rolled_back`, or `retired`
- activation, expiration, supersession, rollback, and audit fields

Risk profiles are policy appetite records. They can constrain calibration, scorecard materialization, authorization, admission effectivity, renewal, suspension, revocation, targeted validation, and rebenchmarking. They must not be accepted as human labels, objective calibration truth, task admission truth, or live runtime enforcement.

Effective risk-profile resolution must be deterministic. If organization, repository, and component/path profiles all exist, the response must state the selected or merged effective basis, every source profile ref, the final constraint digest, and conflict handling. A write-capable authorization request with no effective risk profile must be blocked unless it references a persisted seed profile basis.

Minimum fields for `policy_calibration_run`:

- calibration-run identity
- repository scope and target policy families
- effective `repository_risk_profile_id` or seed risk-profile basis, risk-profile version, risk-profile digest, inheritance/override basis, and risk-constraint summary
- trigger kind and run attempt number
- predecessor calibrated policy profile refs
- calibration input manifest digest and exact manifest ref
- calibration truth contract version, truth-observation manifest digest/ref, and truth-observation summary
- evidence slice coverage and exclusion summary
- automatic control and baseline summaries
- unsafe false-positive summary, positive-control false-negative summary, and high-tier authorization control summary
- repeated-run variance, canonical verification coverage, release coverage, and maintenance-finding summaries
- candidate profile refs, selected profile ref, sensitivity-analysis refs, impact-preview refs, promotion gate summary, status, blocker codes, and audit fields

Minimum fields for `calibrated_policy_profile`:

- calibrated-profile identity
- semantic policy family, such as `authorization_semantics_v1`
- repository scope and applicability slices
- effective risk-profile ref/version/digest and risk-constraint summary
- parameter digest and full parameter artifact ref
- calibration-run ref and input manifest digest
- exact `authorization_policy_version`, `scorecard_policy_version`, `coverage_policy_version`, `release_admission_policy_version`, and `reliability_policy_version` values governed by the profile
- evidence coverage, objective-control separation, held-out validation, repeated-run confidence, sensitivity, and impact-preview summaries
- truth basis digest, unsafe false-positive metrics, high-tier authorization applicability summary, and parameter authority summary
- lifecycle state: `candidate`, `shadow`, `active`, `paused`, `superseded`, `rolled_back`, or `blocked`

Calibration commands and events must not require a human baseline, human label, manual benchmark acceptance, or human participation in benchmark generation/running. Human governance records may annotate, pause, or roll back profile state, but normal profile truth is computed from objective evidence and automatic controls.

### 4.6 Replay environment specification

Minimum fields:

- runtime image or build recipe reference
- dependency resolution inputs
- network and tool policy
- seed or deterministic setup inputs where relevant
- build provenance and digest references

### 4.7 Evaluation run

Minimum fields:

- run identity
- task identity
- optional benchmark evaluation identity
- optional benchmark release-membership identity
- run basis type such as `benchmark_evaluation` or `ad_hoc`
- attempt number
- tested-agent snapshot identity
- optional upstream agent-configuration identity
- evaluation mode and adapter purity level
- adapter manifest identity, declared observation boundary, and run environment declaration
- ACUT identity field evidence-basis summary copied from the tested-agent snapshot
- run observation basis for adapter/wrapper observations that must not rewrite ACUT identity
- immutable capability envelope covering tool policy, network or egress posture, runtime limits, and evidence destination
- run-submission reference
- canonical-verification-record reference
- started and finished timestamps
- run status
- run outcome class and score state when terminal scoring has classified the run
- canonical verifier result
- score-bundle references including score input evidence digest when scored; a run summary must not select one score implicitly when multiple immutable score bundles exist
- evidence bundle reference, including exact sealed bundle version and content digest when the run summary points at evidence consumed by verification or scoring
- For benchmark-linked child runs, `benchmark_release_membership_id` is only unique within the parent `benchmark_evaluation_id`; consumers must not treat membership identity alone as a cross-evaluation run key.

### 4.7a Run submission and canonical verification

Minimum fields for `run_submission`:

- `run_submission_id`
- `run_id`
- `tested_agent_snapshot_id`
- `evaluation_mode`
- `adapter_purity_level`
- submitted patch/result/artifact references
- agent-submitted trace/log/tool/model summary references when present
- submission producer identity, timestamp, digest, and declared redaction state

Minimum fields for `canonical_verification_record`:

- `canonical_verification_record_id`
- `run_id`
- `run_submission_id`
- `task_id`, `environment_id`, and verifier identity
- clean-room workspace/image digest
- scoring-relevant policy version
- patch/result application status
- hidden-test or repository-native verifier outputs
- canonical pass/fail result and failure class
- `verification_attempt_number`
- exact sealed evidence bundle version/digest references and trusted Barcarolle evidence digest

Correctness and admission root evidence must come from `canonical_verification_record` and other `trusted_barcarolle_evidence`. Agent-submitted traces may affect audit confidence or risk flags, but must not independently decide pass/fail. Idempotent canonical-verification retries reuse the same `verification_attempt_number` and must reproduce the same trusted evidence digest and verifier evidence bundle digest. Semantic reverification under the same verifier basis uses a new attempt number so verifier repair or instability does not collide with the earlier record.

### 4.8 Authorization decision

Minimum fields:

- decision identity
- evaluated scope
- authorization policy version. `authorization_policy_version` is canonical; `policy_version` is a deprecated read/write alias for the same value during migration and must not be persisted as an independent second field.
- tested-agent snapshot identity
- evaluated subject label, requested admission subject, production-fidelity / subject-applicability basis, evaluation mode, adapter purity level, and ACUT identity
- target-condition basis identity and structured target-condition boundary
- score evidence basis showing which evidence trust tiers were used and which were score-contributing
- canonical-verification-record references for correctness root evidence
- score input set identity, denominator summary, missing-run summary, minimum sample summary, reliability label, and stability summary when the decision is scorecard-backed
- ACUT binding/attestation basis tying the submitted result to the tested-agent snapshot
- License-consumption compatibility basis for the requested repository operation surface
- consumer certificate/status profile basis for signed certificate validity defaults, optional unbounded certificate artifacts, status freshness, status-watermark, and lifecycle-sequence requirements
- policy gate results for correctness, subject applicability, ACUT binding/attestation, License-consumption compatibility, and risk-profile constraints
- authorized capability-envelope identity/coverage and partial-evaluation policy
- authorization-readiness state
- resulting trust tier or permission scope
- supporting benchmark release and benchmark scorecard references
- rationale summary
- reviewer or policy engine identity

`Inference`: direct authorization decisions remain benchmark-policy outputs over an immutable scorecard and therefore represent `fresh` evidence only relative to that exact scorecard identity, including its `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, calibrated policy-profile basis, effective risk-profile basis, `evaluated_capability_envelope_id`, evaluated subject, requested admission subject, production-fidelity basis, and gate basis. Later bounded reuse or supplementation under changed conditions must stay explicit on the change-review/admission side rather than being inferred as a rewritten benchmark fact.

### 4.9 Tested-agent snapshot

Minimum fields:

- `tested_agent_snapshot_id`
- optional upstream `agent_configuration_id`
- repository or repository-scope reference
- evaluated subject label such as `native_agent` or `Agent + Harness`
- model/provider identity
- prompt, tool, permission, memory, and runtime digests
- control-loop digest, run-environment declaration, adapter manifest digest, evaluation mode, and adapter purity level
- canonical artifact refs or equivalent durable evidence for prompt, tool profile, permission profile, memory strategy, and runtime policy
- ACUT field evidence basis map, using `declared`, `adapter_observed`, `third_party_attested`, or `barcarolle_trusted` per material ACUT field
- capture timestamp
- provenance summary

The tested-agent snapshot is the canonical identity for the ACUT being evaluated, but each material field must retain its evidence basis. In `patch_only` and `trace_submission`, native workspace, network, tool posture, and some runtime-environment fields are usually `declared` or at most `third_party_attested`, not `barcarolle_trusted`; admission and console reads must preserve that distinction instead of presenting all ACUT fields as equally verified. Those modes can still support high-tier native YOLO admission when correctness evidence, production fidelity, ACUT binding/attestation, and License-consumption compatibility pass. If the mode is `harness_native`, the subject label is `Agent + Harness`.

### 4.10 Agent change review

Minimum fields:

- `agent_change_review_id`
- repository scope
- baseline `tested_agent_snapshot_id`
- candidate `tested_agent_snapshot_id`
- baseline and candidate ACUT field evidence-basis summaries
- optional baseline `benchmark_evaluation_id`
- optional baseline `benchmark_scorecard_id`
- optional prior `repository_agent_admission_id`
- structured change classification across execution-condition, ACUT field evidence-basis, and interpretation/authorization deltas
- target-condition basis identity and structured target-condition boundary
- optional evidence-lineage label such as `reused` or `supplemented`, required only when accepted carry-forward evidence is being recorded
- review outcome such as `carry_forward_acceptable`, `targeted_review_required`, or `full_rebenchmark_required`
- reviewer identity, review timestamp, and rationale summary
- applicability boundaries across scope, time, and admitted evolution state

### 4.11 Repository-agent admission/license

Minimum fields:

- `repository_agent_admission_id`
- `repository_id` and scope descriptor
- admitted `tested_agent_snapshot_id`
- admission basis kind plus one or more supporting references such as `benchmark_evaluation_id`, `benchmark_scorecard_id`, `authorization_decision_id`, or `agent_change_review_id`
- evidence-lineage label: `fresh`, `reused`, or `supplemented`
- evaluated subject label and admitted subject, such as native YOLO or harness-bound operation
- production-fidelity / subject-applicability basis for the admission
- evaluation mode, adapter purity level, canonical-verification basis, and evidence trust tiers covered by the admission
- ACUT field evidence-basis summary covered by the admission
- ACUT binding/attestation basis and License-consumption compatibility basis
- policy gate results that justify the granted tier
- target-condition basis identity and structured target-condition boundary
- covered capability-envelope identity/coverage and authorization-readiness state
- admission status and effective window
- freshness or expiry boundary
- admission lifecycle sequence and consumer certificate/status profile
- latest signed License-certificate ref, status ref/watermark, or certificate availability state when materialized
- reviewer or policy identity
- rationale summary

The scope descriptor for admission and authorization must include the repository/resource boundary plus the permission action or risk class. Execution posture, evaluated subject, admitted subject, mode, adapter boundary, License-consumption compatibility basis, and interpretation basis belong in `target_condition_basis_identity` / `target_condition_basis`, so effectivity can be resolved per authorization boundary rather than per repository alone.

### 4.12 Repository-agent operating observation and state

Minimum fields for append-only operating observation:

- `repository_agent_operating_observation_id`
- `repository_id` and scope descriptor
- observed `tested_agent_snapshot_id`
- `state_source`
- optional `evaluation_mode` and `adapter_purity_level` observed or declared for this live state
- optional `adapter_manifest_digest`
- optional `target_condition_basis_identity`
- optional supporting `repository_agent_admission_id`
- optional supporting `agent_change_review_id`
- observed timestamp
- observer identity or source provenance
- summary for audit and operator reads

If the operating observation links to an admission or change review, any supplied mode, purity, adapter manifest, or target-condition basis must match the linked basis or be recorded as a drift/conflict observation rather than silently overriding the projection. If no admission/change review is linked, these fields are the observation's own basis for projecting uncovered or outside-admission state.

Minimum fields for derived operating state:

- `repository_agent_operating_state_id`
- `repository_id` and scope descriptor
- current `tested_agent_snapshot_id`
- coverage state such as exact-match, carry-forward-admitted, pending-targeted-review, rebenchmark-required, or outside-admission
- evidence-lineage label: `fresh`, `reused`, or `supplemented`
- selected/default evaluated subject, admitted subject, production-fidelity basis, evaluation mode, adapter purity level, canonical-verification basis, and evidence trust-tier summary for list views
- ACUT identity field evidence-basis summary, ACUT binding/attestation basis, and License-consumption compatibility basis for the selected/default basis
- run observation-basis summary for the selected/default basis, kept separate from ACUT identity
- `coverage_entries[]`, with one entry per target-condition coverage basis including stable coverage entry identity, admission/review refs, evaluated subject, admitted subject, production-fidelity basis, mode, purity, adapter manifest digest, target-condition basis, coverage and drift state, granted trust tier, admission status, freshness state/deadline, risk-profile basis and gate result, evidence lineage, canonical-verification basis, evidence trust-tier basis, ACUT identity field basis, ACUT binding/attestation basis, License-consumption compatibility basis, run observation basis when applicable, covered capability-envelope identity/coverage, admission lifecycle sequence, certificate profile, status-freshness profile, signed-certificate availability, latest status watermark, and next required action
- optional selected/default `repository_agent_admission_id` for summary display
- optional latest `agent_change_review_id`
- operating-state version and latest signed certificate/status summary for consumer reads
- observed timestamp and state source
- summary for operator read models

### 4.12a License certificate, status, receipt, and audit event

Minimum fields for a signed License certificate:

- `license_certificate_id`, certificate digest, contract/schema version, canonicalization algorithm, issuer, certificate signing-key id, issuer key-set version, issuer-key status ref/digest, issuer-key status and validity window, signing algorithm, signature, signed timestamp, and key-status checked timestamp
- `certificate_valid_not_before`, nullable `certificate_valid_not_after`, optional `renew_after`, certificate-validity profile basis, `status_surface_ref`, `status_sequence_at_issuance`, `status_watermark_at_issuance`, `max_status_staleness`, and optional `next_status_poll_after`
- `repository_id`, scope descriptor, `repository_agent_admission_id`, `repository_agent_operating_state_id`, coverage entry id, target-condition basis identity, target-condition basis digest, admission lifecycle sequence, operating-state version, and event/status watermark for `issued` certificates
- admitted tested-agent snapshot identity, evaluated subject, admitted subject, subject-applicability basis, ACUT field evidence-basis summary, ACUT binding/attestation basis, License-consumption basis, covered capability-envelope identity/digest, operation/risk inclusions and exclusions, admission status at issuance, granted tier, evidence lineage, freshness state/deadline, risk-profile basis, policy gate results, supporting refs, supersession refs, certificate state, and non-consumable reason codes when applicable

The certificate is the durable signed License artifact. An `issued` certificate must bind one admission to exactly one current operating-state coverage entry; admission-only or ambiguous projections are explicit `non_consumable` diagnostics. The certificate is consumer-verifiable and cacheable until its explicit validity expiry when one is present; the seed policy allows unbounded certificate artifacts because current Barcarolle-conformant `allow` is governed by fresh signed status. It is not a session/run lease, a runtime checkpoint, or live-process attestation.

Minimum fields for signed License status:

- `license_status_id`, optional status-log-entry id, certificate id/digest, admission id, operating-state id, coverage entry id, target-condition basis identity, status sequence, status watermark, previous status digest, log root/segment digest, and event-stream watermark
- lifecycle state (`effective`, `suspended`, `revoked`, `expired`, `superseded`, `non_consumable`, or `issuer_key_invalid`), transition kind, cause codes, reviewer or policy identity, status effective timestamp, published timestamp, optional `consumer_deny_after`, admission lifecycle sequence, operating-state version, freshness state/deadline, granted tier, superseding refs, certificate validity summary, certificate-signing-key status, status-signing-key status, `max_status_staleness`, `status_fresh_until`, signature, and signed timestamp

Minimum fields for signed issuer-key status:

- `issuer_key_status_ref`, issuer identity, issuer key id, issuer key-set version, governed public-key digest, key purpose (`certificate_signing`, `status_signing`, or both), issuer-key status, status sequence, key-status watermark, previous key-status digest/log pointer, event-stream watermark, published timestamp, and status effective timestamp
- key validity window, optional retirement timestamp, optional emergency-retirement timestamp, optional revocation timestamp, cause codes, key-status signer identity, key-status signing-key id, signer key-set or trust-anchor version, signing algorithm, canonicalization algorithm, key-status digest, signature, and signed timestamp

Minimum fields for a status receipt:

- `license_status_receipt_id`, consumer identity/version, receipt source, received timestamp, acknowledged timestamp, certificate id/digest, status id/digest, status sequence, status watermark, event-stream watermark, key-status refs/digests, verification result, receipt result, and reason codes

Minimum fields for a License-consumption audit event:

- `license_consumption_audit_event_id`, consumer identity/version, operation correlation id, and consumer decision timestamp
- requested repository, scope, operation, risk class, target condition, tested-agent snapshot, admission subject, and capability-envelope digest
- result and machine-readable reason codes
- local policy overlay result, certificate identity/digest, status identity/digest/watermark, certificate and status issuer-key status refs/digests, signature verification results, admission id, operating-state id, coverage entry id, lifecycle sequence, operating-state version, event-stream watermark, granted tier, admission status, freshness state/deadline, certificate validity timestamps, status freshness timestamps, evidence lineage, risk-profile basis, policy gate basis, and failure mode when applicable

Status receipts and audit events are append-only explanations of consumer acknowledgement and behavior. They may be submitted to Barcarolle for compliance review and stale-consumer reporting, but they do not give Barcarolle runtime action authority.

### 4.13 Admission review record

Minimum fields:

- `admission_review_id`
- review subject kind such as task candidate, validation result, benchmark release, task retirement, release maintenance finding, or post-release invalidation
- `task_candidate_id`
- optional `validation_result_id`
- optional benchmark-release or retirement reference when review applies to release certification or post-release maintenance
- optional release-maintenance-finding reference when review applies to post-release invalidation outside a single task retirement
- `review_required`
- `review_state`: `pending`, `approved`, `rejected`, `repair_required`, `waived_warning`, or `retired`; candidate projections may additionally use `not_required`
- `compliance_state`
- deterministic gate summary
- review reason codes and required fixes
- waived warning codes when the rubric allows a warning to be waived
- reviewer identity
- reviewed timestamp
- rationale summary
- supersession or prior-review reference where applicable

Hard benchmark-admission failures such as confirmed future/answer leakage, no faithful replay, or D-grade sole oracle are not valid waiver targets for certified tasks.

`repair_required` review records require `required_fixes[]` and block approval until repair and revalidation produce a superseding review. `waived_warning` records require `waived_warning_codes[]` and only apply to non-hard warnings.

### 4.13a Leakage report and post-release finding

Minimum fields:

- `leakage_report_id`, subject kind and subject identity
- `T_task`, source-time evidence refs, agent-visible input inventory, and ACUT-visible surface entries with refs or digests
- `leakage_kind[]`, `leakage_severity`, `leakage_handling_decision`, `review_required`, redaction/revalidation lineage, report ref, and report digest
- `release_maintenance_finding_id` when a post-release finding applies beyond a single retired task
- release-maintenance subject kind and subject ref
- finding type, cause code, invalidation severity, evidence refs, affected release memberships, scorecards, authorization decisions, repository-agent admissions, required next actions, finding status, and effective timestamp

Task-level quarantine uses `task_retirement`; release-wide, scorecard, authorization-decision, repository-admission, and release-coverage invalidation uses `release_maintenance_finding`.

### 4.14 Controlled assessor artifact reference

Minimum fields:

- artifact identity
- artifact type
- evidence producer identity
- evidence trust tier: `trusted_barcarolle_evidence`, `adapter_observed_evidence`, `agent_submitted_evidence`, or `third_party_evidence`
- source class such as task digest, canonical verifier log, wrapper observation, native trace, CI result, or provider report
- summary or summary reference safe for default read surfaces
- digest and whether the artifact is score-contributing
- parent evidence bundle identity, manifest version, and content digest when the artifact is part of a sealed evidence bundle version
- optional assessment contribution mode, such as `advisory` or `score_contributing`, when the artifact is emitted by Judge-side scoring logic
- `sensitivity_label`
- `redaction_state`
- `audience_scope`
- `blind_safe`
- `default_access`
- optional full artifact reference when policy allows

Golden and Judge artifact refs should use this contract so validation, scoring, and UI reads can distinguish safe summaries from restricted answer-bearing payloads. Agent-submitted artifacts should be marked as audit evidence unless a separate Barcarolle trusted verification record makes the underlying result score-contributing.

Evidence bundles are append-only versioned manifests. The immutable bundle identity is `subject_type + subject_id + bundle_kind + manifest_version` or the opaque `evidence_bundle_id` derived from that tuple and manifest digest. Supported subjects include `candidate_generation_run`, `task_candidate`, `validation_result`, `leakage_report`, `task`, `task_retirement`, `release_maintenance_finding`, `environment`, `evaluation_run`, `run_submission`, and `canonical_verification_record`. `subject_type + subject_id + bundle_kind` is only the logical current/latest series used by read projections. This lets pre-candidate Golden discovery artifacts attach to `candidate_generation_run`, and post-candidate Golden validation artifacts attach before task approval without inventing a `task_id`. Backfill and artifact repair must append a new sealed bundle version instead of mutating an earlier version, and any score, Judge assessment, canonical verification, scorecard, or authorization explanation must retain the exact bundle version and content digest it consumed.

### 4.15 Governed assessor configuration

Minimum fields:

- `assessor_configuration_id`
- `configuration_fingerprint`
- assessor kind such as `golden` or `judge`
- repository or repository-scope reference
- model/provider identity and configuration digests
- output schema version
- governance state such as registered, candidate, shadow, advisory, active, superseded, or rolled back
- predecessor or superseded configuration reference where applicable
- comparison baseline reference where applicable
- promotion-review reference or rationale summary

The backend must recompute `configuration_fingerprint` from normalized model, prompt, tool, memory, runtime, output-schema, and assessor-role descriptors. `repository_scope + assessor_kind + configuration_fingerprint` is the natural key; any material configuration change registers a new assessor configuration before lifecycle transitions can promote it.

## 5. Synchronous Interfaces

The following command/query set is the stable minimum.

### 5.1 Repository intake

- `RegisterRepositorySnapshot`
  - Input: repository identity, source revision, snapshot provenance, and import mode.
  - Output: registered snapshot identity and import status.
  - Use when a repository or new revision enters the system.

- `GetRepositorySnapshot`
  - Input: repository identity plus revision or snapshot selector.
  - Output: snapshot metadata, provenance, and available artifact pointers.

- `ListRepositorySnapshots`
  - Input: repository identity and optional time or revision filter.
  - Output: ordered snapshot summaries.

### 5.2 Signal extraction and task mining

- `ExtractRepositorySignals`
  - Input: snapshot identity.
  - Output: structured signals and extraction status.

- `ReserveCandidateGenerationRun`
  - Input: repository identity, snapshot identity, generation strategy, signal/input manifest digest, optional governed Golden configuration identity, Golden input-manifest digest when Golden is used, selection policy version, and semantic generation attempt number.
  - Output: candidate-generation-run identity and reserved generation-run record.
  - This command is the write path for reserving pre-candidate Golden discovery, selection, or contract-synthesis evidence before a candidate exists. Evidence bundles created before candidate creation must use `candidate_generation_run` as their subject.
  - The natural key includes `golden_input_manifest_digest` when Golden is used, so two different Golden input packages cannot collapse into one generation run.

- `CompleteCandidateGenerationRun`
  - Input: candidate-generation-run identity, completion status, optional failure cause and completion summary, optional exact Golden output evidence-bundle version/content digest, and selected output digest plus selection/ranking identity when the completion status is `completed`.
  - Output: append-only completion-event identity and projected generation-run record.
  - Completion appends metadata to the generation-run event stream. It does not rewrite the reserved natural key. `failed` or `superseded` completions may omit selected-output fields but must carry a failure cause or summary. A different completion for the same reserved run is `policy_conflict` unless it uses a new semantic attempt number.

- `GetCandidateGenerationRun`
  - Input: candidate-generation-run identity.
  - Output: reserved basis, completion metadata when present, exact output evidence-bundle refs, and linked task candidates.

- `ListCandidateGenerationRuns`
  - Input: repository identity plus optional snapshot, Golden configuration, status, time, or pagination filters.
  - Output: ordered generation-run summaries, including runs that produced no task candidate.

- `CreateTaskCandidate`
  - Input: snapshot identity, optional candidate-generation-run identity, signal references, task family, source anchor, source refs, fixed `T_task`, generation-context lineage, task statement, allowed/disallowed inputs, expected artifact shape, required permissions, capability/component/risk tags, duplicate-cluster identity, provisional oracle-profile draft, provisional leakage-risk summary with `leakage_kind[]`, severity, handling decision, ACUT-visible surfaces, exact report ref/digest when available, and optional Golden-assisted discovery/selection/contract-synthesis refs.
  - Output: task candidate identity and draft status.
  - The command must not invent task semantics that are unsupported by repository evidence. When Golden materially contributed before candidate creation, the referenced `candidate_generation_run_id`, governed configuration identity, selected output digest, exact evidence-bundle version/content digest, and selection identity must be part of the generation-context lineage.
  - The command reserves admission metadata for later validation; it does not certify the candidate.

- `GetTaskCandidate`
  - Input: task candidate identity.
  - Output: stored candidate draft, lifecycle status, source evidence references, `T_task`, admission gate draft, leakage report refs, oracle-profile draft, capability/risk tags, duplicate-cluster summary, and admission-review lineage fields such as `review_required`, `review_state`, review reason codes, and latest review references.

- `ListTaskCandidates`
  - Input: repository identity plus optional snapshot, status, task-family, `review_state`, `review_required`, or compliance filters.
  - Output: ordered candidate summaries.

- `ApproveTaskCandidate`
  - Input: task candidate identity, a successful validation result identity, automated task-admission policy result or digest, and optional admission-review identity only when approval follows a governance exception, annotation, or override.
  - Output: approved task identity, approval status, and the stable `approval_record` defined as an admission-review record.
  - Approval is the step that materializes the canonical `task` resource after validation and automated policy admission succeed.
  - `review_required` is governance routing metadata, not a normal benchmark-acceptance prerequisite. If the validation result is `needs_review`, ambiguous, leaky, unsafe, weak, or unreplayable, normal approval is blocked until objective repair/revalidation produces a certifying policy result. An exceptional governance override may be recorded, but that path is excluded from normal calibration evidence unless a later objective validation basis certifies it.
  - The referenced validation result must carry `admission_verdict = certify`, oracle grade A or B, passed required probes, no confirmed leakage, and a satisfied task-quality gate summary under the active benchmark-admission policy.

- `CreateAdmissionReviewRecord`
  - Input: review subject kind, subject identity such as task candidate, validation result, benchmark release, task retirement, or release maintenance finding, reviewer identity, review decision (`pending`, `approved`, `rejected`, `repair_required`, `waived_warning`, or `retired`), compliance state, deterministic gate summary, review reason codes, required fixes or waived warnings when applicable, rationale, and optional supersession reference.
  - Output: durable admission-review identity and the stored admission-review record.
  - This is the explicit write entrypoint for governance lineage used by annotation, pause, repair, rollback, override, or exceptional policy ownership.
  - `repair_required` requires required fixes; `waived_warning` requires waived warning codes and cannot waive hard failures.

- `RetireTaskCandidate`
  - Input: task candidate identity and retirement cause.
  - Output: terminal retirement status.

- `CreateReleaseMaintenanceFinding`
  - Input: release-maintenance subject kind and subject ref, benchmark release identity, finding type, cause code, invalidation severity, optional leakage summary fields and exact report ref/digest, evidence refs, affected release/scorecard/authorization/admission refs where known, required next actions, finding status, review requirement, reviewer identity, and rationale.
  - Output: release-maintenance-finding identity, stored finding, and invalidation impact summary.
  - This is the post-release path for release-wide coverage drift, scorecard invalidation, authorization-decision invalidation, repository-admission suspension/revocation basis, and leakage findings that are not solely represented by a task retirement.

- `GetAdmissionReviewRecord`
  - Input: admission-review identity.
  - Output: stored admission-review record with reviewer, decision, timestamp, rationale, and compliance fields.

- `ListAdmissionReviewRecords`
  - Input: one of task candidate identity, validation-result identity, or repository identity, plus optional `review_state`, `review_required`, `compliance_state`, or reviewer filters.
  - Output: ordered admission-review summaries.

### 5.3 Replay planning and environment reconstruction

- `PlanReplayEnvironment`
  - Input: task candidate identity, base revision, and dependency clues.
  - Output: replay plan, chosen verifier, and reconstruction strategy.
  - Replay planning operates on the candidate before approval.

- `GetReplayPlan`
  - Input: replay plan identity.
  - Output: stored replay plan, feasibility status, and linked candidate or task reference.

- `ListReplayPlans`
  - Input: one of task candidate identity or task identity, plus optional feasibility or time filters.
  - Output: ordered replay-plan summaries.

- `BuildReplayEnvironment`
  - Input: replay plan and build policy.
  - Output: environment identity, build artifact references, and build status.

- `GetReplayEnvironment`
  - Input: environment identity.
  - Output: stored environment metadata, build status, reproducibility label, and linked plan reference.

- `ListReplayEnvironments`
  - Input: one of task candidate identity, task identity, or replay plan identity, plus optional status filters.
  - Output: ordered environment summaries.

- `ValidateReplayEnvironment`
  - Input: environment identity and task candidate identity.
  - Output: validation result identity, validity decision, reproducibility label, benchmark-admission policy version, oracle profile and grade, validation probe results, queryable leakage fields (`leakage_kind[]`, severity, handling decision, review requirement, ACUT-visible surfaces, redaction/revalidation lineage, report ref, and report digest), task-quality gate summary, admission verdict, review reason codes, failure cause if any, and optional Golden/reference artifact references when the validation path produced them.
  - Validation operates on the candidate and produces the approval prerequisite for task materialization.
  - Grade C evidence, including Golden/Judge/human rubric signals, is advisory. Grade D oracles reject or quarantine the candidate and cannot be used as the sole certified-task oracle.

- `GetValidationResult`
  - Input: validation result identity.
  - Output: stored validation verdict, contamination flags, reproducibility label, oracle profile, validation probe results, leakage report summary fields and exact report ref/digest, task-quality gate summary, optional Golden/reference artifact references, linked candidate or task reference, and any attached admission-review lineage.

- `ListValidationResults`
  - Input: one of task candidate identity, task identity, or environment identity, plus optional verdict filters.
  - Output: ordered validation-result summaries.

`Inference`: the planner and builder may be split across multiple workers, but the contract should still present them as distinct responsibilities because replay failure and task failure are different outcomes.

### 5.4 Benchmark registry and release publication

- `GetBenchmarkDefinition`
  - Input: benchmark-definition identity.
  - Output: stable benchmark definition, repository scope, and current release pointers.

- `ListBenchmarkDefinitions`
  - Input: repository identity plus optional scope or status filters.
  - Output: ordered benchmark-definition summaries.

- `PublishBenchmarkRelease`
  - Input: benchmark-definition identity, approved-task references or publication rule, release note, publication policy, and release-admission policy version.
  - Output: immutable benchmark release identity, membership snapshot identity, release coverage profile, supported authorization scopes, unsupported authorization scopes, release certification verdict, and publication status.
  - Release publication is the canonical step that freezes the benchmark basis for later comparison.
  - Certified release publication must reject D-grade membership, confirmed leakage, and unsupported authorization claims. Non-certified diagnostic releases may be published only with explicit status and must not support repository-agent authorization.

- `GetBenchmarkRelease`
  - Input: benchmark-release identity.
  - Output: stored release metadata, immutable release-membership snapshot, release coverage profile, supported/unsupported authorization scopes, release-admission policy version, certification verdict, and any linked release-admission review records.

- `ListBenchmarkReleases`
  - Input: benchmark-definition identity plus optional publication-state or time filters.
  - Output: ordered benchmark-release summaries.

- `GetBenchmarkScorecard`
  - Input: benchmark-scorecard identity.
  - Output: benchmark-level aggregate result tied to one benchmark release and one tested-agent snapshot, with explicit scoring semantics version, `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, `calibrated_policy_profile_id` or seed basis, risk-profile ref/version/digest when scorecard policy used appetite constraints, aggregation algorithm, aggregate score, diagnostic completed score, complete `score_input_set_digest`, denominator summary, weighting summary, missing-run summary, minimum sample summary, reliability label, top-level `task_family_coverage`, release coverage profile ref or digest, release-admission policy version, release certification verdict, supported/unsupported-scope summary, `evaluated_capability_envelope_id`, evaluated capability-envelope coverage, authorization-readiness summary, invalidation status and refs when post-release findings affect the basis, and optional upstream agent-configuration reference when available.
  - Authorization policy must read task-family thresholds, missing release weight, critical-family flags, and benchmark-basis-change flags from `task_family_coverage`; `coverage_summary` is aggregate and `metric_breakdown` is diagnostic.
  - Authorization policy must also respect the release's `supported_authorization_scopes[]` and `unsupported_authorization_scopes[]`; scorecard completion can narrow support but cannot widen beyond the release profile.
  - Missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, or blocked entries must appear in the score input set and missing-run summary; callers must not infer denominator coverage only from contributing score-bundle refs.
  - Exact get must not accept only `benchmark_evaluation_id`, because one benchmark evaluation can have multiple immutable scorecards under different scorecard policy, coverage policy, evaluated capability envelope, score input set, evidence trust basis, or score-basis Judge lineage.
  - If fresh benchmark-authoritative interpretation is needed under a changed coverage policy, risk profile, or a different evaluated capability envelope, callers must materialize or select the scorecard keyed to that full basis; reinterpreting an older scorecard in place must not be described as fresh evidence.

- `ListBenchmarkScorecards`
  - Input: benchmark-evaluation identity plus optional complete scorecard-basis filters such as scorecard policy version, coverage policy version, evaluated capability envelope, evaluation mode, adapter purity, score input set digest, evidence trust-basis digest, and score-basis Judge lineage.
  - Output: ordered benchmark-scorecard summaries.
  - List queries may support exact semantic resolution when the full basis is supplied, but incomplete selectors must remain multi-result instead of selecting an implicit scorecard.

### 5.5 Task registry

- `GetTask`
  - Input: task identity.
  - Output: approved task metadata plus the validation and environment references that admitted it.

- `ListTasks`
  - Input: repository identity plus optional status, task-family, retirement, or approval-time filters.
  - Output: ordered approved-task summaries.

- `RetireTask`
  - Input: task identity, retirement or quarantine cause, invalidation severity, optional leakage summary fields and exact leakage report ref/digest when leakage-related, finding source, evidence refs, optional affected release/scorecard/admission refs, optional replacement task, reviewer identity, and rationale.
  - Output: durable task-retirement identity and the stored retirement/quarantine record.
  - This is the post-approval path for leakage, oracle invalidation, flakiness, duplicate overweight, source-provenance failure, replay drift, or policy retirement. It must not edit historical benchmark releases or scorecards in place.

### 5.6 Tested-agent snapshots and evolution governance

- `RegisterTestedAgentSnapshot`
  - Input: repository scope, stable `snapshot_fingerprint`, optional upstream agent-configuration identity, evaluated subject label, the digests or descriptors that define the evaluated agent setup, `acut_field_evidence_basis`, and provenance or attestation refs supporting every non-`declared` basis value.
  - Output: immutable tested-agent snapshot identity and snapshot summary.
  - This is the canonical write path for the evaluated-reference resource used by benchmark evaluations, later change reviews, admissions, and operating-state projections. `tested_agent_snapshot_id` remains the canonical opaque identity; `snapshot_fingerprint` is the stable natural-key/idempotency anchor for the same repository-scoped snapshot contents.
  - The backend must validate that `acut_field_evidence_basis` uses only legal `ACUTFieldEvidenceBasis` values, covers every material ACUT field required by the contract, and is consistent with provenance, adapter manifest, and attestation refs. For example, `third_party_attested` requires a third-party artifact reference, and `barcarolle_trusted` requires a Barcarolle-produced trusted evidence reference.
  - The backend must recompute the canonical `snapshot_fingerprint` from the submitted repository-relevant digests, descriptors, subject label, and ACUT field evidence-basis map before persistence. If a caller-supplied fingerprint does not match the recomputed canonical value, the command must reject the request rather than persisting a mismatched identity. Upgrading evidence basis, for example from `declared` to `third_party_attested` or `barcarolle_trusted`, creates a new tested-agent snapshot instead of mutating the old row.

- `GetTestedAgentSnapshot`
  - Input: tested-agent snapshot identity.
  - Output: immutable tested-agent snapshot detail, including the repository-relevant configuration digests, canonical artifact refs, ACUT field evidence-basis map, supporting provenance/attestation refs, and external configuration reference when present.

- `ListTestedAgentSnapshots`
  - Input: repository identity or scope, plus optional upstream agent-configuration identity, time, or fingerprint filters.
  - Output: ordered tested-agent snapshot summaries.

- `RecordAgentChangeReview`
  - Input: repository scope, baseline tested-agent snapshot identity, candidate tested-agent snapshot identity, supporting benchmark-evaluation or scorecard reference, structured change classification across execution-condition, ACUT field evidence-basis, and interpretation/authorization deltas, explicit target-condition basis, optional evidence-lineage label, requested scope, reviewer identity, and review rationale.
  - The request may include caller-provided baseline/candidate ACUT field evidence-basis summaries or an explicit `acut_field_evidence_basis_delta` for readability, but the backend must derive canonical summaries from the referenced snapshots and reject mismatches.
  - Output: append-only agent-change-review identity and stored review record, including backend-derived baseline/candidate ACUT field evidence-basis summaries and the field-basis delta used by the review.
  - The contract must support explicit outcomes such as `carry_forward_acceptable`, `targeted_review_required`, `full_rebenchmark_required`, and `blocked`.
  - Baseline and candidate snapshot identities may match only when the reviewed change is outside the ACUT identity, such as interpretation policy or a narrower authorization target condition. If evaluation mode, adapter purity, adapter manifest, run-environment declaration, or ACUT field evidence basis changes, the candidate must be a new tested-agent snapshot before any fresh benchmark/run can use that boundary.
  - The target-condition basis must separate the target execution boundary from the target interpretation or authorization basis so later audit can answer exactly what was approved.
  - `evidence_lineage` is only valid when `review_outcome = carry_forward_acceptable`; non-accepting outcomes must leave lineage absent rather than inventing a sentinel state.

- `GetAgentChangeReview`
  - Input: agent-change-review identity.
  - Output: stored change review with baseline fact references, baseline/candidate ACUT field evidence-basis summaries, field-basis delta, structured delta classification, explicit target-condition basis, optional evidence-lineage label, outcome, reviewer identity, rationale, and applicability boundaries.

- `ListAgentChangeReviews`
  - Input: repository identity or scope, baseline or candidate tested-agent snapshot identity, and optional outcome or time filters.
  - Output: ordered change-review summaries.

- `RecordRepositoryAgentAdmission`
  - Input: repository identity, scope, admitted tested-agent snapshot identity, admission basis, explicit target-condition basis, evidence-lineage label, granted trust tier, status, freshness deadline, optional consumer certificate/status profile, reviewer or policy identity, and rationale.
  - Output: repository-agent admission identity and stored admission record, including granted trust tier, evidence-lineage label, explicit target-condition basis, evaluated capability-envelope coverage, freshness deadline, admission lifecycle events, lifecycle sequence, certificate/status availability state, and authorization-readiness state.
  - This is the explicit write path for repository license or admission lineage. It must never overwrite the historical benchmark evaluation fact that justified the record.
  - `scope` must include the repository/resource boundary plus the permission action or risk class being authorized. The target-condition basis carries the execution posture, evaluation mode, adapter boundary, and interpretation basis.
  - For any one `repository_id + scope + target_condition_basis_identity`, at most one admission may be effective at a time. A new effective admission for the same tuple must supersede the prior effective admission in the same append-only workflow transition. Different target-condition bases, such as native YOLO `patch_only`, observed-wrapper, and harness-bound admissions, may coexist for the same repository/resource scope when policy allows them.

- `RecordRepositoryAgentAdmissionTransition`
  - Input: repository-agent admission identity, transition kind (`suspend`, `lift_suspension`, `supersede`, `revoke`, or `expire`), previous status, next status, cause, optional resolution summary, evidence refs, reviewer or policy identity, reviewed timestamp, and effective timestamp.
  - Output: append-only admission lifecycle event plus the refreshed admission projection, new lifecycle sequence, affected certificate refs, and latest status watermark when known.
  - `lift_suspension` is valid only from `suspended` to `effective` on the same admission when admitted snapshot, scope, target-condition basis, covered capability envelope, evaluated/admitted subject, subject-applicability basis, granted tier, evidence basis, gate basis, and freshness deadline are unchanged.
  - If any of those fields change, the caller must write a new effective admission that supersedes the suspended admission instead of lifting it.

- `GetRepositoryAgentAdmission`
  - Input: repository-agent admission identity.
  - Output: stored admission record with admitted snapshot, basis references, granted trust tier, evidence-lineage label, explicit target-condition basis, effective window, freshness boundary, status, admission lifecycle events, evaluated capability-envelope coverage, and authorization-readiness state.

- `ListRepositoryAgentAdmissions`
  - Input: repository identity or scope, admitted tested-agent snapshot identity, and optional status or time filters.
  - Output: ordered repository-agent admission summaries.

- `RecordRepositoryAgentOperatingObservation`
  - Input: repository identity, scope, observed tested-agent snapshot identity, state source, optional evaluation mode, optional adapter purity level, optional adapter manifest digest, optional target-condition-basis identity, optional linked admission or change-review identity, and observed timestamp.
  - Output: append-only operating-observation identity plus the refreshed operating-state summary for that repository scope, including coverage, drift, evidence-lineage labels, evaluated/admitted subject labels, risk-profile basis, ACUT identity field evidence-basis summary, ACUT binding/attestation basis, License-consumption compatibility basis, run observation-basis summary, and `coverage_entries[]` for every target-condition basis that currently covers or fails to cover the live snapshot. Each entry must include granted tier, admission status, freshness state, freshness deadline, and risk-profile gate result.
  - This is the explicit write path for live-state facts. The derived operating-state read model is intentionally separate from benchmark evaluation and admission because it answers what is live now, not only what was previously judged.
  - If linked admission or change-review identity is present, supplied mode, purity, adapter, and target-condition-basis values must match that linked basis or be surfaced as drift/conflict instead of silently overriding it. If no linked basis is present, the supplied values are operating-observation metadata, not admission evidence.
  - The projection must resolve conflicting operating observations by source precedence first, then by latest `observed_at`, then by latest persisted observation identity as a deterministic final tie-break. The default precedence order is deployment observation over operator declaration or selection over policy sync; any future source must be normalized into one of those precedence classes before it can affect current-state projection.

- `GetRepositoryAgentOperatingState`
  - Input: repository identity plus scope selector.
  - Output: current operating-state summary, current tested-agent snapshot, selected/default evaluated subject, admitted subject, evaluation mode, selected/default adapter purity, adapter manifest basis when present, aggregate coverage state, drift state, evidence-lineage label, selected/default risk-profile basis, ACUT identity field evidence-basis summary, ACUT binding/attestation basis, License-consumption compatibility basis, run observation-basis summary, `coverage_entries[]` with granted tier, admission status, freshness state, freshness deadline, risk-profile gate result, lifecycle sequence, certificate profile, status-freshness profile, certificate availability, and latest status watermark for each entry, operating-state version, the precedence-selected supporting operating observation, and linked admission/change-review references.

- `GetLicenseCertificate`
  - Input: repository identity, scope selector, target-condition basis identity, tested-agent snapshot identity, admission subject, optional admission identity, nullable operating-state identity or coverage entry identity as selection hints, and optional requested operation/risk/capability-envelope digest for certificate selection.
  - Output: signed License certificate, certificate state, non-consumable reason codes when applicable, latest signed status, and next status poll deadline.
  - This query signs or returns a durable certificate over an admission plus exactly one operating-state coverage entry when the certificate is consumable. If no unique consumer-ready coverage entry exists, it must return `non_consumable` with reason codes rather than an allow-capable admission-only certificate. It may compute matching diagnostics, but consumers still own current-status checks, local enforcement, and local policy overlays.

- `ListLicenseCertificates`
  - Input: repository identity, admission identity, operating-state identity, coverage entry identity, target-condition basis identity, issuer key identity, certificate state, or time filters.
  - Output: ordered certificate summaries.

- `GetLicenseStatus` / `ListLicenseStatusLog`
  - Input: certificate identity, admission identity, operating-state identity, coverage entry identity, target-condition basis identity, status sequence/watermark, replay cursor, or time filters.
  - Output: current signed License status record or ordered status-log entries with lifecycle state, status sequence, status watermark, issuer-key status basis, status freshness, and next poll deadline.

- `GetLicenseIssuerKeyStatus`
  - Input: issuer key identity, optional issuer key-set version, and optional verification time.
  - Output: signed issuer-key-status record with issuer identity, issuer key id, key purpose, key-set version, governed public-key digest, validity window, status effective timestamp, retirement/emergency-retirement/revocation timestamps when present, status digest, monotonic status sequence, key-status watermark, event-stream watermark, key-status signer identity, signing algorithm, canonicalization algorithm, signature, and signed timestamp needed for certificate/status verification and audit replay.

- `RecordLicenseStatusReceipt`
  - Input: consumer identity/version, receipt source, received timestamp, acknowledged timestamp, certificate identity/digest, status identity/digest, status sequence, status watermark, event-stream watermark, certificate/status key-status refs, verification result, receipt result, and reason codes.
  - Output: append-only status receipt identity and stored receipt record.

- `RecordLicenseConsumptionAuditEvent`
  - Input: consumer identity/version, operation correlation id, decision timestamp, requested repository/scope/operation/risk/target-condition/capability/snapshot/admission-subject fields, result, reason codes, optional local policy overlay result, certificate identity/digest, status identity/digest/watermark, certificate and status issuer-key status refs/digests, signature verification results, admission id, operating-state id, coverage entry id, lifecycle sequence, operating-state version, event-stream watermark, granted tier, admission status, freshness state/deadline, certificate validity timestamps, status freshness timestamps, evidence lineage, risk-profile basis, policy gate basis, and failure mode.
  - Output: append-only License-consumption audit event identity and stored audit record.

- `GetLicenseConsumptionAuditEvent` / `ListLicenseConsumptionAuditEvents`
  - Input: audit identity or repository/consumer/admission/certificate/status/result/time filters.
  - Output: stored audit event or ordered audit summaries.

### 5.7 Benchmark evaluation, runner integration, and submission

- `StartBenchmarkEvaluation`
  - Input: benchmark-release identity, tested-agent snapshot identity, optional upstream agent-configuration identity, evaluation policy, evaluation mode, adapter purity level, adapter manifest, run environment declaration, assurance mode, attempt number, and the requested capability-envelope policy used to derive per-run immutable contracts.
  - Output: benchmark-evaluation identity, initial state, and the persisted benchmark-basis contract used to authorize child-run planning.
  - This is the primary evaluation entrypoint for cross-task comparison and later authorization.
  - The server must load the referenced `tested_agent_snapshot` and verify that supplied evaluation mode, adapter purity, adapter manifest, and run environment declaration match the snapshot's canonical normalized values. A mismatch means the caller is not evaluating the referenced ACUT and must be rejected unless a new tested-agent snapshot is registered first. A governed target-condition basis can later explain carry-forward or authorization scope, but cannot alter this fresh benchmark fact.
  - Benchmark-evaluation identity is pinned to the tuple `benchmark_release_id + tested_agent_snapshot_id + evaluation_policy_version + evaluation_mode + adapter_purity_level + capability_envelope_contract_id + assurance_mode + attempt_number`, so stricter future assurance modes, different runner modes, and materially different execution-condition contracts remain distinct benchmark facts instead of masquerading as same-basis retries.
  - `attempt_number` is a command input supplied by the caller. It starts at `1` for the first semantic attempt under the same benchmark-evaluation basis and increments only when the caller intentionally starts a new semantic attempt with a new idempotency key. Transport retries must reuse both the same idempotency key and the same `attempt_number`; the service must not auto-increment attempt number while handling a retry.

- `GetBenchmarkEvaluation`
  - Input: benchmark-evaluation identity.
  - Output: benchmark-evaluation status, coverage summary, child-run references, ACUT identity, evaluation mode, adapter purity, adapter manifest summary, persisted capability-envelope contract identity/reference, coverage-gate summary, and `benchmark_scorecard_refs[]` when available.
  - `benchmark_scorecard_refs[]` is a convenience reference list, not an implicit selected scorecard. Any single-scorecard view must state a read-model selection policy or call `GetBenchmarkScorecard` by `benchmark_scorecard_id` / `ListBenchmarkScorecards` with a complete scorecard-basis selector.

- `ListBenchmarkEvaluations`
  - Input: repository identity, benchmark-definition identity, benchmark-release identity, tested-agent snapshot identity, or optional upstream agent-configuration identity, plus optional status or time filters.
  - Output: ordered benchmark-evaluation summaries.

- `StartRunnerInvocation`
  - Input: task identity, environment identity, tested-agent snapshot identity, optional upstream agent-configuration identity, evaluation mode, adapter purity level, adapter manifest, run environment declaration, attempt number, runtime limits, immutable capability envelope, and optional benchmark-evaluation or release-membership reference.
  - Output: run identity, runner-invocation state, persisted capability-envelope identity, persisted capability-envelope reference, and expected run-submission contract.
  - Direct task invocations are secondary. They may be used for diagnostics, reruns, or partial execution inside a benchmark evaluation, but they are not the canonical comparison surface by themselves.
  - `patch_only` and `trace_submission` runners are external/native by default. `observed_run` may wrap the native agent without changing the internal loop. `harness_native` is non-default and must label the ACUT as `Agent + Harness`.
  - The server must verify that supplied evaluation mode, adapter purity, adapter manifest, and run environment declaration match the referenced `tested_agent_snapshot` and, for benchmark-linked runs, the parent `benchmark_evaluation`. A mismatch must not be treated as a retry of the same run; it is `policy_conflict` for an existing basis or validation error before acceptance.
  - `run_attempt_slot` is the envelope-independent idempotency slot. For benchmark-linked child runs it is `benchmark_evaluation_id + benchmark_release_membership_id + attempt_number`; for ad hoc runs it is `task_id + tested_agent_snapshot_id + environment_id + attempt_number`.
  - For ad hoc runs, the direct caller supplies `attempt_number`. For benchmark-linked child runs, the parent `BenchmarkEvaluationWorkflow` or an explicit child-rerun operator command supplies `attempt_number` when signaling `StartRunnerInvocation`; runner workers must never allocate it implicitly.
  - Accepted run identity is `run_attempt_slot + capability_envelope_id + evaluation_mode + adapter_purity_level + adapter_manifest_digest`. Reruns under a different parent benchmark evaluation, release membership, task, environment, or attempt number are therefore different slots and may create new run identities without conflicting with earlier evaluations.
  - The command boundary must normalize the requested capability envelope, evaluation mode, adapter purity, and adapter manifest before replay/conflict handling. A repeated request in the same `run_attempt_slot` with the same normalized values should return the original accepted run or a stable `idempotency_conflict`; a request in that slot that resolves to a different normalized value on any of those axes must return `policy_conflict` because it is trying to change the immutable run contract rather than retry the same execution fact. A request in a different `run_attempt_slot` creates a new run identity, even if the normalized values match an earlier run.
  - Transport retries must reuse the same idempotency key, `attempt_number`, and attempt basis. A semantic rerun must use a new idempotency key and the next `attempt_number` in the relevant ad hoc or benchmark-linked run-attempt series.

- `SubmitRunResult`
  - Input: run identity, submitted patch/result/artifact refs, optional native trace/log/tool/model summaries, producer identity, submission digest, and redaction metadata.
  - Output: `run_submission_id`, accepted submission manifest, evidence-ingestion status, and next canonical-verification state.
  - This command records what the external/native agent or harness-backed runner produced. It does not by itself establish correctness.

- `RecordCanonicalVerification`
  - Input: run identity, run-submission identity, verifier identity, scoring-relevant policy version, clean-room workspace/image digest, patch-application status, verifier outputs, policy checks, canonical pass/fail result, verification attempt number, trusted evidence digest, and exact sealed verifier evidence-bundle version/digest.
  - Output: `canonical_verification_record_id`, trusted Barcarolle evidence references, exact verifier evidence-bundle version, and verification status.
  - This command is normally workflow-owned rather than caller-owned. It is the correctness root for scoring and admission.

- `CancelRunnerInvocation`
  - Input: run identity and cancellation reason.
  - Output: cancellation acknowledgement and terminal state if cancellation succeeds.

- `GetEvaluationRun`
  - Input: run identity.
  - Output: run status, runner-invocation summary, evaluation mode, adapter purity, run-submission reference, canonical-verification reference, `score_bundle_refs[]`, evidence trust-tier summary, ACUT identity field evidence-basis summary, run observation basis, and the persisted immutable capability envelope.
  - `score_bundle_refs[]` is a convenience list of immutable score bundles, not an implicit selected score. Each ref should carry `score_bundle_id`, `score_input_evidence_digest`, `evidence_trust_basis_digest`, `authorization_eligible`, and score-basis Judge lineage. Any single-score view must state a read-model selection policy or call `GetRunScore` by `score_bundle_id`.

- `ListEvaluationRuns`
  - Input: benchmark-evaluation identity, benchmark-release-membership identity, task identity, tested-agent snapshot identity, optional upstream agent-configuration identity, or time window.
  - Output: ordered run summaries.
  - Benchmark child-run drill-down should use `benchmark_evaluation_id` and may narrow to `benchmark_release_membership_id`; membership identity alone is not globally unique across benchmark evaluations.

### 5.8 Scoring and authorization

- `ComputeRunScore`
  - Input: terminal run identity, canonical-verification-record identity when one exists, trusted terminal outcome evidence digest for scoreable pre-verification zeroes when no canonical verification record exists, scoring policy version, and optional multi-run context.
  - Output: `score_bundle_id`, scoring semantics version, run outcome class, score state, failure class, failure taxonomy version, outcome owner, raw correctness score, effective correctness score, correctness score, process score, stability label, repeated-run group/trial summary when applicable, supporting metrics, risk flags, authorization-blocking risk flags, authorization eligibility flag, score identity basis, `score_input_evidence_digest`, `evidence_trust_basis_digest`, sealed score-input evidence refs, evidence trust-tier basis, ACUT identity field evidence-basis summary, run observation-basis summary, Judge contribution mode, and optional mode-aware Judge assessment references or summaries.
  - Correctness must be rooted in `trusted_barcarolle_evidence`, especially canonical verification. Agent-submitted evidence can support process analysis, confidence adjustment, and risk findings, but must not be the sole pass/fail basis.
  - Scoreable agent-owned failures such as verified failure, agent timeout, malformed agent submission, or trusted policy violation produce score bundles with `correctness_score = 0`. Platform-owned infra failures, operator cancellations, unresolved verifier flakiness, and missing canonical verification are represented as missing or blocked scorecard input entries rather than as hidden positive or negative score bundles.
  - `authorization_eligible` means the score bundle may be selected into an authorization-bearing scorecard. It requires a trusted canonical verification record for positive or verified outcomes, while scoreable agent-owned zeroes may rely on trusted terminal-outcome evidence.
  - The evidence trust-basis digest must be exposed separately, and the score input evidence digest must cover exact sealed evidence bundle versions/digests, run observation-basis digest, evidence trust-basis digest, artifact contribution modes, and any other score-contributing or confidence-contributing evidence input. Evidence repair or backfill that changes those inputs must produce a new immutable score bundle instead of overwriting or colliding with the previous score.
  - If the active scoring policy makes Judge output score-contributing, the persisted score must carry the governed `judge_configuration_id` as an independent score-identity axis in addition to `scoring_policy_version`.
  - If attached Judge output is advisory only, the artifacts must say so and canonical score identity stays on the explicit `none` Judge-lineage basis.

- `GetRunScore`
  - Input: `score_bundle_id`.
  - Output: persisted score bundle, including its score-basis identity and any Judge-side assessment references if the scoring path used them.
  - Exact get must not accept only `run_id`, because one run can have multiple immutable score bundles under different scoring policies, score input evidence digests after evidence repair or backfill, or score-basis Judge lineages.

- `ListRunScores`
  - Input: run identity plus optional complete score-basis filters such as canonical-verification-record identity or terminal outcome evidence digest, scoring policy version, score input evidence digest, and score-basis Judge lineage.
  - Output: ordered score-bundle summaries.
  - List queries may support exact semantic resolution when the full basis is supplied, but incomplete selectors must remain multi-result instead of selecting an implicit score bundle.

- `RegisterRepositoryRiskProfile`
  - Input: organization or repository scope, optional parent profile, risk-profile version, risk tolerance class, constraint artifact or inline constraint summary, expected constraint digest, lifecycle target such as draft or candidate, and actor identity.
  - Output: `repository_risk_profile_id`, backend-derived constraint digest, effective-profile preview for covered scopes, and lifecycle state.
  - The backend must validate constraint shape, recompute the digest, reject malformed tier or scope matrices, and preserve the profile append-only. A profile may document external License-consumption assumptions, but it must not create a Barcarolle runtime enforcement rule.

- `GetRepositoryRiskProfile`
  - Input: `repository_risk_profile_id` or exact organization/repository/scope/version selector.
  - Output: stored risk profile, constraint digest, lifecycle state, inheritance basis, transition history, and impact-preview refs when available.

- `ResolveEffectiveRiskProfile`
  - Input: organization or repository scope plus optional component/path, permission class, risk class, requested tier, target condition, evaluation mode, adapter purity, and evidence trust basis.
  - Output: effective risk-profile basis, selected source profiles, final constraint digest, conflict handling, and whether the scope is blocked without a persisted seed or active profile.

- `ListRepositoryRiskProfiles`
  - Input: organization, repository, scope, lifecycle state, risk tolerance class, predecessor, activation window, or constraint digest filters.
  - Output: ordered risk-profile summaries.

- `ApplyRepositoryRiskProfileTransition`
  - Input: risk-profile identity, transition type such as `activate`, `pause`, `resume`, `supersede`, `rollback`, or `retire`, actor identity, governance rationale, optional transition gate refs, and optional supersession target.
  - Output: updated lifecycle state, durable transition record, effective-profile selection effect, and triggered impact or recalibration refs when applicable.
  - Activation changes future appetite constraints and can trigger impact preview, policy calibration, reauthorization, suspension, revocation, targeted validation, or full rebenchmarking. It does not rewrite historical scorecards, decisions, admissions, or operating-state facts.

- `StartPolicyCalibration`
  - Input: repository scope, target policy families, predecessor calibrated profile refs, effective risk-profile ref or request to resolve the active profile, trigger kind, optional requested evidence window, optional requested release/scorecard scope, and run attempt number.
  - Output: `policy_calibration_run_id`, accepted calibration manifest handle, truth-observation manifest handle when available, and workflow status.
  - The command starts an automated calibration workflow. It may request automatic controls and baseline runs through existing benchmark workflows, but it must not accept human labels or manual benchmark acceptance as calibration truth.

- `GetPolicyCalibrationRun`
  - Input: `policy_calibration_run_id`.
  - Output: calibration run status, effective risk-profile basis, risk-constraint summary, input manifest digest/ref, truth-observation manifest digest/ref, truth-observation summary, evidence slice coverage, excluded slice summary, control/baseline summary, unsafe false-positive summary, high-tier authorization control summary, risk-budget consumption, sensitivity refs, candidate profile refs, selected profile ref, promotion gate summary, and blocker codes.

- `ListCalibrationTruthObservations`
  - Input: calibration run identity plus optional observation kind, truth basis, semantic slice, split, exclusion status, unsafe false-positive result, or candidate profile filters.
  - Output: ordered truth-observation summaries for traceability; no write path for labels.

- `ListPolicyCalibrationRuns`
  - Input: repository scope, target policy family, predecessor profile, selected profile, status, trigger kind, or time window.
  - Output: ordered calibration-run summaries.

- `GetCalibratedPolicyProfile`
  - Input: `calibrated_policy_profile_id` or exact policy-version selector.
  - Output: calibrated policy profile, effective risk-profile basis, parameter digest, truth basis digest, unsafe false-positive metrics, high-tier authorization applicability summary, parameter authority summary, applicability slices, lifecycle state, calibration-run ref, promotion gate results, and impact-preview refs.

- `ListCalibratedPolicyProfiles`
  - Input: semantic policy family, repository scope, lifecycle state, predecessor profile, policy-version fields, activation window, or applicability slice filters.
  - Output: ordered calibrated-profile summaries.

- `ApplyCalibratedPolicyProfileTransition`
  - Input: calibrated profile identity, transition type such as `promote`, `shadow`, `pause`, `resume`, `rollback`, or `supersede`, actor identity, automated transition gate refs for workflow-owned activation/resume/supersession including truth-observation completeness, unsafe false-positive, high-tier applicability, sensitivity, and parameter-authority gates, governance rationale for pause/rollback/annotation, and optional supersession target.
  - Output: updated lifecycle state and durable transition record.
  - `promote`, `shadow`, `resume`, and active-profile activation are workflow-owned and require machine-checkable gate refs. Human-initiated transitions are governance actions, not calibration labels; they can pause, annotate, roll back, or request rerun, but cannot supply promotion truth.
  - `pause` removes a profile from active selection for new scorecards and authorization decisions while leaving existing scorecards, decisions, admissions, and operating-state facts unchanged. Selection falls back to the latest eligible non-paused active predecessor for the same policy surface; if none exists, new materialization for that slice is blocked until automated `resume` or `supersede` succeeds.

- `RegisterGovernedAssessorConfiguration`
  - Input: assessor kind, repository scope, normalized model/prompt/tool/memory/runtime/output-schema descriptors, optional expected configuration fingerprint, optional predecessor or comparison-baseline reference, and creator identity.
  - Output: governed assessor configuration identity, backend-derived configuration fingerprint, and stored configuration record.
  - Re-registering the same natural key is idempotent; changing a material field creates a new `assessor_configuration_id`.

- `GetGovernedAssessorConfiguration`
  - Input: assessor-configuration identity.
  - Output: governed assessor configuration with version digests, governance state, promotion lineage, and comparison lineage.

- `ListGovernedAssessorConfigurations`
  - Input: one of repository identity, scope, or assessor kind, plus optional governance-state or comparison-baseline filters.
  - Output: ordered assessor-configuration summaries.

- `ApplyGovernedAssessorTransition`
  - Input: assessor-configuration identity, transition type such as promote, demote, or rollback, and reviewer identity plus rationale.
  - Output: updated governance state and a durable transition record.
  - This is the explicit governed-assessor lifecycle entrypoint used for append-only promotion, demotion, and rollback operations.

- `DecideAuthorization`
  - Input: benchmark scorecard, scope, `authorization_policy_version`, calibrated policy-profile ref when the policy version is calibrated, effective risk-profile ref or request to resolve the active profile, requested admission subject, requested operation, and requested capability envelope. A request field named `policy_version` may be accepted only as an alias for `authorization_policy_version`.
  - Output: requested trust tier, granted trust tier, policy outcome, permission scope, denial or downgrade reason, authorized capability-envelope identity/coverage, calibrated policy-profile ref/digest, risk-profile ref/version/digest, risk-profile gate result, evaluated subject, requested admission subject, production-fidelity / subject-applicability basis, evaluation mode, adapter purity, ACUT field evidence-basis summary, ACUT binding/attestation basis, License-consumption compatibility basis, consumer certificate/status profile basis, policy gate results, evidence trust-tier basis, canonical-verification coverage, release-admission policy version, release certification verdict, release coverage profile ref/digest, requested-scope release coverage result, supported/unsupported-scope summaries, invalidation refs, and authorization-readiness state.
  - Per-run score bundles may contribute supporting evidence, but a benchmark-authoritative authorization decision should resolve to benchmark-release and benchmark-scorecard context.
  - Decisions must not mix scorecards across ACUT, benchmark release, evaluated subject, requested admission subject, production-fidelity basis, evaluation mode, adapter purity, canonical-verification basis, or evidence trust-tier basis unless a governed change review explicitly records the reuse or supplementation.
  - Tier, threshold, subject-applicability, ACUT-binding, License-consumption compatibility, risk-appetite constraints, freshness, and external License-consumption semantics are defined in `docs/architecture/authorization-semantics.md`.

- `GetAuthorizationDecision`
  - Input: decision identity or repository scope.
  - Output: stored decision, rationale summary, authorized capability-envelope identity/coverage, and authorization-readiness state.

### 5.9 Evidence and audit lookup

- `AppendEvidenceArtifact`
  - Input: subject selector such as candidate-generation-run, task-candidate, validation-result, leakage-report, task, task-retirement, release-maintenance-finding, run, submission, canonical-verification, or environment reference; bundle kind; optional base evidence-bundle identity for backfill or repair; artifact type; content reference; provenance; and optional manifest-version assertion.
  - Output: evidence artifact identity plus the sealed evidence-bundle identity, manifest version, and content digest.

- `GetEvidenceBundle`
  - Input: subject selector such as candidate-generation-run, task-candidate, validation-result, task, run, submission, canonical-verification, environment, or evidence bundle identity, plus optional bundle kind and manifest version. If only a subject and bundle kind are supplied, the read model may resolve the current/latest sealed version for browsing.
  - Output: immutable evidence manifest version, content digest, and artifact pointers.

## 6. Asynchronous Events

The system should use append-only events for cross-module handoff and audit replay. Events are the durable interface between decoupled workers.

### 6.1 Repository and task events

- `RepositorySnapshotRegistered`
- `RepositorySignalsExtracted`
- `CandidateGenerationRunReserved`
- `CandidateGenerationRunCompleted`
- `TaskCandidateCreated`
- `TaskCandidateApproved`
- `TaskCandidateRejected`
- `TaskCandidateRetired`
- `TaskRetired`
- `TaskQuarantined`
- `ReleaseMaintenanceFindingRecorded`
- `RepositoryRiskProfileRegistered`
- `RepositoryRiskProfileTransitioned`
- `EffectiveRiskProfileResolved`

### 6.2 Replay and environment events

- `ReplayEnvironmentPlanned`
- `ReplayEnvironmentBuildStarted`
- `ReplayEnvironmentBuilt`
- `ReplayEnvironmentBuildFailed`
- `ReplayEnvironmentValidated`
- `ReplayEnvironmentRejected`

### 6.3 Benchmark lifecycle events

- `BenchmarkReleasePublished`
- `BenchmarkReleaseCoverageProfileComputed`
- `TestedAgentSnapshotRegistered`
- `BenchmarkEvaluationRequested`
- `BenchmarkEvaluationStarted`
- `BenchmarkEvaluationCompleted`
- `BenchmarkEvaluationFailed`
- `BenchmarkEvaluationCanceled`
- `BenchmarkScorecardPublished`
- `AgentChangeReviewRecorded`
- `RepositoryAgentAdmissionRecorded`
- `RepositoryAgentAdmissionTransitionRecorded`
- `RepositoryAgentOperatingObservationRecorded`
- `RepositoryAgentOperatingStateUpdated`
- `LicenseCertificateIssued`
- `LicenseStatusChanged`
- `LicenseIssuerKeyStatusChanged`
- `LicenseStatusReceiptRecorded`
- `LicenseConsumptionAuditEventRecorded`

These events make benchmark publication, evaluation progress, and scorecard materialization first-class audit surfaces instead of requiring downstream consumers to infer benchmark lifecycle from child-run events alone.

### 6.4 Run and scoring events

- `EvaluationRunQueued`
- `EvaluationRunStarted`
- `EvaluationStepRecorded`
- `EvaluationRunCompleted`
- `EvaluationRunFailed`
- `EvaluationRunCanceled`
- `RunScored`
- `PolicyCalibrationRunCompleted`
- `CalibratedPolicyProfileTransitioned`
- `AuthorizationDecisionRecorded`

### 6.5 Event envelope

Every event should carry:

- event identity
- `contract_version`
- event type
- timestamp
- producer module
- `request_id`
- `correlation_id`
- `causation_id`
- primary subject identity, such as `repository_id`, `task_id`, `run_id`, or `decision_id`
- payload reference or inline payload

`Assumption`: payloads should be immutable once emitted. If a record needs correction, emit a compensating event instead of mutating history.

## 7. State Machines

### 7.1 Task candidate state machine

Recommended task-candidate states:

`Draft -> Candidate -> Planned -> EnvironmentReady -> Validated -> Approved`

Non-terminal repair state:

- `RepairRequired`

Terminal states:

- `Rejected`
- `Retired`
- `Failed`

State rules:

- Replay planning, environment build, and validation all operate on the `task_candidate` record before approval.
- A candidate cannot move to `Approved` until a successful validation result exists for its replay environment.
- `RepairRequired` is entered when validation or admission review returns `repair_required`; repair must produce a new candidate/replay/validation basis before the candidate can return to `Candidate`, `Planned`, `EnvironmentReady`, or `Validated`.
- Approval materializes the canonical `task` resource; the candidate remains as the audit record for how the task was admitted.
- A candidate can be retired at any point before approval if contamination, drift, or oracle weakness is detected.

### 7.2 Task state machine

Recommended task states:

`Approved`

Terminal or exceptional states:

- `Retired`

State rules:

- A task is created only by successful approval of a validated candidate.
- A task retains the admitted replay environment and validation lineage that justified approval, but downstream execution does not mutate the task lifecycle itself.
- Run progress belongs to `evaluation_run`, aggregate scoring belongs to `score_bundle` / `benchmark_scorecard`, and benchmark publication belongs to `benchmark_release`.
- A task can be retired when contamination, drift, or oracle weakness is detected.

### 7.3 Run state machine

Recommended run states:

`Queued -> InvokingRunner -> AwaitingSubmission -> EvidenceIngesting -> CanonicallyVerifying -> Completed`

Terminal or exceptional states:

- `Failed`
- `Canceled`

State rules:

- `InvokingRunner` covers task package delivery, native runner launch, wrapper setup, or harness-native startup depending on mode.
- `AwaitingSubmission` covers the interval where an external/native agent or harness-backed runner must submit patch/result/artifacts.
- `EvidenceIngesting` records submitted, observed, trusted, and third-party artifacts with producer and trust-tier metadata.
- `CanonicallyVerifying` covers clean-room patch/result application and verifier execution after a submitted result reaches canonical verification.
- Positive or verified correctness outcomes must not be marked `Completed` unless the `run_submission`, evidence bundle, and `canonical_verification_record` are persisted.
- Scoreable pre-verification agent-owned zeroes may be marked `Completed` as completed failures without a `canonical_verification_record` only when trusted Barcarolle terminal-outcome evidence proves the accepted run timed out, produced an agent-owned malformed/empty submission, or violated trusted policy before canonical verification could produce a record. That completed-failure transition is the state-machine trigger for `ScoreWorkflow` to compute a zero score bundle using the trusted terminal-outcome evidence digest.
- Missing canonical verification without trusted terminal-outcome evidence blocks positive correctness, verified pass/fail scoring, and authorization eligibility; it is represented as unverified, missing, or blocked scorecard input rather than a hidden positive or negative score bundle.
- `patch_only` runs may skip process observation and may still have high native YOLO production fidelity. They require canonical verification before they can claim positive or verified correctness, or authorization eligibility for those outcomes; scoreable agent-owned zeroes may rely on trusted terminal-outcome evidence when no canonical verification record exists.

### 7.4 Authorization state machine

Recommended authorization states:

`Proposed -> Effective -> Superseded -> Revoked`

State rules:

- Authorization decisions are derived from benchmark scorecards plus policy version; per-run score bundles are supporting drill-down evidence.
- A later policy version may supersede an earlier decision without rewriting the earlier audit record.

### 7.4a Repository risk-profile state machine

Recommended risk-profile states:

`Draft -> Candidate -> Active -> Superseded`

Pause, rollback, and terminal transitions:

`Candidate|Active -> Paused`
`Paused -> Active`
`Active|Paused -> Superseded|RolledBack|Retired`

State rules:

- Risk-profile records are append-only policy appetite resources; new constraints create a new profile version or superseding profile.
- At most one effective profile basis should resolve for a repository scope after organization, repository, and component/path precedence rules are applied.
- Activation changes future calibration and authorization inputs and may trigger impact preview, recalibration, reauthorization, suspension, revocation, targeted validation, or full rebenchmarking.
- Activation, pause, rollback, and retirement do not rewrite historical scorecards, decisions, admissions, or operating-state coverage entries.
- A risk-profile transition can require human governance authority, but it is not a calibration truth label and cannot manually promote a calibrated policy profile.

### 7.4b Policy calibration state machine

Recommended calibration-run states:

`Requested -> GatheringEvidence -> GeneratingControls -> RunningBaselines -> FittingProfiles -> ValidatingProfiles -> Completed`

Terminal or blocked states:

`Failed | Blocked | Canceled`

Recommended calibrated-profile states:

`Candidate -> Shadow -> Active -> Superseded`

Rollback and blocked transitions:

`Candidate|Shadow|Active -> Blocked`
`Active|Superseded -> RolledBack`
`Active|Shadow -> Paused`
`Paused -> Active` only through workflow-owned `resume`
`Paused -> Superseded|RolledBack`

State rules:

- Calibration-run records are append-only; reruns create new records.
- Candidate profiles are produced from a calibration run and must carry exact input manifest, truth-observation, objective-control, unsafe false-positive, held-out validation, sensitivity, parameter-authority, and impact-preview refs.
- Normal promotion to `Active` is automated and requires machine-checkable promotion gates, including high-tier control-power gates for any claimed `G4` or `G5` applicability slice.
- Human governance may pause, annotate, or roll back a profile, but human review is not calibration truth and is not required for normal benchmark generation, benchmark running, or profile promotion.
- `Paused` removes the profile from active selection for new scorecards and authorization decisions. Existing facts keep their recorded profile refs. Active selection falls back to the latest eligible non-paused active predecessor for the same semantic family, repository scope, applicability slice, and policy-version surface; if none exists, new materialization for that slice is blocked.
- Resume from `Paused` to `Active` is workflow-owned and requires machine-checkable gate refs. If parameters or applicability change, the valid path is a superseding profile rather than resume.
- A profile that changes scorecard-level facts requires new scorecards under the new policy versions before authorization treats the changed interpretation as fresh benchmark evidence.

### 7.5 Agent change review state machine

Recommended review outcomes:

`CarryForwardAcceptable`, `TargetedReviewRequired`, `FullRebenchmarkRequired`, `Blocked`

State rules:

- Change review records are append-only; a later review supersedes an earlier one by writing a new record.
- A carry-forward outcome may justify a new repository-agent admission for the candidate tested-agent snapshot, but it must not rewrite the baseline benchmark evaluation.
- Change review writes must record structured delta classification that distinguishes execution-condition changes, ACUT field evidence-basis changes, and interpretation/authorization changes.
- If `review_outcome = carry_forward_acceptable`, change review writes must also record the resulting `reused` or `supplemented` evidence lineage.
- If `review_outcome` is `targeted_review_required`, `full_rebenchmark_required`, or `blocked`, change review writes must leave `evidence_lineage` absent rather than implying accepted reuse.
- Change review writes must also record an explicit target-condition basis so the approved execution boundary and interpretation/authorization basis are auditable rather than inferred from lineage labels alone.

### 7.6 Repository-agent admission state machine

Recommended admission states:

`Proposed -> Effective -> Suspended -> Effective`

Terminal or replacement transitions:

`Effective|Suspended -> Superseded|Revoked|Expired`

State rules:

- Admissions are repository-scoped governance records, not benchmark facts.
- Admission may be based directly on a benchmark decision or on a later governed change review.
- `Suspended` is a reversible emergency hold. External consumers must treat suspended, revoked, and expired admissions as `G0 no_admission`.
- Reinstatement writes a `lift_suspension` lifecycle transition on the same admission and projects status back to `Effective`. It is allowed only when the admitted snapshot, scope, target-condition basis identity, covered capability envelope, evaluated/admitted subject, subject-applicability basis, granted tier, evidence basis, evidence lineage, gate basis, and freshness deadline are unchanged; otherwise the valid path is a new superseding admission.
- `lift_suspension` requires recorded cause resolution, evidence refs or reviewer rationale, no remaining revocation condition, an open freshness deadline, and required governance review for `G4`, `G5`, high-impact or critical-path suspension causes, and any `G3` admission whose original grant required governance review.
- For any one `repository_id + scope + target_condition_basis_identity`, at most one admission may be `Effective`; a later effective admission for the same tuple must supersede the prior effective admission explicitly. Multiple effective admissions may exist for the same repository/resource scope only when their target-condition bases or authorization dimensions differ and policy permits that coexistence.
- Current operating state may point at one or more admissions through `coverage_entries[]`, but changing operating state must not rewrite the admission history.
- Admissions and operating-state reads must propagate the explicit `fresh`/`reused`/`supplemented` evidence-lineage label rather than leaving operators to infer it from basis references alone.
- Admissions and operating-state reads must also expose the explicit target-condition basis so operators can tell what execution and interpretation boundary is currently covered.
- Every lifecycle transition increments an admission lifecycle sequence. Signed License certificates, signed status records, and operating-state coverage entries must copy that sequence so consumers can reject stale certificate/status projections after suspend, revoke, expire, supersede, or lift events.
- Suspension, revocation, expiration, and supersession publish matching signed License status changes for write-capable consumption. A consumer that misses the event cannot claim current Barcarolle-conformant `allow` after its status-staleness bound, even if the durable certificate validity window has not expired.

### 7.7 Repository-agent operating observation semantics

Recommended observation rule:

- Each operating observation is append-only and auditable.
- Later observations do not mutate earlier observations; they provide new fact input to the projection layer.
- `repository_agent_operating_state` is the derived read model over admissions, change reviews, benchmark facts, and the precedence-selected operating observation for that scope.
- The read model remains one row per repository scope, but `coverage_entries[]` must preserve every relevant target-condition/admission coverage basis for the current snapshot. Top-level coverage fields are summaries only when more than one entry exists.
- Each coverage entry must carry stable coverage entry identity, `granted_trust_tier`, `admission_status`, `freshness_state`, `freshness_deadline`, `risk_profile_basis`, `risk_profile_gate_result`, `evidence_lineage`, evaluated subject, admitted subject, production-fidelity basis, ACUT binding/attestation basis, License-consumption compatibility basis, admission lifecycle sequence, certificate profile, status-freshness profile, signed-certificate availability, and latest status watermark directly. Consumers may dereference the linked admission for audit, but they must not depend on a second lookup for these core authorization fields.
- Entries without a covering admission must set `granted_trust_tier = G0`, `admission_status = none`, and `freshness_state = not_applicable`.
- The default precedence order is deployment observation over operator declaration or selection over policy sync.
- Within the same precedence class, the projection chooses the latest `observed_at`; if that still ties, it chooses the latest persisted `repository_agent_operating_observation_id` as the deterministic final tie-break.
- Signed-certificate generation is available only from coverage entries with a covering admission whose status, freshness, target condition, capability envelope, and status profile are consumer-readable. Consumable certificate generation must bind one certificate to exactly one such coverage entry. Uncovered or ambiguous entries must return non-consumable diagnostic projections or no certificate with explicit reason codes.
- Future `state_source` values must be mapped into one of those precedence classes before they can drive the current-state projection.

## 8. Error Semantics

All synchronous interfaces should return structured domain errors with:

- machine-readable error code
- human-readable message
- retryability flag
- subject identity
- optional remediation hint

Recommended domain error classes:

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

- `validation_failed`, `task_rejected`, `contaminated_or_leaked`, and `flaky_or_unstable` are expected non-retryable outcomes unless new evidence is added.
- `environment_build_failed` may be retryable when the failure is infrastructure-related.
- `idempotency_conflict` should return the original resource reference when the request was already accepted with the same normalized business key, including any immutable capability-envelope identity.
- `policy_conflict` should be used when `StartRunnerInvocation` tries to reuse an already accepted `run_attempt_slot` while changing the normalized capability envelope, evaluation mode, adapter purity, adapter manifest, or any run-environment value that must match the referenced ACUT snapshot.
- `internal_error` should never be the only persisted outcome for a business decision; it must be paired with a traceable failure event.

`Inference`: the exact retry classification can be refined later, but the interface should already separate deterministic domain rejection from transient infrastructure failure.

## 9. Idempotency

Idempotency is required for all write-like commands.

### 9.1 Idempotency key rules

- Every mutating command must accept an idempotency key.
- The idempotency scope should include the command type, caller identity, and natural business key.
- Replays of the same command must return the original outcome or a stable conflict response.
- Commands whose natural business key includes `attempt_number` must receive that attempt number explicitly before workflow ID derivation. Reusing an idempotency key with a different attempt number or different attempt basis is `idempotency_conflict`; using a different idempotency key with the next attempt number is the explicit signal for a semantic new attempt.

### 9.2 Natural keys

Recommended natural keys:

- repository snapshot: repository identity + source revision + import mode
- repository risk profile: organization or repository scope + risk-profile version; equivalent profile registration is idempotent by organization or repository scope + constraint digest
- candidate generation run: repository identity + snapshot identity + generation strategy + signal/input manifest digest + selection policy version + optional Golden configuration identity + optional Golden input-manifest digest + generation attempt number
- task candidate: repository identity + snapshot identity + generation-context lineage + task family + contract version, where generation-context lineage includes candidate-specific selection identity and Golden-assisted discovery/selection lineage when applicable
- replay environment: task candidate identity + plan version
- leakage report: subject kind + subject identity + report digest
- release maintenance finding: subject kind + subject ref + finding type + cause code + evidence digest
- tested-agent snapshot: repository scope + snapshot fingerprint
- agent change review: repository scope + baseline tested-agent snapshot + candidate tested-agent snapshot + review sequence
- repository-agent admission: repository scope + admitted tested-agent snapshot + admission basis identity + target-condition-basis identity
- repository-agent operating observation: repository scope + observed timestamp + state source + observed tested-agent snapshot identity
- license certificate: repository-agent admission + target-condition-basis identity + operating-state version + admission lifecycle sequence + certificate schema version + certificate digest
- license status record: license certificate + status sequence + status watermark
- license status receipt: consumer identity + license status + status watermark + acknowledged timestamp
- license consumption audit event: consumer identity + operation correlation id + decision timestamp + certificate digest + status watermark
- benchmark evaluation: benchmark release identity + tested-agent snapshot identity + evaluation policy version + evaluation mode + adapter purity level + capability-envelope contract identity + assurance mode + attempt number
- evaluation run: accepted run identity is `run_attempt_slot + capability-envelope identity + evaluation mode + adapter purity level + adapter manifest digest`; ad hoc `run_attempt_slot` is `task identity + tested-agent snapshot identity + environment identity + attempt number`; benchmark-linked `run_attempt_slot` is `benchmark evaluation identity + benchmark release-membership identity + attempt number`
- canonical verification record: run-submission identity + verifier identity + verifier image digest + scoring-relevant policy version + verification attempt number
- evidence bundle: subject type + subject identity + bundle kind + manifest version; subject type + subject identity + bundle kind is only the current/latest read-model series
- score bundle: run identity + canonical-verification-record identity or trusted terminal outcome evidence digest + scoring policy version + score input evidence digest + score-basis Judge lineage, where the lineage axis is score-contributing `judge_configuration_id` or explicit `none`
- benchmark scorecard: benchmark evaluation identity + scorecard policy version + coverage-policy version + reliability-policy version + calibrated policy profile or seed basis + repository risk profile or seed basis + risk-profile digest + evaluated capability-envelope identity + evaluation mode + adapter purity level + score input set digest + evidence trust-basis digest + score-basis Judge lineage, where the lineage axis is score-contributing `judge_configuration_id` or explicit `none`
- authorization decision: repository scope + `authorization_policy_version` + calibrated policy profile or seed basis + repository risk profile or seed basis + risk-profile digest + benchmark scorecard identity + authorized capability-envelope identity + `target_condition_basis_identity`
- policy calibration run: repository scope + target policy families + repository risk profile or seed basis + risk-profile digest + calibration input manifest digest + trigger kind + run attempt number
- calibrated policy profile: semantic policy family + repository scope + repository risk profile or seed basis + risk-profile digest + parameter digest + applicability slice digest
- governed assessor configuration: repository scope + assessor kind + configuration fingerprint

`Inference`: `source_anchor` remains provenance for where the candidate came from, while `snapshot_id + generation_context_lineage` is the regeneration-safe task-candidate identity. The generation-context axis must capture extractor lineage plus candidate-specific selection identity at minimum and may widen to broader candidate-build context, including `candidate_generation_run_id`, selected Golden output digest, and exact evidence-bundle version/content digest, when that context materially changes candidate semantics.

### 9.3 Retry behavior

- Safe query retries must be allowed without side effects.
- Mutating commands must be safe to retry after timeouts or transport failures.
- Retry-safe semantics are especially important for workflow workers and queue consumers.

## 10. Versioning

### 10.1 Contract versioning

- Every request, response, and event should carry `contract_version`.
- Backward-compatible additions should keep the same major contract version.
- Breaking changes should introduce a new major contract version or an explicit new event type family.

### 10.2 Artifact and schema versioning

The system should version independently:

- task specification schema
- replay environment schema
- event schema
- score schema
- authorization policy schema
- License certificate schema
- License status schema
- License status receipt schema
- License consumption audit-event schema
- policy calibration manifest schema
- calibrated policy profile schema

### 10.3 Evolution rules

- New optional fields may be added without breaking older consumers.
- Required field removals are breaking changes.
- Renaming a field is breaking unless the old field remains present during a deprecation window.
- Consumers should ignore unknown fields when possible.

`Assumption`: the project will prefer additive evolution first, because the benchmark and trace formats need long-term replay compatibility.

## 11. Audit Fields

Every persisted record that can affect a score or authorization decision should include:

- creator or producer identity
- creation timestamp
- source revision or snapshot reference
- upstream artifact reference
- ACUT field evidence-basis summary when the record interprets a tested-agent snapshot
- `request_id`
- `correlation_id`
- `causation_id`
- contract and schema versions
- provenance summary
- evidence bundle reference when applicable
- admission-review lineage where governance annotation, repair, pause, override, rollback, or exceptional policy ownership affected the record
- Golden configuration identity and assessment artifact references when Golden materially contributed to validation
- score-basis Judge configuration identity when Judge materially contributed to canonical scoring, plus any attached Judge assessment references that remain advisory audit material
- policy calibration run identity and calibrated policy-profile identity when calibrated parameters affect score, coverage, reliability, or authorization interpretation
- repository risk-profile identity, version, digest, and effective-profile basis when appetite constraints affect calibration, scorecard materialization, authorization, admission, or operating-state interpretation
- signed License-certificate identity, digest, lifecycle sequence, operating-state version, status identity, and status watermark when a consumer-facing certificate/status affects a decision or audit record
- License-consumption audit-event identity when applicable

For evaluation runs and decisions, also store:

- tested-agent snapshot identity
- optional upstream agent-configuration identity
- environment identity
- policy version
- verifier identity
- stability label
- retirement or rejection reason

These fields are required so that a reviewer can reconstruct why a task was accepted, how a runner was integrated, how a submitted result was verified, and why a permission decision was made.

## 12. Required Scope and Later Extensions

### 12.1 Required

- repository snapshot registration and lookup
- signal extraction
- candidate-generation-run reservation, completion, lookup, and list queries
- task candidate creation and approval
- task-level benchmark-admission gate, oracle-profile, first-class leakage-report resource/query fields, review-reason, and admission-verdict fields
- replay planning
- environment build and validation
- admission-review lineage sufficient to answer required-review compliance queries
- task retirement/quarantine records sufficient to drive post-release invalidation
- release-maintenance findings sufficient to model release, scorecard, authorization, admission, and coverage invalidation
- benchmark release coverage profiles with supported and unsupported authorization scopes
- runner invocation, submission, status, and cancellation
- canonical verification
- evidence capture with producer, trust tier, source class, redaction, digest, and score-contribution metadata
- score computation
- repository risk-profile registration, effective-profile resolution, transition, and impact-trigger refs
- automatic policy calibration runs, calibration truth-observation reads, and calibrated policy-profile reads/lifecycle writes
- authorization decision recording
- governed assessor configuration lineage reads for promotion and comparison auditability
- validation-result and score records able to carry optional Golden/Judge assessment references or summaries without changing the canonical lifecycle chain; advisory Judge refs stay audit-only, while score-contributing Judge lineage splits canonical score identity
- task/run/submission/verification/decision audit fields
- idempotency and contract versioning

### 12.2 Later extension

- multi-repository federation
- richer policy tiers
- multiple verifier families per task
- richer task retirement analytics beyond the required invalidation path
- cross-run statistical stability models
- external audit export formats
- richer replay diff visualizations

`Inference`: later extensions should not change the required contract surface unless a clear compatibility need appears.

## 13. Main Chain Coverage Check

This contract supports the required main chain:

- Task generation: repository snapshot -> signals -> candidate_generation_run -> task_candidate -> approval.
- Replay: candidate -> replay plan -> environment build -> validation with benchmark-admission gates -> approval.
- Release certification: approved certified tasks -> benchmark release -> release coverage profile -> supported/unsupported authorization scopes.
- Runner integration: validated environment -> runner invocation -> run submission -> evidence ingestion.
- Canonical verification: run submission -> clean-room patch/result application -> canonical verification record.
- Scoring: canonical verification record -> score bundle -> stability label.
- Risk profile governance: organization/repository appetite profile -> effective risk-profile basis -> calibration and authorization constraints.
- Policy calibration: effective risk-profile basis + benchmark releases + scorecards + canonical verification records + automatic controls/baselines + repeated-run summaries -> policy calibration run -> calibrated policy profile.
- Authorization: benchmark scorecard with ACUT/mode/purity/verification/evidence-trust basis + calibrated policy profile + effective risk-profile basis -> policy decision -> effective access scope.

It also covers the required cross-cutting semantics:

- error and retry distinction
- idempotency on mutating commands
- contract and schema versioning
- immutable audit fields
- async event handoff for durable replay

## 14. Source Alignment

- `docs/analysis/requirements.md` supports the need for replayability, auditability, graded output, and trust boundaries.
- `docs/architecture/system-design.md` defines the repository-specific pipeline and the separation between generation, validation, execution, evidence, scoring, and policy.
- `docs/architecture/authorization-semantics.md` defines the authorization tier scale, threshold gates, risk-profile gate, policy outcomes, freshness windows, and signed License-consumption contract.
- `docs/architecture/policy-calibration.md` defines explicit risk-profile inputs plus automatic threshold, weighting, coverage, reliability, and policy-promotion calibration.
- `docs/decisions/dependency-selection.md` supports a durable workflow and typed API boundary, which is consistent with the command/query/event contract style.
- `docs/draft/abstract.md` frames the repository-level agent-license goal and the need for graded authorization.
- `docs/research/**` supports the emphasis on repository-native oracles, replay fidelity, event traces, and benchmark trustworthiness.

## 15. Summary

The stable contract is a pipeline of commands and events around repository snapshots, task candidates, replay environments, evaluation runs, scores, authorization decisions, repository-agent admissions, signed License certificates, signed License status records/logs, status receipts, and consumer audit records. The interface should stay narrow, replayable, and auditable. It should not encode business implementation details or assume a specific transport beyond stable command/query/event semantics.
