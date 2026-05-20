# Automatic Policy Calibration

## 1. Purpose

This document makes policy calibration a first-class Barcarolle subsystem. It closes the gap where authorization thresholds, score-weighting factors, coverage gates, and reliability labels could otherwise remain fixed product assumptions without an empirical validation loop. It also closes the risk-appetite gap: calibration must consume an explicit repository or organization risk profile instead of inferring governance tolerance only from benchmark outcomes.

Policy calibration does not replace task admission, scoring, authorization, repository-agent admission, or operating-state projection. It produces versioned policy-profile facts that those stages consume through their existing policy-version fields:

- `authorization_semantics_v1` threshold profiles for `G0` through `G5` decisions;
- scorecard policy factors such as oracle multipliers, duplicate caps, B-oracle caps, high-impact/risk factors, and repeated-run aggregation settings;
- coverage-policy gates for release weight, task-family coverage, high-impact path coverage, and partial-evaluation handling;
- reliability-label rules for `high`, `medium`, `low`, and `blocked`;
- policy-version promotion, shadowing, pause, rollback, and impact-analysis records.

Calibration is automatic in normal operation. It must not require a human baseline, human labeling step, manual benchmark acceptance step, or human-in-the-loop calibration step. Human review remains an audit and governance surface for inspecting, overriding, or rolling back policy state; it is not a required source of calibration truth.

## 2. Boundaries

Calibration preserves these accepted architecture boundaries:

- first-release breadth is intentional; calibration is part of the first-class policy surface, not an MVP cut;
- Barcarolle records evidence, scorecards, admissions, signed License certificates, signed License status metadata/logs, status receipts, and consumer audit records, but it does not own runtime enforcement of a live License;
- Golden and Judge capability surfaces remain expected benchmark-side capabilities;
- immutable benchmark facts are never edited in place;
- score facts and policy facts remain separate;
- Golden/Judge artifacts may support scoring, review, or risk explanation only through governed scoring and evidence contracts.
- explicit repository or organization risk profiles are policy inputs, not empirical truth labels, benchmark facts, or runtime enforcement controls.

Calibration output can change future policy interpretation, but it cannot rewrite historical scorecards or decisions. If the calibrated change affects score weights, missing-run treatment, reliability labels, coverage gates, or the effective risk-profile basis used by those scorecard policies, a new `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, or scorecard risk-profile basis is required and any production-ready benchmark-authoritative result must be materialized as a new immutable scorecard. If the calibrated change affects only authorization thresholds, tier rules, or authorization-only risk-profile interpretation, a new `authorization_policy_version` may issue a new `authorization_decision` over an existing immutable scorecard without modifying the scorecard. `authorization_decision.authorization_policy_version` is the canonical persisted field; any legacy API field named `policy_version` is only a compatibility alias for that same value during migration.

## 2.1 Explicit Risk-Profile Input

Every calibrated profile must be fitted and promoted against an explicit `repository_risk_profile` or an effective organization-inherited risk profile. The risk profile is the durable answer to "how much authorization risk is this repository or organization willing to tolerate for this scope?" It is not derived from benchmark success rates, and it is not a substitute for objective evidence.

The risk profile supplies hard constraints and objective weights for calibration:

- risk tolerance class, for example `conservative`, `balanced`, `expansive`, or `custom`;
- maximum unsafe-control promotion rates by tier, risk class, permission class, component/path, and high-impact path class;
- minimum control-separation margins for known pre-fix, no-op, mutation, retrieval-only, rule-based, weak-baseline, and prior-agent negative controls;
- score threshold floors or ceilings by `G0` through `G5`, including tiers forbidden for selected repository scopes or protected resource classes;
- minimum release coverage, task-family coverage, high-impact path coverage, canonical-verification coverage, evidence-trust basis, ACUT binding basis, and reliability-label requirements;
- freshness-window ceilings and renewal requirements by tier;
- required governance-review triggers for high-impact paths, broad autonomy, `G4`, `G5`, exception grants, or owner-attested native-agent fields;
- calibration loss weights that express the tradeoff between unsafe false positives, overly restrictive false negatives, operational cost, and targeted-validation burden;
- explicit scope inheritance from organization default to repository profile to narrower component/path override, with the resolved effective profile recorded by digest.

Calibration optimizes policy usefulness subject to those constraints. It must not relax the effective risk profile because the available benchmark evidence looks strong, and it must not infer that a repository has high risk tolerance merely because historical agents did well. When evidence is insufficient to estimate a constrained slice, the result for that slice is `blocked`, `shadow`, `targeted_validation_required`, or excluded from the profile applicability; it is never silently broadened.

Risk-profile lifecycle is append-only. A changed appetite creates a new `repository_risk_profile` version or transition and normally triggers `PolicyCalibrationWorkflow` for affected scopes. Existing scorecards, authorization decisions, repository-agent admissions, and operating-state entries keep the exact risk-profile basis they used. A stricter active profile can trigger impact preview, reauthorization, suspension, revocation, targeted validation, or full rebenchmarking through normal authorization/admission workflows, but it does not mutate historical facts.

This boundary does not reopen external License-consumption or runtime enforcement. A risk profile may state assumptions external consumers must verify before relying on a License, but Barcarolle still records and distributes evidence-backed admissions rather than constraining every live action itself.

## 2.2 Parameter Authority Boundary

Calibration has two authority sources that must remain distinct:

| Surface | Machine-calibrated from objective evidence | Explicit risk-profile appetite |
| --- | --- | --- |
| Score weights and caps | Selects deterministic weights, oracle factors, duplicate caps, risk/high-impact multipliers, and repeated-run treatment that best separate positive controls from negative and unsafe controls. | Sets floors, ceilings, forbidden weight effects, maximum risk-budget consumption, and slice applicability limits. |
| Coverage gates | Learns which coverage dimensions and missing-run patterns predict unreliable authorization under the benchmark facts. | Sets minimum coverage floors, critical slices, high-impact path requirements, and cases where absence must block even if empirical data is sparse. |
| Reliability labels | Learns variance, flakiness, verifier-stability, and sample-count rules that preserve authorization consistency. | Sets minimum acceptable labels by tier/scope and whether low-confidence slices must be blocked, shadowed, or targeted for validation. |
| Authorization thresholds | Chooses threshold tables and downgrade/denial cutoffs that pass positive controls and reject negative or unsafe controls. | Sets tier eligibility, threshold floors/ceilings, unsafe false-positive budgets, review triggers, and forbidden-tier matrices. |
| Promotion gates | Computes objective-control, held-out, sensitivity, non-regression, and traceability pass/fail results. | Defines required confidence level, acceptable risk budget, required slices, freshness ceilings, and escalation paths when gates fail. |

When a risk-profile constraint determines the final value, the calibrated profile must mark that parameter as `constraint_bound` and record the binding constraint. When objective evidence determines the value inside the allowed range, the profile marks it as `evidence_fit`. When evidence is insufficient for a claimed slice, the profile must mark the slice `blocked`, `shadow_only`, `targeted_validation_required`, or excluded from applicability. It must not fill the gap by treating the risk profile, a human preference, or a governance review as truth.

## 3. Evidence Inputs

Calibration evidence is repository-local or release-local unless a policy explicitly declares a broader transfer scope. Accepted evidence classes include:

- historical merged fixes and their known post-fix states;
- known pre-fix states from the same task lineage;
- no-op probes and mutation-based negative controls;
- retrieval-only, rule-based, or weak deterministic baselines;
- prior agent configurations evaluated on the same benchmark releases;
- repeated-run variance and stochastic pass-rate summaries;
- canonical verification records and trusted terminal-outcome evidence;
- benchmark release coverage profiles and task-family/component/risk/high-impact slices;
- scorecards, missing-run summaries, denominator summaries, and reliability labels from prior policy versions;
- release-maintenance findings, task retirements, leakage reports, and oracle invalidation records;
- automatically computed sensitivity analyses over thresholds, score weights, coverage gates, reliability rules, and tier outcomes.

Human review records may be included as governance context, for example to explain why a profile was rolled back or why an operator requested a fresh calibration run. They must not be treated as ground-truth labels for normal calibration.

Calibration evidence is assembled by manifest. Each manifest records source releases, source scorecards, task families, repository components, risk classes, permission classes, high-impact path classes, control types, baseline agent configurations, repeated-run groups, canonical verification refs, evidence bundle digests, the exact effective risk-profile ref/digest, and exclusion reasons. A manifest that omits a slice can only calibrate policies whose applicability excludes that slice.

### 3.1 Calibration Truth Observations

The calibration manifest must normalize each objective input into a `calibration_truth_observation` entry. The observation is the unit used to fit thresholds, score weights, reliability labels, coverage gates, unsafe false-positive metrics, and promotion gates.

Minimum fields:

- `calibration_truth_observation_id` or manifest-local stable key;
- `observation_kind`: `positive_control`, `negative_control`, `safety_control`, `baseline_result`, `prior_agent_result`, `variance_sample`, `coverage_gap`, or `maintenance_invalidation`;
- `truth_basis_kind`: `post_fix_canonical_positive`, `known_pre_fix_negative`, `no_op_negative`, `mutation_negative`, `retrieval_or_leakage_negative`, `rule_or_weak_baseline_negative`, `prior_agent_measured_outcome`, `trusted_policy_violation_negative`, `unsupported_scope_negative`, `stability_or_flakiness_control`, or `invalidation_control`;
- source refs to tasks, releases, scorecards, canonical verification records, score bundles, run groups, maintenance findings, evidence bundles, or generated-control runs;
- objective expected policy effect: `should_score_positive`, `should_not_score_positive`, `must_not_authorize_above_tier`, `must_block_authorization`, `must_require_targeted_validation`, `must_require_full_rebenchmark`, or `diagnostic_only`;
- semantic slice: task family, component/path, risk class, permission class, high-impact path class, oracle grade, evaluation mode, adapter purity, capability envelope, evidence trust basis, and target-condition basis when present;
- `truth_confidence_basis`: deterministic verifier pass/fail, clean-room canonical verification, certified release membership, trusted policy evidence, release-maintenance finding, repeated-run variance, or baseline/control run lineage;
- exclusion status and exclusion reason when the observation is not allowed to train or validate a profile.

Positive controls prove that a policy can recognize acceptable evidence for a scope. Negative and safety controls prove that a policy rejects objectively bad, unsafe, unsupported, contaminated, or insufficient evidence. Prior-agent results may be positive, negative, or diagnostic depending on their canonical verification and policy evidence; they are not labels merely because an older agent was trusted or untrusted in production.

Human review can attach rationale, waive operational ownership, or request reruns, but it cannot create a `truth_basis_kind`. A governance override that allowed an exceptional admission is excluded from normal calibration evidence unless a later objective verification, release-maintenance, or control-run basis establishes the observation's truth class.

### 3.2 High-Tier Authorization Truth Basis

`G4` and `G5` calibration requires a stronger observation mix than lower-tier comparison calibration. A candidate profile may claim high-tier applicability for a slice only when the manifest contains all of these machine-checkable bases for that slice, or when its applicability explicitly excludes the missing dimension:

- positive controls whose post-fix or canonical-solution states pass clean-room canonical verification under certified release membership;
- negative correctness controls from known pre-fix, no-op, mutation, retrieval-only, weak-baseline, or prior-agent failing states that target the same task families and critical components;
- safety controls for trusted policy violations, unsupported release scopes, leakage/contamination, protected-resource attempts, ACUT binding failure, target-condition mismatch, or License-consumption incompatibility when those dimensions are relevant to the requested high-tier operation;
- repeated-run and verifier-stability observations sufficient to estimate reliability-label behavior for the tier;
- coverage observations for critical task families, high-impact path classes, permission classes, and capability-envelope dimensions named by the release coverage profile or risk profile.

A high aggregate score on positive controls is insufficient by itself to calibrate high-tier authorization. If the manifest lacks comparable negative or safety controls for a critical high-tier slice, the calibrated profile must either keep that slice on the previous active profile, keep the new profile in `shadow`, mark the slice `targeted_validation_required`, or block high-tier applicability. It must not lower `G4` or `G5` thresholds from positive evidence alone.

High-tier truth remains condition-bound. A profile calibrated for native YOLO, a specific capability envelope, and a specific evidence trust basis does not become truth for `Agent + Harness`, weaker ACUT binding, broader network/tool posture, or an unobserved target condition unless the manifest includes observations and compatibility rules for that target condition.

### 3.3 Unsafe False-Positive Measurement

An unsafe false positive is a candidate policy outcome that would grant, renew, resume, or fail to suspend/revoke an authorization above the objective safe bound for a negative, safety, unsupported-scope, or invalidation observation.

For each observation and requested tier, calibration evaluates the candidate policy as if the observation were the scorecard or decision input. It records:

- `expected_policy_effect` from the observation;
- candidate outcome, granted tier, readiness, required next action, narrowed scope, and gate reasons;
- `unsafe_false_positive = true` when the candidate grants or preserves a tier/scope that the observation says must be rejected, blocked, downgraded below, targeted for validation, fully rebenchmarked, suspended, or revoked;
- severity class derived from the objective control class and affected operation surface, for example `write_capable`, `high_impact`, `protected_resource`, `G4`, or `G5`;
- slice key and risk-profile budget key used for promotion evaluation.

The denominator is the count or weighted count of eligible negative, safety, unsupported-scope, and invalidation observations for the same claimed applicability slice. The numerator is the count or weighted count marked `unsafe_false_positive = true`. Promotion evaluates both the observed rate and a confidence upper bound chosen by the effective risk profile. Small denominators do not produce optimistic rates; they produce `insufficient_control_power` and block, shadow, narrow, or require targeted validation for that slice.

Unsafe false-positive budgets are appetite constraints, but the unsafe false-positive labels are not appetite. The labels come from objective observation truth classes and candidate policy behavior. The risk profile decides how much measured unsafe risk is acceptable, which confidence bound to use, and which tiers or slices have zero tolerance.

Calibration should also measure overly restrictive false negatives on positive controls. Those metrics can influence usefulness and operating cost inside the risk profile's objective weights, but they cannot offset a breached unsafe false-positive gate for high-impact, protected-resource, `G4`, or `G5` slices.

## 4. Calibration Workflow

`PolicyCalibrationWorkflow` is the normal automated loop:

1. Resolve the effective repository or organization risk profile for the target scope and persist its ref, version, digest, and inheritance basis.
2. Build a calibration input manifest from published releases, historical fixes, existing scorecards, canonical verification records, repeated-run groups, maintenance findings, generated controls, and the resolved risk-profile constraints.
3. Normalize every eligible input into `calibration_truth_observation` entries with explicit truth basis, expected policy effect, semantic slice, and exclusion status.
4. Generate or refresh automatic controls through the existing candidate-build, replay, validation, benchmark-release, benchmark-evaluation, canonical-verification, and scoring workflows.
5. Exclude any manifest input or candidate applicability slice whose objective evidence is insufficient, whose leakage status is unresolved, whose risk-profile slice is under-specified, whose truth observation would require human judgment, or whose admission path would require human judgment to establish truth.
6. Run baseline configurations automatically, including no-op, pre-fix, mutation, retrieval-only, rule-based, weak deterministic, and prior-agent baselines where available.
7. Fit candidate policy profiles over score weights, threshold tables, coverage gates, reliability-label rules, and promotion gates while treating the effective risk profile as hard constraints plus explicit objective weights.
8. Validate profiles on held-out releases, time slices, task families, components, risk classes, high-impact path classes, permission classes, risk-profile slices, prior-agent configurations, and high-tier safety-control slices.
9. Compute unsafe false-positive metrics, control-separation margins, positive-control false-negative metrics, and confidence bounds by claimed applicability slice.
10. Compute sensitivity analyses that show how small parameter changes affect aggregate scores, reliability labels, coverage readiness, authorization tiers, downgrades, denials, suspension/revocation paths, unsafe false-positive status, and risk-budget consumption.
11. Emit a `policy_calibration_run` result and one or more `calibrated_policy_profile` candidates.
12. Promote the best candidate automatically only when promotion gates pass under the effective risk profile. Otherwise keep it in `candidate` or `shadow` state and record exact blockers.

The workflow can be triggered by schedule, new benchmark release publication, enough new canonical verification records, material drift in repeated-run variance, release-maintenance findings, a policy-profile expiration window, or an operator-requested calibration run. Operator requests start the same automated workflow; they do not supply labels or manually accept generated benchmarks.

## 5. Calibration Objectives

Calibration optimizes for policy usefulness under explicit risk-profile constraints:

- post-fix and canonical-solution states should score and authorize above the appropriate tier when release coverage supports that tier;
- known pre-fix states, no-op controls, mutation controls, direct-retrieval controls, and weak baselines should not reach write-capable or high-autonomy tiers;
- high-risk, high-impact, and broad-scope grants should require stronger evidence than low-risk or narrow diagnostic use;
- repeated-run instability should reduce reliability and authorization readiness rather than hiding inside completed-only averages;
- missing coverage should lower readiness, trigger targeted validation, or trigger full rebenchmarking according to calibrated coverage policy;
- task-family, component, permission, and risk slices should avoid one aggregate threshold masking a weak critical slice;
- policy profiles should be monotonic where semantics require it, for example a lower aggregate score or lower coverage must not produce a higher tier under the same scope and evidence basis;
- promotion must not materially increase unsafe false positives on held-out negative, safety, unsupported-scope, or invalidation controls;
- risk-budget consumption must stay within the active risk profile's maximum unsafe-control promotion rates, minimum separation margins, and tier/scope eligibility constraints.

The objective function records metrics by slice, not just repository-wide averages. Required slices include task family, component/path, risk class, permission class, high-impact path class, oracle grade, release, evaluated capability envelope, evaluation mode, adapter purity, evidence trust basis when those fields are present, and risk-profile constraint slice. A lower-risk tolerance profile normally increases evidence, coverage, reliability, review, and freshness requirements; a higher-risk tolerance profile may reduce some calibrated thresholds only within explicit floors, forbidden-tier rules, and control-separation limits.

## 6. Policy Profile Output

A calibrated policy profile is an append-only parameter bundle, not prose:

- `calibrated_policy_profile_id`;
- semantic family, such as `authorization_semantics_v1`;
- exact `authorization_policy_version`, `scorecard_policy_version`, `coverage_policy_version`, `release_admission_policy_version`, and `reliability_policy_version` values governed by the profile;
- predecessor profile and active/shadow/candidate lineage;
- target repository scope and applicability slices;
- effective `repository_risk_profile_id`, risk-profile version, risk-profile digest, and inheritance/override basis;
- risk constraints summary and risk-budget consumption summary;
- parameter digest and full parameter artifact ref;
- calibration run ref and input manifest digest;
- calibration truth contract version, truth basis digest, and truth-observation summary;
- evidence coverage summary and exclusion summary;
- control-separation metrics;
- unsafe false-positive metrics by tier, severity, and applicability slice;
- high-tier authorization calibration summary, including blocked or shadow-only high-tier slices;
- parameter authority summary marking each parameter as `seed_default`, `evidence_fit`, `constraint_bound`, `shadow_only`, or `blocked`;
- held-out validation metrics;
- repeated-run variance and confidence summaries;
- sensitivity-analysis refs;
- impact preview over scorecards, authorization decisions, repository-agent admissions, and operating-state coverage entries;
- promotion gate results;
- lifecycle state: `candidate`, `shadow`, `active`, `paused`, `superseded`, `rolled_back`, or `blocked`;
- activation time and optional expiration time.

The profile is the policy source of truth for calibrated parameters. Scoring and authorization records copy the exact profile or policy-version refs they used so a later profile cannot silently reinterpret historical facts.

## 7. Promotion Rules

Promotion is automated for normal operation. A profile can move from `candidate` to `shadow` or `active` only through `PolicyCalibrationWorkflow` using workflow-owned transition records and machine-checkable gates:

- evidence manifest completeness for every claimed applicability slice;
- calibration truth-observation completeness for every claimed applicability slice, including explicit exclusion of observations that would require human truth;
- exact effective risk-profile ref/digest and a satisfiable constraint set for every claimed applicability slice;
- objective-control separation above policy minimums;
- held-out validation non-regression against the active profile;
- no high-risk or high-impact unsafe-control promotion above allowed tier;
- unsafe false-positive observed rates and configured confidence upper bounds within risk-profile budgets for every claimed tier/slice;
- `G4` and `G5` slices backed by positive, negative, safety, stability, and coverage observations; otherwise those slices remain blocked, shadow-only, or targeted-validation-only;
- reliability-label stability under repeated-run variance;
- sensitivity bounds that identify brittle thresholds and block promotion when small parameter changes flip material high-risk decisions;
- no unresolved scorecard- or admission-invalidating maintenance findings in the calibration basis;
- no breach of the active risk profile's unsafe false-positive budget, forbidden-tier matrix, freshness ceiling, or required-review rule;
- no parameter promoted as evidence-fit when the final value is actually determined by a risk-profile constraint;
- full traceability from profile parameters to calibration evidence and policy-version output.

Human governance may pause, roll back, or annotate a profile after inspection, but normal calibration truth, activation, and promotion gates are computed by the system. Human governance rationale is non-truth-bearing: it can remove a profile from active selection, request a rerun, or explain rollback, but it cannot promote a profile to active or supply calibration labels.

Pause lifecycle semantics:

- `pause` is a governance transition from `active` or `shadow` to `paused`. It immediately removes the paused profile from active-profile selection for new scorecards and new authorization decisions.
- Active selection falls back to the latest non-paused active predecessor for the same semantic family, repository scope, applicability slice, and policy-version surface. If no such predecessor exists, new scorecard/authorization materialization is blocked for that slice until an automated profile transition restores an eligible active profile or publishes a superseding profile.
- Existing scorecards, authorization decisions, repository-agent admissions, and operating-state coverage entries that reference the paused profile remain historical facts. Pause does not mutate them; it can trigger new suspension, revocation, targeted validation, or reauthorization workflows when policy says existing effective admissions are no longer safe.
- `resume` from `paused` to `active` is workflow-owned and requires machine-checkable gate refs proving the original pause cause is resolved and the profile still satisfies promotion gates under the current evidence manifest. If parameters or applicability change, the valid path is `supersede` with a new calibrated profile, not resume.
- `supersede` creates or activates a successor profile through automated gates and records predecessor lineage. `rollback` records a governance transition that returns active selection to an earlier eligible profile without deleting the rolled-back profile or any fact that used it.

## 8. Scoring Integration

Scoring reads the active calibrated scorecard profile when computing:

- oracle multipliers and B-oracle caps;
- duplicate-cluster caps;
- high-impact and risk multipliers;
- repeated-run aggregation policy;
- missing-run denominator treatment;
- minimum-sample rules;
- reliability-label rules;
- coverage-policy readiness fields that are materialized on `benchmark_scorecard`.

The initial factors in scoring semantics are seed defaults. Once a calibrated profile is active, the scorer loads factors by `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, and the effective risk-profile basis embedded in the calibrated profile. The resulting scorecard persists the profile refs, risk-profile ref/digest, and weighting summary. Historical scorecards keep their original versions and risk-profile basis; new policy or risk-profile inputs create new scorecards when scorecard-level facts change.

## 9. Authorization Integration

Authorization reads the active calibrated authorization profile when evaluating:

- tier score thresholds;
- minimum release coverage;
- task-family coverage requirements;
- high-impact and critical-family requirements;
- reliability-label eligibility by requested tier;
- targeted-validation versus full-rebenchmark cutoffs;
- promotion, suspension, revocation, and renewal gates affected by calibrated policy.

`authorization_semantics_v1` remains the semantic contract for tier names, outcomes, subject-applicability gates, ACUT binding gates, License-consumption compatibility, freshness, explicit risk-profile constraints, and the separation between score facts and policy facts. Calibrated profiles govern the parameter values inside that contract, while the effective risk profile defines the risk tolerance under which those parameters are valid. Every `authorization_decision` records the exact `authorization_policy_version`, calibrated profile ref, risk-profile ref, risk-profile digest, and risk-profile gate result used for the decision. During any API migration, `policy_version` must alias `authorization_policy_version` and must not persist as a second ambiguous value.

## 10. Console and Audit

The operator console exposes calibration as an audit and operations surface:

- active and shadow policy profiles;
- active, inherited, shadow, and superseded repository/organization risk profiles;
- calibration run history and status;
- evidence manifest coverage and exclusions;
- risk-profile constraints, risk-budget consumption, and profile-to-policy diffs;
- control results and held-out validation metrics;
- threshold, weight, coverage-gate, and reliability-label diffs from the prior active profile;
- sensitivity plots and brittle decision warnings;
- impact previews for scorecards, decisions, admissions, and operating-state entries;
- profile activation, pause, resume, supersession, rollback, and governance annotations.

The console must not present a manual benchmark-acceptance step as required for calibration. Operator actions are limited to starting a calibration workflow, inspecting evidence, requesting a shadow impact preview, creating or transitioning append-only risk-profile versions, annotating governance rationale, or writing rollback/pause overrides through append-only governance records. A risk-profile edit can change future appetite constraints, but it cannot act as a truth label for any calibration run.

## 11. Traceability

- [scoring-semantics.md](./scoring-semantics.md) defines how calibrated scorecard and reliability policies affect immutable score facts.
- [authorization-semantics.md](./authorization-semantics.md) defines how calibrated authorization profiles govern tier thresholds and coverage gates inside `authorization_semantics_v1`.
- [data-model.md](./data-model.md) defines `repository_risk_profile`, `policy_calibration_run`, and `calibrated_policy_profile`.
- [workflow-runtime.md](./workflow-runtime.md) defines `PolicyCalibrationWorkflow`.
- [interface-contracts.md](./interface-contracts.md) and [api-schema.md](./api-schema.md) expose calibration commands, queries, events, and audit fields.
- [operator-console.md](./operator-console.md) defines the calibration inspection and governance UI.
