# Requirements Analysis: Golden Agent and Judge Agent

## 1. Purpose and scope

This document turns the current proposal into explicit requirement themes for the repository-specific "Agent License" project. It extends the existing framing in `docs/draft/abstract.md` and `docs/analysis/requirements.md` by making `Golden Agent` and `Judge Agent` first-class capabilities rather than leaving them implicit inside benchmark generation or scoring machinery.

This is a requirements analysis document, not an architecture or governance decision record. It deliberately does **not**:

- lock a single implementation topology;
- require that either theme map to one model, one service, or one workflow step;
- assign final adjudication authority to automation alone.

Source basis: `docs/draft/abstract.md`, `docs/analysis/requirements.md`, `.orchestrator/phase.md`, `.orchestrator/subagents/phase_phase_20260421_golden_judge_integration__explore__requirements_analysis__20260421104300/orchestrator_readme.md`

## 2. Why the proposal needs explicit requirement themes

The current project framing already establishes four stable facts:

1. The project is repository-specific, not a generic coding benchmark.
2. The evaluation target is a full agent configuration, not a base model in isolation.
3. Trust depends on replayable tasks, executable verification, and auditable traces.
4. The end goal is graded authorization or repository-specific trust signaling, not raw benchmark ranking alone.

Those points are already present in the abstract, the existing requirements analysis, and the research corpus. What the proposal adds is a requirement-level separation between:

- the capability that creates and maintains repository-specific "gold" or reference evidence; and
- the capability that interprets that evidence to judge a candidate agent configuration or run.

That separation is justified by the corpus:

- benchmark-generation research shows that repository history, tests, CI, and execution replay can produce trustworthy evaluation artifacts, but only with strong provenance and replay controls;
- trustworthiness research shows that weak oracles, leakage, and shared-trust-boundary evaluators can invalidate judgments even when tasks look realistic;
- agent-evaluation research shows that the object being judged is the whole workflow, including prompt, tools, memory, permissions, and runtime policy.

Source basis: `docs/research/replayable-repository-task-construction.md`, `docs/research/repository-specific-benchmark-generation-related-work.md`, `docs/research/environment-replay-and-reproducible-execution.md`, `docs/research/benchmark-trustworthiness-risks.md`, `docs/research/agent-configuration-evaluation.md`

## 3. Problem definition

The problem is not just "generate repository tasks" and not just "score an agent." The project needs a repository-scoped trust workflow that answers:

- what repository-grounded evidence should count as "gold" for evaluating a candidate workflow here;
- how that evidence can be built and maintained without leaking answers or silently degrading;
- how a candidate agent configuration should be judged against that evidence;
- how those judgments can support graded authorization without over-claiming automation authority.

Public prior work only partially covers this. Existing benchmark lines provide strong building blocks for task mining, environment replay, execution harnessing, and trajectory capture, but the research corpus consistently shows four gaps that matter directly here:

- repo-specific benchmark generation is still immature relative to fixed shared benchmarks;
- benchmark validity is fragile under provenance leakage, weak tests, and evaluator compromise;
- most public evaluations still under-specify the full agent configuration as the judgment target;
- public systems rarely map benchmark outcomes into repository- or module-scoped trust decisions.

Source basis: `docs/draft/abstract.md`, `docs/analysis/requirements.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/benchmark-trustworthiness-risks.md`, `docs/research/agent-configuration-evaluation.md`

## 4. Theme definitions

### 4.1 Golden Agent

`Golden Agent` is the requirement theme for the capability that produces and maintains the repository-specific "gold" used for trustworthy evaluation.

In scope for this theme are capabilities such as:

- deriving tasks from repository history and workflow artifacts;
- constructing or preserving executable reference states, hidden verifiers, and quality labels;
- extracting canonical context, expected behaviors, or intermediate evidence where that improves evaluation quality;
- attaching provenance, replayability, and confidence metadata to the resulting artifacts.

This definition does **not** require that the project ship one literal autonomous "golden" model. The requirement is that this capability exist explicitly in the system design and data model.

### 4.2 Judge Agent

`Judge Agent` is the requirement theme for the capability that evaluates a candidate agent configuration or run against repository-specific gold artifacts and produces an auditable judgment.

In scope for this theme are capabilities such as:

- consuming benchmark evidence, execution traces, verifier outputs, and policy criteria;
- judging success, risk, scope, and confidence for a candidate workflow;
- producing scores, findings, and authorization recommendations suitable for governance workflows;
- escalating uncertain or underspecified cases for human review instead of masking them.

This definition does **not** require that the Judge Agent be the sole or final authority. The requirement is that repository-specific judgment be explicit, evidence-based, and governance-compatible.

## 5. Functional requirements

### 5.1 Golden Agent requirements

| ID | Requirement |
|---|---|
| `GOLD-1` | The system MUST treat Golden Agent as an explicit capability for constructing and maintaining repository-specific gold artifacts, not as an implicit by-product of generic benchmark generation. |
| `GOLD-2` | Golden Agent outputs MUST be grounded in repository-native evidence where available, including commits, issues, PRs, tests, CI/build artifacts, docs, and review history, rather than generic prompt-only task synthesis. |
| `GOLD-3` | Golden Agent MUST preserve provenance and temporal boundaries for every gold artifact so the system can distinguish pre-task evidence from post-task or answer-leaking evidence. |
| `GOLD-4` | Golden Agent MUST support executable evaluation artifacts, including replayable environments, verifier definitions, or equivalent reference checks; when faithful replay is not achievable, it MUST mark the artifact as lower-trust or exclude it from high-trust evaluation. |
| `GOLD-5` | Golden Agent SHOULD produce intermediate evidence where useful, such as localization hints, canonical context, expected state transitions, or process labels, because the research corpus shows final patch pass/fail alone is too weak for trustworthy judgment. |
| `GOLD-6` | Golden Agent MUST emit artifact-quality metadata, including reproducibility status, oracle strength, leakage risk, freshness status, and any known caveats. |
| `GOLD-7` | Golden Agent SHOULD support multiple repository task families over time, such as issue/PR replay, CI or environment failures, dependency breakage, and feature or refactor tasks, because the corpus shows no single task family is sufficient to represent repository trust. |
| `GOLD-8` | Golden Agent MUST make its outputs inspectable and reusable by downstream evaluation logic instead of embedding unrecoverable decisions inside opaque prompts or transient runtime state. |

Source basis: `docs/research/replayable-repository-task-construction.md`, `docs/research/repository-specific-benchmark-generation-related-work.md`, `docs/research/environment-replay-and-reproducible-execution.md`, `docs/research/repository-context-selection-and-cross-file-editing.md`, `docs/research/benchmark-trustworthiness-risks.md`

### 5.2 Judge Agent requirements

| ID | Requirement |
|---|---|
| `JUDGE-1` | The system MUST treat Judge Agent as an explicit capability for repository-specific evaluation and judgment, not as a thin wrapper around raw test pass/fail. |
| `JUDGE-2` | Judge Agent MUST evaluate the full candidate agent configuration or run context, including model, prompt, tools, memory, permissions, runtime policy, and control loop, because the corpus shows these factors materially change outcomes. |
| `JUDGE-3` | Judge Agent MUST consume both outcome evidence and process evidence, including verifier outputs, traces, context selection behavior, localization behavior, and execution history, when those signals are available. |
| `JUDGE-4` | Judge Agent MUST be able to produce scoped judgments, such as per-repository, per-module, per-task-family, or per-risk-surface findings, instead of only a single undifferentiated global score. |
| `JUDGE-5` | Judge Agent MUST report uncertainty, missing evidence, benchmark-quality caveats, and irreproducibility conditions explicitly rather than converting them into unjustified confidence. |
| `JUDGE-6` | Judge Agent MUST support comparison across candidate configurations and across benchmark refreshes so the system can reason about drift, regression, and relative trust. |
| `JUDGE-7` | Judge Agent MUST produce outputs that can feed graded authorization or trust decisions, while remaining compatible with human review and policy controls outside the judging step. |
| `JUDGE-8` | Judge Agent SHOULD surface rationale in a form that links judgments back to the underlying artifacts, traces, and policy-relevant evidence. |

Source basis: `docs/research/agent-configuration-evaluation.md`, `docs/research/repository-context-selection-and-cross-file-editing.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/benchmark-trustworthiness-risks.md`

### 5.3 Common requirements

| ID | Requirement |
|---|---|
| `COMMON-1` | The system MUST keep Golden Agent and Judge Agent explicit in requirements, interfaces, and data flows even if later implementation chooses to co-locate or partially share infrastructure. |
| `COMMON-2` | The system MUST remain repository-specific: trust claims and evidence produced for one repository or repository area MUST NOT be assumed to generalize automatically to another. |
| `COMMON-3` | The system MUST version repository state, environment state, benchmark artifacts, and evaluation runs so that both gold construction and judging remain replayable. |
| `COMMON-4` | The system MUST preserve audit artifacts sufficient for post-hoc review, including provenance, commands or tool events, verifier results, and judgment outputs. |
| `COMMON-5` | The system SHOULD support refresh and maintenance because the corpus shows static public suites degrade quickly under contamination and ecosystem drift. |
| `COMMON-6` | The system MUST support human governance for benchmark disputes, Golden/Judge artifact review, and high-impact trust decisions, while automated benchmark generation/running and automatic policy calibration remain operable without human acceptance as a required truth source. |

Source basis: `docs/draft/abstract.md`, `docs/analysis/requirements.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/environment-replay-and-reproducible-execution.md`, `docs/research/benchmark-trustworthiness-risks.md`

## 6. Quality and governance requirements

These are cross-cutting constraints on both themes.

| ID | Requirement |
|---|---|
| `QG-1` | The system MUST control provenance leakage. Gold construction and judging must avoid using future commits, leaked gold patches, web-discovered answers, or equivalent answer-revealing signals unless those are explicitly modeled as contamination findings. |
| `QG-2` | The system MUST treat oracle quality as a first-class concern. Weak, narrow, wide, or gameable tests must be detectable, recorded, and reflected in confidence or benchmark eligibility. |
| `QG-3` | The system MUST separate the evaluator trust boundary from the agent-under-test as far as practical, because shared-state evaluation enables reward hacking and harness compromise. |
| `QG-4` | The system MUST support repeated execution, variance tracking, or equivalent stability controls for claims that influence graded trust. |
| `QG-5` | The system MUST preserve provenance and version identity for both gold artifacts and judging logic so later comparisons remain interpretable. |
| `QG-6` | The system MUST support governance-compatible outputs, including evidence for approval, denial, restriction, or escalation, rather than assuming a single binary permit/deny workflow. |
| `QG-7` | The system MUST allow high-impact decisions to remain reviewable and overridable by human policy owners, because the corpus does not support fully autonomous final adjudication as a mature practice. |

Source basis: `docs/research/benchmark-trustworthiness-risks.md`, `docs/research/environment-replay-and-reproducible-execution.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/agent-configuration-evaluation.md`

## 7. Evaluation requirements

The project needs evaluation requirements for both the candidate agent workflow and the Golden/Judge capability surfaces themselves.

| ID | Requirement |
|---|---|
| `EVAL-1` | The evaluation stack MUST measure final task outcomes and intermediate process signals where available, including context selection, localization, planning, execution, and verification behavior. |
| `EVAL-2` | Golden Agent outputs MUST be evaluated on benchmark yield, replayability, oracle quality, leakage resistance, and maintenance status, not only on how many tasks are produced. |
| `EVAL-3` | Judge Agent outputs MUST be evaluated on agreement with verifiable outcomes, calibration under uncertainty, quality of rationale, and suitability for scoped trust decisions. |
| `EVAL-4` | Evaluation reports MUST include cost, runtime, and resource-policy context, because the literature shows these are outcome-relevant parts of the tested workflow. |
| `EVAL-5` | Evaluation reports MUST support per-repository, per-module, and per-task-family breakdowns when the benchmark corpus can support them. |
| `EVAL-6` | Evaluation procedures SHOULD support repeated-run summaries or equivalent uncertainty reporting for any result used in graded authorization. |
| `EVAL-7` | Evaluation outputs MUST remain auditable enough that a human reviewer can reconstruct why a judgment was reached and whether benchmark quality limited that judgment. |

Source basis: `docs/research/agent-configuration-evaluation.md`, `docs/research/repository-context-selection-and-cross-file-editing.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/benchmark-trustworthiness-risks.md`

## 8. Non-goals and deferred decisions

The current proposal and corpus do **not** justify resolving the following in this document.

### 8.1 Explicit non-goals

- Defining a single implementation topology for Golden Agent or Judge Agent.
- Requiring one model, provider, prompt stack, or runtime for either theme.
- Declaring that Judge Agent is the final authority for admission, merging, or permissions.
- Declaring that Golden Agent must generate every benchmark artifact autonomously without human review.
- Treating one public benchmark family or one task family as sufficient for repository trust.
- Collapsing repository-specific trust into a universal cross-repository license.

### 8.2 Deferred decisions

- implementation details for the calibrated policy profiles that govern threshold parameters inside the already-defined trust-grade semantics;
- repository-specific refinements to the mapping from benchmark outcomes to permission scopes beyond the current authorization semantics;
- how much manual review is required before gold artifacts are accepted outside the automatic policy-calibration path;
- whether first release deployment targets one repository at a time or a multi-repository control plane;
- the final artifact schema used to exchange gold evidence, traces, and judgments;
- the final operational placement of human review in the workflow.

These are deferred because the corpus supports them as design questions, but does not settle them as requirements facts.

## 9. Traceability summary

| Requirement area | Proposal linkage | Corpus linkage |
|---|---|---|
| Explicit Golden Agent theme | The current phase brief requires Golden Agent to become a formal, explicit capability rather than implicit implementation detail. | Benchmark-generation, replay, and trustworthiness notes show the need for an explicit gold/reference-construction capability. |
| Explicit Judge Agent theme | The current phase brief requires Judge Agent to become a formal, explicit capability without fixing final authority. | Agent-configuration and evaluation-infrastructure notes show that judgment must target the full workflow and remain auditable. |
| Common replay/audit requirements | Existing requirements already require replayability, trace capture, and graded output. | Environment replay and infrastructure notes show that versioning and audit trails are foundational, not optional. |
| Governance and human-review boundary | The proposal boundary explicitly says not to hard-code Golden/Judge as sole final admission authority. | Trustworthiness research shows that weak oracles, leakage, and evaluator compromise require explicit governance surfaces; automatic policy calibration remains a separate objective-evidence loop. |
| Scoped trust outputs | The abstract and existing requirements frame the project as repository-specific graded authorization. | Research gaps show current public systems rarely support repository/module/task-type trust outputs, which makes this a necessary project-level requirement. |

Primary sources referenced above: `docs/draft/abstract.md`, `docs/analysis/requirements.md`, `.orchestrator/phase.md`, `docs/research/agent-configuration-evaluation.md`, `docs/research/replayable-repository-task-construction.md`, `docs/research/repository-context-selection-and-cross-file-editing.md`, `docs/research/repository-evaluation-infrastructure-landscape.md`, `docs/research/environment-replay-and-reproducible-execution.md`, `docs/research/benchmark-trustworthiness-risks.md`, `docs/research/repository-specific-benchmark-generation-related-work.md`

## 10. Conclusion

The defensible requirement-level interpretation of the proposal is:

- `Golden Agent` must exist as an explicit capability theme for producing trustworthy repository-specific gold/reference artifacts.
- `Judge Agent` must exist as an explicit capability theme for evaluating candidate agent workflows against that gold and producing auditable, scoped trust judgments.
- both themes must remain replayable, auditable, leakage-aware, and governance-compatible;
- neither theme should be over-specified yet as a fixed topology or sole final authority.

That framing is consistent with the current project intent and with the strongest patterns in the research corpus.
