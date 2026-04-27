# Golden Agent and Judge Agent Governance

## Status

Proposed on 2026-04-21.

## Scope and alignment

This memo defines the governance rules for two optional benchmark-side agents:

- `Golden Agent`: produces reviewable reference artifacts for a benchmark candidate or validation path on the trusted side before task approval.
- `Judge Agent`: reads sealed benchmark evidence and produces structured review outputs about run quality, policy risk, and comparison to trusted references.

This decision does not replace the current benchmark-governance direction already established in the architecture:

- the evaluated object is the full agent configuration, not only a base model;
- benchmark evidence remains append-only and tied to the canonical resource chain;
- validation, scoring, and authorization stay on separate trust boundaries;
- task approval, retirement, supersession, and revocation remain explicit lifecycle actions;
- repository-native or deterministic verifiers remain the primary correctness oracle.

Where this memo makes an assumption because the product shape is not yet locked, it states that explicitly and defers the schema or automation detail.

## Context

The current design already supports repository-scoped benchmark governance through approved tasks, replay environments, sealed evidence bundles, score bundles, and authorization decisions. The open question is how to use `Golden Agent` and `Judge Agent` without collapsing those boundaries.

The research corpus supports three important constraints:

- benchmark trustworthiness degrades when hidden answers, verifier logic, and agent-writable state share a boundary;
- whole agent configurations must be versioned and compared as workflows, not as model names;
- weak oracles, contamination, non-mergeable changes, or permission-impacting ambiguity must be blocked, quarantined, repaired, retired, or routed to governance instead of becoming normal benchmark truth.

## Decision summary

- Treat `Golden Agent` and `Judge Agent` as first-class, separately versioned agent configurations under governance, not as implicit helper prompts.
- Keep both agents outside the evaluated agent's writable workspace and outside the hot authorization path.
- Allow `Golden Agent` to use trusted benchmark-side inputs, including hidden post-fix or review data, but never expose its outputs to the evaluated run.
- Allow `Judge Agent` to read only sealed evidence, trusted reference artifacts, and policy/scoring context by manifest reference, never live sandbox state.
- Require append-only audit records for every Golden/Judge run, including input manifests, output artifacts, configuration identity, and reviewer or override lineage.
- Keep repository-native verifier results and deterministic scoring primary. Golden/Judge outputs are advisory unless a later decision explicitly expands their authority.
- Keep normal benchmark admission and calibration on automated policy gates. Human governance can annotate, pause, roll back, override, or own exceptional policy decisions, but it is not normal benchmark-acceptance truth.
- Roll out both agents in shadow and advisory modes before any narrower, explicitly approved automation scope.

## Role definition and trust boundaries

### Golden Agent

`Golden Agent` exists to create benchmark-side reference material that improves comparison and review. It may generate one or more of:

- a candidate reference patch or change summary;
- a reference file set or dependency set;
- a task rationale or decomposition;
- a stronger review rubric for what a good solution should preserve or avoid.

`Assumption`: the exact artifact set is not locked yet. The governance rule is that every Golden output is a trusted-side reference artifact, not the benchmark truth by itself.

Golden-specific boundary rules:

- It runs on the candidate/validation side once a task candidate, replay context, and trusted benchmark-side inputs are available; it may inform validation and review before task approval.
- It may read hidden benchmark-side material, including the human fix or review history, if that access is necessary for reference construction.
- Its outputs must stay in trusted evidence storage and must not be mounted into the evaluated agent sandbox.
- A Golden artifact may inform comparison and review, but it may not silently replace the repository-native verifier or approve a task by itself.

### Judge Agent

`Judge Agent` exists to evaluate sealed run evidence after execution. It may produce:

- structured quality findings about the submitted patch or trajectory;
- comparison notes against the task contract and any approved Golden artifact;
- risk tags such as likely leakage, weak-oracle suspicion, non-mergeable patch shape, or scope violation;
- a recommendation to accept a specific score-bundle or scorecard basis, escalate to review, or route the task/run to repair or retirement review.

Judge-specific boundary rules:

- It reads sealed evidence bundles, verifier outputs, task metadata, and trusted reference artifacts by manifest reference only.
- It does not read from live sandbox paths, executor-local state, or mutable workspace mounts.
- It may recommend score or policy review, but it may not directly publish benchmark membership changes or effective authorization decisions.
- When Judge output conflicts with the deterministic verifier, the result is `needs_review`, not silent override.

## Auditability requirements

Golden and Judge outputs must fit the existing audit chain rather than create a parallel one. At minimum, each run must record:

- `assessor_configuration_id` for the Golden or Judge configuration;
- prompt, tool, memory, runtime-budget, and permission-profile digests;
- model or external service version identifiers;
- task, environment, run, score, and decision references used as inputs;
- manifest references and checksums for every input and output artifact;
- `request_id`, `correlation_id`, `causation_id`, `schema_version`, and contract version;
- reviewer actions, overrides, supersession, and retirement links where applicable.

Golden/Judge artifact refs must also carry stable controlled-read semantics:

- sensitivity classification;
- redaction state;
- audience scope for full reads;
- blind-safe status;
- summary-safe metadata for default read surfaces.

Golden artifacts and Judge reports should be stored as append-only evidence artifacts linked to `candidate_generation_run`, task/candidate, run, score, or decision records until a dedicated artifact schema is justified.
Non-blind-safe Golden/Judge artifacts should default to summary-only expansion on general validation, scoring, and operator read surfaces unless the caller holds the required audience and sensitive-artifact permission.

No cleanup rule should remove the manifest or lineage for a Golden/Judge artifact that influenced a score, review, retirement, or authorization outcome.

Admission-review lineage is written by the validation/governance review workflow for annotation, pause, override, rollback, repair ownership, or exceptional policy ownership. Normal task approval still requires automated policy admission; governance review references do not become benchmark-acceptance truth. Governed-assessor promotion, demotion, and rollback are internal governance workflow operations owned by `GovernedAssessorWorkflow`; they remain append-only and reviewer-attributed rather than ad hoc metadata edits.

## Versioning policy

Both agents must be versioned as governed configurations, not as free-form prompts.

The minimum version boundary for each release is:

- model identifier and provider version;
- system prompt and rubric digest;
- tool surface and permission profile;
- retrieval or memory strategy digest, if present;
- runtime budget and retry policy;
- scoring-policy version and policy version visible to the agent;
- output schema version.

Versioning rules:

- New assessor configurations are registered through a backend-owned write path that normalizes the material fields and recomputes `configuration_fingerprint`.
- The natural key is `repository_scope + assessor_kind + configuration_fingerprint`; re-registering the same normalized configuration is idempotent.
- Any change to one of the fields above creates a new `assessor_configuration_id`.
- Comparisons must be run against a frozen task slice and the same replay/evidence conditions whenever practical.
- Production uses a champion/challenger model: one pinned active version per repository scope, plus explicit challenger runs before promotion.
- Promotions, demotions, and rollbacks are append-only lifecycle events tied to reviewer identity and rationale.

The system should expose a stable governed assessor configuration read lineage for both Golden and Judge, including:

- configuration identity and assessor kind;
- version digests and output schema version;
- governance state such as candidate, shadow, advisory, active, superseded, or rolled back;
- predecessor/supersession lineage;
- comparison-baseline lineage;
- promotion-review linkage and comparison summary refs.

## Comparison protocol

Golden and Judge versions should be compared differently because they serve different functions.

### Golden Agent comparison

Compare candidate Golden versions on a frozen candidate-side adjudication set, including reconstructible approved and non-approved outcomes where reviewable, using:

- reviewer acceptance rate for produced reference artifacts;
- usefulness to later governance review, measured by reduced reviewer time or fewer unresolved ambiguities;
- discriminative value, measured by how often the artifact helps explain differences between test-passing but behaviorally different solutions;
- stability across reruns on the same task slice;
- contamination or overfitting risk discovered during review.

### Judge Agent comparison

Compare candidate Judge versions on a frozen adjudication set with known objective outcomes, deterministic verifier results, control outcomes, and optional historical governance annotations using:

- agreement with objective accept, escalate, reject, quarantine, or repair outcomes;
- precision and recall on high-cost findings such as leakage suspicion, non-mergeable patch shape, or weak-oracle flags;
- rate of harmful false positives, especially recommendations that would incorrectly block or downgrade a run;
- rate of harmful false negatives, especially missed leakage or missed policy-risk cases;
- explanation quality, measured by whether reviewers can trace the recommendation back to sealed evidence quickly.

For both agents, live shadow evaluation on new tasks should continue after offline comparison so the system can detect drift before promotion.

## Governance Boundaries

Normal benchmark admission, benchmark generation/running, and policy calibration remain automated. Human governance is reserved for these non-truth-bearing or exceptional cases:

- annotating, pausing, overriding, rolling back, or owning an exceptional policy path for benchmark tasks that are not normal calibration evidence;
- accepting a new Golden artifact family into active governance workflows;
- first use of Golden or Judge in a repository, module, or task family;
- any Golden or Judge disagreement with deterministic verifier results;
- any recommendation that could grant, deny, revoke, or narrow effective repository permissions;
- contamination, leakage, flakiness, or weak-oracle suspicions;
- retirement, repair, supersession, or revocation actions driven partly by Golden/Judge output.

These governance actions may change lifecycle state or require repair, but they do not label calibration truth and do not manually accept generated benchmarks for normal admission. Ambiguous, leaky, weak, unsafe, or unreplayable cases remain excluded, blocked, quarantined, retired, or routed to exceptional governance.

## Measurable value

Neither agent is justified by novelty alone. Each one must show repository-governance value beyond the existing verifier and review flow.

### Golden Agent value

Golden is valuable only if it improves benchmark governance in measurable ways such as:

- reducing reviewer time to understand whether a run is meaningfully correct;
- increasing the rate at which semantically wrong but test-passing outputs are detected;
- improving consistency of review outcomes across reviewers;
- helping identify tasks that should be repaired or retired because the current oracle is too weak.

### Judge Agent value

Judge is valuable only if it improves post-run governance in measurable ways such as:

- catching leakage, weak-oracle, or non-mergeable-output cases earlier than governance review alone;
- reducing review effort without increasing harmful authorization errors;
- producing stable recommendations across reruns and nearby task variants;
- surfacing repository-specific policy or scope violations that final-pass metrics hide.

Shared rule:

- reported value must include both benefit and cost, including reviewer time, runtime cost, latency added to benchmark publication, and downstream override rate.
- no promotion should rely only on aggregate agreement; promotion should also inspect the small number of highest-cost disagreements.

## Rollout strategy

Use a four-stage rollout for both agents.

This rollout governs Golden/Judge assessor exposure and reviewer trust in their outputs. It is not the automatic policy-calibration loop for authorization thresholds, score weights, coverage gates, or reliability labels; that loop is defined separately and does not rely on human baselines as calibration truth.

### Stage 0: Offline backfill

- Run Golden on historical candidate-side adjudication sets that include reconstructible non-approved outcomes where reviewable.
- Run Judge on sealed evidence sets with known objective outcomes and optional historical governance annotations.
- Build adjudication sets and reviewer-readiness checks before any production exposure.

### Stage 1: Shadow mode

- Run both agents on live benchmark traffic.
- Store outputs as evidence artifacts only.
- Do not show them as default operator inputs and do not let them affect score or policy state.

### Stage 2: Advisory mode

- Show outputs in the review queue and run-detail views.
- Allow reviewers to mark outputs useful, incorrect, incomplete, or unsafe.
- Continue to require workflow-owned machine-checkable transitions for benchmark and authorization state changes; human action is limited to governance annotations, pause, rollback, override, or exceptional policy ownership.

### Stage 3: Narrowly scoped automation

- Permit limited workflow shortcuts only where historical evidence shows low-risk benefit.
- Example scope: automatic review prioritization or draft retirement suggestions.
- Do not allow direct permission grants or revocations based solely on Golden/Judge output.

Any move beyond Stage 3 requires a new decision memo with repository-scoped evidence that the narrower automation is reliable and auditable.

## Explicitly deferred

This memo intentionally does not decide:

- the final artifact schema for Golden outputs or Judge reports;
- whether Golden should generate one reference patch, multiple candidate references, or only structured rubrics;
- whether Judge should be a single model, a debate/committee pattern, or a hybrid deterministic plus learned system;
- whether Golden/Judge outputs should contribute numeric score components rather than review metadata only;
- cross-repository thresholds for promotion, since value and risk are expected to vary by repository and task family;
- fully automated permission grants, denials, revocations, or task publication based only on Golden/Judge output;
- self-training or automatic prompt updates from reviewer feedback;
- a dedicated persistence resource type beyond the current evidence and lifecycle records.

## Consequences

This decision keeps Golden and Judge useful without letting them undermine the benchmark's core trust story. They can improve comparison, review efficiency, and benchmark maintenance, but only if their own configurations are versioned, audited, compared, and human-governed with the same rigor as the agents they help evaluate.
