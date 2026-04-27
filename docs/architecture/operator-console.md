# Operator Console Architecture

## 1. Purpose

This document defines the operator console for repository owners and platform operators who need to inspect repository-specific benchmark state, review evidence, and act on authorization outcomes. It translates the existing repository/task/release/evaluation/run/evidence/decision architecture into a user-facing control surface without changing the underlying resource model in:

- `docs/architecture/system-design.md`
- `docs/architecture/module-design.md`
- `docs/architecture/benchmark-admission-rubric.md`
- `docs/architecture/scoring-semantics.md`
- `docs/architecture/policy-calibration.md`
- `docs/architecture/interface-contracts.md`
- `docs/architecture/data-model.md`
- `docs/architecture/api-schema.md`
- `docs/architecture/workflow-runtime.md`

The frontend baseline remains the inherited React + Next.js + TanStack Query stack from `docs/decisions/dependency-selection.md` and `docs/decisions/module-dependencies.md`. This document does not lock a component kit, charting library, or live-stream transport.

## 2. Design principles

### 2.1 Repository-first navigation

The console should treat one repository as the primary decision boundary. Global views exist for operators, but every actionable item should resolve back to a repository, task, run, or authorization record.

### 2.2 Preserve the audit chain

The UI may group states into simpler labels for comprehension, but it must retain the canonical resource chain:

`repository_snapshot -> candidate_generation_run -> task_candidate -> replay_plan -> replay_environment -> validation_result -> task -> benchmark_definition -> benchmark_release -> benchmark_release_membership -> tested_agent_snapshot -> benchmark_evaluation -> evaluation_run -> run_submission -> evidence_bundle -> canonical_verification_record -> score_bundle -> benchmark_scorecard -> authorization_decision -> repository_agent_admission -> repository_agent_operating_observation -> repository_agent_operating_state`

Policy calibration is a sidecar audit chain over those immutable facts:

`repository_risk_profile + benchmark_release + canonical_verification_record + score_bundle + benchmark_scorecard + controls/baselines + maintenance findings -> policy_calibration_run -> calibrated_policy_profile -> future scorecards and authorization decisions`

The UI may still group adjacent stages for comprehension, but the detail view for each stage should expose the raw lifecycle state, provenance, and cross-links to the upstream and downstream records.
Golden/Judge summaries should appear as attached candidate-generation, validation-, and score-side overlays on that chain, not as a separate parallel navigation model.
Benchmark-admission rubric outputs should appear on the existing task, validation, release, review, retirement, scorecard, decision, admission, and operating-state views. The console must not present Golden/Judge findings or human review records as normal task approval, benchmark acceptance, calibration truth, or authorization authority.
Post-evaluation agent changes should appear as an append-only governance overlay on that chain: `tested_agent_snapshot (baseline) + tested_agent_snapshot (candidate) -> agent_change_review -> repository_agent_admission -> repository_agent_operating_observation -> repository_agent_operating_state`.
License certificates, signed status records, status receipts, and consumer audit events hang off the admission and operating-state coverage chain: `repository_agent_admission + repository_agent_operating_state.coverage_entries[] -> license_certificate -> license_status_record/log -> license_status_receipt / license_consumption_audit_event`. Every benchmark, run, scorecard, decision, admission, certificate, status, receipt, audit, and operating-state view should show ACUT identity, evaluation mode, adapter purity, ACUT identity field evidence basis, run observation basis when present, canonical verification basis, evidence trust-tier basis, score input set identity, denominator/missing-run basis, and reliability label so operators do not confuse native-agent results with `Agent + Harness` results, with fully trusted runtime-boundary verification, or with partial/incomplete scorecards.
Every scorecard and decision view should also show the exact calibrated policy-profile ref or seed profile and the effective risk-profile ref/digest used for weighting, coverage, reliability, and authorization thresholds.
UI labels should describe the default runtime boundary as the Runner Integration Layer, not as an agent framework.

### 2.3 Prefer workflow-aware actions over optimistic UI

The write APIs are synchronous command submissions that hand work off to asynchronous workflows. The console should therefore present actions as "request and monitor" flows, not as immediate local mutations.

### 2.4 Separate read concerns from control concerns

Inspection-heavy workflows should not require the same privileges as mutation-heavy workflows. The console should support rich read-only audit paths even when the user cannot approve tasks, start runs, or override decisions.

### 2.5 Load large evidence lazily

Evidence manifests are queryable control-plane records, while large artifacts live in external blob storage. The console should browse manifests and summaries first, then fetch raw logs, patches, or verifier outputs on demand.

## 3. Personas

| Persona | Primary questions | Primary actions |
| --- | --- | --- |
| Repository owner | Can this agent configuration be trusted here, and under what scope? | Review repository health, inspect approved tasks, compare configurations, review scores, accept or reject authorization outcomes, initiate refresh or reevaluation. |
| Platform operator | Which workflow is stuck, failed, flaky, or unreplayable? | Monitor queue-visible work, inspect run and environment failures, cancel or retry runs, track evidence completeness, escalate retirements or policy review. |
| Auditor or governance reviewer | Why was access granted, denied, or revoked? | Inspect immutable evidence, score rationale, policy version, and supersession history without requiring run-operation privileges. |

Repository owners are the default primary audience. Platform operators need broader cross-repository visibility, and auditors need deep read paths with minimal mutation ability.

## 4. Information architecture

### 4.1 Top-level areas

The console should expose six top-level areas:

1. `Repositories`
   Repository index and repository-centric workspaces. This is the default landing area for owners.
2. `Review Queue`
   Cross-repository governance queue for annotation, pause, override, rollback, repair ownership, exceptional policy decisions, suspected leakage, weak or borderline oracle grades, high-risk release coverage, ambiguous validation failures, Golden low-confidence cases, Judge escalations, retirement/invalidation review, or decision overrides. Normal task/release materialization remains an automated policy-admission result.
3. `Runs`
   Cross-repository operational surface for active, recent, failed, or flaky evaluation runs.
4. `Policy Calibration`
   Active, shadow, blocked, superseded, and rolled-back policy profiles plus calibration run history, sensitivity analyses, and impact previews.
5. `Risk Profiles`
   Organization, repository, and component/path risk-appetite profiles, effective-profile resolution, lifecycle transitions, and impact previews.
6. `Decisions`
   Current effective authorization decisions plus superseded and revoked history.

Evidence should not be a standalone top-level area. It is meaningful only in the context of a run, task, environment, or decision.

### 4.2 Repository workspace model

Each repository workspace should group information into seven stable subareas:

- `Overview`
  Freshness, active decision, benchmark coverage, recent run health, and open review items.
- `Snapshots`
  Repository snapshots and intake provenance.
- `Tasks`
  Task candidates, approved tasks, replay readiness, and retirement status.
- `Benchmarks`
  Benchmark definitions, immutable releases, release memberships, tested-agent snapshots, benchmark evaluations, and scorecards.
- `Runs`
  Repository-scoped evaluation history for one or more tested-agent snapshots or upstream agent configurations.
- `Policy`
  Effective risk profile, active calibrated policy profile, calibration impact, risk-profile transitions, and repository-specific policy blockers.
- `Decisions`
  Effective and historical authorization outputs, repository admissions, and current operating-state summaries by repository or narrower scope.

This layout follows the state boundaries in `docs/architecture/module-design.md`: catalog state, derived signal state, replay state, runner-integration state, submission state, canonical-verification state, evidence state, benchmark state, and policy state stay conceptually separate even when the UI presents them side by side.

### 4.3 Core cross-links

The console should preserve these navigation links everywhere:

- snapshot -> candidate-generation runs and candidate/task(s) derived from that snapshot
- task candidate -> candidate-generation run when present, `T_task`, admission hard-gate summary, queryable leakage severity/handling/surfaces plus exact leakage report, oracle-profile draft, replay plan/environment/validation results, Golden summaries if present, plus approved task or rejection/retirement/repair record
- task -> source candidate, approved replay plan/environment, validation status, and benchmark releases that include it
- benchmark definition -> releases published under that stable benchmark line
- benchmark release -> immutable membership snapshot, release coverage profile, supported/unsupported authorization scopes, benchmark evaluations, scorecards, and downstream decisions
- risk profile -> effective repository scope, parent/override chain, constraint digest, calibration runs, truth-observation summaries, calibrated policy profiles, scorecards/decisions/admissions using the profile, impact previews, and transition history
- calibrated policy profile -> calibration run, evidence manifest, sensitivity analysis, impact preview, scorecards/decisions that used the profile, supersession, rollback, and active/shadow state
- tested-agent snapshot -> benchmark evaluations, change reviews, repository admissions, and current operating-state records that reference it
- benchmark evaluation -> child runs, ACUT identity, evaluation mode, adapter purity, per-run score bundles, benchmark scorecards, tested-agent snapshot, and same-benchmark comparison context
- run -> run submission, exact evidence bundle versions, canonical verification record, evidence trust-tier summary, Judge summary if present, exact per-run score bundles with score input evidence digests, run outcome class, score state, failure class, parent benchmark evaluation, and downstream authorization decision
- decision -> supporting benchmark scorecard, benchmark release, release coverage profile, unsupported-scope reason codes, tested-agent snapshot, ACUT identity, evaluation mode, adapter purity, calibrated policy-profile basis, risk-profile basis, canonical verification basis, `score_input_set_digest`, `evidence_trust_basis_digest`, denominator summary, missing-run summary, minimum-sample summary, reliability label, evidence trust-tier basis, run set, task scope, policy version, invalidation refs, and any linked Golden/Judge review artifacts
- policy calibration run -> input manifest, truth-observation manifest, objective controls, baseline runs, evidence slice coverage, excluded slices, unsafe false-positive metrics, high-tier authorization control power, held-out validation metrics, sensitivity analysis, candidate profiles, selected profile, promotion gates, and blocker codes
- repository-agent admission -> supporting benchmark fact or change review, admitted snapshot, evaluation mode, adapter purity, canonical verification basis, evidence trust-tier basis, effective scope, explicit supersession chain, and current operating-state rows that rely on it
- operating state -> current snapshot, backend-resolved coverage entries across effective admissions, selected/default evaluation mode, selected/default adapter purity, adapter manifest digest when present, target-condition bases, ACUT identity field evidence-basis summary, run observation-basis summary, canonical verification basis, evidence trust-tier basis, latest change review, latest operating observation, and any required next action such as targeted review or full re-benchmark

## 5. Screen map

| Screen | Purpose | Primary data |
| --- | --- | --- |
| `Repository index` | Find repositories and see which ones need attention. | repository summary, latest snapshot, effective decision, open review counts, run health summary |
| `Repository overview` | Summarize benchmark posture for one repository. | repository metadata, freshness signal, active decision, current benchmark release, benchmark coverage, recent runs, pending reviews |
| `Snapshot detail` | Inspect one repository snapshot and its provenance. | repository snapshot, imported artifact refs, extraction status, downstream candidates |
| `Task candidate detail` | Inspect draft/validated candidate before automated approval, repair, governance routing, or retirement. | task candidate, candidate-generation run and exact Golden output evidence-bundle version when present, source anchor, `T_task`, source refs, allowed/disallowed inputs, expected artifacts, admission hard-gate summary, leakage severity/handling/surfaces and exact report digest/ref, oracle profile/probes, context refs, replay plan, replay environment summary, latest validation result, automated admission result, review state, approval/history records, Golden summary if present, governance actions |
| `Task detail` | Inspect an approved benchmark task across replay, release-membership, run, and retirement state. | task, source candidate, approved replay plan, approved replay environment, approval validation result, release membership list, run list, retirement markers |
| `Benchmark definition detail` | Inspect one stable repository benchmark line and its release history. | benchmark definition, scope, latest release pointer, historical releases, refresh history |
| `Benchmark release detail` | Inspect one immutable benchmark publication snapshot. | benchmark release metadata, release-membership snapshot, release coverage profile, supported/unsupported authorization scopes, oracle-grade distribution, duplicate-cluster caps, leakage clearance, publication rationale, related benchmark evaluations, scorecards |
| `Tested-agent snapshot detail` | Inspect one immutable evaluated-reference or operating snapshot. | tested-agent snapshot digests, ACUT manifest, evaluation mode, adapter purity, adapter manifest, run-environment declaration, ACUT field evidence-basis map, provenance, related benchmark evaluations, change reviews, admissions, operating-state links |
| `Benchmark evaluation detail` | Inspect one tested-agent snapshot evaluated against one benchmark release. | benchmark evaluation status, child-run coverage, release basis, capability-envelope contract basis, ACUT identity, evaluation mode, adapter purity, adapter manifest, ACUT field evidence-basis summary, benchmark scorecard reference list with each scorecard's `aggregate_score`, diagnostic completed score, `score_input_set_digest`, `evidence_trust_basis_digest`, denominator/missing-run summaries, scorecard policy, coverage policy, evaluated capability envelope, reliability label, and Judge lineage, comparison context, evidence-lineage label (`fresh` for direct benchmark facts) |
| `Repository runs` | Filter runs for one repository or configuration. | run summaries, status filters, tested-agent snapshot filter, evaluation-mode filter, adapter-purity filter, optional agent-configuration filter, score bundle reference list; any selected summary must display the read-model selection policy |
| `Run queue` | Global operator view of active/recent/failed runs. | evaluation runs across repositories, queue state, status, started/finished times |
| `Run detail` | Deep inspection of one evaluation run. | run summary, parent benchmark evaluation and release-membership refs when present, ACUT identity, evaluation mode, adapter purity, adapter manifest, observation boundary, ACUT identity field evidence-basis summary, separate run observation-basis panel, run submission, canonical verification record, exact evidence bundle versions and content digests, evidence trust-tier panel, artifact refs, verifier outputs, Judge summary if present, governed Judge configuration lineage if present, run outcome class, score state, failure class/outcome owner, score bundle reference list with score input evidence digests, decision links; any selected score summary must display the read-model selection policy |
| `Agent change review detail` | Inspect one post-evaluation carry-forward decision. | baseline snapshot, candidate snapshot, baseline/candidate ACUT field evidence-basis summaries, field-basis delta, structured condition-delta classification, supporting benchmark fact, explicit target-condition basis, evaluation mode, adapter purity, canonical verification basis, evidence trust-tier basis, evidence-lineage label, review outcome, applicability boundaries, reviewer rationale |
| `Policy calibration index` | Browse calibration runs and policy profiles. | active/shadow profile by repository scope, calibration status, target policy families, promotion gate result, last activation, blocked profiles, rollback history |
| `Risk profile index` | Browse effective and historical appetite profiles. | organization/repository scope, active profile, inherited parent, risk tolerance class, constraint digest, lifecycle state, pending transitions, open impact previews |
| `Risk profile detail` | Explain one repository or organization risk profile. | scope, parent/override chain, constraint digest/ref, tier constraint matrix, unsafe-control budgets, coverage/reliability/evidence floors, freshness ceilings, review triggers, external-consumer assumptions, lifecycle transitions, affected calibration runs, profiles, scorecards, decisions, admissions, and operating-state entries |
| `Policy calibration run detail` | Inspect one automatic calibration run. | calibration input manifest digest/ref, truth-observation manifest digest/ref, effective risk-profile ref/digest, risk constraints, evidence slice coverage, excluded slices, automatic controls, baseline runs, repeated-run variance, canonical verification coverage, release coverage, unsafe false-positive metrics, high-tier authorization control power, parameter authority summary, risk-budget consumption, candidate profiles, selected profile, sensitivity analyses, impact previews, promotion gates, blocker codes |
| `Calibrated policy profile detail` | Explain one threshold/weight/coverage/reliability profile. | semantic policy family, exact policy-version fields, risk-profile ref/digest, parameter digest/ref, applicability slices, validation metrics, sensitivity summary, risk-budget consumption, impact preview, lifecycle state, activation/supersession/rollback history, scorecards and decisions using the profile |
| `Review queue` | Human governance worklist for annotations, pauses, rollbacks, overrides, repair ownership, and escalations. | suspected future/answer leakage, B-oracle high-impact use, C/D oracle findings, ambiguous validation failures, release unsupported-scope or high-risk coverage reviews, Golden low-confidence cases, Judge escalations, agent change reviews, targeted-review requests, retirement/invalidation reviews, policy override requests |
| `Decision index` | Browse effective and historical authorization outputs. | authorization decisions, repository admissions, signed License certificates/status, receipts, and consumer audit status filtered by repository, scope, trust tier, status |
| `Decision detail` | Explain one authorization decision and its supersession history. | decision record, scope, policy version, calibrated policy-profile ref/digest, risk-profile ref/digest and gate result, rationale, supporting benchmark scorecard including scoring semantics version, aggregation algorithm, `aggregate_score`, diagnostic completed score, coverage-policy basis, reliability-policy basis, `score_input_set_digest`, `evidence_trust_basis_digest`, denominator summary, missing-run summary, minimum-sample summary, reliability label, benchmark release, release coverage profile, supported/unsupported-scope summary, tested-agent snapshot, evaluation mode, adapter purity, ACUT field evidence-basis summary, canonical verification basis, evidence trust-tier basis, evidence-lineage label, invalidation refs, linked runs/tasks, governed Golden/Judge configuration lineage when relevant |
| `Repository admission detail` | Inspect one repository-scoped license/admission record. | admitted snapshot, supporting decision or change review, explicit target-condition basis, risk-profile basis, evaluation mode, adapter purity, ACUT field evidence-basis summary, canonical verification basis, evidence trust-tier basis, evidence-lineage label, effective window, freshness deadline, admission lifecycle sequence, consumer certificate/status profile, latest signed certificate ref/digest, latest status ref/watermark, certificate validity, status freshness, supersession history, linked operating-state views |
| `Operating state detail` | Inspect what snapshot is currently running and whether it is covered. | current snapshot, aggregate coverage state, drift state, selected/default evaluation mode, selected/default adapter purity, adapter manifest digest, `coverage_entries[]` table by target-condition basis, ACUT identity field evidence-basis summary, run observation-basis summary, canonical verification basis, evidence trust-tier basis, evidence-lineage label, admission lifecycle sequence, certificate availability, latest status watermark, linked admissions, latest change review, next required action |
| `License certificate detail` | Inspect one signed consumer certificate. | certificate id/digest, signature and issuer key status, schema version, certificate validity timestamps, admission and operating-state refs, coverage entry, lifecycle sequence, operating-state version, target-condition basis, capability envelope, freshness state, status surface ref, latest status watermark, matching diagnostics, evidence refs |
| `License status detail` | Inspect signed lifecycle status for a certificate. | status id/digest, lifecycle state, status sequence/watermark, signature and status-signing-key status, certificate-signing-key status, suspend/revoke/expire/supersede transition, effective timestamp, published timestamp, status freshness, consumer deny-after timestamp, superseding refs, receipt coverage |
| `Consumer audit detail` | Inspect how an external consumer used a License. | consumer identity/version, requested scope/operation/risk/target-condition/capability/snapshot, certificate id/digest, status id/digest/watermark, signature verification result, lifecycle sequence, event watermark, result, reason codes, local policy overlay result, stale/read-failure details, linked admission and operating-state coverage entry |

The run detail screen is the deepest inspector in the product. It is where owners verify that a score is credible and where operators diagnose whether a failure belongs to environment replay, runner integration, submission, canonical verification, verifier logic, Judge assessment, scoring classification, or policy mapping. It must warn when evidence is weak (`patch_only`), trace-only (`trace_submission`), observation-boundary-limited (`observed_run`), harness-contaminated (`harness_native` / `Agent + Harness`), unverified, incomplete, infra-failed, verifier-flaky, or missing from the scorecard denominator.

## 6. Key workflows

### 6.1 Pre-admission evaluation

1. Repository owner enters the repository workspace and checks the current effective decision and task coverage.
2. The owner reviews candidate tasks or approved tasks linked to the current repository snapshot.
3. The owner selects a benchmark release for the repository and starts a benchmark evaluation for a selected ACUT against that immutable release basis, with visible evaluation mode and adapter purity.
4. The console moves to run monitoring rather than assuming immediate completion.
5. After scoring completes, the owner inspects the benchmark scorecard, release basis, run submissions, canonical verification records, evidence trust-tier basis, and resulting authorization decision.
6. If the decision is acceptable, the repository owner may issue or confirm a repository-agent admission for that tested-agent snapshot; if not, the owner requests more runs, narrower scope, carry-forward review, or denial. The console should treat admission effectivity as backend-resolved, with one effective admission per `repository_id + scope + target_condition_basis_identity` rather than a client-side guess. The UI may show multiple effective admissions for the same repository/resource scope only when their target-condition bases or authorization dimensions differ, and the operating-state detail must render those as separate `coverage_entries[]` instead of selecting one as the whole truth.
7. After admission effectivity, the console exposes the signed License certificate/status profile, latest certificate digest, certificate validity, latest status watermark, status freshness, and certificate availability for each coverage entry. Operators can copy identifiers or inspect status state, but the UI must not present certificate issuance or status publication as Barcarolle runtime enforcement of downstream actions.

### 6.2 Refresh after repository drift

1. A newer snapshot or drift marker appears in the repository overview.
2. The owner or operator compares the latest snapshot with the snapshot behind the current effective decision.
3. The console highlights which benchmark release, tasks, replay environments, or prior decisions are potentially stale.
4. The user requests candidate regeneration, release publication, or reevaluation against a newer release.
5. The console tracks the new benchmark evaluation and presents the new decision as superseding, not overwriting, the earlier decision.

### 6.3 Post-evaluation agent evolution review

1. A repository owner or operator opens the current operating-state detail and sees that the current snapshot or target-condition boundary has diverged from the last exact evaluated or admitted basis.
2. The console shows the baseline tested-agent snapshot, the candidate current snapshot or changed target-condition boundary, baseline/candidate ACUT identity field evidence-basis summaries, evaluation mode, adapter purity, canonical verification basis, evidence trust-tier basis, the supporting benchmark fact, and any existing repository admission.
3. The reviewer records an append-only change review with outcome such as `carry_forward_acceptable`, `targeted_review_required`, or `full_rebenchmark_required`, plus structured classification for execution-condition, ACUT field evidence-basis, and interpretation/authorization deltas and the explicit target-condition basis under review.
4. If carry-forward is accepted for the requested scope, the console shows the new repository-agent admission, the appended operating observation if one was recorded, and the refreshed operating-state coverage entries derived from those facts, including every target-condition basis and whether the accepted evidence is `reused` or `supplemented`.
5. If targeted review or full re-benchmark is required, the console keeps the operating-state drift visible until the required follow-up is completed.

### 6.3a Risk appetite change

1. A repository owner or governance reviewer opens the risk profile detail and creates a new candidate profile or activates an inherited organization profile for the repository scope.
2. The console shows the parent/override chain, normalized constraint digest, forbidden-tier matrix, coverage and reliability floors, freshness ceilings, required review triggers, and external-consumer assumptions before transition.
3. On activation, pause, rollback, or supersession, the console routes the command through `RiskProfileGovernanceWorkflow` and shows the effective-selection effect.
4. The console then tracks triggered impact previews, policy calibration runs, reauthorization decisions, admission suspension/revocation reviews, targeted-validation requirements, or full-rebenchmark requirements as separate workflow results.
5. Existing scorecards, decisions, admissions, and operating-state entries continue to display their original risk-profile basis. The UI must not relabel old facts as if the new appetite had been in force.

### 6.4 Failed or flaky run triage

1. A platform operator enters the global run queue and filters to `failed`, `canceled`, or suspiciously unstable runs.
2. The operator opens run detail and checks the coarse run timeline before loading heavy artifacts.
3. The operator classifies the issue as replay failure, runner-integration failure, submission failure, canonical-verification failure, Judge escalation, deterministic task rejection, or transient infrastructure problem.
4. If the failure is transient and permissions allow it, the operator retries or restarts the run.
5. If the problem is deterministic, the operator escalates to task retirement, replay repair, or policy review instead of repeatedly rerunning the same failure.

### 6.5 Candidate governance and retirement review

1. A reviewer enters the governance queue and opens a task candidate detail page.
2. The reviewer inspects the source anchor, `T_task`, allowed/disallowed inputs, expected artifacts, task-quality hard gates, oracle grade and validation probes, replay plan/environment, latest validation result, review state and approval history, any Golden summary, leakage severity/handling/surfaces, exact leakage report digest/ref, and contamination flags.
3. Normal task materialization happens only through an automated policy-admission result. The reviewer can annotate, request repair/revalidation, pause an exceptional path, record an override rationale, or retire it with cause and evidence links; those governance records do not supply calibration truth.
4. The resulting task or retirement record remains linked to the original candidate so the audit trail stays intact.

### 6.5a Release certification governance

1. A reviewer opens a benchmark release draft that needs governance attention.
2. The console shows release coverage by task family, component/path, capability, risk class, permission class, high-impact path class, oracle grade, duplicate cluster, flakiness/runtime, recency, and leakage clearance.
3. Automated release certification computes supported authorization scopes and unsupported scopes. The reviewer can annotate, request targeted task generation, request repair, pause publication, or record an exceptional diagnostic-only publication rationale.
4. Once published, the release coverage profile is immutable. Later findings create retirement, invalidation, or superseding-release records rather than editing the old release.

### 6.6 Audit and explanation

1. An auditor or repository owner opens a decision detail page.
2. The console shows the effective scope, trust tier, policy version, rationale summary, and supersession chain.
3. The reviewer drills down to the supporting benchmark scorecard, immutable benchmark release, any Judge summary attached to contributing per-run scores, then to the source runs, run submissions, canonical verification records, evidence bundle, `candidate_generation_run`, and candidate-side Golden artifacts if relevant.
4. The console preserves raw states and timestamps so the reviewer can explain not just what was decided, but why and from which evidence.
5. For consumer-facing audits, the reviewer can drill from admission to signed certificate, status record/log, receipt, and consumer audit event, verifying signature status, certificate validity, status freshness, lifecycle sequence, status watermark, target-condition/capability matching result, local policy overlay, and stale/read-failure reason codes.

### 6.7 Policy calibration audit

1. A platform operator opens the policy calibration index and selects a repository or scope.
2. The console shows the active calibrated profile, shadow profiles, blocked candidates, superseded profiles, and rollback history.
3. The operator opens a calibration run and inspects the input manifest, truth-observation manifest, objective controls, baseline runs, unsafe false-positive metrics, high-tier control power, held-out slice metrics, repeated-run variance, sensitivity analysis, and impact preview.
4. The console lets authorized governance users start a calibration run, request a shadow impact preview, annotate a profile, pause a profile, or record a rollback. It must not present human acceptance as a required calibration label or manual benchmark-acceptance step.

## 7. Permission-aware UI behavior

The console should authorize by capability and resource scope, not by route alone. The exact human-login framework is intentionally deferred, so the frontend assumption is only that the session can resolve a user identity plus repository- and scope-level capabilities from the backend.

| Capability class | UI behavior |
| --- | --- |
| Repository read | Can view repository, snapshot, task, run, score, and decision summaries. |
| Sensitive evidence read | Can open raw logs, patches, transcripts, and any artifact marked sensitive or redacted-aware. |
| Candidate governance | Can annotate, request repair/revalidation, record overrides, or retire task candidates when lifecycle state permits; cannot supply normal benchmark acceptance truth. |
| Run execution | Can start evaluation runs for allowed repositories, tasks, and agent configurations. |
| Run operation | Can cancel, retry, or reopen operationally relevant runs when state permits. |
| Decision review | Can view scoped decisions and rationale history. |
| Decision override | Can issue or confirm override-style authorization actions, always with explicit rationale capture. |
| License consumption audit read | Can view signed certificate/status details, receipts, and consumer audit events for scoped repositories. |
| Policy calibration governance | Can start calibration runs, request shadow impact previews, pause or roll back calibrated profiles, and annotate governance rationale without supplying calibration labels. |

The UI should follow these rules:

- Hide routes only when the user lacks any read permission for the resource. Otherwise prefer visible-but-disabled actions with a reason.
- Gate actions by both capability and backend lifecycle state. A user with `run operation` still cannot cancel a terminal run or approve a candidate that has already been retired.
- Treat repository scope as first-class. A user may be able to operate on repository `A` but only view repository `B`.
- Treat sensitive artifacts separately from summary evidence. A user may see that a transcript exists without being able to load the raw transcript.
- Require a rationale input for any override, revocation, or retirement action because the backend persists append-only business records rather than destructive updates.

`Inference`: repository owners and operators will sometimes overlap, but the console should not assume they are the same person or carry the same privileges.

## 8. Frontend state boundaries

### 8.1 Server state

The following should be treated as server state owned by backend APIs and cached through TanStack Query:

- repository summaries and repository detail data
- snapshot lists and snapshot detail
- task candidate lists/detail and approved task lists/detail
- replay plan, replay environment, and validation-result lists/detail
- admission review lists/detail and compliance state where the backend exposes them
- tested-agent snapshot lists/detail, agent change review lists/detail, repository-admission lists/detail, signed License certificate/status detail/list, status receipts, License-consumption audit events, and current operating-state detail
- evaluation run lists/detail, run submissions, and canonical verification records
- score and authorization decision records, including attached Golden/Judge summaries or artifact refs when present
- policy calibration runs, calibration truth observations, calibrated policy profiles, unsafe false-positive summaries, high-tier control-power summaries, sensitivity summaries, and impact previews
- governed Golden/Judge configuration lineage and promotion/comparison summaries when present
- evidence manifests and artifact metadata

The frontend should not maintain its own durable copy of these objects outside query caches. Mutations should invalidate or refetch affected resources rather than locally fabricating the new canonical state.

### 8.2 Local UI state

The following should stay local to the page or URL:

- filters, sort, pagination cursor, selected repository/tested-agent/admission scope, evaluation mode, adapter purity, and evidence trust tier
- selected tab or drawer
- evidence panel expansion state
- diff mode, artifact viewer mode, and comparison baseline choice
- draft form inputs for commands such as "start run" or "approve candidate"

Shareable inspection state such as filters and selected comparison baseline should live in the URL. Non-shareable view state such as panel width or disclosure state can remain local.

### 8.3 Command state

Because mutating APIs hand work off to workflows, each write action should create short-lived command state in the client:

- generated idempotency key
- submitted payload summary
- returned resource handle
- last observed status
- last error code if the command or workflow failed

This command state should disappear once the canonical resource query reflects the terminal outcome.

### 8.4 Live progress state

The console should assume polling:

- poll `GetCandidateGenerationRun`, `ListCandidateGenerationRuns`, `GetTaskCandidate`, `ListReplayPlans`, `ListReplayEnvironments`, and `ListValidationResults` while admission work is still in progress
- poll `GetEvaluationRun` and `ListEvaluationRuns` for active run state
- poll `GetEvidenceBundle` when new artifacts are expected
- poll decision detail while an authorization workflow is still `proposed`
- poll `GetPolicyCalibrationRun` while calibration is gathering evidence, generating controls, running baselines, fitting profiles, or validating profiles

The console should not require a websocket or SSE transport because live-stream transport is still deferred in the dependency memo. If streaming is added later, it should update the same query cache rather than introducing a separate competing state model.

## 9. API usage assumptions

### 9.1 Query and command shape

The console assumes the command/query vocabulary already defined in `docs/architecture/interface-contracts.md` and `docs/architecture/api-schema.md`:

- queries such as `GetCandidateGenerationRun`, `ListCandidateGenerationRuns`, `GetTaskCandidate`, `ListTaskCandidates`, `GetAdmissionReviewRecord`, `ListAdmissionReviewRecords`, `GetTask`, `ListTasks`, `GetReplayPlan`, `ListReplayPlans`, `GetReplayEnvironment`, `ListReplayEnvironments`, `GetValidationResult`, `ListValidationResults`, `GetTestedAgentSnapshot`, `ListTestedAgentSnapshots`, `GetAgentChangeReview`, `ListAgentChangeReviews`, `GetRepositoryAgentAdmission`, `ListRepositoryAgentAdmissions`, `GetRepositoryAgentOperatingState`, `GetEvaluationRun`, `ListEvaluationRuns`, `GetBenchmarkScorecard`, `ListBenchmarkScorecards`, `GetRunScore`, `ListRunScores`, `GetPolicyCalibrationRun`, `ListPolicyCalibrationRuns`, `GetCalibratedPolicyProfile`, `ListCalibratedPolicyProfiles`, `GetAuthorizationDecision`, `GetEvidenceBundle`, `GetGovernedAssessorConfiguration`, and `ListGovernedAssessorConfigurations`
- commands for candidate-generation-run reservation/completion, candidate approval/retirement, replay planning, environment build/validation, tested-agent snapshot registration, agent change review, repository admission, operating-observation record, runner invocation/cancel, run submission, canonical verification, scoring, risk-profile governance, policy calibration, calibration truth-observation reads, calibrated profile transition, and authorization

`GetValidationResult`, exact `GetRunScore`, and scorecard/score list views should be able to surface attached Golden/Judge artifact refs or summaries when those capabilities were used, without requiring separate top-level UI resource types. Non-blind-safe Golden/Judge refs should default to summary-only presentation unless the viewer has the required audience and sensitive-evidence access.

The frontend may use composed read models for convenience, but those read models should resolve back to canonical resources instead of inventing new persistent entities.

### 9.2 Async mutation contract

The console assumes every mutating command:

1. accepts an idempotency key;
2. returns a resource handle and current status quickly;
3. reaches terminal business state later through workflow completion.

This means action flows should route users toward the resulting detail page or queue item immediately after submission.

### 9.3 Status handling

The API schema and interface contracts expose detailed lifecycle values such as:

- candidate/task lifecycle values, including the candidate-side phases from `Draft` through `Approved`, the non-terminal `RepairRequired`, terminal `Rejected`, `Retired`, and `Failed`, and the task-side states `Approved` or `Retired`
- validation admission verdict values such as `certify`, `reject`, `needs_review`, and `repair_required`, review-state values `not_required`, `pending`, `approved`, `rejected`, `repair_required`, `waived_warning`, and `retired`, plus oracle-grade labels, leakage finding severities, and leakage handling decisions
- run phases from `queued` through `invoking_runner`, `awaiting_submission`, `evidence_ingesting`, `canonically_verifying`, and `completed`, plus `failed` and `canceled`
- benchmark release publication phases such as `draft`, `published`, `superseded`, and `retired`
- release certification values such as `certified`, `diagnostic_only`, `needs_review`, and `rejected`
- benchmark scorecard availability once aggregate scoring completes
- scoring values such as run outcome class, score state, aggregate score, completed score, reliability label, denominator summary, missing-run summary, and score input set identity
- policy calibration values such as calibration run status, profile lifecycle state, promotion gate result, sensitivity blocker, and impact-preview status
- risk profile values such as risk-profile lifecycle state, effective-selection effect, constraint digest, risk-budget blocker, and triggered recalibration or reauthorization status
- decision phases from `proposed` through `effective`, plus `superseded` and `revoked`

The UI may group these into broader labels like `Needs review`, `In progress`, or `Terminal`, but detail screens should preserve the raw API value for traceability.

### 9.4 Pagination and filtering

List screens should assume cursor-based pagination plus shared filters such as:

- `repository_id`
- `task_id`
- `run_id`
- `agent_configuration_id`
- `evaluation_mode`
- `adapter_purity_level`
- `evidence_trust_tier`
- `repository_risk_profile_id`
- `risk_profile_digest`
- `status`
- time-window filters
- sort and order

This keeps repository-local and cross-repository views consistent.

### 9.5 Artifact access

The console should assume evidence manifests arrive inline, while heavy artifact bodies arrive by `content_ref` and may require a signed URL or backend proxy. Artifact viewers should therefore:

- render manifest metadata first
- fetch artifact bodies only when opened
- tolerate late-arriving append-only evidence
- distinguish "artifact exists but access denied" from "artifact missing"
- default Golden/Judge artifacts to summary-only when they are marked non-blind-safe or restricted to narrower review audiences
- display evidence subject type/id, producer, source class, trust tier, digest, redaction state, evidence bundle manifest version/content digest, and whether the artifact is score-contributing
- display ACUT identity field evidence-basis values separately from run observation basis so declared native-agent metadata is not confused with adapter-observed, third-party-attested, or Barcarolle-trusted snapshot facts

Mode and trust labels should use the stable values `patch_only`, `trace_submission`, `observed_run`, `harness_native`, `A0_transport_only`, `A1_environment_wrapper`, `A2_tool_mediation`, `A3_harness_native_controller`, `trusted_barcarolle_evidence`, `adapter_observed_evidence`, `agent_submitted_evidence`, `third_party_evidence`, `declared`, `adapter_observed`, `third_party_attested`, and `barcarolle_trusted`.

### 9.6 Error handling

The UI should map structured domain errors into three user-facing classes:

- deterministic business rejection such as `task_rejected`, `validation_failed`, or `permission_denied`
- retryable infrastructure failure such as `environment_build_failed` when marked retryable
- unexpected internal failure that still preserves a traceable subject identity

This distinction matters because operators need different next actions for "try again", "retire this task", and "investigate the platform".

## 10. Non-goals and boundaries

This document intentionally does not define:

- the visual design system or component library
- a charting package
- a real-time streaming transport
- public or external-user authentication flows
- host-infrastructure operations dashboards unrelated to repository/task/run/decision control

Those choices belong in later design work after the first real evidence-dense workflows are proven.
