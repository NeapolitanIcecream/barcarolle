# Scoring Semantics

## 1. Purpose

This document defines the design-contract semantics for Barcarolle score facts. It closes the gap between canonical verification, per-run score bundles, benchmark scorecards, and `authorization_semantics_v1`.

It does not introduce a parallel scoring product. The contract is implemented through the existing `evaluation_run`, `canonical_verification_record`, `score_bundle`, `benchmark_scorecard`, `repository_risk_profile`, `authorization_decision`, evidence, Judge, release, admission, and calibrated policy-profile records described in the surrounding architecture docs.

Scoring policy family: `scoring_semantics_v1`.
Calibration design: [policy-calibration.md](./policy-calibration.md).

## 2. Non-Negotiable Boundaries

- Correctness is rooted in `canonical_verification_record` and other `trusted_barcarolle_evidence`.
- Agent-submitted traces, self-run tests, and native logs can inform process, risk, confidence, and audit. They cannot by themselves create positive correctness.
- `Golden Agent` is validation-side support. It can improve task admission and review but does not score runs.
- `Judge Agent` is scoring-side support. It can be advisory or governed score-contributing, but it does not write authorization decisions directly.
- Scoring writes immutable facts. Recomputing under a different policy, evidence input set, missing-run set, canonical verification basis, or score-contributing Judge lineage creates a new score or scorecard identity.
- Authorization consumes scorecards and release context. A denial, downgrade, suspension, or revocation must not mutate the underlying score facts.
- Score weights, coverage gates, and reliability-label rules are policy-profile parameters constrained by the effective repository or organization risk profile. Automatic calibration can promote new values, but production use of changed scorecard-level parameters requires a new immutable scorecard under the exact `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, `calibrated_policy_profile_id` or seed basis, and `repository_risk_profile_id` or seed risk-profile basis when appetite constraints affected the scorecard policy.

## 3. Per-Run Score Semantics

### 3.1 Correctness Source of Truth

The per-run correctness source of truth is the trusted canonical verification basis:

- `run_submission_id`;
- `canonical_verification_record_id`;
- verifier identity, verifier image digest, and scoring-relevant verifier policy;
- patch/result application status;
- canonical verifier outputs, hidden-test outputs, and trusted policy-check outputs;
- exact sealed evidence bundle IDs, manifest versions, and content digests consumed by scoring.

`score_bundle.correctness_score` is computed from that basis. A score bundle that carries positive correctness must reference a canonical verification record whose trusted evidence digest is included in `score_input_evidence_digest`.

### 3.2 Run Outcome Classes

Scoring must classify each accepted run attempt before aggregation.

| Outcome class | Score-bundle presence | Correctness score | Coverage treatment | Notes |
| --- | --- | ---: | --- | --- |
| `verified_pass` | Required | 100 before oracle and aggregation weighting | Completed and verified | Canonical verifier passes and trusted policy checks pass. |
| `verified_fail` | Required | 0 | Completed and verified | Canonical verifier or objective policy check rejects the submitted result. |
| `agent_timeout` | Required when timeout is inside the accepted run envelope | 0 | Completed failure | The ACUT failed to submit a valid result before the evaluated runtime limit. |
| `malformed_or_empty_submission` | Required when the malformed result is agent-produced | 0 | Completed failure | Missing patch/result, wrong artifact shape, or unreadable submission under the accepted task contract. |
| `policy_invalid` | Required when trusted evidence shows post-acceptance policy violation | 0 and critical risk flag | Completed but authorization-blocking for affected scopes | Examples: unauthorized protected-resource edit, forbidden network/tool use, tampering with visible tests where policy disallows it. |
| `unverified` | No positive score bundle | No correctness score | Missing verification coverage | No trusted canonical verification record exists. |
| `incomplete_infra_or_evidence` | No positive score bundle | No correctness score | Missing coverage; reliability degraded | Evidence ingestion, object storage, verifier bootstrap, or platform-owned completion failed. |
| `operator_canceled` | No positive score bundle unless cancellation happened after a scoreable terminal outcome | No correctness score | Missing coverage | Human or workflow cancellation before scoreable terminal state. |
| `infra_failed` | No positive score bundle | No correctness score | Missing coverage; reliability degraded | Platform, runner adapter, clean-room environment, or verifier infrastructure failed independently of the ACUT result. |
| `verifier_flaky_unresolved` | No positive score bundle for authorization | No correctness score | Missing or blocked coverage | Reverification cannot establish a stable trusted verdict. |

Score bundles should include `run_outcome_class`, `score_state`, `failure_class`, `failure_taxonomy_version`, `outcome_owner` (`agent`, `barcarolle_infra`, `operator`, `third_party`, or `unknown`), `authorization_eligible`, and `authorization_blocking_risk_flags[]`. `score_state` values are `scoreable_positive`, `scoreable_zero`, `non_scoreable_missing`, `blocked`, and `invalidated`; non-scoreable values normally appear on scorecard input entries rather than as positive score bundles. Runs without a score bundle still appear in scorecard input-set entries as missing or blocked items so incomplete evaluations cannot look better than complete ones.

### 3.3 Failure Taxonomy

`failure_class` is machine-readable and versioned by `failure_taxonomy_version`. `scoring_semantics_v1` recognizes at least:

- `patch_apply_failed`;
- `build_failed_after_submission`;
- `test_or_verifier_failed`;
- `policy_check_failed`;
- `agent_timeout`;
- `resource_limit_exceeded_by_agent`;
- `malformed_submission`;
- `empty_submission`;
- `wrong_artifact_type`;
- `unauthorized_tool_or_network_use`;
- `protected_resource_violation`;
- `evidence_missing_or_corrupt`;
- `canonical_verifier_bootstrap_failed`;
- `canonical_verifier_flaky`;
- `operator_canceled`;
- `runner_adapter_failed`;
- `unknown_unclassified`.

Only failures whose `outcome_owner` is `agent` or trusted policy evidence against the submitted result can become scoreable zeroes. Platform-owned failures remain missing coverage and degrade reliability; they do not become evidence that the ACUT was wrong.

### 3.4 Process Score, Risk Flags, and Judge Outputs

`process_score` is separate from correctness. It may summarize localization, context selection, tool use, test discipline, trace consistency, or resource use when the evidence basis supports those claims.

Default `scoring_semantics_v1` treatment:

- `correctness_score` is rooted in canonical verification.
- `process_score` is diagnostic unless the scoring policy explicitly declares a process contribution or cap.
- Critical trusted risk flags can set `authorization_readiness = blocked` for affected scopes even when correctness is high.
- Advisory Judge output can contribute explanations, risk flags, review triggers, and confidence labels but cannot change correctness.
- Score-contributing Judge output is allowed only when an active governed Judge configuration and scoring policy declare the exact contribution. In that mode Judge may reduce or cap a score, assign process sub-scores, or mark semantic ambiguity, but it must not turn a canonical failure into a positive correctness pass.

When Judge is score-contributing, `score_basis_judge_lineage = judge_configuration_id` is part of score and scorecard identity. When Judge is advisory only, the identity axis is explicit `none`; advisory artifacts remain attached audit material.

## 4. Task and Oracle Weighting

### 4.1 Release Weight Versus Score Weight

`benchmark_release_membership.inclusion_weight` is the immutable release weight. It is used for release coverage and same-benchmark comparison.

`score_weight` is the deterministic aggregation weight used by a scorecard. It is derived from immutable release membership plus the scorecard policy. It does not mutate the release. The scorecard must persist a `weighting_summary` that shows, per membership or group:

- release weight;
- requested-scope inclusion;
- duplicate-cluster cap factor;
- oracle multiplier and B-oracle cap factor;
- high-impact or risk multiplier;
- final score weight;
- denominator inclusion reason.

Coverage gates use release weight. `aggregate_score` uses final score weight. Both denominators must be persisted so operators can distinguish "we did not run enough release weight" from "we ran it and scored poorly."

### 4.2 Default Weight Derivation

For each release membership in the evaluated requested scope, the seed policy derives weights as follows:

1. Start with `base_weight = benchmark_release_membership.inclusion_weight`.
2. Set `scope_factor = 1` if the membership is inside the evaluated capability envelope and requested scope, otherwise `0`.
3. Apply duplicate-cluster caps proportionally within each duplicate cluster. Default cap: no duplicate cluster may contribute more than 10% of requested pre-oracle score weight unless the release policy declares a different cap.
4. Apply oracle multiplier:
   - `A_strong_behavioral`: `1.00`;
   - `B_objective_partial`: `0.85`;
   - `C_auxiliary`: `0` for certified scoring;
   - `D_weak`: `0` and not allowed in certified release membership.
5. Apply high-impact and risk multiplier when the requested scope depends on that risk class:
   - normal: `1.00`;
   - high-impact path or high-risk permission class: `1.25`;
   - critical path plus high-risk permission class: `1.50`.
6. Apply B-oracle total cap proportionally across all B-oracle memberships after duplicate, oracle, and risk factors. Default cap: B-oracle tasks may contribute at most 30% of requested pre-B-cap score weight, and at most 15% for high-impact, high-risk, `G4`, or `G5` interpretation.
7. Apply a final normalization only for reporting percentages; do not renormalize away missing runs.

If automatic calibration changes any factor, cap, reliability rule, or order above, it must publish a calibrated policy profile and use a new `scorecard_policy_version`, `coverage_policy_version`, `reliability_policy_version`, `calibrated_policy_profile_id`, and effective risk-profile basis as appropriate. The seed values are initial policy parameters, not permanent constants. Historical scorecards keep the exact version, risk-profile basis, and weighting summary they were computed with.

### 4.3 Tag Effects

Task-family, component/path, permission, capability, risk, and high-impact tags affect aggregation in four ways:

- they filter which release memberships are in the requested score and coverage denominator;
- they create required coverage slices such as `task_family_coverage`, component/path coverage, permission coverage, and high-impact-path coverage;
- they select risk multipliers and critical missing-coverage rules;
- they determine whether a partial scorecard can support a narrowed authorization scope.

Tags do not change a run's per-run correctness. They determine how that run contributes to benchmark and authorization interpretation.

## 5. Repeated-Run and Stability Semantics

### 5.1 Trial Grouping

Transport retries are not trials. Semantic attempts are trials only when the accepted run identity has a distinct command-supplied `attempt_number`.

For benchmark-linked runs, a repeated-run group is keyed by:

`benchmark_evaluation_id + benchmark_release_membership_id + capability_envelope_id + evaluation_mode + adapter_purity_level + adapter_manifest_digest + scoring_policy_version`

For ad hoc runs, it is keyed by:

`task_id + environment_id + tested_agent_snapshot_id + capability_envelope_id + evaluation_mode + adapter_purity_level + adapter_manifest_digest + scoring_policy_version`

Canonical reverification attempts of the same submission measure verifier stability. They are not new ACUT trials.

### 5.2 Default Trial Aggregation

`scoring_semantics_v1` uses `mean_of_trials` unless a policy explicitly declares another trial policy such as `first_attempt_only` or `best_of_k`. `best_of_k` must be treated as a different evaluated capability envelope if the admitted operating condition allows multiple attempts.

For each repeated-run group:

- `scoreable_trial_count` counts score bundles with scoreable outcome classes.
- `planned_trial_count` comes from the evaluation or stability policy.
- `pass_count` counts `verified_pass` outcomes after policy-valid filtering.
- `pass_rate = pass_count / scoreable_trial_count` when scoreable count is nonzero.
- `trial_mean_score` is the mean effective correctness score over scoreable trials.
- missing, canceled, infra-failed, or verifier-flaky trials are reported separately and reduce coverage/reliability.

The membership-level `task_score` used by scorecard aggregation is `trial_mean_score` for the default policy. A stochastic agent with a 60% pass rate therefore contributes about 60 points for that task, not 100 points from its best trial.

### 5.3 Stability Labels

Score bundles and scorecards must expose stable labels:

- `stable`: required trials agree within policy tolerance and verifier evidence is stable.
- `agent_stochastic`: agent outcomes vary but verifier is stable; pass-rate scoring is valid.
- `agent_unstable`: agent outcomes vary beyond authorization tolerance.
- `verifier_flaky`: canonical verification is inconsistent for the same submitted artifact or verifier basis.
- `infra_unreliable`: platform failures prevent a reliable score.
- `insufficient_trials`: policy required more trials than were completed.
- `blocked`: instability prevents authorization interpretation.

Agent stochasticity reduces score through pass-rate or mean-trial scoring. Verifier flakiness and platform instability should not be converted into agent failure; they block readiness, require targeted validation, or route the task/release to maintenance.

## 6. Benchmark Scorecard Aggregation

### 6.1 Score Input Set Identity

`benchmark_scorecard.score_input_set_digest` is the digest of the complete score input set, not only the successful score bundles. The canonical input set is a sorted list of entries keyed by `benchmark_release_membership_id` and repeated-run group. Each entry records:

- release membership identity and task identity;
- release weight and final score weight;
- selected score-bundle IDs and their `score_input_evidence_digest` values when scoreable;
- missing or blocked status when no score bundle contributes;
- run outcome classes and failure summaries;
- trial policy and repeated-run summary;
- oracle grade and weighting factors;
- task-family/component/path/capability/permission/risk tags;
- score-basis Judge lineage.

A later run completion, evidence repair, new score bundle, changed missing-run classification, changed selected trial policy, changed weighting policy, or changed Judge lineage creates a new score input set digest and therefore a new immutable scorecard.

### 6.2 Aggregate Formula

For a scorecard over requested release scope `R`:

```text
requested_release_weight = sum(release_weight_m for m in R)
requested_score_weight = sum(score_weight_m for m in R)

task_contribution_m =
  score_weight_m * task_score_m / 100       when scoreable
  0                                        when missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, or blocked

aggregate_score =
  round_half_even(100 * sum(task_contribution_m) / requested_score_weight, 2)
```

If `requested_score_weight = 0`, the scorecard has no aggregate score and `authorization_readiness = blocked`.

The scorecard may also expose `completed_score` as a diagnostic mean over scoreable completed score weight only. `completed_score` is not an authorization threshold input because it can hide missing coverage.

### 6.3 Coverage Denominators

The scorecard must persist:

- `requested_release_weight`;
- `completed_release_weight`;
- `verified_release_weight`;
- `missing_release_weight` grouped by reason;
- `requested_score_weight`;
- `completed_score_weight`;
- `verified_score_weight`;
- `missing_score_weight` grouped by reason;
- task-family, component/path, permission, capability, risk, and high-impact-path denominators.

Missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, and blocked runs contribute zero to `aggregate_score` and count against coverage. They also drive `authorization_readiness` and reliability labels so operators can distinguish "low score" from "not enough trustworthy evidence."

### 6.4 Minimum Sample and Reliability

`minimum_sample_summary` is a policy input, not a UI nicety. It records:

- scoreable task count;
- scoreable release weight;
- covered task families;
- covered critical families;
- covered high-impact path classes;
- completed repeated-run trial counts;
- missing or blocked sample gaps;
- threshold result for the requested tier or comparison context.

Seed reliability labels:

| Label | Meaning |
| --- | --- |
| `high` | Coverage, sample count, canonical verification, and stability satisfy the requested high-tier policy gates. |
| `medium` | Enough evidence for comparison or lower-tier policy, with no critical missing family. |
| `low` | Useful diagnostic score but below authorization sample or coverage expectations. |
| `blocked` | Policy-invalid, verifier-flaky, infra-unreliable, invalidated, or too incomplete for authorization interpretation. |

Authorization policies and risk profiles may require stricter tier-specific minimums. Automatic calibration may promote new reliability rules through `reliability_policy_version` when repeated-run variance, canonical verification coverage, missing-run behavior, controls, explicit risk-profile constraints, and slice-level sensitivity analyses support the change. The label never widens release-supported scope; it can only explain, narrow, block, or require more evaluation.

### 6.5 Calibration Inputs and Outputs

`PolicyCalibrationWorkflow` may compute candidate scoring profiles from repository historical fixes, known pre-fix states, no-op and mutation controls, retrieval-only or rule-based baselines, prior agent configurations, repeated-run variance, canonical verification records, release coverage profiles, task-family/component/risk slices, explicit risk-profile constraints, and sensitivity analyses. It normalizes those inputs into calibration truth observations for objective expected policy effects, unsafe false-positive measurement, high-tier control power, and parameter-authority summaries. It must not require human baselines or human labels. The risk profile constrains the optimization and records appetite; it does not supply objective truth labels.

The scorer consumes only promoted profile parameters and the effective risk-profile basis embedded in those parameters. A calibration run can produce shadow impact estimates over old score inputs, but those estimates are calibration artifacts, not benchmark-authoritative scorecards. When a calibrated profile or risk-profile change alters score weights, reliability rules, or coverage gates, `ScoreWorkflow` must materialize a new immutable `benchmark_scorecard` before authorization treats the changed interpretation as fresh benchmark evidence.

## 7. Evidence and Judge Semantics

### 7.1 Evidence Trust Tiers

Evidence tiers contribute as follows:

| Evidence tier | Correctness | Process/risk/confidence | Authorization/binding |
| --- | --- | --- | --- |
| `trusted_barcarolle_evidence` | May root correctness when produced by validation, canonical verification, or scoring workers | Yes | Yes |
| `adapter_observed_evidence` | No independent positive correctness | Yes, within declared observation boundary | Can support binding/attestation if policy allows |
| `agent_submitted_evidence` | No independent positive correctness | Yes for audit, trace consistency, and risk | Can support declared behavior only with review; cannot be sole high-tier binding |
| `third_party_evidence` | No independent positive correctness unless converted into trusted Barcarolle verification | Yes | Can support attestation when source and digest are accepted |

Every score must record `evidence_trust_basis` and `evidence_trust_basis_digest`. Evidence repair or backfill that changes a score-contributing or confidence-contributing input creates a new score bundle.

### 7.2 Judge Contribution Modes

Judge artifacts carry one of these contribution modes:

- `advisory`: visible in audit/review, no score or confidence effect, no score identity effect.
- `confidence_contributing`: affects reliability, risk, review triggers, or `authorization_readiness`; included in `score_input_evidence_digest`.
- `process_contributing`: affects `process_score`; included in `score_input_evidence_digest`.
- `score_contributing`: affects correctness, score cap, or aggregate score; includes governed `judge_configuration_id` as score-basis lineage.

Only `score_contributing` Judge lineage splits the explicit `score_basis_judge_lineage` axis. Confidence- or process-contributing Judge inputs still affect `score_input_evidence_digest` so recomputation is auditable.

## 8. Authorization Interaction

### 8.1 Policy Inputs

`authorization_semantics_v1` treats these scorecard fields as policy inputs:

- `aggregate_score`;
- `coverage_summary`;
- `task_family_coverage`;
- component/path, permission, capability, risk, and high-impact-path coverage summaries when requested by scope;
- `canonical_verification_coverage`;
- `minimum_sample_summary`;
- `aggregate_stability_label`;
- `reliability_label`;
- `authorization_readiness`;
- `invalidation_status` and invalidation refs;
- `evidence_trust_basis`;
- risk-profile basis and risk-profile gate summary when scorecard policy used appetite constraints;
- `score_input_set_digest`;
- `score_basis_judge_lineage`;
- evaluated capability-envelope coverage;
- release coverage profile, supported scopes, and unsupported scopes.

Diagnostic UI fields include raw process details, per-run traces, advisory Judge rationale, `completed_score`, detailed metric drill-down, and human-readable summaries unless a scoring or authorization policy explicitly promotes one of them to a policy input.

### 8.2 Partial, Stale, and Invalidated Scorecards

- Partial evaluation sets `authorization_readiness = partial` or `blocked` depending on missing dimensions and coverage policy. It cannot silently grant broader scope.
- Staleness is evaluated from `benchmark_scorecard.created_at`, release status, task retirement, and authorization freshness windows. A stale scorecard is not rewritten; later reuse belongs in change review/admission lineage.
- Scorecard-invalidating maintenance findings set invalidation status or create a superseding scorecard. Existing scorecards remain immutable and auditable.
- Release coverage remains a hard cap. Scorecard completion can narrow release support but cannot widen `benchmark_release.supported_authorization_scopes[]`.

## 9. API, Workflow, and Storage Integration

### 9.1 Model Extensions

`score_bundle` should expose:

- `scoring_semantics_version`;
- `run_outcome_class`, `score_state`, `failure_class`, `failure_taxonomy_version`, and `outcome_owner`;
- `raw_correctness_score`;
- `effective_correctness_score`;
- `process_score`;
- `risk_flags[]` and `authorization_blocking_risk_flags[]`;
- `authorization_eligible`;
- repeated-run group identity and trial summary when applicable;
- Judge contribution mode and score-basis Judge lineage;
- exact score input evidence refs, `score_input_evidence_digest`, and `evidence_trust_basis_digest`.

`benchmark_scorecard` should expose:

- `scoring_semantics_version`;
- `aggregation_algorithm`;
- complete `score_input_set_digest` and input-entry summary, including missing entries;
- `weighting_summary`;
- release and score denominators;
- `missing_run_summary`;
- `minimum_sample_summary`;
- `reliability_label`;
- `calibrated_policy_profile_id` or exact calibrated policy-profile refs when the scorecard used a calibrated profile;
- `repository_risk_profile_id` or exact risk-profile seed/ref/digest when appetite constraints affected scorecard policy inputs;
- `reliability_policy_version` when distinct from the scorecard policy;
- `completed_score` as diagnostic;
- policy-input versus diagnostic metric classification.

### 9.2 Command and Query Implications

`ComputeRunScore` must return the run outcome class, failure taxonomy, score state, `score_input_evidence_digest`, `evidence_trust_basis_digest`, Judge contribution mode, and `authorization_eligible`.

`GetRunScore` must return exact score identity. It must not infer "latest score for run" unless a read-model selection policy is named.

`GetBenchmarkScorecard` must return aggregate formula inputs: score input set identity, missing-run summary, denominator summary, weighting summary, reliability label, and policy-input classification. It must not select a scorecard by `benchmark_evaluation_id` alone.

`ListBenchmarkScorecards` may provide convenience filters but must preserve multi-result behavior unless the complete scorecard basis is supplied.

### 9.3 Workflow Invariants

`ScoreWorkflow` must:

- load exact sealed evidence bundle versions, not current/latest pointers;
- load canonical verification records by identity;
- classify scoreable versus non-scoreable terminal outcomes deterministically;
- compute repeated-run summaries before aggregate scorecard assembly;
- compute score weights from immutable release membership and policy versions;
- load calibrated policy-profile parameters and effective risk-profile constraints only by exact promoted profile/version reference;
- include missing and blocked entries in score input set identity;
- write new immutable records for recomputation instead of updating old score facts.

The control plane must reject or block aggregation that mixes tested-agent snapshots, benchmark releases, evaluation modes, adapter purity levels, capability envelopes, score policies, evidence trust bases, or score-contributing Judge lineages without an explicit governed comparison rule.

## 10. Audit Invariants

- A score or scorecard is reproducible from its stored identity, exact inputs, policy versions, evidence bundle versions, and deterministic weighting algorithm.
- A scorecard that used calibrated parameters is reproducible from its stored calibrated policy-profile ref, risk-profile ref/digest when used, and parameter digest.
- A scorecard can be invalidated, superseded, or made stale, but it is never edited in place.
- Missing-run and infra-failure facts are preserved in the score input set, not hidden in prose.
- Positive correctness requires trusted Barcarolle verification.
- Advisory Judge output is never a hidden policy input.
- Scorecard policy inputs are explicitly marked so `authorization_semantics_v1` can consume them without scraping diagnostic JSON.
