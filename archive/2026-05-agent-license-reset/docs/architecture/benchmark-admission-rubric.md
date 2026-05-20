# Benchmark Admission Rubric

## 1. Purpose

This document defines Barcarolle's executable rubric for admitting tasks into a benchmark release and for deciding which release coverage can support repository-agent authorization. It closes the design gap between candidate generation and release publication: a task is not benchmark-worthy merely because it was mined from history, and a release is not authorization-worthy merely because it has many tasks.

The rubric applies before a `task_candidate` becomes a `task`, again when a `benchmark_release` is published, and again when post-release contamination, oracle failure, or coverage drift is discovered. It does not change Barcarolle's core boundaries:

- task generation, replay planning, validation, benchmark release publication, runner integration, canonical verification, scoring, authorization, repository admission, and operating state remain separate stages;
- Golden and Judge outputs are supporting evidence, governance signals, and confidence inputs, never sole final authority for task approval, score pass/fail, benchmark acceptance truth, or authorization grant unless a governed scoring policy explicitly makes Judge score-contributing as defined in [scoring-semantics.md](./scoring-semantics.md);
- ACUT evaluation, repository-agent admission, and downstream runtime enforcement remain distinct.

## 2. Admission Principle

The benchmark-admission rule is conservative: every certified task must have auditable provenance, faithful replay, a strong enough oracle, leakage clearance, bounded runtime, and a declared authorization relevance profile. Every certified release must publish the authorization scopes it supports and the scopes it does not support.

Barcarolle records these facts through existing resources:

- `task_candidate` stores mined intent, `T_task`, source evidence, proposed task boundary, admission gates, leakage findings, capability/risk tags, and review state.
- `replay_plan` and `replay_environment` store faithful reconstruction evidence.
- `validation_result` stores oracle grade, validation probes, flakiness/runtime results, leakage scan output, and the aggregate benchmark-admission verdict.
- `admission_review_record` stores governance decisions and reason codes for annotation, pause, override, rollback, repair ownership, or exceptional policy ownership. It is not normal calibration evidence or a normal benchmark-acceptance prerequisite.
- `task` stores the approved benchmark instance and a copy of the certified task profile needed for release membership.
- `benchmark_release` and `benchmark_release_membership` store immutable membership plus the release-level coverage profile and supported/unsupported authorization scopes.
- `task_retirement` records post-release quarantine, retirement, replacement, and invalidation causes.
- `benchmark_scorecard`, `authorization_decision`, `repository_agent_admission`, and `repository_agent_operating_state` consume release coverage and invalidation facts without rewriting the benchmark history.

No parallel "rubric product" is introduced. The rubric is a deterministic policy layer over those objects.

## 3. Task Quality Hard Gates

Each `task_candidate` receives a `task_admission_gate_results` map. A hard-gate failure prevents normal approval unless the gate explicitly allows repair and revalidation. Ambiguous, leaky, weak, unsafe, or unreplayable cases are excluded, blocked, quarantined, retired, or routed to governance; they are not required for normal calibration evidence. Human governance can annotate or own an exceptional override path, but it cannot turn confirmed leakage, unreplayability, a D-grade oracle, or unresolved ambiguity into a normal certified calibration task.

| Gate | Required evidence | Failure handling |
| --- | --- | --- |
| Provenance and time boundary | `source_anchor.source_type` is a supported repository evidence class, `source_refs[]` are present, `T_task` is fixed, and all agent-visible inputs are derived from repository state or public context at or before `T_task`. | Missing provenance or unfixed `T_task` rejects the candidate. Ambiguous linkage blocks or routes to governance and cannot be normal calibration evidence until repaired and revalidated. |
| Replayability | A `replay_plan` selects a base revision, dependency strategy, verifier reference, and network/tool posture; `replay_environment` builds faithfully or records a bounded partial-fidelity reason allowed by policy. Baseline replay and setup checks pass. | Unreplayable environments reject or mark repair required. Approximate replay cannot certify a write-capable authorization task unless policy explicitly narrows scope. |
| Task boundary | Problem statement has a non-empty goal, allowed and disallowed inputs, expected artifact shape, required permissions, and explicit component/path/task-family scope. | Vague or overbroad tasks route to repair, exclusion, or governance; unbounded multi-day work rejects or must be split. |
| Non-retrieval work | Candidate requires code/config/test/debug work or a reasoned engineering decision; the statement does not include final diff, exact patch, magic constants, or step-by-step repair instructions. | Direct answer retrieval rejects the candidate. Overspecified hints route to redaction and revalidation only if the solution is no longer exposed. |
| Bounded complexity | Candidate has enough substance to evaluate repository competence but is not so broad that runtime, canonical patch size, or touched files exceed policy limits for its task family. | Too small rejects as low-signal or auxiliary-only. Too large routes to splitting or rejection. |
| Independence and duplicate control | Candidate has a duplicate-cluster identity and similarity below policy threshold against existing certified tasks, or the cluster's release weight is capped. | Near-duplicates may be kept as auxiliary diagnostics but cannot overweight a certified release. |
| Safety and permission mapping | Required permissions, protected resources, external-service assumptions, network needs, secrets posture, and high-impact file classes are declared. No real secrets or production credentials are required. | Unsafe or unbounded permission requirements reject. High-risk surfaces trigger stricter automated release-level component coverage requirements and may route to governance for policy ownership, but governance review is not normal admission truth. |

Supported `source_anchor.source_type` values include issue, PR, commit, failing test, CI failure, regression, dependency break, migration, refactor, and spec or docs change when repository evidence makes the expected transition executable.

## 4. Oracle Quality and Validation Probes

Every candidate has an `oracle_profile` attached to `validation_result`. The profile grades the oracle, identifies the verifier family, records confidence and limits, and lists the probes used to validate that oracle.

| Grade | Meaning | Eligibility |
| --- | --- | --- |
| `A_strong_behavioral` | Deterministic behavioral oracle that checks the intended transition, accepts the canonical solution, rejects no-op and known bad patches, has low flakiness, and stays within runtime budget. | Certified tasks and high-risk authorization scopes. |
| `B_objective_partial` | Objective verifier that covers the primary failure mode and rejects no-op, but is narrower or less semantically complete than grade A. | Certified tasks when release policy limits B weight and scope. |
| `C_auxiliary` | Golden summary, Judge assessment, human rubric, diff similarity, style review, localization hint, or other evidence that helps review but is not an objective pass/fail oracle. | Advisory only. Cannot be the sole certified-task oracle. |
| `D_weak` | Patch similarity only, file-touched check only, unstructured subjective judgment, text answer match, unrelated tests, or verifier that cannot distinguish no-op from success. | Reject, quarantine, or keep outside certified release membership. |

Certified task minimum:

- oracle grade is A or B;
- canonical/reference solution passes in the replay environment;
- no-op fails;
- at least one known bad solution fails, such as the historical pre-fix state, a mutation, an incomplete patch, or a policy-selected adversarial patch;
- repeated validation runs establish flakiness at or below the policy threshold;
- p95 verifier runtime is within the task-family budget;
- verifier logs and failure messages do not leak the complete implementation.

Required validation probes:

- `canonical_solution_probe`: applies the trusted historical or reconstructed solution and confirms the target-state verifier passes.
- `no_op_probe`: runs the verifier without changes and confirms failure when the task is expected to require a change.
- `known_bad_probe`: applies one or more bad or incomplete patches and confirms rejection.
- `base_state_probe`: confirms the base snapshot exhibits the expected failure or missing behavior.
- `flakiness_probe`: repeats base and target checks enough times for the task-family policy.
- `runtime_budget_probe`: records verifier runtime and resource use.
- `oracle_log_leakage_probe`: checks visible verifier output for solution-bearing details.
- Optional `mutation_or_equivalence_probe`: detects tests that only validate superficial changes or a single implementation shape.

Golden may generate or summarize reference artifacts for these probes, but the validation result must still record the objective verifier outcome. Judge may later identify oracle suspicion from run evidence, but it does not retroactively approve a task; it routes maintenance review or retirement.

## 5. Leakage Detection and Handling

Barcarolle distinguishes future leakage from answer leakage.

Future leakage exists when information created after `T_task` is visible to the ACUT through the task prompt, workspace, retrieval corpus, examples, memory preload, issue/PR context, docs, logs, tool-accessible files, or runner package. Post-`T_task` artifacts may be used by trusted validation and canonical verification only when they are kept outside the ACUT boundary and referenced as hidden oracle material.

Answer leakage exists when the ACUT can recover the expected solution without solving the task, including direct final patches, exact repair steps, target-file over-disclosure, magic constants, distinctive identifiers, hidden tests in the workspace, or verifier output that reveals the complete implementation.

Each candidate stores or links a `leakage_report` with:

- `T_task` and source-time evidence;
- agent-visible input inventory and digests;
- leakage kind: `future`, `answer`, `artifact_exposure`, or `provenance`;
- ACUT-visible surface entries such as prompt, workspace, retrieval corpus, examples, memory preload, issue/PR context, docs, logs, tool-accessible files, runner package, verifier logs, or hidden tests;
- future-artifact scan results;
- prompt/diff overlap, identifier overlap, and literal overlap scores;
- hidden-test and verifier-log exposure checks;
- retrieval-only or weak-baseline canary results when configured;
- finding severity: `none`, `minor_redactable`, `suspected`, or `confirmed`;
- handling decision: `clear`, `redact_and_revalidate`, `requires_review`, `reject`, `quarantine`, or `retire`;
- review requirement;
- exact report ref and digest;
- redaction and revalidation lineage when handling is `redact_and_revalidate`.

The API and data model expose the report ref plus queryable summary fields on `task_candidate`, `validation_result`, and any post-release finding that consumes the report: `leakage_kind[]`, `leakage_severity`, `leakage_handling_decision`, `leakage_review_required`, `acut_visible_surfaces[]`, `redaction_revalidation_lineage`, `leakage_report_ref`, and `leakage_report_digest`. Consumers must not infer confirmed, suspected, or redacted leakage by parsing an opaque blob.

Handling rules:

- `confirmed` future or answer leakage rejects a pre-release candidate.
- `suspected` leakage sets governance routing fields and blocks normal approval. The candidate can proceed only after redaction and full revalidation produce a non-suspected objective leakage result, or through an explicit exceptional governance path that is excluded from normal calibration evidence.
- `minor_redactable` metadata leakage can be redacted only before task approval and must be followed by full replay, oracle probes, and leakage scans.
- Leakage discovered after release writes `task_retirement` or `release_maintenance_finding` records, quarantines affected tasks from new releases, invalidates affected scorecards when score impact is material, and may suspend or revoke repository-agent admissions whose scopes depended on the contaminated evidence.

## 6. Suite and Release Coverage Profile

A `benchmark_release` is certified only for the authorization scopes covered by its released task population. Release publication computes a `release_coverage_profile` from immutable membership and certified task profiles:

- task count and release weight by task family, capability, component/path, risk class, required permission class, high-impact path class, and source type;
- oracle-grade distribution by count and weight;
- A-oracle weight, B-oracle weight, C advisory-only references, and D count;
- duplicate-cluster weights and maximum single-cluster contribution;
- flakiness and runtime-budget distribution;
- recent-task coverage for repositories or components with fast drift;
- canonical-verification readiness expectations for later benchmark evaluations;
- high-risk permission coverage by component, not just repository-wide average;
- unsupported authorization scopes and the missing coverage dimensions that made them unsupported.

Default release certification expectations are policy-versioned rather than hard-coded in prose. Automatic policy calibration may promote updated release-admission or coverage-profile parameters when objective evidence, controls, and the effective risk-profile constraints support them; the seed stance is:

- D-grade oracles are forbidden in certified release membership.
- C-grade evidence is advisory and cannot contribute certified release weight.
- A-grade oracle weight should dominate release weight; B-grade weight is capped by policy and must be visible in the release profile.
- Confirmed leakage count must be zero.
- Duplicate cluster weight must stay within policy caps.
- High-risk write or autonomous scopes require component-specific and high-impact-path coverage, not a repo-wide average.
- Every published release declares `supported_authorization_scopes[]` and `unsupported_authorization_scopes[]`.

Release coverage weight and score weight are deliberately separate. Release publication freezes `benchmark_release_membership.inclusion_weight`, oracle grade, duplicate-cluster identity, high-impact/risk tags, permission tags, and coverage profiles. Later scorecards derive score weights from those immutable facts under [scoring-semantics.md](./scoring-semantics.md), applying oracle discounts, B-oracle caps, duplicate-cluster caps, and high-impact/risk weighting without editing release membership.

Calibration may consume release coverage profiles, validation probes, no-op/known-bad/mutation controls, historical pre-fix states, and post-release maintenance findings to improve future policy profiles. It must not retroactively edit the release profile or turn a human review outcome into calibration truth.

## 7. Mapping Coverage to Authorization Scope

Authorization cannot exceed measured release coverage. The authorization policy consumes `benchmark_scorecard.task_family_coverage`, the scorecard's evaluated capability envelope, and the release `release_coverage_profile`:

- A requested scope is eligible only if it is a subset of a release-supported scope and the scorecard completed enough release weight for that subset.
- A whole-repository grant requires every repository-policy critical task family and high-impact path class for the requested tier.
- A component, path, module, task-family, or permission-specific grant may be narrower than the release, but must name the narrowed scope in `authorized_capability_envelope` and `target_condition_basis`.
- A high-risk permission class such as broad shell, workflow/dependency/build/test edits, protected-resource automation, merge/release automation, or secret-adjacent work requires coverage for the relevant component or high-impact path class.
- Unsupported scope produces `targeted_validation_required`, `full_rebenchmark_required`, `downgrade`, or `deny` according to `authorization-semantics.md`; it must not become a hidden warning inside a grant.

Release coverage is release evidence. A later scorecard can fail to complete enough of a certified release, and a later authorization decision can narrow further, but neither may widen beyond the release-supported coverage profile.

## 8. Model and Schema Extensions

The existing object model is extended through fields, summaries, exact evidence refs, and two supporting resources: `leakage_report` for machine-readable leakage findings and `release_maintenance_finding` for post-release invalidation subjects that are broader than a single task retirement. These resources do not replace the candidate, task, release, scorecard, authorization, or admission lifecycles.

`task_candidate` additions:

- `T_task`, `source_anchor.source_type`, `source_refs[]`, and source-time provenance;
- `allowed_inputs`, `disallowed_inputs`, and `expected_artifacts`;
- `required_permissions`, `capability_tags[]`, `component_tags[]`, `risk_class`, and `high_impact_path_classes[]`;
- `duplicate_cluster_id`, similarity score, and release-weight cap recommendation;
- `task_admission_gate_results`;
- `oracle_profile_draft`;
- `leakage_kind[]`, `leakage_severity`, `leakage_handling_decision`, `leakage_review_required`, `acut_visible_surfaces[]`, `redaction_revalidation_lineage`, `leakage_report_ref`, `leakage_report_digest`, and contamination summary;
- `review_reason_codes[]` and proposed reviewer action.

`validation_result` additions:

- `benchmark_admission_policy_version`;
- `oracle_profile` with grade, verifier family, confidence, scope, known limitations, runtime, flakiness, and probe results;
- `validation_probe_results[]`;
- `leakage_kind[]`, `leakage_severity`, `leakage_handling_decision`, `leakage_review_required`, `acut_visible_surfaces[]`, `redaction_revalidation_lineage`, `leakage_report_ref`, and `leakage_report_digest`;
- `task_quality_gate_summary`;
- `admission_verdict`: `certify`, `reject`, `needs_review`, or `repair_required`;
- `review_reason_codes[]`.

`task` additions:

- certified task profile copied from the approving validation result, including oracle grade, capability/component/risk tags, duplicate cluster, required permissions, leakage clearance, and benchmark-admission policy version.

`benchmark_release` and `benchmark_release_membership` additions:

- release membership copies task-family, capability, component, risk, oracle-grade, duplicate-cluster, and required-permission summaries at publication time;
- `release_coverage_profile`;
- `supported_authorization_scopes[]`;
- `unsupported_authorization_scopes[]`;
- `release_admission_policy_version`;
- release certification verdict and governance refs when publication involved annotation, pause, override, rollback, or exceptional policy ownership.

`benchmark_scorecard`, `authorization_decision`, `repository_agent_admission`, and `repository_agent_operating_state` additions:

- references to the release coverage profile or digest used for authorization interpretation;
- unsupported-scope and missing-coverage reason codes when policy narrows, downgrades, or denies;
- invalidation/suspension cause refs when post-release contamination affects the basis.

`task_retirement` additions:

- retirement/quarantine cause code, including `leakage_confirmed`, `oracle_invalid`, `oracle_weakened`, `flaky_over_threshold`, `environment_unreplayable`, `duplicate_overweight`, `source_provenance_invalid`, or `policy_retired`;
- subject kind is always `task` for task retirement; release-wide or scorecard/admission-wide maintenance is represented by `release_maintenance_finding`;
- affected release memberships, scorecards, authorization decisions, repository-agent admissions, and replacement task refs where known;
- invalidation severity: `advisory`, `quarantine`, `scorecard_invalidating`, or `admission_invalidating`.

`release_maintenance_finding` additions:

- subject kind: `benchmark_release`, `benchmark_release_membership`, `benchmark_scorecard`, `authorization_decision`, `repository_agent_admission`, or `release_coverage_profile`;
- finding type such as `post_release_leakage`, `oracle_invalidation`, `coverage_drift`, `evidence_corruption`, `policy_change`, or `scope_unsupported`;
- invalidation severity: `advisory`, `quarantine`, `scorecard_invalidating`, or `admission_invalidating`;
- leakage summary fields when the finding is leakage-related;
- affected release memberships, scorecards, authorization decisions, repository-agent admissions, and required next actions.

`admission_review_record` additions:

- review subject kind, reason codes, deterministic gate summary, governance decision, required fixes, waived warnings if any, exception/override classification, and supersession reference.

Admission review and candidate governance states use one shared vocabulary:

- `pending`: review exists or is required, but no final decision has been recorded.
- `approved`: governance approves an exceptional path or annotation; normal task materialization still requires automated admission gates to pass.
- `rejected`: the subject must not proceed under the reviewed basis.
- `repair_required`: deterministic fixes are required before another validation or release-certification attempt; `required_fixes[]` must be populated.
- `waived_warning`: non-hard warnings are accepted with `waived_warning_codes[]`, rationale, and bounded scope. This does not supply benchmark truth.
- `retired`: the candidate or task is removed from active certification path.

`task_candidate.review_state` also allows `not_required` as a projection value when no governance review is required. `not_required` is not a valid append-only `admission_review_record.review_state`. A candidate in `review_state = repair_required` must also project candidate lifecycle status `RepairRequired` until repair and revalidation create a new validation result and a superseding governance state. A `waived_warning` review can accompany approval only when the automated validation verdict can otherwise certify and no hard failure is present.

## 9. Workflow Integration

Candidate build:

- freezes `T_task`;
- records source provenance, task boundary, proposed capability/risk tags, and duplicate-cluster identity;
- ensures Golden-assisted discovery lineage is captured in `candidate_generation_run` and `generation_context_lineage` when used.

Replay and environment build:

- builds the replay plan and environment separately from validation;
- records unreplayability as a domain outcome rather than allowing approval by approximation.

Validation:

- runs base-state, target-state, no-op, known-bad, flakiness, runtime, and leakage probes;
- assigns oracle grade and admission verdict;
- writes `validation_result` and sets `review_required` / `review_reason_codes` on the candidate when needed;
- materializes `task` only after an accepted validation result and automated policy-admission result exist.

Governance review:

- writes append-only `admission_review_record` entries for high-risk, borderline, suspected leakage, weak oracle, Golden/Judge conflict, duplicate, operator-requested review, pause, override, rollback, or exceptional policy ownership;
- normal approval still requires objective gate success; governance records can require fixes and revalidation, annotate decisions, or own an exceptional non-calibration path, but they do not directly convert a weak candidate into a certified task.

Benchmark release:

- reads approved task profiles;
- computes release coverage and supported/unsupported authorization scopes;
- rejects or keeps a release in draft when certification gates fail for the requested release type;
- publishes certified immutable membership only after automated release certification passes; a recorded policy exception may publish a non-certified diagnostic release, but that release cannot support repository-agent authorization or normal calibration evidence.

Scoring and authorization:

- consume the frozen release profile and scorecard coverage;
- cannot use task families, components, permission classes, or oracle grades that were not present in the release profile to justify broader scope;
- route unsupported or post-release-invalidated evidence to targeted validation, full rebenchmarking, suspension, revocation, downgrade, or denial.

Policy calibration:

- consumes immutable release, validation, scorecard, canonical-verification, control, and maintenance evidence to calibrate future release-admission, coverage, scoring, reliability, and authorization policy profiles;
- runs automatic controls and baselines through existing workflows;
- excludes calibration subjects whose objective truth would require human judgment;
- writes `policy_calibration_run`, `calibration_truth_observation`, and `calibrated_policy_profile` records rather than changing release membership, release coverage, scorecards, or decisions in place.

Maintenance:

- post-release findings enter `RetirementWorkflow`;
- affected scorecards and admissions are not edited in place, but new invalidation, suspension, revocation, or supersession records point back to the task-retirement cause.

## 10. Governance Routing

The automated admission policy must either certify, repair/revalidate, reject, quarantine, retire, or block ambiguous cases. Human governance may be required by repository policy for annotation, pause, override, rollback, or exceptional policy ownership, but governance records are not normal benchmark acceptance truth and are not calibration labels.

Route these cases to governance while excluding them from normal calibration evidence until objective repair/revalidation succeeds:

- suspected future or answer leakage;
- any high-risk permission or high-impact path class entering a release or authorization scope;
- B-grade oracle used for a high-impact or high-tier scope;
- any C-grade Golden/Judge/human evidence that materially affects reviewer confidence, even though it cannot be sole authority;
- duplicate clusters close to the policy cap;
- partial replay fidelity or environment approximation;
- flakiness near threshold;
- verifier logs with possible solution-bearing output;
- conflict between deterministic validation and Golden/Judge findings;
- first `G3` repository admission for a scope, every `G4` or `G5` grant, reused/supplemented lineage, partial coverage, and any post-release invalidation that may affect an effective admission.

Governance outcomes are append-only:

- `pending`: governance review exists or is required, but no final decision has been recorded.
- `approved`: governance accepts an annotation or exceptional policy path; automated gates still decide normal certification.
- `rejected`: candidate/release/admission must not proceed.
- `repair_required`: deterministic fixes are needed before rerun and `required_fixes[]` must be populated.
- `waived_warning`: non-hard warning accepted with rationale and bounded scope.
- `retired`: candidate or task is removed from active certification path.

Candidate review projections add `not_required` only when no governance review is required. `repair_required` is a governance outcome and a non-terminal candidate lifecycle state; after repair, replay and validation rerun and any previous review is superseded by a new review record. Hard failures such as confirmed leakage, no replay, and D-grade sole oracle cannot be converted to certified status by `waived_warning`.

## 11. Post-Release Quarantine, Retirement, and Invalidation

Immutable releases remain historically queryable, but their evidentiary effect can be curtailed after publication.

Post-release findings include:

- confirmed future or answer leakage;
- verifier bug, hidden-test exposure, or oracle invalidation;
- flakiness above threshold;
- replay environment no longer reconstructable for required maintenance;
- duplicate-cluster overweight discovered after release;
- source provenance invalidation;
- evidence-bundle corruption or restricted artifact exposure.

Handling path:

1. Write a `task_retirement` when the finding retires or quarantines a specific task, or a `release_maintenance_finding` when the subject is a release, release membership, scorecard, authorization decision, repository-agent admission, or release coverage profile. The record must include subject kind, cause, severity, evidence refs, affected memberships, affected scorecards/admissions where known, and required next actions.
2. Mark affected tasks as quarantined from future releases; if the task is already approved, set task retirement markers rather than editing the old approval.
3. Compute affected benchmark releases, scorecards, authorization decisions, repository admissions, and operating-state coverage entries.
4. For advisory impact, surface warnings and require review on renewal.
5. For scorecard-invalidating impact, exclude affected evidence from future scorecards and require a new scorecard, targeted validation, or new release before fresh authorization.
6. For admission-invalidating impact, route to `suspend` or `revoke` on `repository_agent_admission` and project `G0` or required next action in operating state.

Any confirmed post-release leakage that could have helped an ACUT pass invalidates affected scorecards for the contaminated scope. Affected admissions must be suspended or revoked unless a still-valid release subset and scorecard can support the same or narrower target condition under the authorization policy.

## 12. Traceability

- [system-design.md](./system-design.md) defines the stage boundaries this rubric plugs into.
- [module-design.md](./module-design.md) defines module ownership for candidate build, replay, validation, release publication, scoring, and authorization.
- [scoring-semantics.md](./scoring-semantics.md) defines how admitted release facts, oracle grades, duplicate caps, and high-impact/risk tags affect scorecard aggregation.
- [policy-calibration.md](./policy-calibration.md) defines how release, validation, scorecard, control, and maintenance evidence calibrate future policy profiles without human baselines or historical rewrites.
- [data-model.md](./data-model.md) defines the resource families and schema extensions that persist admission facts.
- [interface-contracts.md](./interface-contracts.md) defines command/query contracts for validation, approval, release publication, scoring, and authorization reads.
- [workflow-runtime.md](./workflow-runtime.md) defines workflow and queue placement for admission probes, review, release certification, and retirement.
- [authorization-semantics.md](./authorization-semantics.md) defines how release coverage and scorecards map to repository-agent admission.
