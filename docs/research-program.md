# Barcarolle Research Program

Status: current research authority, 2026-08-30.

This document supersedes the metric priorities and method restrictions in
earlier task-selection studies and the 2026-08-13 strategic briefing. Dated
documents remain useful evidence and decision history, but they do not define
the current roadmap.

## First Principle

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
research domain because their work can be executed, independently checked,
versioned, and compared with tasks that arrive later. The principle is broader
than task selection, benchmark construction, or any one coding-agent harness.

A self-evolving agent uses experience or evaluation feedback to make
behavior-changing updates that persist across tasks. The update may change
model weights, persistent prompts, memory, skills, tools, retrieval, collaboration,
harness code, or runtime policy. The updater may be the agent itself, another
agent, or a declared program; its degree of autonomy is part of the experiment.
The evaluated object is therefore not only a frozen agent snapshot, but also
each parent-to-child transition and the complete agent lineage produced by a
declared update process.

In this project, a reliable evaluation is a versioned, auditable process that
produces decision-useful evidence about a declared future-task outcome even
when the evaluated agent can learn from the evaluation. Reliability is always
conditional on the task population, outcome definition, agent lineage and
optimizer, evaluator feedback, optimization budget, threat model, time
horizon, and decision. It is never a claim of universal or permanent resistance
to Goodhart effects.

“Reliable evaluation” is the broad engineering objective here. The narrower
measurement-science meaning of reliability—repeatability under declared
sources of variation—is one required property, alongside predictive validity,
integrity, uncertainty, coverage, and robustness to adaptation. These
properties must be reported separately; they must not be collapsed into a new
single score.

## One-Minute Summary

The first principle is operationalized by three primary numerical objectives
in the initial coding-agent domain:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

The first two objectives are separate mean absolute error (MAE) metrics.
Reliability requires both to satisfy predeclared, decision-derived absolute
limits with adequate uncertainty and coverage. Objective 3 separately measures
degradation from the same evaluation method's no-optimization baseline
(`b=0`). A named-comparator non-inferiority rule is useful for choosing among
acceptable methods, but cannot make two absolutely inaccurate methods reliable.
Report both errors as functions of a measurable optimization budget, such as
the number of candidates, evaluator queries, rounds, feedback bits, tokens, or
compute.

Research is not limited to selecting historical tasks. Candidate methods
include task generation, task sampling and weighting, statistical outcome
models, calibration and abstention, evaluator feedback policies,
evaluator updating, adversarial stress testing of evaluators and metrics, and
agent–evaluator coevolution.

Every method must ultimately be tested on an independent temporal test set:
future real-world tasks that were unavailable while optimizing the agent,
updating the evaluator, designing attacks, or choosing promotion thresholds. A
generated or adversarial task is not representative of future work merely
because it is executable, difficult, or exposes a failure.

The repository currently implements much of the fresh-workspace execution for
cooperative agents, verification, result-provenance, and static time-split
evaluation path. It does not yet implement built-in task generation,
repeated-optimization experiments, adversarial stress testing of evaluators and
metrics, or agent–evaluator coevolution. See
[`implementation-status.md`](implementation-status.md).

## Terms Used In This Document

- An **agent** is the complete evaluated system: model, harness, persistent
  prompts and configuration, tools, retrieval, edit loop, retries, runtime
  policy, and any persistent mutable state. In ordinary prose, “agent” is
  lowercase; `AgentRecord` and similar names refer to exact code records.
- A **self-evolving agent** carries behavior-changing updates across tasks.
  Evaluation must state which components may change, what evidence drives an
  update, and whether state is reset, continued, or forked between runs.
- An **evaluation method** is the complete measurement protocol: target
  outcome, task source, execution and verification, estimator, uncertainty,
  coverage, feedback, abstention, fallback, and any evaluator-update rule. An
  **evaluator** is a versioned realization of that method. It is broader than a
  predictor, grader, judge, or hidden check.
- An **agent optimizer** proposes and selects agent changes using the permitted
  evaluator feedback.
- An **agent lineage** is the version graph produced by an agent optimizer,
  including rejected and unevaluated candidates as well as promoted versions.
- A **reference standard** is the independent labeling and adjudication process
  used to determine the target outcome. For coding tasks it may combine hidden
  executable checks with independent semantic review.
- **Rolling-origin evaluation** means backtesting over repeated time-based
  train/test splits. It is used for development and comparison before a live
  prospective study.
- **Prospective evaluation** means fixing the protocol before future real-world
  tasks arrive and keeping their outcomes hidden until the declared test time.
- **Meta-evaluation** means evaluating evaluators and their metrics.
- **Optimization budget** is a measurable limit on evaluator-guided search,
  such as candidate count, evaluator queries, feedback bits, tokens, or compute.
- An **evaluator feedback policy** specifies what information the agent
  optimizer receives and how often it may query the evaluator.
- A **run context** contains the task or user input and temporary evaluation,
  deployment, interface, or feedback cues supplied within a frozen agent and
  runtime policy. It is recorded separately from the agent version.
- **Agent–evaluator coevolution** means alternating bounded agent optimization
  with evaluator selection or updating.

When notation is useful, `M` is the complete frozen evaluation method, `E_k` is
the evaluator version active in epoch `k`, and `U` is the frozen
evaluator-update rule that may produce `E_(k+1)`. Updating `E_k` under `U` does
not change `M`; changing the method or `U` creates a new method condition.

The default pass-rate estimand is **operational behavior**—what an exact agent
actually does under a declared deployment-like harness and runtime policy.
Performance under a separate, predeclared capability-elicitation protocol is a
different estimand. An elicitation that changes persistent configuration or the
generation, tool, or runtime policy creates a child agent version. Varying only
task input or temporary cues permitted by the frozen policy creates a
run-context condition for the same version. Neither may be pooled silently into
the original target.

Public and handoff documents should use these established terms consistently.

## Evaluation Object: Snapshot, Transition, And Lineage

Let `A_k` be an exact agent snapshot after `k` updates, including its persistent
state. A declared agent optimizer `O` produces candidates through a process of
the form:

```text
A_(k+1) = O(A_k, permitted evaluator feedback, task experience, budget, seed)
```

Reliable evaluation asks three different questions:

1. **Snapshot:** how will `A_k` perform on future real-world tasks?
2. **Transition:** did a parent-to-child or incumbent-to-challenger update
   produce a real change, including regressions?
3. **Lineage:** what outcomes does the complete update process produce from a
   fixed initial agent under a declared evaluator, feedback policy, budget
   path, task stream, and random seed?

The minimum lineage evidence includes all parents, merges or other provenance
edges, the changed components and update artifact, task and feedback exposure,
optimizer and evaluator versions, budget counters, promotion or rejection
decision, rollback, and outcome status. Keeping only the final winner destroys
the evidence needed to measure selection optimism, path dependence, or missed
useful branches.

When persistent prompts, memory, skills, tools, or harness artifacts evolve, distinguish
the system that writes an update from the task-solving agent that must retrieve,
activate, and follow it. Cross updater identity, executor identity, and artifact
type when feasible. Report update validity, activation, adherence, and final
task benefit separately; an impressive-looking update or capable updater does
not establish that the deployed executor improves.

Snapshot and trajectory evaluation are complementary. Snapshot evaluation
freezes one agent state while measuring it on a common task cohort. Trajectory
evaluation lets state change according to the declared update rule over an
ordered stream. Task order, state persistence, and repository state are part of
the treatment, not implementation noise. When comparing evaluation methods,
fork the same initial agent and repository state, hold optimizer budgets fixed,
and use common future tasks and replicate slots across branches.

Retain a version-by-task-block outcome matrix. Pass-to-fail and fail-to-pass
transitions, backward and forward transfer, learning speed, cost, lineage depth,
and the quality of descendants are useful diagnostics for understanding the
process. They do not replace pass-rate MAE, pass-rate-difference MAE, or their
full curves by optimization budget. A parent that produces strong descendants
may be valuable to a search policy while still being a poor deployment choice.

The evaluated agent and evaluator may be fixed or updated independently:

| | Evaluator fixed within the study | Evaluator updated by a predeclared rule |
| --- | --- | --- |
| Agent fixed | Static calibration and cost baselines. | Tests evaluator updating and scale comparability. |
| Agent self-evolves | Core stress test for adaptation to a fixed evaluation. | Optional agent–evaluator coevolution experiment. |

Evaluating self-evolving agents is the project context. Evolving the evaluator
is only one candidate method; a fixed evaluator that remains accurate through
the declared optimization budget can satisfy the first principle.

## The Three Objectives

At a repository and time cutoff `t`, let `F_t` be a predeclared block of future
real-world tasks. Let `p_t(a)` be agent `a`'s pass rate on `F_t`, and let
`delta_t(a,b) = p_t(a) - p_t(b)`. Before the tasks or their outcomes are
available, an evaluator emits `p_hat_t(a)` for individual agents and defines
`delta_hat_t(a,b)` for agent pairs, either directly or by derivation.

The study must state whether `F_t` is a fixed external task distribution or an
on-policy workload affected by earlier agent actions. If an evolving agent
changes the repository or user behavior that produces later tasks, historical
fixed-distribution replay does not identify that performative, on-policy
outcome without additional prospective evidence.

The target agent identity includes its model snapshot, harness, persistent prompts, tool
policy, and relevant runtime settings. A changed harness is a changed agent,
not an implementation detail to average away.

### Objective 1: Pass-Rate Prediction Error

For one agent:

```text
pass_rate_error(t, a) = abs(p_hat_t(a) - p_t(a))
```

This is the primary snapshot-level target. The primary aggregate is pass-rate
MAE over a predeclared population of repositories, time cutoffs, agents, and
forecast horizons. Report
repository-equal and expected-traffic weighting separately when they answer
different deployment questions. A horizon of the next 5 tasks, the next 10
tasks, and the next calendar month are different targets and must not be
silently pooled.

### Objective 2: Pass-Rate-Difference Prediction Error

For a predeclared ordered pair of agents `(a, b)`:

```text
pass_rate_difference_error(t, a, b) =
    abs(delta_hat_t(a,b) - delta_t(a,b))
```

This is the primary transition-level target when `(a,b)` is a child–parent or
challenger–incumbent pair. The primary aggregate is pass-rate-difference MAE
over the declared pair population. The pair population may contain all pairs,
parent–child versions, incumbent–challenger comparisons, or another
deployment-relevant set; it must be fixed before outcomes are examined.

An evaluator may predict `delta_hat_t(a,b)` directly with a paired response
model, or derive it as `p_hat_t(a) - p_hat_t(b)`. The method must declare which
contract it uses before outcomes are observed. If it emits both marginal and
direct pair predictions, also report the coherence residual:

```text
coherence_residual(t,a,b) =
    delta_hat_t(a,b) - (p_hat_t(a) - p_hat_t(b))
```

Coherence is a diagnostic, not a substitute for accuracy. For a derived
difference predictor, if the signed pass-rate errors are `e_a` and `e_b`, the
difference error is `abs(e_a - e_b)`, so their covariance matters. Therefore:

- run compared agents on the same tasks and paired replicate slots;
- compute the target difference from paired outcomes, and allow either a direct
  pair predictor or a declared difference of marginal predictors;
- use common random seeds or other paired controls when they are part of the
  declared execution design;
- report sign errors, rank agreement, and decision regret only as secondary
  diagnostics, not as substitutes for numerical difference error.

The current code derives pair predictions from marginal pass-rate predictions
and computes aggregate `pairwise_gap_mae`; the historical field name is
retained for compatibility. Direct pair prediction is not yet implemented, and
training and reporting do not yet give the metric equal status across time
splits and agent-pair populations.

### Objective 3: Robustness Under Repeated Evaluator-Guided Optimization

Let `b` denote a predeclared optimization budget for the complete evaluation
method and agent-update process. For each budget, compute the same two errors:

```text
pass_rate_mae(b)
pass_rate_difference_mae(b)
```

and their within-method change from the same method's no-optimization baseline
(`b=0`):

```text
increase_in_pass_rate_mae(b) = pass_rate_mae(b) - pass_rate_mae(0)
increase_in_difference_mae(b) =
    pass_rate_difference_mae(b) - pass_rate_difference_mae(0)
```

The full curves at prespecified budgets are primary. Also report the worst
error up to the maximum budget, area under each degradation curve, and the
first budget at which a predeclared within-method degradation tolerance is
crossed. Summary statistics must not hide a late collapse.

This is distinct from the comparator-relative constraint used to choose among
methods:

```text
comparator_excess_pass_rate_mae_m(b) =
    pass_rate_mae_m(b) - pass_rate_mae_named_comparator(b)
```

At every predeclared evaluation budget, a candidate may receive decision
priority for lower pass-rate-difference MAE only when this excess stays within
its predeclared non-inferiority margin. A method's degradation from its own
no-optimization baseline (`b=0`) cannot establish that it is competitive with
the named comparator.

This objective does not introduce a third proxy score or a generic
reward-hacking detector. It measures whether Objectives 1 and 2 remain accurate
as the evaluator becomes a target of optimization.

A valid claim is bounded by the tested agent optimizer, feedback channel,
budget, threat model, repositories, agent families, and temporal test set. Do
not claim permanent or universal resistance to Goodhart effects.

## Evaluation And Method-Selection Stages

The three objectives are necessary numerical evidence, but they do not alone
make an evaluation reliable. Evaluation and method selection proceed through
four stages in order. A reliability claim must pass Stages 1 and 2, plus Stage
3 when it covers evaluator-guided optimization. Stage 4 chooses among methods;
it cannot upgrade one that failed an earlier applicable stage.

### 1. Evidence Validity

The future task source, outcome definition, execution, verification, and
information boundaries must support the declared estimand. Evidence is invalid
for a reliability claim if the agent changed or read private checks, scorers,
monitors, result records, or sealed future outcomes; if the reference standard
is not specified and operated independently of the candidate evaluator, its
builder and update process, its selection process, and the agent optimizer; or
if the task label is not credible under its declared semantics. Fail closed
operationally, but report an integrity violation separately rather than
recoding it as an ordinary task failure.

### 2. Absolute Error Limits

At every predeclared evaluation budget, both errors must satisfy
decision-derived absolute limits:

```text
pass_rate_mae_m(b) <= tau_rate
pass_rate_difference_mae_m(b) <= tau_difference
```

Use the predeclared uncertainty procedure for this decision. As specified in
[`statistical-protocol.md`](statistical-protocol.md), require simultaneous
one-sided upper confidence bounds across the declared budgets and critical
strata to remain below their limits. Predeclare any critical repository,
agent-family, harness, or lineage strata;
a good macro average must not hide complete failure on a decision-critical
group. For one deployment decision, keep these limits fixed across optimization
budgets so the claim cannot pass by moving its target. If the intended decision
changes with budget, treat it as a separately named claim with separately
derived limits. There is no universal numerical threshold. Without limits
derived from the intended decision, the result is comparative or descriptive
and must not be called a reliable evaluator.

### 3. Degradation Under Optimization

Separately require both errors to remain within predeclared degradation limits
relative to the same method's no-optimization baseline:

```text
pass_rate_mae_m(b) - pass_rate_mae_m(0) <= gamma_rate(b)
pass_rate_difference_mae_m(b) - pass_rate_difference_mae_m(0)
  <= gamma_difference(b)
```

An initially inaccurate method can pass this degradation test, so it never
replaces the absolute error limits.

### 4. Method Comparison

Among methods that pass the earlier applicable stages,
pass-rate-difference MAE may receive decision priority only when pass-rate MAE
is no more than a predeclared margin worse than a named comparator:

```text
pass_rate_mae_m(b) - pass_rate_mae_comparator(b) <= epsilon(b)
```

For a static `b=0` study, degradation under optimization is `not_applicable`,
not silently passed. Comparator non-inferiority ranks otherwise acceptable
methods; it is not an absolute error test. Coverage, abstention, cost, and
integrity remain hard constraints rather than terms that a scalar score may
trade away.

## What Counts As Valid Evidence

The target distribution is future real-world tasks under a declared inclusion
policy. A study must specify:

- repository population and weighting;
- task inclusion, exclusion, and label-maturity rules;
- operational behavior or elicited capability target, including the exact
  harness, tools, runtime, persistent-state, and elicitation policy;
- agent and agent-pair population;
- agent lineage, editable components, state reset or persistence, task order,
  and update rule when agents evolve;
- forecast horizon;
- task and replicate pairing;
- information available at the time cutoff;
- treatment of missing, censored, invalid, and abstained outcomes;
- optimization budget, evaluator feedback, and evaluator-update rule when
  Objective 3 is studied;
- independent task-source and reference-standard provenance, plus absolute
  error limits and critical strata for any reliability claim.

Rolling-origin results are development evidence unless the method and analysis
were fixed before each future block became available. A prospective test set
supports stronger claims only when its tasks and outcomes remained unavailable
to the agent optimizer, task generator, evaluator builder, red team, and
evaluator-selection procedure.

Use separate temporal datasets for separate decisions:

1. **development data** for building agent and evaluator candidates;
2. **evaluator-selection validation data** for choosing or updating an
   evaluator;
3. **prospective test data** used once for the final claim.

Once validation or test outcomes influence a method, those outcomes become
development data for later work. They cannot remain independent test evidence.

A later timestamp does not prove that information was unseen. Preserve actual
task, test, repository, transcript, and artifact availability. Evaluation-
awareness probes, reward-hack detectors, randomized integrity canaries, and
monitor scores diagnose specific failure mechanisms; none replaces observed
accuracy on the independent future-task target.

## Threat Model

Keep six failure mechanisms separate because they require different fixes and
may occur together:

1. **distribution shift**: repositories, task mix, time, agent family, harness,
   or ability change without evaluator-aware optimization;
2. **performative change**: evaluator feedback or earlier agent actions change
   the later agent, repository, user behavior, or task-arrival distribution;
3. **adaptive overfitting**: repeated feedback lets an optimizer learn finite
   evaluator idiosyncrasies without violating the benchmark boundary;
4. **strategic underperformance or evaluation-context sensitivity**: an agent
   recognizes testing or deployment cues and conditionally hides, reveals, or
   changes behavior; awareness without a behavioral effect is only a risk
   factor, not evidence of this failure;
5. **reward hacking or benchmark-integrity violation**: an agent reads or
   alters tests, hidden checks, scorer state, monitors, reports, or execution
   controls;
6. **overfitting during evaluator selection**: the evaluator builder overfits
   the finite red-team suite or the metric used to select evaluators.

Hidden checks and isolated workspaces reduce direct access to correctness
evidence. They do not establish that the task distribution represents future
work. Fresh tasks reduce exposure but do not establish predictive validity.
Changing the evaluator may move the proxy without solving evaluator-selection
overfitting.

Persistent memory, skills, tools, and repository changes create an additional
propagation path: one misleading or malicious experience can affect later
sessions after the original trigger disappears. Record authoring, storage,
retrieval, activation, execution, rollback, and later harm separately instead
of treating the final pass rate as a complete causal explanation.

For every repeated-optimization experiment, fix the attacker's knowledge and
authority:

- black-box access to an aggregate score;
- task or per-task feedback access;
- trace or transcript access;
- white-box access to evaluator or scorer implementation;
- control over workspace, tests, imports, processes, or network state;
- influence over generated tasks, judges, monitors, or evaluator training data.

Also distinguish four outcomes:

- adaptive overfitting within the permitted interface;
- an integrity violation, which invalidates the capability result and receives
  its own failure label;
- strategic underperformance or context-conditioned behavior;
- ordinary or performative distribution change without an integrity attack.

## Candidate Method Families

No method receives priority because it resembles the current implementation.
Each method must produce the same two predictions and face the same
optimization protocol.

| Method family | Main idea | Evidence needed to retain it | Main risk |
| --- | --- | --- | --- |
| Task sampling and weighting | Allocate real historical tasks using uncertainty, agent disagreement, coverage, cost, and logged sampling probabilities. | Both MAEs improve on new time splits under a valid sampling estimator. | A small subset reconstructs old agents but misses new agent or harness interactions. |
| Statistical outcome modeling | Fit hierarchical item response theory (IRT), matrix-completion, calibrated Bernoulli models, or direct paired-outcome models over agents, tasks, repositories, harnesses, and time. | Calibrated marginal and pair predictions improve for held-out agents and future task blocks. | Item parameters or pair interactions change across agent families or over time. |
| Forecast-based task generation | Forecast likely future task categories and use multiple independent pipelines to create executable task instances. | Generated outcomes predict both metrics on future real-world tasks. | A task-generation pipeline's style or tests determine the ranking. |
| Hybrid task allocation | Allocate budget jointly across sampled real tasks and generated tasks. | Achieves a target error at lower cost than real-only, generated-only, and random baselines. | Informativeness is optimized at the expense of representativeness. |
| Evaluator feedback policies and updating | Limit feedback precision or frequency and replace evaluator material only at fixed epoch boundaries. | Slows degradation at equal agent-search budget without blocking ordinary improvement. | It merely slows learning or introduces uncalibrated drift. |
| Adversarial stress testing | Generate agent variants, task/check attacks, and metric perturbations that maximize prediction error on independent data. | Attacks transfer to unseen attack families or future real-world tasks and lead to lower primary errors. | The process overfits one red-team generator or rewards difficulty alone. |
| Evaluator portfolios | Combine diverse candidate evaluators or outcome models. | Improves average and worst-group errors under agent and task shift. | Components share blind spots, so apparent diversity is cosmetic. |
| Agent–evaluator coevolution | Alternate bounded agent optimization with evaluator selection or updating. | Extends the optimization budget over which both errors stay within predeclared limits. | The evaluator-selection rule becomes a new proxy that can itself be gamed. |
| Coverage checks and abstention | Detect weak support and decline a precise prediction or use a fallback. | Improves a predeclared risk–coverage curve and unconditional fallback outcome. | Accuracy rises only because difficult cases are excluded. |
| Deployment-like replay and capability elicitation | Compare operational behavior across evaluation cues and run a separate, predeclared elicitation ladder when elicited capability is the target. | Context effects and elicitation false negatives are measured on held-out agents and tasks without changing the operational behavior estimand. | A synthetic “deployment-like” context is treated as deployment, or a newly elicited agent is mislabeled as the old version. |
| Lineage-aware branching | Fork the same ancestor across evaluator and feedback conditions while retaining the complete version graph. | Common-cohort comparisons identify which evaluation methods cause better future trajectories. | Search-policy censoring or task order makes an expanded branch look intrinsically better. |

Combined methods require component ablations. For example, task generation plus
adaptive sampling is not evidence for generation unless the same generator
with neutral sampling and the same sampler on real-only tasks are both tested.

## Statistical Requirements

The exact estimator contracts are in
[`statistical-protocol.md`](statistical-protocol.md). The minimum requirements
are:

- compare agents on common tasks and paired replicates;
- preserve repository, time-cutoff, task-dependency, agent-family, and run-level
  clustering in uncertainty estimates;
- when tasks are sampled non-uniformly, use a declared randomized design with
  positive inclusion probability and the matching Horvitz–Thompson, Hájek,
  Hansen–Hurwitz, or sequential adaptive estimator;
- never mix inclusion probabilities, draw probabilities, conditional proposal
  probabilities, weights, or variance formulas from different designs;
- report the design-based estimate beside a model-assisted estimate when an
  outcome model guides sampling;
- treat disagreement between those estimates as possible misspecification or
  drift, not as values to average automatically;
- report uncertainty and coverage for both primary metrics;
- report abstention coverage and the unconditional fallback policy;
- predeclare decision-derived absolute limits for both errors, the uncertainty
  rule used to test them, and any critical strata;
- name the comparator and fix the comparator-relative pass-rate MAE margin at
  every predeclared evaluation budget before giving pass-rate-difference MAE
  decision priority;
- separately predeclare the allowable within-method degradation from the
  no-optimization baseline (`b=0`) for both primary errors.

Importance weighting can correct unequal sampling within a declared task
population. It cannot prove that historical or generated tasks represent
future real-world tasks.

## Independent Evidence Architecture

Reliable evaluation needs three information flows whose roles must not be
collapsed:

```text
agent optimization
  evaluator feedback -> agent optimizer -> complete agent lineage

optional evaluator update
  development data + consumed validation + red-team evidence
  -> evaluator builder -> next evaluator version at a declared boundary

independent prospective evidence
  authentic future tasks + independent reference standard
  -> frozen predictions for declared snapshots, transitions, and budgets
  -> both primary errors, uncertainty, integrity status, and claim decision
```

The first flow may be frequent and visible. The second is optional: a fixed
evaluator remains a valid candidate. The third is the only source of final
predictive-validity evidence and must remain unavailable to both earlier flows
until predictions and the relevant update epoch are frozen.

Use a prequential cohort lifecycle. Before a future cohort opens, freeze the
initial state or checkpoint, predictions, update algorithm, evaluator-update
rule, feedback and data-access policies, budgets, randomization, and analysis.
After its outcome is scored, that cohort may become development data for later
epochs, but it permanently loses independent-test status. The next claim
requires a newly sealed cohort.

For coevolution, the prospective contract freezes the evaluator-update
algorithm, update schedule, selection rule, allowed data, and randomness—not
one evaluator artifact for all future time. Each evaluator version remains
fixed within its declared epoch, and every prediction is fixed before its
cohort outcomes open. This lets the method adapt without allowing it to select
itself on the same evidence used to certify reliability.

## Recommended Coevolution Protocol

Treat the part of an evaluation method that may change between epochs as a
versioned combination of:

```text
task source
task validation and admission rules
task allocation and weights
statistical outcome model
feedback policy
evaluator-update rule
uncertainty, abstention, and fallback policy
```

Keep hidden checks, workspace isolation, independent outcome review, and sealed
prospective cohorts outside the updateable combination. They remain versioned
parts of the complete evaluation method, but must not be modified by the
evaluated agent or certified by the candidate evaluator itself.

Use three nested information boundaries:

1. The agent optimizer sees the current evaluator version and only the
   permitted feedback. It never sees the current sealed prospective outcomes
   or evaluator-selection data. A retired earlier cohort may enter later agent
   development only when the frozen data-access and feedback rules allow it.
2. Evaluator builders and red teams may use earlier time splits and declared
   attacks. They do not see the next evaluator-selection validation set.
3. A separate prospective test set is opened only after the initial evaluator
   version, complete evaluation method, evaluator-update rule, agent-update
   rule, budgets, and current cohort predictions have been fixed.

Within each epoch:

1. Fix the common ancestor state, agent optimizer, candidate budget, evaluator
   version, feedback policy, tasks visible to the optimizer, state-persistence
   policy, and future task window. Fork comparable conditions from that common
   state.
2. Generate agent candidates and evaluate relevant pairs on the same task and
   replicate schedule.
3. Preserve the full agent lineage, including rejected, rolled-back, and
   unevaluated candidates, not only the apparent winner.
4. After search ends, freeze the current evaluator version's predictions for
   all declared agent snapshots, pairs, and budget checkpoints. Only then open
   the epoch's prospective cohort and compute both primary errors, uncertainty,
   coverage, and integrity status.
5. Apply Stages 1 and 2, plus Stage 3 for the repeated-optimization claim, at
   every predeclared budget. Apply Stage 4 only for a matched method comparison:
   use the named-comparator pass-rate MAE margin before giving average or
   worst-group pass-rate-difference MAE decision priority.
6. Independently stress-test task sources, hidden checks, workspaces, scorers,
   aggregation rules, feedback, and evaluator metrics, with held-out attack
   families for selection.
7. Build candidate evaluator versions for the next epoch only from data allowed
   by the frozen update rule, and freeze those candidates before using the
   just-opened cohort for next-version selection. Choose, mix, or reject the
   next evaluator version only at the epoch boundary.
8. Retire the opened cohort from independent-test use. It may help select
   `E_(k+1)` under the frozen rule, but it cannot validate `E_(k+1)`; that
   requires the next sealed prospective cohort.

This is a proposed design, not an established solution. Its central hypothesis
is that adversarial stress testing reveals exploitable prediction residuals
before ordinary agent search, while independent temporal validation prevents
the red team from defining the target.

## Adversarial Stress Testing Of Evaluators And Metrics

The red team should test the measurement procedure, not only produce harder
tasks. Candidate tests include:

- ability-preserving transformations for which predictions should remain
  stable;
- real capability improvements for which predictions should improve;
- exploit-only changes that raise the public score without improving future
  pass rate;
- near-tie agent pairs, where small numerical difference errors change the
  decision;
- changes to pair composition, repository weights, horizon, tie handling,
  missing-cell policy, and abstention policy;
- increasing the number of agent candidates while evaluator sample size stays
  fixed;
- aggregate, rounded, thresholded, per-task, and trace-level feedback;
- paired overt-evaluation, cue-reduced, and deployment-like contexts, with
  evaluation-context effects reported per agent and pair;
- controlled agents with known hidden coding capabilities, evaluated with a
  predeclared prompting, sampling, tool, demonstration, and fine-tuning ladder;
- transfer across model families and harnesses;
- lineage holdout for monitors, attacks, and integrity detectors;
- attacks on tests, graders, monitors, task generators, and reporting code;
- protocol-aware attacks in which the red team knows the monitor, thresholds,
  feedback, and update rules;
- evaluator tampering and test leakage, using workspace/file-access logs and an
  independent reference evaluator;
- contrastive detection that compares candidate runs with benign reference
  runs while holding out complete exploit families;
- coverage- and mutation-guided strengthening of hidden checks, with separate
  semantic review of every added check;
- a known performance ceiling for leakage detection when a task admits several
  semantically equivalent valid outputs;
- selection against an evaluator portfolio to reveal correlated blind spots.

For persistent memory, skills, tools, or generated data, include attacks that
test authoring, later retrieval, activation, execution, and fresh-session harm.
A clean final transcript does not rule out a malicious artifact that propagates
to descendants.

An attack is useful when it predicts evaluator error on an unseen attack family
or future real-world tasks. Merely lowering an agent's evaluator score is not a
successful meta-evaluation result.

An agent's statement or latent probe score that it recognizes an evaluation is
not enough. The relevant diagnostic is a controlled change in task behavior or
pair difference across contexts. Conversely, failure to elicit a known hidden
capability is evidence about the elicitation protocol, not proof that the
capability is absent.

## Reference Standards And Check Strength

Separate two regimes before choosing feedback or optimization intensity:

- In a **strong-verification regime**, the outcome is defined by an automatic
  check that is close to the complete task specification, such as an exact
  mathematical objective or fully executable invariant. Rich, frequent
  feedback may be reasonable, although it still does not establish that the
  chosen tasks represent future real work.
- In an **incomplete-specification regime**, visible or hidden tests cover only
  part of the intended behavior. Passing the check is a fallible label, and
  repeated optimization may discover test-specific shortcuts. Repository issue
  resolution usually belongs here unless independent semantic evidence shows
  otherwise.

The regime is a property of the task and reference standard, not of whether the
check is hidden. For incomplete specifications, limit or randomize feedback,
audit tests independently, retain workspace and artifact evidence, and use
coverage, mutation, differential, and semantically reviewed test strengthening.
Always report the original and strengthened outcomes separately. Success of
self-improving search in strong-verification domains must not be used as
evidence that a repository evaluator with incomplete checks is reliable.

## Task Generation Protocol

Use separate generators for separate purposes:

- an **agent-independent, forecast-based task generator** proposes task
  categories intended to resemble future real-world tasks;
- an **adversarial task generator** proposes red-team tasks aimed at known or
  suspected weaknesses.

At historical time cutoffs, fix a forecast and use at least two independent
task-instantiation pipelines per predicted category. Measure three properties
separately:

1. whether the forecasted categories match future real-world tasks once they
   arrive;
2. whether agent pass rates and pass-rate differences are consistent across
   independent generation pipelines;
3. whether outcomes on generated tasks predict both primary metrics on future
   real-world tasks.

Execution success and hidden-check correctness are necessary task-quality
conditions. They are not evidence of representativeness. Adversarial tasks may
remain valuable for training or stress testing even when they receive zero
weight in the estimate of future real-world pass rate.

For generated or strengthened checks, report coverage and mutation-detection
rates, audit semantic correctness independently, and keep the original and
strengthened outcome definitions separate. A changed pass rate or ranking is
evidence that the original checks were incomplete; it is not by itself evidence
of prediction on future real-world tasks.

## Evidence Tracks And Integration Sequence

Stage 0 is a prerequisite for any live claim. Stages A, B, and C plus the
adversarial fixtures can proceed in parallel; their lettering is not a ranking
of method families. Stage D integrates the instruments into a controlled live
loop, and Stage E is the one-use prospective confirmation.

### Stage 0: Evaluation Contract And Controlled Failure Tests

Fix the operational behavior or elicited capability target, independent task
source and reference standard, absolute error limits, critical strata, agent-state and
lineage schema, reset/fork/continuation policy, task order, update rule,
feedback channels, and budget counters.

Before a live self-evolving agent study, test the protocol with controlled
agents that exhibit ordinary behavior, known hidden coding capabilities,
test/scorer access, evaluator-aware score targeting, benign updates, and
regressions. Randomize evaluation cues and retain complete task, artifact, and
workspace evidence. The goal is to measure known false negatives and false
positives in the evaluation apparatus, not to estimate the prevalence of these
behaviors in deployment.

### Stage A: Static Two-Metric Baselines

Use existing per-task outcomes and no paid calls. Recompute previously analyzed
development panels with both primary metrics.

Include:

- all eligible history;
- recent history;
- equal-budget random sampling;
- the historical `consensus_rate_match` method;
- an IRT or mid-difficulty subset;
- randomized comparison-aware sampling using common-task disagreement and
  logged inclusion probabilities;
- simple calibrated marginal outcome models and a direct paired-outcome model;
- an outcome model using coding-task features, with separate model and harness
  effects, following the Agent Psychometrics baseline.

This stage calibrates the static instruments and tests whether the second metric
changes which methods appear promising. It is not a prerequisite that one
static method “wins” before self-evolving agents can be studied.

### Stage B: Predictive Validity Of Generated Tasks

Run the task-generation protocol above on historical time cutoffs. Keep
category forecasting, executable task creation, consistency across generation
pipelines, and future-outcome prediction as separate results.

### Stage C: Simulated Optimization With A Fixed Candidate Archive

For predeclared values of `N`, select the best of `N` agent versions from an
existing archive using each evaluator. Then measure both errors on a separate
set of future real-world tasks. This tests whether larger search budgets amplify
evaluator residuals before paying for a live repeated evaluator-guided
optimization experiment.

Include controlled agent variants with known benign changes and implanted
exploit mechanisms. Hold out complete exploit families, not random instances,
and measure false positives as well as improvement in both primary metrics.
Preserve the version graph, and replay both evaluator-chosen paths and a
randomized exploration floor so descendant evidence is not available only for
high-scoring parents.

### Stage D: Controlled Repeated Evaluator-Guided Optimization

Fork the same initial agent and repository state. Hold the agent optimizer,
candidate or compute budget, task order, repositories, future task windows, and
randomization contract fixed. Change only the evaluation-method condition:

- static full-history evaluator;
- one frozen static comparator that passes the Stage 0 integrity preflight;
- periodically updated evaluator without adversarial stress testing;
- evaluator updated using adversarial stress tests and temporal validation;
- agent–evaluator coevolution under a predeclared update policy, when included;
- evaluator built only from adversarially generated tasks, without calibration
  to future real-world tasks, as a negative control.

Run a factorial comparison of feedback granularity and evaluator-update
policy, use independent seeds, and evaluate budget checkpoints on the same
future cohort or against concurrent randomized controls. Report full error
curves by optimization budget, the rate of evaluator-approved agent changes
that make future performance worse, coverage, cost, pass-to-fail regressions,
and regret from selecting the wrong agent. Also report updater quality,
artifact activation, and executor benefit separately when harness, memory, or
skill artifacts evolve.

### Stage E: Prospective Confirmation

Before a new time window begins, fix the task generators, task-instantiation
pipelines, initial evaluator, evaluator-update algorithm and schedule, attack
families, evaluator-selection rule, data-access policy, budgets, agent
optimizer, state policy, randomization, and analysis code. A declared update
rule may create later evaluator versions, but each version and its predictions
must be frozen before the relevant future cohort opens. Keep future real-world
tasks unavailable until their declared maturity time. Only this stage can
support a prospective reliability claim under repeated evaluator-guided
optimization.

## Immediate Work

1. Freeze the Stage 0 contract and add the minimum records for exact agent
   snapshots, persistent state, lineage edges, update artifacts, agent
   optimizers, evaluator versions, feedback, queries, budgets, rounds, and
   epochs.
2. Make both primary metrics, absolute limits, uncertainty, coverage, and
   integrity status equally visible in reports and research summaries.
3. Re-score existing public panels with the Stage A baselines and replay Stage
   C on fixed agent lineages.
4. Run controlled evaluation-context, capability-elicitation, and protocol-
   aware integrity tests before using an uncontrolled self-evolving agent.
5. In parallel, prototype Stage B and adversarial stress tests with held-out
   attack and agent lineages.
6. Once the closed-loop records and fixed-archive replay are reproducible, run
   a small instrumented Stage D pilot. It needs a frozen comparator and valid
   protocol, not a previously declared “winning” static method. Treat evaluator
   evaluator updating and coevolution as optional experimental arms.

This order makes the target errors and optimization budget measurable before a
large paid campaign. It is not a renewed restriction to task selection.

## What Prior Work Does And Does Not Establish

The annotated review in [`literature-review.md`](literature-review.md) covers
psychometrics, active testing, temporal validation, adaptive data analysis,
Goodhart effects, performative feedback, continual learning, self-evolving
agents, dynamic benchmark construction, capability elicitation,
evaluation-context effects, AI control, meta-evaluation, red teaming, and
coding-agent benchmarks.

The strongest cross-cutting conclusions are:

- statistical outcome models and randomized adaptive sampling can reduce static
  evaluation cost under stated assumptions;
- a recent coding-specific IRT extension predicts static task-level outcomes
  for new task sets and model–harness combinations, making it a strong baseline
  but not evidence of temporal or pair-difference accuracy;
- direct, paired comparison is statistically different from estimating two
  independent means or reporting global rank correlation;
- recent self-evolving-agent benchmarks show that task order, persistent state,
  held-out transfer, replay, intermediate snapshots, and cost expose failures
  hidden by a final score, but they do not establish future-task prediction;
- coding-agent evolution work separates current benchmark performance from
  descendant productivity, and separates writing a harness update from the
  executor's ability to use it; neither diagnostic replaces the two MAEs;
- time-based validation is necessary when the task and agent populations
  change;
- evaluator feedback is performative: it changes the agent and may change the
  future repository or task distribution, so retraining or updating is an
  intervention rather than a passive measurement update;
- repeated use of finite test data and optimization of imperfect reward models
  can create selection bias or reward overoptimization;
- controlled sandbagging and capability-elicitation studies show that observed
  behavior may understate known capability, while other evidence finds that
  verbalized evaluation awareness alone has limited or model-dependent effects;
  measure behavior causally rather than inferring intent from awareness;
- AI-control and adaptive-monitor studies show that a static monitor result
  under an unaware attacker does not establish integrity against an agent that
  knows the protocol;
- dynamic and adversarial data collection can expose blind spots but can also
  reduce out-of-domain performance or change model rankings;
- current coding benchmarks show recurring problems with task validity,
  contamination, test-suite completeness, scorer exploitation, and harness
  dependence;
- coding benchmark audits show that stronger tests can reject previously
  passing patches and change rankings, so benchmark integrity and future
  predictive validity must be reported separately;
- model-generated test cases, red teaming, evaluator ensembles, and
  coevolving training systems are plausible components, not proof of the full
  Barcarolle design.

No located work demonstrates the complete target: an evaluation method with
valid outcomes, useful uncertainty, and preserved numerical pass-rate and
pass-rate-difference accuracy throughout a declared self-evolving coding-agent
process. Whether the complete target is achievable, and under which bounded
conditions, is the central open question. Evaluator coevolution is one optional
hypothesis to compare with fixed evaluators, scheduled updating, and other
methods; no located result establishes that it solves the problem.

## Claims Supported By Current Evidence

Current repository evidence supports:

- an auditable static execution and verification boundary;
- calculation of static pass-rate and aggregate pass-rate-difference metrics;
- one narrow retrospective task-selection result with known weighting and
  transfer failures;
- a concrete reason to study agent-family, harness, repository, and temporal
  shift;
- external evidence that repeated proxy optimization and scorer manipulation
  can invalidate fixed evaluators.

It does not support:

- a production evaluator;
- a generated-task distribution that predicts future agent outcomes;
- a method trained directly for pass-rate-difference MAE;
- implemented persistent-state snapshots, complete agent lineages, update
  artifacts, or evaluator-feedback records;
- implemented records and reporting that enforce the operational behavior
  versus elicited capability separation;
- decision-derived absolute error limits;
- robustness under repeated evaluator-guided optimization;
- resistance to Goodhart effects;
- successful adversarial stress testing of evaluators and metrics, or
  agent–evaluator coevolution;
- unlimited or permanent reliability.

Every future report must identify the behavior or capability target, exact
agent snapshot or lineage, state policy, objectives measured, agent-pair
population, optimization budget, feedback channel, evaluator-update rule,
absolute limits, coverage, integrity status, weighting, temporal validation or
test set, and whether the result is retrospective development, rolling-origin,
adversarial stress-test, or prospective evidence.
