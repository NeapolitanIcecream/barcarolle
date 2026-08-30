# Research Improvement Backlog

Last reviewed: 2026-08-30.

Status: active. The current objectives and experiment design are in
[`research-program.md`](research-program.md); the supporting evidence is in
[`literature-review.md`](literature-review.md).

The earlier task-selection-only ledger is preserved in dated experiment
reports, especially
[`experiments/2026-08-05-research-phase-summary.md`](experiments/2026-08-05-research-phase-summary.md),
and in Git history. Its results remain valid under their original protocols;
its roadmap and metric priority have been superseded.

## First Principle

Barcarolle exists to provide reliable evaluation methods for self-evolving
agents. Repository-level coding agents are the first concrete domain. The
evaluation object includes a frozen agent snapshot, each parent-to-child
transition, and the complete agent lineage produced by a declared agent
optimizer, feedback policy, task stream, budget path, state policy, and seed.

The three numerical objectives below are the primary empirical objectives for
this mission. Evaluation and method selection proceed through four stages: evidence
validity; decision-derived absolute error limits with adequate uncertainty and
coverage; bounded degradation under evaluator-guided optimization; and only
then method comparison. A reliability claim must pass the first two stages and
the third when it covers evaluator-guided optimization. Agent–evaluator
coevolution is one candidate method; evaluating a self-evolving agent does not
require the evaluator itself to evolve.

## Active Objectives

Barcarolle optimizes:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

The first two are separate primary metrics. Objective 3 measures how much each
complete evaluation method degrades from its no-optimization baseline (`b=0`).
At the later method-comparison stage, give pass-rate-difference MAE decision
priority only when the method's pass-rate MAE is no more than a predeclared
margin worse than a named comparator at every budget. Absolute error limits,
within-method degradation limits, and comparator-relative margins answer
different questions and must not be substituted for one another.

Evidence may now include agent pairs, stateful sequences of candidate agent
versions, full lineage graphs, evaluator versions, evaluator feedback, and
optimization budgets. Task budget, forecast horizon, pair population, state
reset or persistence, task order, feedback policy, and evaluator-update rule
remain experiment choices that must be fixed before outcomes are examined.

## Method Scope

Candidate methods include:

- task sampling and weighting;
- statistical outcome models, including IRT, matrix, hierarchical, calibrated,
  and direct paired-outcome models;
- forecasting future task categories and generating executable task instances;
- joint allocation across real and generated tasks;
- coverage checks, abstention, and fallback policies;
- evaluator feedback policies, query accounting, and evaluator updating;
- stateful task streams, common-ancestor branching, and complete lineage
  evaluation;
- deployment-like context audits and separately scoped capability elicitation;
- adversarial stress tests of tasks, checks, scorers, feedback, metrics, and
  agent variants;
- evaluator portfolios and agent–evaluator coevolution.

No method may use only its own generated tasks to select itself and then call
that score future predictive validity. Final evidence comes from future
real-world tasks that were kept unavailable during agent optimization,
evaluator update, attack design, threshold choice, and final method selection.

## What The Current Code Can Reuse

- `pairwise_gap_mae` already computes the requested aggregate numerical error
  for predicted pass-rate differences over common agent outcomes. The field
  name is historical; public prose should use “pass-rate-difference MAE.”
- Task and check validation, hidden-check verification, exact static
  agent/result identity, rolling-origin chronology, and fixed result matrices
  remain useful for every method family. Persistent state and version-lineage
  identity are not yet represented.
- The prepared-package generator boundary can import generated tasks before a
  built-in task generator exists.
- Existing public per-task agent outcomes can support the first static and
  fixed-archive optimization studies without paid calls.

## Missing Experiment Contracts

| Missing capability | Evidence required before calling it implemented |
| --- | --- |
| Direct training for agent differences | A trainer or allocator optimizes paired pass-rate-difference loss and is replayed on held-out time splits and agents. |
| Equal reporting of both primary metrics | Cross-time summaries expose pass-rate and pass-rate-difference MAE with the same provenance, completeness, and recomputation checks. |
| Evaluation and method-selection stages | Independent reference standard, two decision-derived absolute error limits, uncertainty, critical strata, coverage, integrity, degradation limits under optimization, and comparator rule are frozen and replayable. |
| Operational behavior versus capability | The study declares which target it estimates. Changes to persistent agent configuration or generation, tool, or runtime policy create a child version; task inputs and temporary cues allowed by a frozen policy are separate run contexts. |
| Stateful agent snapshots | All behavior-affecting model, harness, persistent prompt and configuration, memory, skill, tool, retrieval, generation, runtime, and persistent-state inputs are versioned, with an exact reset, continuation, or fork policy. |
| Complete agent lineage | Primary and merge parents, other provenance edges, update artifacts, changed components, evidence exposure, optimizer, mutation, round, budget, selection status, and rollback are recorded and replayable. |
| Evaluator feedback and queries | Evaluator version, query count, feedback channel and detail, task disclosure, and epoch are recorded. |
| Repeated optimization | The same ancestor, agent optimizer, task order, state policy, budget, and common future cohort are replayed across evaluator conditions with future outcomes kept independent until search ends. |
| Cross-version comparability | Evaluator updating uses overlap, bridge tasks or agents, measurement-invariance diagnostics, or direct prospective calibration; a rising score alone is not treated as agent improvement. |
| Evaluation-context audit | Paired evaluation-cue and deployment-like conditions estimate behavior and pair-difference effects; awareness scores alone are not accepted as behavior evidence. |
| Predictive validity of generated tasks | Category forecasts, executable task creation, consistency across independent generation pipelines, and prediction of future real-world agent outcomes are measured separately. |
| Meta-evaluation | Attacks, evaluator candidates, temporal validation data, selection rules, and held-out attack families are separated so no dataset selects itself. |
| Adversarial isolation | The execution adapter prevents the declared agent from reading or modifying private checks, scorers, monitors, or host state. |

## Candidate Methods And Decision Rules

| Method | State | Decision rule |
| --- | --- | --- |
| Full eligible history | active baseline | Keep as the no-compression baseline, not as the definition of the project. |
| Equal-budget random and recent tasks | active baselines | Retain for budget and recency calibration. |
| `consensus_rate_match` | fixed historical baseline | Re-score for pass-rate differences; never tune again on the same five-repository pass-rate result. |
| IRT or mid-difficulty subset | active comparator | Retain only if later time splits and held-out agent/harness tests support both primary metrics. |
| Comparison-aware task allocation | active comparator | Directly target information about deployment-relevant agent differences on common tasks. |
| Hierarchical outcome model | active comparator | Require calibration, residual audits, sample-size checks, and cold-start/harness-shift tests. |
| Outcome model using coding-task features | active comparator | Separate model and harness effects; test on later task sets and unseen model–harness combinations. |
| Forecast-based task generation | active design | Require multiple independent task-instantiation pipelines and prediction of future real-world outcomes. |
| Adversarial task generation | active stress-test method | Do not mix raw adversarial pass rates into the target distribution of future real-world tasks without calibration. |
| Evaluator feedback policy | active protocol | Compare aggregate, rounded or thresholded, per-task, and trace feedback at equal search budget. |
| Controlled agent variants | active low-cost stress test | Hold out exploit families; measure false positives and improvement in both primary errors. |
| Adversarial stress testing | active hypothesis | Retain attacks that transfer to unseen attacks or future real-world tasks, not attacks that merely lower a score. |
| Evaluator portfolios | active comparator | Test selection directly against the portfolio to reveal correlated blind spots. |
| Agent–evaluator coevolution | optional live arm after protocol readiness | Compare with a fixed evaluator and equal-data update-only baseline after lineage, feedback, integrity, and prospective-cohort contracts are replayable. A winning static method is not a prerequisite. |
| Coverage checks and abstention | supporting method | Report risk–coverage and the unconditional fallback; do not hide difficult cases. |
| Common-ancestor lineage branching | active experimental design | Fork identical ancestor and repository state across evaluation methods; retain random exploration so descendant evidence is not available only for evaluator-favored parents. |
| Deployment-like replay and capability elicitation | active diagnostic | Estimate context effects separately from a predeclared elicitation ladder; never relabel a modified agent as the original version. |

## Previous-Phase Evidence

The previously analyzed mini-SWE-agent v2 development panel contained thirteen
model configurations across 500 SWE-bench Verified tasks. Under its fixed,
repository-equal pass-rate-MAE protocol, `consensus_rate_match` beat full
history by `0.006140` at H5 and `0.013774` at H10, where H5/H10 means the next 5
or 10 tasks after a time cutoff.

The same evidence prevents a broad claim:

- weighting time cutoffs instead of repositories reversed the differences to
  `+0.004284` and `+0.001864`;
- internal leave-one-out prediction for three modern full systems lost by
  `+0.014960` and `+0.024006`;
- thirteen reference systems predicting those three systems on common Verified
  tasks lost by `+0.017513` and `+0.007707`.

These results are useful baselines and evidence of population shift. They do
not show how the method performs on pass-rate-difference MAE or under repeated
optimization.

Evidence sources:

- [`experiments/2026-07-31-consensus-rate-selector.md`](experiments/2026-07-31-consensus-rate-selector.md);
- `../examples/modern_agent_panel/evidence/consensus-rate-summary.json`;
- `../examples/modern_agent_panel/evidence/consensus-rate-transfer-diagnostic.json`.

## Immediate Work Packages

WP0 establishes the common evidence contract. WP1 through WP4 are then
parallel evidence tracks, not an ordering of preferred methods. WP5 starts only
after lineage, feedback, budget, and prospective-cohort replay are reproducible;
it does not require a winning static method.

### WP0: Evaluation Contract And Controlled Failures

- declare operational behavior or capability elicitation as the target;
- define the independent future-task source, reference standard, label audit,
  and one-use cohort lifecycle;
- predeclare absolute error limits, uncertainty decisions, critical strata,
  coverage, abstention, integrity invalidation, degradation limits under
  optimization, and the separate method-comparison rule;
- define exact agent state, editable components, reset/continuation/fork
  policy, task order, update rule, and lineage provenance;
- build controlled ordinary, hidden-capability, score-targeting, test-access,
  scorer-tampering, benign-update, and regression fixtures;
- verify that known integrity failures invalidate the capability claim and do
  not become ordinary pass/fail cells.

Exit evidence: a completely offline, replayable study in which the protocol
correctly distinguishes known valid outcomes, ordinary task failures,
abstention, hidden-capability false negatives, and integrity violations.

### WP1: Static Replay With Both Metrics

- add evidence-backed pass-rate-difference summaries beside pass-rate
  summaries;
- define agent-pair populations and paired uncertainty;
- replay existing panels with full, recent, random, historical baseline, IRT,
  models using coding-task features, marginal and direct paired-outcome models,
  plus comparison-aware allocation methods;
- separate results with no prior agent outcomes (cold start), with prior outcomes
  (warm start), with the same harness, and across harnesses.

Exit evidence: a table showing whether method conclusions change when
pass-rate-difference MAE receives equal status, with no new paid calls.

### WP2: Stateful Agent Lineages And Optimization Budgets

- define the minimum experiment records for evaluator version, exact persistent
  agent state, primary and merge parents, other provenance edges, update
  artifact, changed components, agent optimizer, evaluator feedback, query
  count, selection status, rollback, and optimization round;
- preserve every candidate and branch, not only the evaluator-selected winner;
- replay best-of-`N` selection for increasing, predeclared `N` over fixed
  agent lineages;
- retain a randomized exploration floor so descendant outcomes are not
  observed only for evaluator-favored parents;
- record feedback information, task order, state policy, and cumulative
  exposure, not only query count;
- create a version-by-future-task-block matrix and report pass-to-fail,
  fail-to-pass, forward-transfer, backward-transfer, and retention diagnostics
  without replacing the two primary MAEs.

Exit evidence: reproducible curves for both errors over a fixed candidate
lineage, plus replay of every transition and selection decision.

### WP3: Predictive Validity Of Generated Tasks

- predeclare the demand-forecasting method independently of failures of the
  target agent;
- use at least two independent task-instantiation pipelines per category;
- validate executable transitions and hidden checks;
- audit generated checks with coverage and mutation testing plus independent
  semantic review;
- measure consistency of agent pass rates and differences across pipelines;
- calibrate generated outcomes only on earlier temporal data;
- evaluate on a separate temporal set of future real-world tasks.

Exit evidence: separate results for category forecasting, executable task
quality, cross-pipeline consistency, and prediction of future agent outcomes.
Executability alone is insufficient.

### WP4: Adversarial Stress Testing Of Evaluators And Metrics

- define attacks on task generation, task sampling and weighting, public tests,
  private checks, workspaces, scorers, aggregation, feedback, monitors, and
  reports;
- start with controlled agent variants containing known benign or exploit
  behaviors;
- run paired overt-evaluation, cue-reduced, and deployment-like contexts and
  estimate both individual and agent-pair context effects;
- run a predeclared capability-elicitation ladder against agents with known
  hidden coding capabilities; treat persistent configuration or policy changes
  as agent-version transitions and temporary cues within a frozen policy as run
  contexts;
- maintain an archive covering different attack mechanisms instead of
  optimizing attack success alone;
- hold out complete exploit and agent-lineage families;
- give a protocol-aware red team the evaluator, monitor, thresholds, feedback,
  and update rules rather than testing only unaware attacks;
- test metric perturbations on near-tie agent pairs;
- log workspace patches and file access to detect evaluator tampering and test
  leakage;
- compare candidate runs with benign reference runs while holding out complete
  exploit families;
- strengthen checks with coverage and mutation guidance, but report original
  and strengthened outcomes separately;
- test a known performance ceiling where tasks admit several equivalent valid
  outputs;
- test whether malicious or misleading memory, skill, tool, and generated-data
  artifacts propagate across descendants and fresh sessions;
- do not select an evaluator without independent temporal validation and
  acceptable performance on both primary metrics.

Exit evidence: attacks predict evaluator error on unseen attack families or
future real-world tasks. Attack success by itself is insufficient.

### WP5: Controlled Repeated-Optimization Experiment

- keep one evaluator fixed within each epoch;
- fork the same initial agent and repository state, then hold the agent
  optimizer, task order, state policy, candidate or compute budget, repository
  time cutoffs, future task blocks, and randomization contract fixed across
  conditions;
- compare a fixed evaluator, a periodically updated evaluator, an evaluator
  updated after adversarial stress testing, and optional agent–evaluator
  coevolution;
- evaluate budget checkpoints on the same future cohort or with concurrent
  randomized controls so time drift is not mislabeled as Goodhart degradation;
- open temporal validation outcomes only after the epoch's agent search ends;
- freeze the evaluator-update algorithm, update schedule, selection rule, and
  data-access policy prospectively; the resulting evaluator artifact may change
  only at those declared boundaries;
- retire every opened validation or test set from future independent-test use.

Exit evidence: bounded error curves by optimization budget for both metrics,
not a universal claim of resistance to Goodhart effects.

## Stop And Selection Rules

- Do not keep optimizing any method on the previously analyzed five-repository
  pass-rate result.
- Do not call an evaluation method reliable unless both primary errors satisfy
  their predeclared absolute limits with the declared uncertainty, coverage,
  integrity, and critical-stratum rules.
- Do not prioritize pass-rate-difference MAE unless pass-rate MAE stays within
  its predeclared margin of the named comparator at every predeclared
  evaluation budget.
- Separately reject methods whose primary errors exceed their predeclared
  within-method degradation limits from the no-optimization baseline (`b=0`).
- Do not use a scalar score to hide failure of either primary metric.
- Do not count abstained cases as successes; report coverage and fallback
  outcomes.
- Do not call adversarial tasks representative of future work without temporal
  calibration.
- Do not reuse data as independent test evidence after its outcomes influence
  evaluator generation, attacks, selection, or tuning.
- Do not start a paid repeated evaluator-guided optimization campaign until the
  WP0 contract, lineage and feedback records, fixed-lineage replay, execution
  isolation, and a cost/power pilot are complete. A frozen comparator is
  required; a winner from the static methods is not.

## Current Claim Boundary

Implemented evidence supports an auditable static benchmark boundary and
static calculation of the two requested errors. It does not yet support a
method trained for pass-rate-difference MAE, a validated generated-task
distribution, persistent-state or lineage evaluation, complete
reliability-claim evidence, enforced separation of operational behavior and
elicited capability, robustness under repeated optimization, adversarial stress
testing of evaluators and metrics, agent–evaluator coevolution, or resistance to
Goodhart effects.
