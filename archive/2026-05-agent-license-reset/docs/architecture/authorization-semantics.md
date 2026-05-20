# Authorization Semantics for Repository-Agent Admission

## 1. Purpose

This document defines the authorization semantics for Barcarolle's repository-scoped agent admission system. It refines the policy layer described in [system-design.md](./system-design.md), [module-design.md](./module-design.md), [benchmark-admission-rubric.md](./benchmark-admission-rubric.md), [scoring-semantics.md](./scoring-semantics.md), [policy-calibration.md](./policy-calibration.md), [interface-contracts.md](./interface-contracts.md), [api-schema.md](./api-schema.md), and [data-model.md](./data-model.md).

The design is intentionally repository-scoped. An admission or License means "this tested-agent snapshot is admitted for this repository scope, target condition, tier, evaluated autonomy/capability envelope, and time window." It is not a universal claim about the agent, model, vendor, harness, or another repository.

Barcarolle is an evidence, benchmark-scorecard, and License issuance/distribution system. It does not implement a runtime enforcement plane that constrains an agent to the licensed level. A Barcarolle License is the repository owner's evidence-backed admission record for a tested-agent snapshot under a target condition; it is not a guardrail mechanism. Downstream systems such as Codex, OpenClaw, CI, IDEs, agent runners, repository policy engines, or organizational workflows may consume the License and apply local policy, but that enforcement behavior is outside Barcarolle's implementation boundary.

This is intentional for the trusted-internal product mode. In the expected use cases, repository owners and ACUT owners are aligned stakeholders using Barcarolle to compare configurations and decide what level of repository access is reasonable, not adversaries trying to bypass a guardrail. A Barcarolle License is therefore a repository-scoped evidence and governance contract: it records what was evaluated, what target condition it applies to, what tier was granted, and what a consumer can inspect. `G5` is the fully trusted YOLO-class tier: after the License is issued, Barcarolle semantics do not impose per-action human approval or a guarded flow inside the licensed scope. A separate consumer may still impose local restrictions, but those restrictions are not part of the `G5` License semantics.

A benchmark scorecard is valuable even when no License is requested. The same evidence chain can support agent-configuration comparison, scorecard reporting, and configuration optimization without issuing a repository-agent License.

Semantic policy family: `authorization_semantics_v1`. Exact decisions record the active calibrated `authorization_policy_version`, calibrated policy-profile ref, and effective repository/organization risk-profile basis used inside that semantic family. `authorization_decision.authorization_policy_version` is canonical; any legacy field named `policy_version` aliases that value and must not persist as a separate identity axis.

## 2. Non-Negotiable Boundaries

- Benchmark facts stay immutable: `benchmark_evaluation`, `evaluation_run`, `canonical_verification_record`, `score_bundle`, and `benchmark_scorecard` record what happened.
- Policy facts stay separate: `authorization_decision` records how a scorecard was interpreted under a policy version.
- Admission facts stay separate: `repository_agent_admission` records the repository-side License that external consumers may verify and consume.
- Operating state stays separate: `repository_agent_operating_state` reports what snapshot is live or selected now and whether it is covered by active admissions.
- Correctness-root evidence must come from deterministic repository-native validation and `trusted_barcarolle_evidence`, especially clean-room `canonical_verification_record` records.
- Golden and Judge artifacts may enrich review, scoring confidence, and risk explanation. They must not directly grant, revoke, or widen permissions.
- Runtime enforcement stays outside Barcarolle. Policy may record the operating envelope, License-consumption assumptions, and external policy compatibility, but Barcarolle does not ship a guard that constrains every agent action.
- Trusted-internal operation does not require cryptographic or adversarial attestation. Declared, owner-attested, adapter-observed, and third-party-attested evidence can be sufficient depending on tier, target condition, and review policy. Attested or adversarial modes can be added later by extending evidence basis and target-condition fields without changing these resource boundaries.
- Thresholds, coverage cutoffs, reliability eligibility, and targeted-validation/full-rebenchmark cutoffs are governed by automatic policy calibration. Calibration output is a policy fact, not a benchmark fact; it can supersede future decisions but cannot mutate historical scorecards or authorization decisions.
- Repository or organization risk appetite is explicit. Authorization must consume an effective `repository_risk_profile` or inherited organization profile as a policy input, and must not infer risk tolerance from benchmark score, release coverage, or calibration evidence alone.

## 3. Admission Tier Taxonomy

The canonical admission scale is `G0` through `G5`. Policy may deny or downgrade a requested tier, but it must not invent unnamed intermediate tiers.

| Tier | Name | License meaning | Outside the License scope |
| --- | --- | --- | --- |
| `G0` | `no_admission` | No Barcarolle-issued License for repository operation. Used for deny, expired, revoked, suspended, or outside-admission state. | All License-covered repository actions. |
| `G1` | `read_only_analysis` | Read repository context, benchmark results, and allowed evidence summaries; produce analysis outside repository write surfaces. | No branches, PRs, commits, issue comments, CI triggers, release actions, secrets, or policy changes. |
| `G2` | `patch_proposal` | Produce patch bundles, review notes, or local validation output for human application; may run allowed local/sandbox checks in the admitted capability envelope. | No direct repository writes, no branch or PR creation, no protected-resource changes. |
| `G3` | `scoped_branch_write` | Create or update owned branches and draft PRs only inside authorized modules, paths, task families, and capability envelope; trigger normal CI for those branches. | No protected-branch merge, release, deployment, secret, workflow-permission, CODEOWNERS, security-policy, or repository-admin changes unless a narrower policy explicitly routes them to human approval. |
| `G4` | `broad_branch_write` | Create or update owned branches and PRs across the admitted repository/resource scope; update code, tests, docs, and build files within that scope; trigger normal CI. | No protected-branch merge, release, deployment, secret, repository-admin, or direct production action. Sensitive workflow/security/permission files require explicit human approval before write or merge. |
| `G5` | `autonomous_yolo_repository_operation` | Fully trusted autonomous YOLO-class repository operation under the licensed scope and evaluated autonomy/capability envelope, with no Barcarolle-defined per-action human approval or guarded flow. The envelope may include high-permission shell, file, network, and tool operation, broad repository edits, high-impact file classes, workflow/dependency/build/test changes, branch/PR automation, merge, release, or other explicitly licensed operations when evidence and repository policy support them. | Anything outside the License scope, target condition, evaluated envelope, freshness window, or repository policy exclusions. `G5` is not universal unlimited permission outside its recorded scope. |

`G5` is the top YOLO-class License tier, not a guarded-flow tier. Human review can be required to issue, renew, suspend, or revoke a `G5` License, but per-action human approval is not intrinsic to `G5` after the License is effective. If an external consumer imposes per-action approval as local policy, that is a consumer-side restriction outside Barcarolle's `G5` semantics.

## 4. Evidence and Threshold Gates

### 4.1 Common Scorecard Inputs

Authorization consumes one benchmark-authoritative `benchmark_scorecard` unless a governed `agent_change_review` explicitly records `reused` or `supplemented` lineage. A scorecard is authorization-eligible only when it records:

- `aggregate_score` on a 0-100 scale;
- scoring semantics version, scorecard policy version, aggregation algorithm, and complete `score_input_set_digest`;
- `coverage_summary` with benchmark-release weight completed under the requested scope;
- `task_family_coverage` for every requested task family or an explicit narrowing reason;
- denominator summary and missing-run summary covering scoreable, unverified, incomplete, canceled, infra-failed, verifier-flaky, policy-invalid, and blocked entries;
- `minimum_sample_summary`, `aggregate_stability_label`, and `reliability_label`;
- release coverage profile reference, supported authorization scopes, unsupported authorization scopes, and benchmark-admission policy versions used by the release;
- `canonical_verification_coverage`;
- `evaluated_capability_envelope_id` and coverage details;
- `evaluation_mode` and `adapter_purity_level`;
- `acut_field_evidence_basis_summary`;
- `evidence_trust_basis`;
- `score_input_set_digest`, exact contributing score-bundle identities, and missing or blocked score input entries;
- `authorization_readiness`.

Policy gates must read task-family eligibility from the stable top-level `benchmark_scorecard.task_family_coverage` field. `aggregate_score` is the score-weight-denominator result computed by scoring semantics; `completed_score` is diagnostic and must not satisfy authorization thresholds. `coverage_summary` is the aggregate release/scope coverage summary, `denominator_summary` and `missing_run_summary` explain missing or blocked evidence, `evaluated_capability_envelope` carries the capability-envelope and partial-evaluation policy inputs, and `metric_breakdown` is diagnostic drill-down. Implementations must not derive task-family gate decisions by scraping `metric_breakdown` or by interpreting prose summaries.

Unverified, incomplete, canceled, infra-failed, verifier-flaky, policy-invalid, and blocked runs may explain missing coverage, but they must not contribute positive correctness score. If canonical verification is absent for a positive score-contributing run, that score input is invalid for authorization. Scoreable agent-owned zeroes such as verified failure, agent timeout, malformed agent submission, or trusted policy violation can remain in the score input set as completed zeroes.

### 4.2 Tier Gates

All thresholds are minimums. A requested tier must pass the active calibrated score and coverage thresholds plus the gate model in Section 5. Evaluation mode is an identity and applicability input, not a standalone maximum-tier cap.

The table below is the seed `authorization_semantics_v1` threshold profile. `PolicyCalibrationWorkflow` may promote a later calibrated profile when repository historical fixes, known pre-fix states, no-op and mutation controls, retrieval-only or rule-based baselines, prior agent configurations, repeated-run variance, canonical verification records, release coverage slices, explicit risk-profile constraints, and sensitivity analyses satisfy the promotion gates in [policy-calibration.md](./policy-calibration.md). A promoted profile must receive a new exact `authorization_policy_version` or calibrated profile ref. Existing decisions keep the profile and risk-profile basis they used.

| Requested tier | Minimum aggregate score | Minimum benchmark coverage | Minimum task-family coverage | Required evidence basis | Required ACUT field basis | Admission-review condition |
| --- | ---: | ---: | ---: | --- | --- | --- |
| `G1` | 50 | 30% of requested release/scope weight | At least one relevant family or an explicitly single-family scope | Canonical verification for every score-contributing run; no critical policy or leakage finding | Material fields present with stable digests; `declared` is acceptable for low-risk read-only scope | Required only for critical warnings, reused/supplemented lineage, or repository policy override |
| `G2` | 65 | 50% | 40% for each authorized family, or scope narrowed to covered families | Same as `G1`; agent-submitted traces are advisory only | Model, prompt/policy, tool profile, permission profile, runtime budget, run environment, mode, purity, and adapter manifest present; declared-only runtime is allowed because tier is non-writing | Required for weak oracle warnings, partial family narrowing, reused/supplemented lineage, or Golden/Judge conflict |
| `G3` | 78 | 75% | 60% for each authorized family; at least two covered families unless the requested scope is single-family by design | Canonical verification coverage at least 95% of completed scored weight; process evidence or attestations must support any runtime, workspace, network, and tool posture claim that affects the admission | Material ACUT fields are stable and reviewable; fields material to the requested operation are `adapter_observed`, `third_party_attested`, `barcarolle_trusted`, or declared with explicit repository-owner attestation plus external License-consumption assumptions that bind the omitted dimension at operation time | Required for first `G3` admission for a repository scope, partial coverage, reused/supplemented lineage, native YOLO high-tier grants from declared/attested fields, or any material risk finding |
| `G4` | 88 | 90% | 80% for every authorized family, with no uncovered critical family | Canonical verification coverage at least 98% of completed scored weight; evidence trust basis includes `trusted_barcarolle_evidence` for correctness and sufficient attested, observed, or trusted process evidence for the target condition | Runtime, workspace, network, permission, tool, adapter, and run-environment posture must be attested, observed, trusted, or matched by explicit License-consumption assumptions; model/prompt/memory digests may be declared only when immutable, reviewable, and not material to the requested operation beyond identity binding | Required for every `G4` grant, renewal, and supplementation |
| `G5` | 94 | 95% | 90% for every authorized family, with explicit coverage of high-impact file or task classes in the requested scope and autonomy envelope | Same as `G4`, plus no unresolved critical Judge, verifier, stability, leakage, or policy-risk finding | Same as `G4`; fields relevant to autonomous YOLO-class operation must be attested, observed, trusted, or explicitly declared with accepted external-policy assumptions in the target condition | Required for issuance, renewal, suspension lift, or revocation review; never required per action by tier semantics |

If a requested tier fails but a lower tier passes all gates, policy returns `downgrade` with the highest passing tier. If no tier passes `G1`, policy returns `deny`.

High-tier authorization must respect the calibrated profile's truth/control applicability. A calibrated `authorization_policy_version` may be used for `G4` or `G5` only when the referenced `calibrated_policy_profile.high_tier_authorization_applicability_summary` marks the requested semantic slice as supported by positive controls, negative controls, safety controls, stability observations, coverage observations, unsafe false-positive measurement, and promotion gates. If the profile marks the slice `blocked`, `shadow_only`, `insufficient_control_power`, or `targeted_validation_required`, authorization must return the corresponding non-grant outcome even if the aggregate score exceeds the numeric tier threshold.

Unsafe false-positive budgets are promotion constraints, not benchmark facts and not risk-profile labels. Authorization consumes the promoted profile result and the effective risk-profile gate result; it does not recompute calibration labels from human review or infer that a repository accepts more risk because an agent scored highly. A risk profile can tighten or forbid a tier after promotion, but it cannot turn an underpowered calibration slice into high-tier support.

### 4.2a Risk-Profile Constraints

Before selecting thresholds or granting a tier, authorization resolves the effective risk profile for the requested repository scope. The source may be an organization default, repository profile, or narrower component/path override, but the resolved `repository_risk_profile_id`, version, digest, inheritance basis, and constraint summary must be persisted on the decision.

A risk profile can tighten or forbid authorization; it cannot create positive evidence. It can require:

- stricter minimum aggregate scores, coverage, reliability labels, canonical-verification coverage, sample counts, ACUT binding basis, or evidence trust basis than the calibrated seed would otherwise require;
- lower maximum tiers for specific risk classes, permission classes, protected resources, high-impact path classes, or target-condition bases;
- `needs_human_review` before effectivity for high-impact paths, broad autonomy, exception grants, or owner-attested native-agent fields;
- shorter freshness windows, earlier renewal, targeted validation, or full rebenchmarking after repository drift;
- suspension, revocation, or reauthorization impact review when the active risk profile becomes stricter than the profile that supported an effective admission.

A risk profile cannot:

- convert unsupported release scope into supported scope;
- treat human preference as benchmark truth or calibration labels;
- bypass clean-room canonical verification, ACUT binding, subject-applicability, License-consumption compatibility, or freshness gates;
- reopen the external License-consumption protocol into a Barcarolle-owned runtime enforcement plane;
- upgrade `patch_only`, `trace_submission`, or `harness_native` evidence beyond the subject and observation boundaries defined in this document.

If no effective risk profile exists, write-capable authorization is `blocked`. A first repository registration may use a persisted seed risk profile such as `default_internal_balanced`, but the seed profile must still be an explicit resource or exact seed basis with a digest so later decisions are auditable.

### 4.3 Authorization Readiness

`authorization_readiness` has these policy meanings:

- `ready`: all gates for the requested scope can be evaluated without narrowing.
- `partial`: some modules, task families, paths, or capability-envelope dimensions are not covered. The policy must either narrow scope or return `targeted_validation_required`.
- `blocked`: evidence is insufficient, stale, conflicting, unverified, contaminated, or outside the evaluated target condition. The policy must deny, suspend, revoke, or require full rebenchmarking.

`reliability_label = blocked` always implies `authorization_readiness = blocked`. `reliability_label = low` may support diagnostic comparison or low-risk `G1`/`G2` decisions only when the requested tier table and repository policy allow it. `G4` and `G5` require a scorecard whose reliability and minimum-sample summaries pass the high-tier gates for every authorized critical family and high-impact path class.

Reliability-label eligibility is calibrated alongside threshold and coverage policy. A later profile may change which label supports which tier, but it must do so through a new calibrated policy profile and must preserve monotonic behavior: weaker reliability cannot authorize a broader or higher-risk scope than stronger reliability under the same scorecard basis.

### 4.4 Benchmark Admission Preconditions

Authorization policy must treat benchmark admission as a hard precondition, not as an informational quality score.

For any write-capable tier, the supporting scorecard must resolve to a certified `benchmark_release` with:

- `release_coverage_profile` present under a known release-admission policy version;
- `supported_authorization_scopes[]` that cover the requested repository scope, task family, component/path, risk class, permission class, high-impact path class, and capability envelope;
- no D-grade oracle in certified release membership;
- no confirmed future or answer leakage in any task that contributes to the requested scope;
- no unresolved `task_retirement` or `release_maintenance_finding` with scorecard- or admission-invalidating severity for the requested scope.

If the release marks the requested scope unsupported, the policy must return `targeted_validation_required`, `full_rebenchmark_required`, `downgrade`, or `deny`; it must not grant and merely warn. High-risk permission classes require component-specific and high-impact-path coverage in the release profile. A repository-wide average cannot satisfy high-risk component authorization when the component itself is uncovered.

Golden and Judge findings may downgrade confidence, trigger review, or force suspension/revocation when they identify oracle or leakage risk. They cannot raise an unsupported release scope to supported, cannot convert C-grade evidence into an objective task oracle, and cannot by themselves grant or widen authorization.

## 5. Gate Model for Mode, Subject Applicability, Binding, License Consumption, and Risk Appetite

Policy must evaluate five independent gates after score and coverage thresholds. The first four gates replace mode-only caps; the fifth prevents calibrated evidence from silently deciding repository risk appetite.

| Gate | Question answered | Passing evidence |
| --- | --- | --- |
| Correctness evidence | Did the submitted result solve the benchmark tasks under the requested scope? | Aggregate score, denominator/missing-run summary, minimum sample, reliability label, task-family coverage, stability, oracle quality, no critical leakage or verifier risk, and clean-room `canonical_verification_record` coverage from `trusted_barcarolle_evidence`. |
| Production fidelity / subject applicability | Did the evaluated subject match the subject being admitted? | A target-condition basis that identifies `native_agent`, `native_agent_with_observer`, `agent_with_tool_mediation`, or `Agent + Harness`, and records whether the requested admission subject is exact, equivalent, narrower, or different. |
| ACUT binding / attestation | Is the submitted result tied to the declared tested-agent snapshot and material configuration? | Backend-registered immutable ACUT digests, submission producer identity, adapter manifest, run-environment declaration, owner or third-party attestations, provider/CI evidence, adapter observations, or Barcarolle-trusted evidence for material fields. |
| License consumption / operating-envelope compatibility | Is the requested License scoped tightly enough for external consumers to verify compatibility with the evaluated target condition and envelope? | A target-condition basis and consumption contract covering repository identity, tested-agent snapshot, admission subject, evaluated envelope, autonomy level, branch/PR ownership when relevant, path/module/task-family scope, protected resources, freshness, suspension/revocation state, and any external approval or enforcement assumptions. |
| Risk appetite / repository policy constraint | Is the requested tier, scope, and operation inside the explicit risk tolerance accepted for this repository or organization? | Effective `repository_risk_profile` basis with satisfied tier, coverage, reliability, evidence-basis, freshness, review, forbidden-scope, and risk-budget constraints for the requested operation. |

### 5.1 Evaluation Mode as Applicability Input

Evaluation mode and adapter purity describe the evaluated subject and observation boundary. They do not by themselves make evidence weak or strong.

| Evaluation basis | Subject/applicability meaning | Authorization consequence |
| --- | --- | --- |
| `patch_only` with `A0_transport_only` or non-mutating `A1_environment_wrapper` | Native agent operates in the common YOLO/full-access style and submits a result for clean-room verification. Production fidelity for native YOLO can be high; process observation may be low. | May support `native_yolo` admissions through high tiers when correctness evidence, ACUT binding/attestation, and License-consumption compatibility pass. If binding or consumption assumptions are weak, downgrade or require targeted validation because of that failed gate, not because of mode. |
| `trace_submission` with `A0_transport_only` or non-mutating `A1_environment_wrapper` | Same native YOLO subject, with additional agent-submitted traces. Traces are audit, binding, or risk evidence, not correctness root evidence. | May support `native_yolo` admissions through high tiers under the same gates. Trace quality can improve or weaken confidence, but cannot replace canonical verification. |
| `observed_run` with `A0_transport_only` or `A1_environment_wrapper` | Native agent loop is preserved while an outer boundary observes or constrains declared workspace, process, command, network, or runtime signals. | Applies directly to the observed target condition. It may authorize unobserved native YOLO only when the wrapper is proven non-material or the target condition explicitly allows equivalent native YOLO operation. |
| `observed_run` with `A2_tool_mediation` | The tool surface is mediated, so the evaluated subject includes that mediation boundary. | Admission applies to the mediated-tool target condition only. It must not be used as fresh evidence for unmediated native YOLO operation. |
| `harness_native` or `A3_harness_native_controller` | The evaluated subject is `Agent + Harness`; Barcarolle or a specified harness controls loop, prompt, tools, or another material controller surface. | May support high-tier harness-bound admission when all gates pass and the License requires the same harness target condition. It is lower-applicability evidence for common native YOLO admission unless separately supplemented by native evidence. |

### 5.1a Native YOLO Evidence Interpretation

Native YOLO admission is condition-bound. The granted tier is meaningful only together with the certificate's target condition, capability envelope, evaluation mode, adapter purity, ACUT field evidence basis, binding/attestation basis, evidence lineage, freshness state, and repository scope. These fields are admission semantics, not display-only metadata.

Open-network native evidence is valid evidence for open-network native target conditions. It should not be downgraded merely because network access was available when the intended production condition also includes network access. Conversely, offline or restricted-network evidence must not be treated as a capability upper bound for full native open-network operation unless a governed compatibility rule explicitly says the restricted condition is equivalent or broader for the requested operation.

Open-network historical-task results should be interpreted as production-fidelity evidence. They may also be blind-capability evidence when task sealing, leakage checks, retrieval controls, memory posture, and evidence basis support that stronger claim, but blind capability is not a precondition for condition-bound native YOLO admission. Sealed or holdout tasks can strengthen the evidence basis without becoming a mandatory separate admission track.

Barcarolle does not enforce runtime behavior. It defines, records, signs, publishes, and audits the applicability semantics of the admission. Downstream use outside the certificate condition is outside Barcarolle's claimed applicability. See [native-yolo-admission-semantics.md](../decisions/native-yolo-admission-semantics.md).

### 5.2 Native YOLO License Path

A high-tier license for common native YOLO agent operation is valid when all of these conditions hold:

1. The requested `target_condition_basis` declares `admission_subject = native_yolo` and the scorecard subject is `native_agent` with `patch_only`, `trace_submission`, or another non-contaminating native mode.
2. Correctness evidence meets the requested tier thresholds through clean-room canonical verification, benchmark score, benchmark coverage, `task_family_coverage`, stability, and oracle quality.
3. Production fidelity is `exact` or policy-defined `equivalent` for native YOLO operation: the benchmarked model, prompt/policy, tool profile, permission profile, runtime budget, memory/retrieval policy, control loop, and intended repository operation posture match the admitted native operation or differ only by a reviewed non-material wrapper.
4. ACUT binding/attestation passes for the requested tier: material snapshot fields have stable digests and provenance; the submitted result is bound to the tested-agent snapshot by producer identity, submission digest, owner or third-party attestation, adapter observation, provider/CI evidence, or Barcarolle-trusted evidence as required by the tier.
5. License-consumption compatibility passes even though Barcarolle does not control the full native loop. At minimum, the License and target condition must state the repository identity, branch/PR creation or update scope when relevant, owned branch boundaries, path/module/task-family scope, protected-resource assumptions, capability/autonomy envelope, freshness, suspension/revocation behavior, and any external approval policy that a consumer must honor.
6. Required governance review is recorded for `G4`, `G5`, first `G3` grants for a repository scope, partial coverage, reused/supplemented lineage, or any material attestation or risk finding. This review controls License issuance or exception ownership; it is not benchmark or calibration truth.

If these conditions pass, `patch_only` or `trace_submission` evidence can support `G3`, `G4`, or `G5` native YOLO admission. The granted tier is then limited by the normal score, coverage, freshness, review, scope, binding, and License-consumption compatibility gates.

### 5.3 Harness-Native Evidence

Harness-native evidence can authorize:

- `Agent + Harness` operation under the exact harness target condition;
- repository operations whose License requires that harness, adapter purity level, target-condition basis, and covered capability envelope;
- process-risk findings, debugging explanations, and supplemental review evidence for native-agent analysis.

Harness-native evidence cannot by itself authorize:

- unmodified common native YOLO operation at `G3` or above;
- a native `tested_agent_snapshot` whose prompt, tool surface, memory, model proxy, control loop, runtime, or adapter boundary differs from the harness subject;
- carry-forward to `patch_only`, `trace_submission`, or unobserved native operation unless a fresh native scorecard or governed supplemented review supplies native-subject evidence that passes all required gates.

Any result from `harness_native` must set the tested-agent snapshot subject label to `Agent + Harness`. If a repository wants both harness-bound and native YOLO admission, it must record separate target-condition bases and may have separate effective admissions for the same repository scope.

### 5.4 Gate Failure Consequences

Gate failures produce deterministic outcomes:

- Missing or conflicting adapter manifest, run-environment declaration, or ACUT identity evidence returns `blocked` readiness or `full_rebenchmark_required` when it changes the evaluated subject.
- Weak but plausibly closable ACUT binding, attestation, production-fidelity, or License-consumption compatibility evidence returns `targeted_validation_required` or `needs_human_review`, where the latter means governance review for License issuance or exception ownership rather than benchmark/calibration truth.
- A risk-profile hard constraint failure returns `downgrade`, `deny`, `targeted_validation_required`, `full_rebenchmark_required`, `suspend`, or `revoke` according to the constrained dimension. A required-review constraint returns `needs_human_review` only when every non-review evidence gate already passes.
- A requested writing tier fails when the requested operation is outside the evaluated operating envelope or cannot be expressed through verifiable License-consumption contract metadata, even if the benchmark score is high.
- If a lower tier passes every required gate, policy returns `downgrade` to the highest passing tier.

## 6. Policy Outcomes

The policy engine emits one of these outcomes. Scorecard interpretation outcomes are recorded on `authorization_decision`. Repository-side lifecycle outcomes are recorded on `repository_agent_admission` transition history when they change admission state.

| Outcome | Meaning | Required next write |
| --- | --- | --- |
| `grant` | Requested tier passes score, coverage, correctness, subject-applicability, ACUT-binding, License-consumption compatibility, explicit risk-profile, freshness, scope, and review gates. | Write an effective `authorization_decision`; if a License is requested, write an effective `repository_agent_admission`. |
| `deny` | No tier is safe, or evidence is blocked. | Write decision with `G0` and denial reason. No effective admission. |
| `downgrade` | Lower tier passes but requested tier does not. | Write decision with requested tier, granted tier, and downgrade reasons; admission may be written only for granted tier. |
| `needs_human_review` | Deterministic benchmark gates pass, but repository governance requires a human decision before License effectivity, override, or exception ownership. | Write proposed decision/admission or route governance review; do not make effective until review is recorded. |
| `targeted_validation_required` | Missing coverage can plausibly be closed by bounded extra tasks, verifier reruns, or focused review. | Write decision with missing coverage dimensions and required validation plan. |
| `full_rebenchmark_required` | ACUT, evaluated subject, mode, adapter purity, target condition, policy basis, evidence basis, or freshness changed too much for reuse. | No new effective admission from old evidence. Start new benchmark evaluation. |
| `revoke` | Existing admission is invalidated by confirmed severe evidence, policy, contamination, or safety failure. | Append revocation transition and cause. External consumers should treat the License as `G0` immediately. |
| `suspend` | Existing admission is temporarily disabled by emergency, unresolved drift, incident, or investigation. | Append suspension transition and cause. External consumers should treat the License as `G0` until lifted or superseded. |
| `lift_suspension` | Existing suspended admission can resume under the same admitted snapshot, scope, target condition, tier, and freshness boundary. | Append suspension-lift transition. Project the same admission back to `effective`; do not widen scope or extend freshness. |

Judge or Golden findings can force `needs_human_review`, `targeted_validation_required`, `downgrade`, `suspend`, or `revoke`. They cannot by themselves force `grant`, raise a tier, or supply benchmark/calibration truth. Raw Judge output is not a policy input unless the benchmark scorecard marks a governed Judge lineage as score-, process-, or confidence-contributing under [scoring-semantics.md](./scoring-semantics.md); even then authorization reads the scorecard fields, not the raw Judge artifact.

## 7. Partial Coverage and Scope Narrowing

Partial coverage is not a UI warning. It changes authorization behavior.

Policy must evaluate coverage by repository scope, task family, path/module set, and capability-envelope dimension. The coverage-policy record used by `coverage_policy_version` must expose these deterministic fields through `benchmark_scorecard.evaluated_capability_envelope.partial_evaluation_policy`, and the scorecard must copy the computed task-family and missing-coverage flags into top-level `benchmark_scorecard.task_family_coverage`:

- `max_missing_release_weight_for_narrowed_grant`;
- `max_missing_release_weight_for_targeted_validation`;
- `critical_task_families[]` for the repository scope and requested tier;
- `high_impact_path_classes[]` for the requested operation or risk class;
- `full_rebenchmark_on_missing_critical_family`;
- `full_rebenchmark_on_missing_high_impact_path`;
- `basis_change_required_for_missing_coverage`, computed true when closing the gap would change `benchmark_release_id`, `scorecard_policy_version`, `coverage_policy_version`, effective risk-profile basis, `evaluated_capability_envelope_id`, `evaluation_mode`, `adapter_purity_level`, ACUT field evidence basis, or the release task population.

If any of these fields are absent, authorization readiness is `blocked` for write-capable tiers. When coverage is partial, policy applies this fixed order:

1. Verify that the requested scope is inside `benchmark_release.supported_authorization_scopes[]`; if it is explicitly unsupported, return the policy outcome named by the unsupported-scope reason unless the request is narrowed first.
2. Compute `missing_release_weight_ratio` from uncovered requested release/scope weight divided by total requested release/scope weight, using the same weighting basis as `coverage_summary`.
3. Compute `missing_critical_family` and `missing_high_impact_path` from `task_family_coverage`, repository path policy, the release coverage profile, and the requested operation/risk class.
4. Return `full_rebenchmark_required` when `basis_change_required_for_missing_coverage` is true, when `missing_release_weight_ratio` is greater than `max_missing_release_weight_for_targeted_validation`, when `missing_critical_family` and `full_rebenchmark_on_missing_critical_family` are both true, or when `missing_high_impact_path` and `full_rebenchmark_on_missing_high_impact_path` are both true.
5. Return `targeted_validation_required` when the requested operation depends on any uncovered task family, path/module set, high-impact path class, permission class, or capability-envelope dimension that did not trigger step 4.
6. Otherwise grant only the covered subset when `missing_release_weight_ratio` is less than or equal to `max_missing_release_weight_for_narrowed_grant` and every retained task family and capability-envelope dimension meets the requested tier gate.
7. If step 6 fails, return `targeted_validation_required`.

A narrowed grant must record the narrowed scope in `authorized_capability_envelope` and `target_condition_basis`, set `authorization_readiness = partial`, and record every excluded dimension in the decision rationale and operating-state `coverage_entries[]`.

Whole-repository `G4` or `G5` requires coverage of every task family that the repository policy marks critical. A repository with only one approved task family may still grant higher tiers for that single-family scope, but the admission scope must say that it is single-family rather than whole-repository general authority.

## 8. Evidence Lineage

`repository_agent_admission.evidence_lineage` and operating-state coverage entries must use exactly these labels:

- `fresh`: direct benchmark scorecard evidence under the exact target condition, mode, purity, capability envelope, coverage policy, ACUT snapshot, and evidence basis used by the admission.
- `reused`: older evidence accepted for an equivalent or narrower target condition without new target-condition execution. Reuse cannot raise tier, widen scope, or outlive the source admission freshness boundary.
- `supplemented`: older evidence accepted only together with targeted validation, focused canonical verification, or governance review that closes named operational gaps. Supplementation cannot erase the original scorecard age, evaluated subject, target condition, or gate basis.

`authorization_decision` from a scorecard is `fresh` only relative to that scorecard identity. Reusing or supplementing old evidence is expressed by `agent_change_review` and `repository_agent_admission`, never by rewriting benchmark facts.

## 9. Freshness, Expiration, Renewal, Supersession, Revocation, Suspension, and Reinstatement

### 9.1 Freshness Windows

Default freshness windows are counted from `benchmark_scorecard.created_at` for fresh admissions:

| Tier | Freshness window |
| --- | ---: |
| `G1` | 180 days |
| `G2` | 120 days |
| `G3` | 90 days |
| `G4` | 60 days |
| `G5` | 30 days |

The admission `freshness_deadline` is the earliest of:

- scorecard creation time plus the tier freshness window;
- explicit benchmark-release retirement time;
- task-retirement or contamination time for a critical task that materially affects the admitted scope;
- policy-defined emergency cutoff;
- governance-review-imposed deadline.

### 9.2 Reuse and Supplementation Windows

For `reused` admissions, `freshness_deadline` is the earliest of:

- source admission freshness deadline;
- source scorecard freshness deadline;
- change-review time plus 45 days.

For `supplemented` admissions, `freshness_deadline` is the earliest of:

- source scorecard freshness deadline;
- latest supplemental validation time plus half of the tier freshness window;
- governance-review-imposed deadline.

Supplementation cannot renew an already stale scorecard into a high tier. If the source scorecard is stale for the requested tier, policy returns `full_rebenchmark_required`.

### 9.3 Renewal

Renewal may be:

- fresh renewal: new benchmark-authoritative scorecard for the same or changed target condition;
- reuse renewal: governance-reviewed carry-forward for equivalent or narrower scope before the source deadline;
- supplemented renewal: targeted validation plus review before the source scorecard expires.

Renewal writes a new admission and explicitly supersedes the prior effective admission for the same `repository_id + scope + target_condition_basis_identity`.

### 9.4 Supersession

For one `repository_id + scope + target_condition_basis_identity`, at most one admission may be `effective`. A newer effective admission must reference `supersedes_repository_agent_admission_id`. Historical admissions remain queryable.

### 9.5 Revocation and Emergency Suspension

Revocation is terminal for that admission record. Use it when evidence is confirmed invalid, contaminated, unsafe, or policy-disqualifying.

Suspension is a reversible hold. Use it when an incident, drift, or investigation requires immediate denial before final disposition. External consumers should treat both `revoked` and `suspended` as `G0`.

Emergency suspension may be issued without waiting for benchmark recomputation when:

- a critical verifier, benchmark, or evidence-bundle flaw is discovered;
- post-release future or answer leakage is confirmed for a task that supported the admitted scope;
- an oracle is invalidated or downgraded below certified eligibility for a task that materially affected the admitted scope;
- the live operating snapshot is outside active admission for a write-capable tier;
- a protected-resource attempt exceeds the admitted operation surface;
- repository policy declares an emergency cutoff.

### 9.6 Suspension Lift and Reinstatement

Lifting a suspension writes an append-only `lift_suspension` transition on the same `repository_agent_admission`; it does not create a new admission. The projected admission status returns from `suspended` to `effective`.

The lift path is allowed only when all checks pass:

- the admission is currently `suspended`;
- `repository_id`, scope, admitted `tested_agent_snapshot_id`, `target_condition_basis_identity`, `covered_capability_envelope_id`, evaluated subject, admission subject, subject-applicability basis, `evaluation_mode`, `adapter_purity_level`, ACUT binding/attestation basis, License-consumption basis, policy gate results, and `granted_trust_tier` are unchanged;
- the original `freshness_deadline` is still open and no supporting benchmark release, critical task, evidence bundle, or scorecard basis has been retired or contaminated;
- the suspension cause has a recorded resolution with evidence refs or reviewer rationale;
- no revocation condition remains;
- the current operating-state coverage entry for the same target condition is still covered except for the suspension state itself;
- required governance review is complete for `G4`, `G5`, any high-impact or critical-path suspension cause, and any `G3` admission whose original grant required governance review.

The transition record must include previous status, next status, suspension cause, resolution summary, evidence refs, reviewer or policy identity, reviewed timestamp, and effective timestamp. The transition must not widen scope, raise tier, change target condition, change evidence lineage, change gate basis, or extend freshness. If any identity, tier, scope, target-condition, capability-envelope, evidence-basis, subject-applicability, binding, or License-consumption field changes, reinstatement must be a new effective admission that supersedes the suspended admission. If evidence is invalid or unsafe, the only valid terminal path is `revoke`; if evidence is stale, the valid path is expiration, renewal, targeted validation, or full rebenchmarking.

## 10. License Consumption Contract

Downstream systems that choose to use a Barcarolle License operationally must consume the repository-agent admission and operating-state coverage projection, not raw scorecards alone. Barcarolle records, signs, distributes, and audits the License consumption contract; it still does not implement the runtime enforcement plane or approve every downstream action. A consumer may enforce locally, but a consumer-readable License must be strong enough for that local enforcement to verify what Barcarolle admitted.

### 10.1 Durable Signed License Certificate

A consumer-facing License is a signed `license_certificate` derived from one `repository_agent_admission` and, for any certificate usable for `allow` over a write-capable or admission-covered operation, exactly one matching `repository_agent_operating_state.coverage_entries[]` entry that explains the currently selected or observed snapshot. The certificate is the durable License artifact that consumers can cache according to repository policy, often on month-scale defaults for high-trust tiers and with no system-level maximum validity cap. It is still a projection of existing Barcarolle records, not a new authorization truth source and not a Barcarolle session, run lease, or runtime checkpoint.

If certificate fields conflict with the admission or operating-state read model, the backend must reject certificate creation or return a signed diagnostic projection with `certificate_state = non_consumable` and machine-readable reason codes. Admission-only or ambiguous diagnostic projections are allowed only as `non_consumable`, for example with `missing_operating_state_coverage`, `multiple_consumer_ready_coverage_entries`, `uncovered_live_snapshot`, or `coverage_entry_not_consumer_ready`; consumers must not use them for `allow`.

Minimum certificate envelope:

- `license_certificate_id`, `contract_version`, `certificate_schema_version`, certificate digest, and canonicalization algorithm.
- `issuer`, certificate signing-key id, issuer key-set version, issuer-key status reference/digest, issuer-key status, issuer-key validity window, signing algorithm, signature, signed timestamp, and key-status checked timestamp.
- Certificate validity: `certificate_valid_not_before`, nullable `certificate_valid_not_after` when the certificate itself has an expiry, optional `renew_after`, and the policy basis that selected the validity profile.
- Status contract: `status_surface_ref`, `status_schema_version`, `status_sequence_at_issuance`, `status_watermark_at_issuance`, `max_status_staleness`, and optional `next_status_poll_after`.
- `repository_agent_admission_id`, `repository_agent_operating_state_id`, `coverage_entry_id`, and `target_condition_basis_identity` for consumable certificates; explicit `non_consumable_reason_codes` when either operating-state or coverage-entry binding is absent.
- `admission_lifecycle_sequence`, `operating_state_version`, and status/event watermark used to produce the certificate.
- Admission status at issuance, status effective timestamp, granted tier, evidence lineage, freshness state, freshness deadline, and supersession refs when present.
- Repository identity, repository alias basis when mirrors or forks are accepted, scope descriptor, outside-scope exclusions, supported operation/risk classes, and admitted subject.
- Admitted `tested_agent_snapshot_id`, evaluated subject label, requested admission subject, subject-applicability basis, ACUT field evidence-basis summary, ACUT binding/attestation basis, and License-consumption basis.
- `covered_capability_envelope_id`, covered capability envelope digest, capability inclusions/exclusions, and target-condition basis digest.
- Authorization policy version, calibrated policy-profile ref/digest, risk-profile basis/gate result, policy gate results, and supporting decision/change-review refs.
- Evidence refs or digests sufficient for audit lookup without embedding large evidence payloads.

The certificate signature verifies integrity and issuer authenticity for the durable License artifact. Consumers verify that the certificate signing key belonged to the issuer key set, was `active` at `signed_at`, and was not revoked with an effective time that invalidates the certificate at the consumer decision time. Key-status fields copied into the certificate support offline validation and audit replay, but current issuer-key status must be checked through the signed status/key-status surface before a consumer claims a current Barcarolle-conformant `allow`.

### 10.2 Signed License Status Surface

Certificate validity is not the lifecycle authority by itself. Barcarolle must publish a separate signed License status surface consisting of current signed status records plus an append-only status log. A status record answers whether a certificate/admission/coverage-entry tuple is currently effective, suspended, revoked, expired, superseded, or invalid because of issuer-key status. A status log entry records the transition and sequence that led to that state.

Minimum signed status fields:

- `license_status_id`, `license_certificate_id`, certificate digest, `repository_agent_admission_id`, `repository_agent_operating_state_id`, `coverage_entry_id`, and `target_condition_basis_identity`.
- `status_sequence`, `status_watermark`, previous status digest/log pointer when available, status log root or segment digest, and event-stream watermark.
- `license_lifecycle_state` (`effective`, `suspended`, `revoked`, `expired`, `superseded`, `non_consumable`, or `issuer_key_invalid`), transition kind, cause codes, reviewed or policy identity, `status_effective_at`, `published_at`, and optional `consumer_deny_after`.
- Current admission status, `admission_lifecycle_sequence`, operating-state version, freshness state/deadline, granted tier, and superseding admission/certificate refs when present.
- Certificate validity summary, including `certificate_valid_not_before`, nullable `certificate_valid_not_after`, the selected validity profile, and whether the certificate is still inside any explicit certificate-expiry window.
- Certificate signing-key status ref/digest/status and status-signing-key status ref/digest/status, each with key-set version, validity window, status sequence, and revocation or emergency-retirement timestamp when present.
- `max_status_staleness`, `status_fresh_until`, and optional `next_status_poll_after`.
- Signature, signing algorithm, canonicalization algorithm, status signer identity, and `signed_at`.

Minimum signed issuer-key-status fields:

- `issuer_key_status_ref`, `issuer`, `issuer_key_id`, issuer key-set version, key purpose (`certificate_signing`, `status_signing`, or both), and the public-key material or key digest being governed.
- `issuer_key_status` (`active`, `retiring`, `retired`, or `revoked`), status sequence, key-status watermark, optional previous key-status digest/log pointer, event-stream watermark, `published_at`, and `status_effective_at`.
- Key validity window, optional `retired_at`, optional `emergency_retired_at`, optional `revoked_at`, and cause codes for non-active states.
- Key-status signer identity, signer key id, signer key-set/trust-anchor version, signing algorithm, canonicalization algorithm, key-status digest, signature, and `signed_at`.

Consumers verify issuer-key status as a signed record, not as unsigned metadata copied beside another object. The key-status record is the coherent pull surface for certificate-signing-key and status-signing-key rotation, retirement, emergency retirement, and revocation. Key-status fields copied into certificates or status records are audit hints and offline replay inputs; current conformant `allow` requires the referenced signed key-status record to verify against the issuer trust anchor or accepted key-status signing authority at the consumer decision time.

The status signer may use the same issuer identity as the certificate signer or a separate status-signing key family, but both key families must be represented in `license_issuer_key_status`. Normal key rotation does not automatically revoke previously issued certificates; it changes which keys may sign new certificates or status records. Key revocation or emergency retirement publishes signed key-status records and matching License status transitions whose effective timestamp determines when affected certificates stop supporting conformant `allow`.

### 10.3 Certificate Validity and Status Freshness

Admission freshness, certificate validity, and status freshness are separate gates:

- `freshness_deadline` is the evidence validity boundary for the admission tier.
- `certificate_valid_not_after` is an optional durable certificate expiry. The seed policy allows it to be absent/unbounded, and when present it must not be treated as a runtime lease.
- `status_fresh_until` or `max_status_staleness` is the maximum age of signed status evidence a consumer may use while claiming a current Barcarolle-conformant `allow`.

The certificate validity profile is a cache and artifact-rotation preference, not the lifecycle authority. The seed policy imposes no system-level maximum certificate validity for any tier; repository risk profiles may set defaults, shorten validity, require explicit expiry, or allow an unbounded certificate artifact. Whether an unexpired or unbounded certificate currently supports Barcarolle-conformant `allow` is still determined by signed status, admission freshness, issuer-key status, exact matching, and local policy.

When `certificate_valid_not_after` is present, the explicit certificate validity window must end no later than the earliest configured certificate-expiry constraint:

- admission effective-window end, if any;
- risk-profile or repository policy certificate-validity override;
- certificate signing-key validity boundary or known key revocation/emergency-retirement effective timestamp;
- certificate-profile explicit expiry.

Seed default certificate-validity profiles for consumable write-capable certificates:

| Granted tier | Default certificate validity | System-level maximum certificate validity |
| --- | ---: | --- |
| `G1` | 360 days | Unbounded |
| `G2` | 240 days | Unbounded |
| `G3` | 120 days | Unbounded |
| `G4` | 60 days | Unbounded |
| `G5` | 30 days | Unbounded |

Seed maximum status-staleness bounds for current Barcarolle-conformant `allow`:

| Granted tier | Maximum status staleness |
| --- | --- |
| `G1` | 7 days |
| `G2` | 24 hours |
| `G3` | 8 hours |
| `G4` | 2 hours |
| `G5` | 1 hour |

Repository risk profiles and local consumers may shorten status-staleness bounds. Repository risk profiles may also choose longer, shorter, or unbounded certificate-validity profiles because certificate validity is not the current-state authority. A local consumer may keep running its own workflow after status becomes stale, but it cannot report that decision as a current Barcarolle-conformant `allow`.

### 10.4 Pull, Push, and Read-Failure Behavior

Barcarolle should expose both pull and push surfaces:

- Pull: query the current `license_certificate` for a repository/scope/target condition, query the current signed License status for a certificate or admission/coverage-entry tuple, retrieve the status log from a watermark, and retrieve signed issuer-key-status records.
- Push: emit certificate-issued/superseded, license-status-changed, admission-transition, operating-state-updated, emergency-invalidation, and issuer-key-status/key-set-rotation events so consumers can refresh caches quickly.

Push is a freshness accelerator, not the sole authority. A conforming consumer must be able to recover the authoritative state by pulling the signed certificate, signed status record/log, and issuer-key status. If the consumer receives a transition event that suspends, revokes, expires, or supersedes a matching admission or certificate, it must refresh status promptly and stop claiming current Barcarolle-conformant `allow` unless the pulled or pushed signed status still proves an effective state.

Stale cache and read-failure rules:

- If no valid signed certificate is available, write-capable consumption must fail closed for Barcarolle-conformant `allow`.
- If no fresh signed status is available within the status-staleness bound, the consumer cannot claim current Barcarolle-conformant `allow`, even if the certificate validity window remains open.
- If Barcarolle cannot be reached but the consumer holds a valid certificate and a signed status record that is still within `max_status_staleness`, the consumer may claim Barcarolle-conformant `allow` only until status freshness expires and only within the certificate's exact scope and capability envelope.
- Certificate expiry, status expiry, read failure past the staleness bound, signature failure, unsupported contract version, unknown issuer key, revoked issuer key, stale lifecycle sequence, stale status watermark, or unverifiable digest means `deny` or `not_barcarolle_conformant` for the Barcarolle decision surface.
- Consumers may choose stricter local behavior, such as requiring online status for `G5` or high-impact paths. That is local policy and does not change Barcarolle tier semantics.

### 10.5 Matching Rules and Consumer Conformance

Target-condition and capability-envelope matching must be deterministic and consumer-readable. A single certificate plus one current status record must satisfy all requested dimensions; consumers must not combine scope from one coverage entry with capability, target-condition, or status facts from another entry.

An operation is inside the Barcarolle License only when all of these checks pass:

1. Repository identity matches exactly, or the certificate explicitly names an accepted mirror/fork alias basis.
2. The live or selected `tested_agent_snapshot_id` matches the admitted snapshot, or a linked change review/admission explicitly admits the later snapshot.
3. Certificate validity is current, status freshness is current, admission status is `effective`, and the signed status record reports `license_lifecycle_state = effective`.
4. Certificate signature, status signature, certificate signing-key status, status-signing-key status, issuer key-set versions, key validity windows, and status watermark are verifiable.
5. The certificate is bound to one `repository_agent_operating_state_id` and one `coverage_entry_id`, and that entry is the source for the requested target-condition coverage. Consumers must treat admission-only or unbound diagnostic projections as `deny` for Barcarolle `allow`.
6. Requested path/module/task-family/resource scope is a subset of the admission scope and not in outside-scope exclusions.
7. Requested operation and risk class are included in the admitted operation surface for the granted tier.
8. Requested admission subject matches the certificate. For example, `harness_bound` admission cannot be consumed as `native_yolo`, and `native_yolo` cannot borrow a harness-bound coverage entry.
9. `target_condition_basis_identity` matches exactly, or the certificate explicitly marks the consumer's condition as equivalent or narrower with the compatibility basis and reviewer/policy identity.
10. Requested capability envelope is a subset of `covered_capability_envelope`, including filesystem scope, branch/PR ownership, shell/tool access, network access, credential or secret exposure, dependency/workflow changes, merge/release authority, and any human-approval assumptions recorded for external policy.
11. ACUT field evidence basis, binding/attestation basis, and production-fidelity basis meet or exceed the certificate requirements for the requested operation.
12. Local policy overlays, if any, do not deny or hold the operation.

Suggested consumer result meanings:

- `allow`: every Barcarolle certificate and status check passes, the status watermark is fresh enough, and local policy permits action.
- `deny`: no certificate, invalid certificate, stale or invalid status, no active admission, expired/stale/suspended/revoked admission, unsupported tier, uncovered scope, capability mismatch, target-condition mismatch, or hard exclusion.
- `not_barcarolle_conformant`: the consumer may have made a local decision, but its certificate/status basis is stale, unconfirmed, or incomplete and cannot be claimed as current Barcarolle `allow`.
- `hold_for_review`: Barcarolle certificate/status checks pass, but external local policy requires human approval before action. This is a consumer-side policy choice and is not intrinsic to `G5`.
- `require_targeted_validation`: requested operation is plausibly coverable but current admission or operating-state entry is partial.
- `require_full_rebenchmark`: requested target condition or capability envelope differs materially from admitted evidence.

### 10.6 Suspend, Revoke, Expire, and Supersede Semantics

Suspension, revocation, expiration, and supersession are admission lifecycle facts that the signed status surface must project as authorization-denying for matching operations. They map to `G0` for Barcarolle License-consumption semantics without implying that Barcarolle killed, paused, checkpointed, or otherwise controlled a live agent.

- `suspend`: reversible emergency hold. Status changes to `suspended` with `consumer_deny_after` no later than the transition `effective_at`. A suspension lift requires a later signed status record after the `lift_suspension` lifecycle sequence and must not extend certificate validity or admission freshness.
- `revoke`: terminal invalidation. Status changes to `revoked`; consumers must treat the certificate/admission as `G0` from the transition `effective_at` for Barcarolle-conformant decisions. Revoked admissions cannot be reinstated.
- `expire`: automatic or explicit end of freshness/effective window. Consumers must deny at `freshness_deadline`, certificate expiry, or effective-window end even without receiving a transition event because those timestamps are inside the certificate and status.
- `supersede`: replacement by a newer effective admission for the same `repository_id + scope + target_condition_basis_identity`. Status changes to `superseded` and names the superseding admission/certificate when available.
- `signing_key_rotate`: normal key replacement. Existing certificates remain valid until the earliest present certificate expiry, signed status invalidation, and any old-key validity boundary that the status/key-status surface marks as certificate-invalidating; normal rotation alone does not force renewal of unbounded certificates unless the key status marks the old key as revoked or emergency retired.
- `signing_key_revoke`: issuer-key invalidation. Barcarolle publishes signed key status plus License status records invalidating affected certificates from the revocation effective timestamp and emits emergency-invalidation events.

Emergency revocation must publish signed invalidation/status promptly and should require conforming consumers to send a status receipt or audit event for the invalidating watermark. Barcarolle can then prove which consumers acknowledged or used a watermark and which consumers are stale or unconfirmed. Barcarolle still cannot force a non-conforming consumer to stop; it can only publish signed status, record receipts/audits, and report non-conformance.

### 10.7 Consumer Receipts and Audit Logging

A consumer that claims Barcarolle License conformance must:

- validate certificate signature, status signature, digests, canonicalization, issuer key status, contract versions, certificate validity, status freshness, lifecycle sequence, and status watermark;
- use admissions and exactly one matching operating-state coverage entry rather than raw scorecards as the consumption source for `allow`;
- apply the matching rules above before reporting any Barcarolle `allow` for a write-capable or admission-covered operation class;
- honor suspend/revoke/expire/supersede status and fail closed for Barcarolle-conformant decisions on stale or unverifiable certificate/status data;
- keep local policy decisions separate from Barcarolle tier semantics;
- write append-only receipt or consumption audit records for every status watermark it acknowledges for write-capable use, every non-read `allow`, and every deny/hold caused by Barcarolle certificate or status state.

Minimum status receipt fields:

- `license_status_receipt_id`, consumer identity/version, integration/environment id, received timestamp, acknowledged timestamp, and receipt source (`pull`, `push`, or `replay`).
- `license_certificate_id`, certificate digest, `license_status_id`, status digest, status sequence, status watermark, event-stream watermark, and issuer-key status refs/digests used to verify the status.
- Receipt result (`acknowledged`, `ignored`, `verification_failed`, or `stale`) and reason codes.

Minimum consumer audit fields:

- `license_consumption_audit_event_id`, consumer identity/version, consumer decision timestamp, and operation correlation id.
- Requested repository, scope, operation, risk class, target-condition basis identity, tested-agent snapshot identity, capability envelope digest, and admission subject.
- Result (`allow`, `deny`, `not_barcarolle_conformant`, `hold_for_review`, `require_targeted_validation`, or `require_full_rebenchmark`) and machine-readable reason codes.
- `license_certificate_id`, certificate digest, certificate signing-key id/status basis, status id/digest, status-signing-key status basis, signature verification results, `repository_agent_admission_id`, `repository_agent_operating_state_id`, coverage entry id, lifecycle sequence, operating-state version, status sequence, and status watermark used.
- Granted tier, admission status, freshness state/deadline, certificate validity timestamps, status freshness timestamps, evidence lineage, risk-profile basis, policy gate basis, and local policy overlay result.
- Failure mode for stale cache, read failure, certificate signature failure, status signature failure, lifecycle mismatch, status-watermark mismatch, target-condition mismatch, capability mismatch, or scope mismatch when applicable.

Consumers may store these logs locally, stream them to Barcarolle through receipt and audit-ingest APIs, or both. Barcarolle records received events for explainability, conformance reporting, stale-consumer detection, and emergency-revocation audit; it does not convert those events into runtime enforcement authority.

### 10.8 Terminology Migration

The old `license_consumption_package` and "package lease" terminology is deprecated for this contract. New design documents and APIs should use:

- `license_certificate` for the durable signed License artifact.
- `license_status_record` and `license_status_log_entry` for signed lifecycle, revocation, supersession, expiration, and issuer-key-status publication.
- `certificate_valid_not_before` / nullable `certificate_valid_not_after` for durable artifact validity.
- `status_fresh_until`, `max_status_staleness`, `status_sequence`, and `status_watermark` for current-consumption freshness.
- `license_status_receipt` and `license_consumption_audit_event` for consumer acknowledgement, use, and stale/unconfirmed-consumer audit.

Legacy "package" may appear only as a backward-compatibility alias or migration note. It must not imply a short runtime ticket, a session/run lease, or a per-action Barcarolle checkpoint.

## 11. Operating-State Drift Interpretation

`repository_agent_operating_state.coverage_entries[]` is the authoritative per-target-condition explanation for the live or selected snapshot. Each entry must carry a stable coverage entry identity and be consumer-ready without requiring an extra admission lookup for core authorization fields. When linked to an admission, the projection copies `granted_trust_tier`, `admission_status`, `freshness_state`, `freshness_deadline`, `evidence_lineage`, evaluated subject, admission subject, subject-applicability basis, ACUT binding/attestation basis, License-consumption basis, certificate profile, status-freshness profile, lifecycle sequence, and certificate/status/audit refs from that admission and its freshness calculation. When no admission covers the entry, the projection sets `granted_trust_tier = G0`, `admission_status = none`, `freshness_state = not_applicable`, leaves `freshness_deadline` absent, and marks consumable certificate generation as unavailable.

Recommended drift states:

| Drift state | Meaning | Required action |
| --- | --- | --- |
| `none` | Live snapshot, mode, adapter, target condition, and capability envelope match an active fresh admission. | Allow according to tier. |
| `covered_carry_forward` | Live snapshot is covered by `reused` or `supplemented` admission. | Allow only within narrowed scope and shorter deadline. |
| `snapshot_drift` | Live snapshot differs from admitted snapshot without accepted change review. | Deny write tiers; require change review or rebenchmark. |
| `condition_drift` | Mode, adapter purity, adapter manifest, run environment, or capability envelope differs. | Require targeted validation or full rebenchmark depending on materiality. |
| `scope_drift` | Requested path, module, task family, or risk class is outside admission scope. | Deny or narrow request. |
| `freshness_drift` | Admission or supporting scorecard is stale for the requested tier. | Require renewal or rebenchmark. |
| `evidence_drift` | Live ACUT field evidence basis is weaker than the admitted basis. | Downgrade, suspend, or require stronger observation. |
| `emergency_suspended` | Active emergency hold exists. | Deny until lifted, superseded, or revoked. |

Operating-state projection may summarize one selected admission at top level, but consumers and operator explanations must inspect all relevant `coverage_entries[]`.

## 12. Minimal Policy Input Shape

The implementation may use OPA, a service-local rule engine, or workflow-owned policy code. The minimum logical input shape is:

```json
{
  "authorization_policy_version": "authorization_semantics_v1@seed",
  "calibrated_policy_profile_id": "cpp_seed",
  "calibrated_policy_profile_digest": "cpp_sha256",
  "calibrated_policy_profile": {
    "high_tier_authorization_applicability_summary": {},
    "unsafe_false_positive_budget_result": {},
    "parameter_authority_summary": {}
  },
  "request": {
    "repository_id": "repo_123",
    "scope": {"paths": ["src/payments/**"], "task_families": ["bugfix"]},
    "requested_tier": "G3",
    "admission_subject": "native_yolo",
    "operation": "create_or_update_pr_branch",
    "risk_class": "normal_code_change",
    "target_condition_basis_identity": "tcb_123",
    "capability_envelope_id": "cap_123",
    "consumer_certificate_profile": {
      "certificate_schema_version": "license_certificate_v1",
      "requested_default_certificate_validity_seconds": 10368000,
      "requested_max_certificate_validity": "unbounded",
      "requested_max_status_staleness_seconds": 28800,
      "requires_lifecycle_sequence": true,
      "requires_status_watermark": true
    },
    "now": "2026-04-24T06:00:00Z"
  },
  "effective_risk_profile": {
    "resolution_state": "resolved",
    "repository_risk_profile_id": "rrp_123",
    "seed_risk_profile_basis": null,
    "risk_profile_version": "2026-04-01",
    "risk_profile_digest": "rpf_sha256",
    "resolved_effective_profile_digest": "erpf_sha256",
    "source_basis": "repository_profile",
    "inheritance_basis": {
      "organization_profile_id": "orp_default",
      "repository_profile_id": "rrp_123",
      "component_or_path_override_ids": [],
      "selected_source": "repository_profile",
      "inheritance_basis_digest": "rpi_sha256"
    },
    "conflict_handling": {
      "conflict_state": "none",
      "conflicting_profile_ids": [],
      "blocked_without_profile": false,
      "block_reason_codes": []
    },
    "constraint_summary": {
      "max_tier_by_scope": {"src/payments/**": "G3"},
      "minimum_release_coverage": 0.80,
      "minimum_task_family_coverage": 0.65,
      "minimum_reliability_label": "medium",
      "required_evidence_basis": ["trusted_barcarolle_evidence", "owner_attestation"],
      "required_review_conditions": ["first_G3_for_repository_scope"],
      "forbidden_scope_reason_codes": [],
      "freshness_days_by_tier": {"G3": 90},
      "risk_budget": {"write_capable_admissions_per_quarter": 4}
    }
  },
  "subject": {
    "tested_agent_snapshot_id": "tas_123",
    "subject_label": "native_agent",
    "evaluation_mode": "observed_run",
    "adapter_purity_level": "A1_environment_wrapper",
    "production_fidelity": "equivalent_native_yolo",
    "subject_applicability": "exact_or_equivalent",
    "acut_field_evidence_basis_summary": {}
  },
  "scorecard": {
    "benchmark_scorecard_id": "bsc_123",
    "benchmark_release_id": "br_123",
    "scoring_semantics_version": "scoring_semantics_v1",
    "scorecard_policy_version": "scoring_semantics_v1",
    "coverage_policy_version": "coverage_policy_v1",
    "reliability_policy_version": "reliability_policy_v1",
    "calibrated_policy_profile_id": "cpp_seed",
    "aggregation_algorithm": "weighted_release_denominator_mean_v1",
    "aggregate_score": 84,
    "completed_score": 91,
    "coverage_summary": {},
    "denominator_summary": {},
    "missing_run_summary": {},
    "minimum_sample_summary": {},
    "reliability_label": "medium",
    "task_family_coverage": {},
    "release_coverage_profile_ref": {"benchmark_release_id": "br_123", "digest": "rcp_sha256"},
    "release_admission_policy_version": "release_admission_v1",
    "release_certification_verdict": "certified",
    "supported_authorization_scope_summary": {},
    "unsupported_authorization_scope_summary": {},
    "canonical_verification_coverage": {},
    "evidence_trust_basis": {},
    "score_input_set_digest": "sis_sha256",
    "score_basis_judge_lineage": "none",
    "authorization_readiness": "ready",
    "created_at": "2026-04-01T00:00:00Z"
  },
  "release": {
    "benchmark_release_id": "br_123",
    "release_admission_policy_version": "release_admission_v1",
    "release_certification_verdict": "certified",
    "release_coverage_profile_digest": "rcp_sha256",
    "supported_authorization_scopes": [
      {
        "scope_id": "scope_payments_bugfix_g3",
        "repository_scope": {"paths": ["src/payments/**"]},
        "task_families": ["bugfix"],
        "risk_classes": ["normal_code_change"],
        "permission_classes": ["code_write"],
        "high_impact_path_classes": [],
        "capability_envelope_ids": ["cap_123"]
      }
    ],
    "unsupported_authorization_scopes": [
      {
        "scope_id": "scope_payments_release_g4",
        "reason_codes": ["missing_high_impact_path_coverage"],
        "missing_dimensions": ["high_impact_path_class"]
      }
    ],
    "requested_scope_coverage": {
      "covered": true,
      "matched_supported_scope_ids": ["scope_payments_bugfix_g3"],
      "coverage_profile_digest": "rcp_sha256",
      "covered_dimensions": ["repository_scope", "task_family", "risk_class", "permission_class", "capability_envelope"],
      "missing_dimensions": [],
      "unsupported_reason_codes": []
    },
    "leakage_clearance": {
      "confirmed_leakage_count": 0,
      "suspected_leakage_count": 0,
      "highest_leakage_severity": "none"
    },
    "open_invalidation_findings": []
  },
  "gate_results": {
    "correctness_evidence": "pass",
    "certified_release_coverage": "pass",
    "subject_applicability": "pass",
    "acut_binding_attestation": "pass",
    "license_consumption_compatibility": "pass",
    "risk_profile_constraints": "pass"
  },
  "risk_profile_gate_result": {
    "result": "pass",
    "risk_profile_digest": "rpf_sha256",
    "resolved_effective_profile_digest": "erpf_sha256",
    "blocked_without_profile": false,
    "required_review": false,
    "constraint_decisions": [
      {
        "constraint": "max_tier_by_scope",
        "requested": "G3",
        "allowed": "G3",
        "result": "pass"
      }
    ]
  },
  "admission": {
    "repository_agent_admission_id": "raa_123",
    "tier": "G3",
    "status": "effective",
    "evidence_lineage": "fresh",
    "freshness_deadline": "2026-06-30T00:00:00Z",
    "covered_capability_envelope_id": "cap_123"
  },
  "operating_state": {
    "coverage_entries": []
  },
  "review": {
    "governance_review_state": "approved",
    "consumer_action_approval": "external_policy"
  }
}
```

`effective_risk_profile` is part of the logical policy input even when a service loads it from a read model. If the repository uses a seed profile, `repository_risk_profile_id` is null and `seed_risk_profile_basis` must name the exact seed family, version, and digest. If no effective profile can be resolved, or inheritance/override precedence conflicts, `resolution_state` is `blocked_without_profile` or `conflict` and write-capable authorization is blocked until a profile transition resolves it.

The minimum logical output shape is:

```json
{
  "outcome": "grant",
  "authorization_readiness": "ready",
  "granted_tier": "G3",
  "downgrade_or_denial_reasons": [],
  "narrowed_scope": null,
  "gate_results": {
    "correctness_evidence": "pass",
    "certified_release_coverage": "pass",
    "subject_applicability": "pass",
    "acut_binding_attestation": "pass",
    "license_consumption_compatibility": "pass",
    "risk_profile_constraints": "pass"
  },
  "calibrated_profile_applicability_result": {
    "result": "pass",
    "high_tier_slice_supported": true,
    "blocked_reason_codes": [],
    "parameter_authority_warnings": []
  },
  "risk_profile_basis": {
    "repository_risk_profile_id": "rrp_123",
    "seed_risk_profile_basis": null,
    "risk_profile_version": "2026-04-01",
    "risk_profile_digest": "rpf_sha256",
    "resolved_effective_profile_digest": "erpf_sha256",
    "inheritance_basis_digest": "rpi_sha256"
  },
  "risk_profile_gate_result": {
    "result": "pass",
    "blocked_without_profile": false,
    "constraint_decisions": [
      {
        "constraint": "max_tier_by_scope",
        "requested": "G3",
        "allowed": "G3",
        "result": "pass"
      }
    ],
    "required_review": false,
    "required_next_action": "none"
  },
  "gate_failure_reasons": [],
  "release_admission_policy_version": "release_admission_v1",
  "release_certification_verdict": "certified",
  "release_coverage_profile_digest": "rcp_sha256",
  "release_scope_coverage_result": {
    "covered": true,
    "unsupported_reason_codes": [],
    "missing_dimensions": []
  },
  "unsupported_scope_reason_codes": [],
  "invalidation_refs_considered": [],
  "required_next_action": "none",
  "admission_or_coverage_entry_ids_used": ["raa_123"],
  "freshness_deadline": "2026-06-30T00:00:00Z",
  "consumer_certificate_profile_basis": {
    "certificate_schema_version": "license_certificate_v1",
    "default_certificate_validity_seconds": 10368000,
    "max_certificate_validity": "unbounded",
    "max_status_staleness_seconds": 28800,
    "requires_lifecycle_sequence": true,
    "requires_status_watermark": true
  },
  "evidence_lineage": "fresh"
}
```

Risk-profile gate results must also represent appetite-driven non-grant behavior without treating the profile as benchmark truth, calibration labels, or runtime enforcement. Representative output fragments:

```json
[
  {
    "case": "forbidden_scope_denial",
    "outcome": "deny",
    "authorization_readiness": "ready",
    "granted_tier": "G0",
    "gate_results": {"risk_profile_constraints": "deny"},
    "risk_profile_gate_result": {
      "result": "deny",
      "reason_codes": ["forbidden_scope_by_profile"],
      "required_next_action": "none"
    }
  },
  {
    "case": "profile_max_tier_downgrade",
    "outcome": "downgrade",
    "authorization_readiness": "ready",
    "granted_tier": "G2",
    "gate_results": {"risk_profile_constraints": "downgrade"},
    "risk_profile_gate_result": {
      "result": "downgrade",
      "requested_tier": "G3",
      "allowed_tier": "G2",
      "reason_codes": ["max_tier_for_scope_exceeded"],
      "required_next_action": "none"
    }
  },
  {
    "case": "targeted_profile_review_required",
    "outcome": "needs_human_review",
    "authorization_readiness": "ready",
    "granted_tier": null,
    "gate_results": {"risk_profile_constraints": "review_required"},
    "risk_profile_gate_result": {
      "result": "review_required",
      "review_target": "repository_security_owner",
      "reason_codes": ["first_G3_for_repository_scope"],
      "required_next_action": "record_governance_review"
    }
  },
  {
    "case": "blocked_without_effective_profile",
    "outcome": "deny",
    "authorization_readiness": "blocked",
    "granted_tier": "G0",
    "gate_results": {"risk_profile_constraints": "blocked_without_profile"},
    "risk_profile_gate_result": {
      "result": "blocked_without_profile",
      "blocked_without_profile": true,
      "reason_codes": ["missing_effective_repository_risk_profile"],
      "required_next_action": "register_or_resolve_repository_risk_profile"
    }
  }
]
```

The release block is mandatory for any decision that can grant, renew, lift suspension, or carry forward write-capable authorization. A policy implementation may load it internally from `benchmark_release_id`, but the logical policy input must include these facts before evaluation; `scorecard.task_family_coverage` and `coverage_summary` are not substitutes for certified release support.

## 13. Scenarios

### 13.1 Native `patch_only` High Score With Weak Binding and Consumption Evidence

Input:

- `aggregate_score = 93`;
- benchmark coverage = 92%;
- task-family coverage = 86%;
- `evaluation_mode = patch_only`;
- `adapter_purity_level = A0_transport_only`;
- runtime, network, workspace, and tool posture are mostly unreviewed `declared` values;
- the License-consumption contract metadata can support patch proposals but cannot bind branch writes to the tested-agent snapshot or express path/task-family compatibility;
- canonical verification passed for all scored runs.

Decision:

- Score and coverage would meet `G4`, and native YOLO production fidelity is high.
- ACUT binding and License-consumption compatibility fail for writing tiers.
- A request for `G3` or `G4` returns `downgrade` to `G2`.
- Admission may allow `patch_proposal` only. It must not license branch writes or PR creation until binding and consumption-contract gaps are closed.
- To request `G3` or above, the repository can add owner/third-party attestations, provider or CI evidence, adapter observations, or external consumer policy that can bind the native YOLO capability envelope. It does not need to abandon native YOLO mode solely because the run was `patch_only`.

### 13.2 Native YOLO `patch_only` High Score With High-Tier License

Input:

- `aggregate_score = 97`;
- benchmark coverage = 97%;
- every requested task family has at least 92% coverage and no uncovered critical family;
- high-impact workflow, dependency, build, and test path classes are covered;
- `evaluation_mode = patch_only`;
- `adapter_purity_level = A0_transport_only`;
- `admission_subject = native_yolo`;
- model, prompt, tool, permission, runtime, memory, and control-loop digests are immutable and reviewable;
- runtime, workspace, network, tool, and permission posture are backed by repository-owner attestation plus provider/CI evidence;
- the requested autonomy envelope includes full-access shell/file/network/tool operation, broad repository edits, workflow/dependency/build/test changes, and branch/PR automation inside the declared repository scope;
- canonical verification coverage is 99%;
- the License-consumption contract metadata names the same target condition, autonomy envelope, freshness window, suspension/revocation behavior, and any external policy exclusions.

Decision:

- Correctness evidence, production fidelity, ACUT binding/attestation, and License-consumption compatibility all pass for native YOLO.
- A `G5 autonomous_yolo_repository_operation` License can be granted after issuance review, bounded to the evaluated native YOLO target condition and autonomy/capability envelope.
- The `G5` License does not authorize actions outside that envelope. Per-action human approval is only required if an external consumer imposes it as local policy.

### 13.3 `observed_run` With Good Coverage and Adapter-Observed Runtime Fields

Input:

- `aggregate_score = 84`;
- benchmark coverage = 82%;
- every requested task family has at least 65% coverage;
- `evaluation_mode = observed_run`;
- `adapter_purity_level = A1_environment_wrapper`;
- workspace, network, runtime budget, and process boundary are `adapter_observed`;
- correctness comes from trusted canonical verification.

Decision:

- The score and coverage meet `G3`.
- Subject applicability and ACUT binding pass for the observed wrapper target condition, but score and coverage do not meet `G4`.
- First `G3` admission requires governance review for License issuance. After approval, the admission is `G3 scoped_branch_write` for the observed wrapper target condition.
- External consumers must require the same target-condition basis. The result authorizes unobserved native YOLO only if the wrapper is reviewed as non-material or the native YOLO target condition is separately admitted.

### 13.4 Harness-Native High Score Requesting Native YOLO Admission

Input:

- `aggregate_score = 96`;
- benchmark coverage = 97%;
- `evaluation_mode = harness_native`;
- `adapter_purity_level = A3_harness_native_controller`;
- subject label is `Agent + Harness`;
- operator requests `G4` admission for common native YOLO operation without the harness.

Decision:

- Correctness evidence may support a high-tier harness-bound admission.
- Subject applicability fails for unmodified native YOLO because the evaluated subject is `Agent + Harness`.
- Native YOLO `G4` returns `full_rebenchmark_required` or `targeted_validation_required`, depending on whether policy can close the gap with bounded native-subject validation.
- The repository may hold a separate `G4` or `G5` harness-bound admission if the License requires use of the harness target condition.

### 13.5 Later Agent Snapshot Change Requesting Carry-Forward

Baseline:

- Active `G3` admission from a fresh native YOLO scorecard;
- freshness deadline is still open;
- admitted scope is `src/payments/**` bug-fix PR branches.

Change:

- candidate tested-agent snapshot changes prompt wording and memory-retention digest;
- model, tools, permissions, adapter, runtime budget, evaluation mode, and capability envelope are unchanged;
- operator requests the same `G3` scope.

Decision:

- This is not a fresh benchmark fact. Record an `agent_change_review`.
- If review classifies the prompt/memory change as non-material for the admitted target condition, outcome is `carry_forward_acceptable` with `evidence_lineage = reused`.
- Write a new `repository_agent_admission` for the candidate snapshot, same or narrower scope, with deadline no later than the source deadline or review time plus 45 days.
- If the request also widens scope, changes tools/permissions/network/runtime, or asks for `G4`, return `targeted_validation_required` or `full_rebenchmark_required` depending on the gap.

## 14. Required Model and Contract Adjustments

Existing model and interface documents already contain most fields. Implementation should make these adjustments where not already present:

- `authorization_decision` records requested and granted trust tiers using `G0` through `G5`.
- `authorization_decision` records the exact calibrated policy-profile ref or profile digest used for threshold, coverage, reliability, and promotion-gate parameters.
- `authorization_decision` records the effective risk-profile ref, version, digest, inheritance basis, and risk-profile gate result used for appetite constraints.
- `authorization_decision` records both requested tier and granted tier when outcome is `downgrade`.
- `authorization_decision` records gate results for correctness evidence, production fidelity / subject applicability, ACUT binding / attestation, License-consumption / operating-envelope compatibility, and risk-profile constraints.
- `authorization_decision` records the consumer certificate/status profile basis needed to make a later License certificate verifiable, including signing family, default certificate validity, optional certificate-expiry override or unbounded-validity setting, status-staleness policy, status-watermark expectations, and lifecycle-sequence expectations.
- `authorization_decision`, `agent_change_review`, and `repository_agent_admission` record the requested admission subject, evaluated subject label, subject-applicability result, and production-fidelity basis inside or alongside `target_condition_basis`.
- `repository_agent_admission.status` includes `suspended` in addition to `proposed`, `effective`, `superseded`, `revoked`, and `expired`.
- `repository_agent_admission` status is projected from append-only lifecycle transitions, including `suspend` and `lift_suspension`.
- `repository_agent_admission` records `freshness_deadline`, `evidence_lineage`, `target_condition_basis_identity`, `covered_capability_envelope_id`, and the granted tier.
- `repository_agent_admission` records the gate basis that made a high-tier native YOLO License meaningful, especially the risk-profile, ACUT binding/attestation, and License-consumption basis.
- `repository_agent_admission` records the consumer certificate/status profile: signing key family, certificate schema, status schema, default certificate validity, optional certificate-expiry override or unbounded-validity setting, status-staleness policy, lifecycle sequence, status-watermark expectations, and latest certificate/status digest/ref when materialized. These are additive projection fields, not separate authorization facts.
- `repository_agent_operating_state.coverage_entries[]` records stable coverage entry identity, drift state, next required action, `granted_trust_tier`, `admission_status`, `freshness_state`, `freshness_deadline`, `evidence_lineage`, risk-profile basis and gate result, evaluated subject, admission subject, subject-applicability basis, ACUT binding/attestation basis, License-consumption basis, lifecycle sequence, certificate profile, status-freshness profile, certificate availability, and latest status watermark for every active or relevant target-condition basis.
- `benchmark_scorecard.task_family_coverage` is the stable policy-gate source for task-family coverage; `coverage_summary` and `metric_breakdown` must not be treated as substitutes.
- `benchmark_scorecard` policy refs, risk-profile refs/digests, and `authorization_decision.authorization_policy_version` must be exact enough to distinguish seed thresholds from calibrated threshold, coverage, reliability, weighting, and appetite-constrained profiles.
- `benchmark_release.release_coverage_profile`, `supported_authorization_scopes[]`, and `unsupported_authorization_scopes[]` cap every authorization decision; scorecards can narrow those scopes but cannot widen them.
- `authorization_decision`, `repository_agent_admission`, and operating-state coverage entries record unsupported-scope reason codes and post-release invalidation refs when those facts drive downgrade, denial, suspension, revocation, targeted validation, or full rebenchmarking.
- External License-consumption inputs should include operation/risk class, target-condition basis identity, admission subject, current tested-agent snapshot identity, requested capability envelope, and the License-consumption basis used by the admission.
- API and event contracts expose signed License certificate query, signed License status lookup/log, signed issuer-key-status lookup and status-change event, lifecycle sequence/status-watermark fields on admission and operating-state events, certificate/status invalidation notification, status receipt ingest, and append-only consumer audit ingest.
- Consumer receipt and audit records capture certificate identity, status identity/watermark, issuer-key status basis, signature verification, matching inputs, decision result, reason codes, lifecycle sequence, certificate validity, status freshness, granted tier, admission status, evidence lineage, risk-profile basis, policy gate basis, and local policy overlay without making Barcarolle responsible for runtime action enforcement.

## 15. Traceability

- `docs/analysis/requirements.md` establishes the repository-specific agent-license goal, graded authorization, and the distinction between benchmark fact, admission, and operating state.
- `docs/architecture/system-design.md`, `docs/architecture/module-design.md`, and `docs/architecture/benchmark-admission-rubric.md` define the separation between generation, validation, executable benchmark admission, release coverage certification, execution, evidence, scorecard, policy, admission, and operating-state surfaces.
- `docs/architecture/policy-calibration.md` defines the automatic empirical calibration loop that governs threshold profiles, score weighting factors, coverage gates, reliability labels, and policy-version promotion without requiring human baselines or human benchmark participation.
- `docs/architecture/interface-contracts.md`, `docs/architecture/api-schema.md`, and `docs/architecture/data-model.md` define the resource names, lifecycle concepts, ACUT field evidence basis, evaluation modes, adapter purity, scorecards, authorization decisions, admissions, and operating state used here.
- `docs/decisions/golden-judge-governance.md` keeps Golden/Judge outputs advisory for authorization.
