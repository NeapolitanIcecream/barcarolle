# Requirements Analysis: Repository-Specific Agent License

## 1. Project Intent

**Fact.** The abstract states that this project is about an “Agent 驾照” mechanism for software repositories. It aims to evaluate a code agent or LLM workflow on repository understanding, rule adherence, and regression-risk control, then support graded authorization based on the evaluation result. The research notes consistently frame the problem as repository-specific, history-grounded, replayable, and trust-oriented. Sources: [docs/draft/abstract.md](/Users/chenmohan/gits/barcarolle/docs/draft/abstract.md), [docs/research/repository-specific-benchmark-generation-related-work.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-specific-benchmark-generation-related-work.md), [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Inference.** The project is not just a benchmark builder. It is a repository-scoped evaluation and governance layer that records benchmark evidence and derives repository-specific trust or admission decisions for a complete agent configuration.

## 2. Target Users

**Fact.** The source materials point to evaluation of repository-level code agents and workflows, not a single model in isolation. That implies users who need to compare, certify, or govern complete agent setups. Sources: [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md), [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-evaluation-infrastructure-landscape.md)

**Inference.** The primary use cases are:

- agent-configuration and agent-framework developers who need a repository-specific evaluation environment for comparing complete agent setups;
- repository owners or maintainers who already have a trust relationship with the tested-agent owner and want quantitative evidence before adopting a new agent configuration;
- platform teams, research groups, companies, or open-source communities comparing agent configurations for a shared repository;
- auditors or governance reviewers who need to explain the evidence, scorecard, and admission history after a decision has been made.

## 3. Problem Definition

**Fact.** Existing public benchmarks are strong on issue-to-patch, PR mining, repository understanding, or execution harnesses, but they do not fully solve the problem of generating a replayable, graded benchmark for one arbitrary repository and one chosen agent workflow. Sources: [docs/research/repository-specific-benchmark-generation-related-work.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-specific-benchmark-generation-related-work.md), [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-evaluation-infrastructure-landscape.md)

**Fact.** The literature also shows that the evaluated object is usually the whole agent configuration, including model, prompt, tools, memory, runtime budget, and permissions. Source: [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Inference.** The core problem is to convert repository history and workflow artifacts into a trustworthy decision input: “How well does this specific agent configuration work in this repository-specific environment, and what evidence-backed admission or comparison result follows from that?”

**Inference.** A complete requirement set therefore needs two explicit benchmark-side capability themes in addition to generic task generation and scoring: a candidate-side `Golden Agent` capability that constructs trustworthy repository-specific reference artifacts for validation and review, and a run-side `Judge Agent` capability that interprets sealed benchmark evidence for scoring and governance without replacing deterministic validators, scorers, or policy controls.

**Requirement.** The primary product mode is trusted internal collaboration under low-adversarial assumptions: repository owners, benchmark operators, and the evaluated agent supply chain are expected to be governed and reviewable, but not cryptographically attested end to end. The system should still keep hard trust boundaries around benchmark evidence, scoring, and policy records so later adversarial or attested modes can layer on stronger guarantees without rewriting the core object model.

**Requirement.** The default operating scenario assumes aligned stakeholders rather than adversarial benchmark participants. In the expected first use cases, the repository owner and the ACUT owner are likely to be people or teams inside the same company, project, research group, or open-source community who share the goal of measuring whether a newly introduced agent can work well in that repository and how it compares with other agent configurations under the same repository-specific conditions. The design therefore treats declared or owner-attested ACUT metadata as usable policy input when the requested tier and target condition allow it, while still separating correctness-root evidence, immutable benchmark facts, scorecards, admissions, and operating-state projections so accidental overclaiming, drift, weak evidence, or later disputes remain auditable.

**Requirement.** The system is not optimized for hostile participants who intentionally try to cheat the benchmark, forge configuration identity, or turn a repository admission into adversarial certification. Strong adversarial operation, cryptographic attestation, and runtime enforcement can be added later as stricter modes over the same semantic boundaries. Their absence is a product-scope choice, not a claim that declarations or traces are sufficient for adversarial certification.

**Requirement.** The architecture documents define the complete system design. Concepts present in the architecture are part of the intended product semantics unless a later design change explicitly removes or replaces them.

**Requirement.** The system should distinguish three separate questions that are often collapsed in informal discussion:

- what immutable benchmark fact was observed;
- what repository-scoped admission or license was granted from that fact or from a later human change review;
- what agent snapshot is currently operating in the repository.

## 4. Key Usage Scenarios

### 4.1 Pre-admission evaluation

**Fact.** The project context explicitly mentions differentiated authorization and “持证上岗”.
**Inference.** Before an agent is allowed to touch a repository, the system should generate tasks from that repository’s history and measure whether the configuration can solve them without violating rules or causing regressions.

### 4.2 Regression-risk check after repository drift

**Fact.** The research emphasizes freshness, historical replay, and environment drift as recurring problems. Sources: [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md), [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Inference.** The system should be re-runnable when dependencies, CI, or repository structure change, so the trust signal stays current.

### 4.3 Compare agent configurations

**Fact.** The literature says prompt format, tool routing, retrieval quality, memory quality, and runtime budget can materially change results. Source: [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Inference.** The same repository benchmark should support side-by-side comparison of multiple configurations, not just a single score.

**Requirement.** The system should expose a canonical benchmark-instance key for comparison. The defensible comparison basis is an immutable benchmark release identity rather than an informal set of whichever approved tasks happened to be run.

### 4.4 Repository/module-specific access control

**Fact.** No reviewed source claims that repo-specific certification is already solved. Sources: [docs/research/repository-specific-benchmark-generation-related-work.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-specific-benchmark-generation-related-work.md), [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Inference.** A likely downstream use is scoped permissions, such as allowing one configuration to work only in a subset of modules or task classes.

### 4.5 Post-evaluation agent evolution review

**Fact.** The literature says the evaluated object is the whole agent configuration, and those configurations change materially when prompt, tools, memory, routing, or runtime budget changes. Source: [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Inference.** A repository owner needs a governed path for changes made after the original benchmark run. Re-running the full benchmark for every edit will often be too expensive, but silently treating every descendant configuration as equivalent would overstate what was actually tested.

**Requirement.** The system should support an append-only post-evaluation review path that can classify a later agent change as `carry_forward_acceptable`, `targeted_review_required`, `full_rebenchmark_required`, or another explicit governed outcome with human responsibility recorded.

## 5. Functional Requirements

### 5.1 Source ingestion

**Fact.** The research repeatedly uses commit history, issues, PRs, tests, CI, docs, and reviews as the raw material for benchmark construction. Sources: [docs/draft/abstract.md](/Users/chenmohan/gits/barcarolle/docs/draft/abstract.md), [docs/research/repository-specific-benchmark-generation-related-work.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-specific-benchmark-generation-related-work.md), [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md)

**Inference.** The system should ingest repository history and metadata sufficient to reconstruct candidate tasks, including at least commits, issues, PRs, tests, and environment files.

### 5.2 Replayable environment reconstruction

**Fact.** Environment replay is a core bottleneck in the literature, and historical fidelity depends on dependency/version reconstruction. Sources: [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md), [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Inference.** The system should reconstruct runnable historical environments or clearly record when it cannot, instead of silently accepting an approximate environment.

### 5.3 Task synthesis

**Fact.** Prior work derives tasks from issue/PR replay, feature tasks, CI failures, dependency breaks, and repository context selection. Sources: [docs/research/repository-specific-benchmark-generation-related-work.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-specific-benchmark-generation-related-work.md), [docs/research/replayable-repository-task-construction.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-context-selection-and-cross-file-editing.md)

**Inference.** The system should synthesize repository-specific tasks that are executable, graded, and tied to the repository’s own engineering history rather than generic prompts.

### 5.4 Golden and judge capabilities

**Inference.** The system should treat `Golden Agent` and `Judge Agent` as explicit benchmark-side capability surfaces rather than implicit by-products of task synthesis or score aggregation.

**Requirement.** `Golden Agent` should construct candidate-side reference artifacts, provenance, confidence markers, and review signals from repository-native evidence so validation and task approval can reason over stronger benchmark-side context without exposing answer-bearing material to the evaluated run.

**Requirement.** `Judge Agent` should consume sealed run evidence, verifier outputs, and optional Golden-derived artifacts to produce auditable, scoped findings that can inform scoring, review, retirement, and authorization workflows while remaining append-only and human-review-compatible.

**Requirement.** Deterministic validation, deterministic scoring, and authorization policy remain the primary authorities. Golden/Judge outputs should enrich those stages and surface ambiguity, not silently override them.

### 5.4a Benchmark admission rubric

**Requirement.** The system should expose executable benchmark-admission criteria before a candidate can become a certified task and before a release can support repository-agent authorization.

**Requirement.** Task admission should check provenance and `T_task`, faithful replay, bounded task scope, non-retrieval work, duplicate pressure, safety/permission mapping, oracle grade, required validation probes, flakiness/runtime limits, and future/answer leakage.

**Requirement.** Release admission should compute coverage by task family, component/path, capability, risk class, permission class, high-impact path class, oracle grade, duplicate cluster, flakiness/runtime, and recency, then publish both supported and unsupported authorization scopes.

**Requirement.** Confirmed future or answer leakage, no faithful replay, or a D-grade sole oracle should block certified task admission. Human review may resolve ambiguity or waive non-hard warnings, but it must not convert those hard failures into certified benchmark evidence.

### 5.5 Benchmark identity and publication

**Inference.** Repository-specific benchmarking needs a first-class benchmark object family, not only a registry of approved tasks. Otherwise the system cannot answer which benchmark a result used, whether two results share the same benchmark basis, or which task membership snapshot supported an authorization outcome.

**Requirement.** The system should define a stable benchmark identity that survives across refreshes, plus immutable benchmark-release snapshots that capture benchmark membership, publication time, and release provenance.

**Requirement.** Benchmark release identity should be the canonical answer for "same benchmark basis". Any digest or helper version may supplement it, but should not replace the stable release identifier.

**Requirement.** Benchmark refreshes should publish a new immutable release under the same benchmark identity rather than rewriting historical membership. Historical evaluations, scorecards, and authorization decisions should stay pinned to the release they used.

### 5.6 Evaluated agent identity

**Requirement.** The system should represent the evaluated subject as a first-class immutable tested-agent snapshot or equivalent evaluated-reference resource, not only as a bare `agent_configuration_id`.

**Requirement.** The tested-agent snapshot should capture the repository-relevant configuration state that can change benchmark meaning, including at least model/provider identity, prompt or policy digests, tool and permission profile, memory or retrieval strategy, runtime budget, and a stable external configuration reference when one exists.

**Requirement.** Every benchmark evaluation, child run, and benchmark scorecard should pin to that immutable tested-agent snapshot so the benchmark fact remains stable even if the live configuration later changes.

### 5.7 Post-evaluation change governance

**Requirement.** The system should support append-only change-review records that compare a later tested-agent snapshot against a previously evaluated or admitted snapshot.

**Requirement.** A change review should record:

- the baseline evaluated or admitted tested-agent snapshot;
- the candidate changed tested-agent snapshot;
- the benchmark evaluation, benchmark release, or scorecard fact that serves as the baseline evidence;
- the review outcome and required next action;
- the responsible human reviewer and review rationale.

**Requirement.** A change review may govern whether a later snapshot can carry forward an earlier benchmark result for a limited scope, but it must not mutate the original benchmark evaluation fact.

**Requirement.** Change governance must distinguish two independent delta classes:

- execution/fact-layer deltas, such as tool policy, network posture, runtime budget, or other capability-envelope changes that alter what it would mean to say the target agent was evaluated under those conditions;
- interpretation/authorization-layer deltas, such as coverage policy, task-family coverage requirements, trust thresholds, or scope rules that reinterpret existing evidence without changing the historical benchmark fact itself.

**Requirement.** Any later decision that continues using older benchmark evidence must carry an explicit evidence-lineage label. `fresh` means the supporting benchmark fact was obtained directly under the target conditions; `reused` means earlier evidence was accepted for bounded use without new target-condition execution; `supplemented` means earlier evidence was accepted only together with additional targeted validation or review. These labels must stay explicit and must not rewrite the original benchmark evaluation.

### 5.8 Repository admission/license and current operating state

**Requirement.** The system should model repository-agent admission or license as its own append-only record, distinct from both the immutable benchmark evaluation fact and the mutable current operating state.

**Requirement.** Admission or license applicability should be explicit across four axes:

- repository scope, such as whole repository, module subset, or task-family subset;
- benchmark basis, such as benchmark definition, release, or task-family slice;
- time, such as effective-from, review timestamp, expiration, or freshness boundary;
- agent-evolution state, such as exact tested snapshot or a later snapshot admitted through an explicit change review.

**Requirement.** The system should expose the current operating state separately so an operator can answer whether the snapshot now running in a repository is exactly the one benchmarked, a later carry-forward-approved descendant, pending review, or outside current admission.

### 5.9 Execution and verification

**Fact.** The reviewed systems rely on repository-native tests, builds, CI replay, or custom verifiers, and they treat execution outcomes as primary truth sources. Sources: [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md), [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-evaluation-infrastructure-landscape.md)

**Inference.** Each synthesized task should be runnable under a verifier with explicit pass/fail semantics, plus enough trace data to replay the run.

### 5.10 Trace capture and auditability

**Fact.** The research repeatedly highlights trajectories, command logs, event streams, and evaluation logs as necessary artifacts. Sources: [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-evaluation-infrastructure-landscape.md), [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md)

**Inference.** The system should keep per-task traces that let a maintainer inspect what the agent did, what it saw, and why the verifier passed or failed it.

### 5.11 Benchmark-level evaluation and graded output

**Fact.** The project abstract explicitly calls for graded authorization; the research suggests performance can vary by workflow, repository, and task family. Sources: [docs/draft/abstract.md](/Users/chenmohan/gits/barcarolle/docs/draft/abstract.md), [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Inference.** The output should be more than pass/fail. It should produce a benchmark-level evaluation of one agent configuration on one benchmark release, plus a benchmark scorecard or equivalent aggregate that can drive trust grades and authorization recommendations.

**Requirement.** Per-task runs may still exist for debugging, spot checks, or incremental execution, but they should be clearly secondary to a benchmark-level evaluation record and benchmark-level scorecard when the system is making cross-task comparisons or authorization decisions.

**Requirement.** Authorization and operator explanations should trace back to benchmark-release context and benchmark-level aggregate results, not only to a single per-task score.

**Requirement.** The system should define stable scoring semantics for per-run correctness, failure classes, process/risk/Judge contribution, task and oracle weighting, repeated-run stability, scorecard aggregation, evidence trust tiers, and score input set identity so `aggregate_score` is reproducible and safe to use as an authorization input.

**Requirement.** The trust-grade scale, evidence-basis gates, subject-applicability gates, explicit risk-appetite constraints, freshness windows, and downstream License-consumption behavior are closed as repository-scoped policy semantics in [docs/architecture/authorization-semantics.md](../architecture/authorization-semantics.md), while score computation and aggregate scorecard semantics are closed in [docs/architecture/scoring-semantics.md](../architecture/scoring-semantics.md). Score/coverage thresholds, score-weighting factors, coverage gates, reliability labels, and policy-version promotion must be governed by the automatic empirical calibration loop in [docs/architecture/policy-calibration.md](../architecture/policy-calibration.md). These semantics are product design assumptions, not claims made by the source literature.

### 5.12 Automatic policy calibration

**Requirement.** The system should automatically calibrate and validate authorization thresholds, score weighting factors, coverage gates, reliability labels, and policy-version promotion using objective repository evidence and controls.

**Requirement.** Normal calibration operation must not require human baselines, human labels, manual benchmark acceptance, or human participation in benchmark generation or benchmark running. Human review may inspect, annotate, pause, or roll back calibrated policy profiles as governance, but it must not be a required source of calibration truth.

**Requirement.** Acceptable calibration evidence includes repository historical fixes, merged PRs, known pre-fix states, no-op and mutation-based negative controls, retrieval-only or rule-based baselines, prior agent configurations, repeated-run variance, canonical verification records, release coverage, task-family/component/risk/high-impact slices, release-maintenance findings, and automatically computed sensitivity analyses.

**Requirement.** Calibration output should be a first-class versioned resource that can govern `authorization_semantics_v1` thresholds, scoring factors, coverage-policy gates, reliability-label rules, and promotion/rollback without rewriting historical scorecards, authorization decisions, admissions, or operating-state entries.

**Requirement.** The first release should include the policy-calibration object model and workflow surface. Calibration may begin from seed profiles while evidence accumulates, but the design should not remove breadth by deferring policy calibration to a loose note or manual spreadsheet.

### 5.12a Explicit repository risk profile

**Requirement.** The system should model repository or organization risk appetite as a first-class versioned policy input, not as an inference from benchmark scores, release coverage, or calibration evidence. Automatic calibration should optimize thresholds, score weights, coverage gates, reliability labels, and `G0` through `G5` authorization thresholds under the resolved risk profile's explicit tolerance constraints.

**Requirement.** A risk profile should support organization defaults, repository profiles, and narrower component/path overrides, with deterministic effective-profile resolution and persisted refs, versions, digests, inheritance basis, and constraint summaries on calibration runs, calibrated policy profiles, scorecards when scorecard policy changes, authorization decisions, admissions, and operating-state coverage entries.

**Requirement.** Risk profiles should be able to express maximum unsafe-control promotion rates, minimum control-separation margins, tier eligibility or forbidden-tier matrices, minimum coverage and reliability floors, evidence-basis and ACUT-binding requirements, freshness ceilings, required review triggers, and risk/cost objective weights by tier, permission class, risk class, task family, component/path, high-impact path class, target condition, evaluation mode, adapter purity, and evidence trust basis.

**Requirement.** A risk profile may tighten, block, or require review for future decisions, but it must not supply calibration truth, rewrite historical facts, convert unsupported release scopes into supported scopes, or become a Barcarolle runtime enforcement mechanism. Existing scorecards, authorization decisions, admissions, and operating-state entries should keep the exact risk-profile basis they used; stricter appetite changes should flow through impact preview, reauthorization, suspension, revocation, targeted validation, or full rebenchmarking as normal append-only policy outcomes.

## 6. Non-Functional Requirements

### 6.1 Reproducibility

**Fact.** Reproducibility and run-to-run stability are recurring concerns in the research. Sources: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md), [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md)

**Requirement.** Results should be replayable from stored artifacts, with clear versioning for repository state, environment state, task definition, benchmark release membership, and evaluation policy.

### 6.2 Trustworthiness

**Fact.** Benchmark leakage, weak oracles, and harness exploits are established risks. Source: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Requirement.** The system should separate the agent workspace from the verifier trust boundary and avoid relying on any artifact that the agent can directly tamper with.

**Requirement.** In trusted internal mode, human review and append-only governance records are the primary control for post-evaluation agent changes. The system should preserve enough integrity boundaries that a stricter future mode can require attested configuration capture, stronger supply-chain proofs, or more adversarial blind-review rules without changing the semantic distinction between benchmark fact, admission/license, and operating state.

### 6.3 Freshness

**Fact.** Several reviewed systems move toward live updates and rolling evaluation because static suites age quickly. Sources: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Requirement.** The evaluation set should be refreshable or regeneratable so it can reflect repository drift and new history.

### 6.4 Auditability

**Fact.** Process-level metrics and trajectory capture are a major theme in the literature. Sources: [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Requirement.** A human reviewer should be able to explain both a per-task score and a benchmark-level scorecard from stored traces, release membership, and benchmark-evaluation lineage, not just from a final aggregate number.

**Requirement.** A human reviewer should be able to explain why missing, unverified, canceled, infra-failed, verifier-flaky, policy-invalid, or blocked runs did or did not contribute to `aggregate_score`, coverage, reliability, and authorization readiness.

**Requirement.** A human reviewer should also be able to explain why a repository-agent admission exists, which exact tested-agent snapshot it applies to, whether a later operating snapshot was admitted by carry-forward review or full rerun, and who accepted responsibility for that decision.

## 7. Constraints and Risks

### 7.1 Historical leakage

**Fact.** Repo history can leak answers through future commits, PR text, linked issues, or searchable web artifacts. Source: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Risk.** If task generation reuses too much directly observable history, the benchmark may measure memorization or lookup rather than repository understanding.

### 7.2 Weak or misaligned oracles

**Fact.** Tests can be too narrow, too broad, or otherwise misaligned with intent. Source: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Risk.** A passing agent may still be behaviorally wrong, while a correct alternate implementation may be rejected.

### 7.3 Environment drift and replay failure

**Fact.** Dependency resolution, package availability, and CI state change over time. Source: [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md)

**Risk.** A task that was valid at extraction time may later become unreplayable or flaky.

### 7.4 Benchmark gaming

**Fact.** The research documents concrete exploit paths against shared-state evaluators and test runners. Source: [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md)

**Risk.** If the verifier or logs sit inside the agent’s control boundary, the agent may optimize the score instead of solving the task.

### 7.5 Overgeneralization

**Fact.** The literature warns that benchmark results differ by repository, task family, and workflow scaffold. Source: [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md)

**Risk.** A score on one repository or task family should not be over-read as a global agent capability claim.

## 8. Open Questions

The source material does not determine all implementation choices. The authorization-specific choices are fixed in [docs/architecture/authorization-semantics.md](../architecture/authorization-semantics.md); the remaining open questions are:

- whether the first release should support one repository, many repositories, or both;
- which artifact types are mandatory versus optional;
- how much human audit and governance review is required around task admission, release certification, policy override, and rollback outside the automatic calibration truth path;
- how benchmark releases should be scheduled or refreshed for long-lived repositories;
- how strict a future attested or adversarial operating mode should be beyond the trusted internal mode defined for this phase.

These are implementation assumptions, not facts from the sources. That uncertainty applies especially to the exact artifact schema and automation authority for `Golden Agent` and `Judge Agent`.

## 9. Source Traceability Summary

- [docs/draft/abstract.md](/Users/chenmohan/gits/barcarolle/docs/draft/abstract.md): project intent, agent-license framing, repository-level trust and authorization goal.
- [docs/research/replayable-repository-task-construction.md](/Users/chenmohan/gits/barcarolle/docs/research/replayable-repository-task-construction.md): executable task construction, replayability, validation, and suitable historical-change criteria.
- [docs/research/repository-context-selection-and-cross-file-editing.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-context-selection-and-cross-file-editing.md): repository understanding, context selection, dependency-aware editing, and process metrics.
- [docs/research/repository-evaluation-infrastructure-landscape.md](/Users/chenmohan/gits/barcarolle/docs/research/repository-evaluation-infrastructure-landscape.md): evaluation stack, harnesses, traces, and infrastructure concerns.
- [docs/research/agent-configuration-evaluation.md](/Users/chenmohan/gits/barcarolle/docs/research/agent-configuration-evaluation.md): whole-agent evaluation object, workflow sensitivity, and process-level metrics.
- [docs/research/benchmark-trustworthiness-risks.md](/Users/chenmohan/gits/barcarolle/docs/research/benchmark-trustworthiness-risks.md): contamination, leakage, weak oracles, harness exploits, and stability risks.
- [docs/research/environment-replay-and-reproducible-execution.md](/Users/chenmohan/gits/barcarolle/docs/research/environment-replay-and-reproducible-execution.md): historical environment reconstruction, replay fidelity, trace capture, and continuous maintenance.

## 10. Conclusion

The most defensible synthesis is that this project needs a repository-specific evaluation pipeline that mines repository history, reconstructs historical execution conditions, admits trustworthy tasks, publishes immutable benchmark releases from those admitted tasks, evaluates full agent configurations against those releases, and records enough evidence to justify a trust or permission decision. The literature supports each of those pieces separately, but not the full repository-scoped governance loop.
