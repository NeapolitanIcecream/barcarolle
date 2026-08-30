# Statistical Protocol

Status: current statistical contract, 2026-08-30. Static rolling-origin details
are implemented in part; repeated-optimization and generated-task-validity
details are research targets until the implementation status says otherwise.

This document fixes the statistical meanings used by reliable evaluation of
self-evolving agents, including rolling-origin development studies,
fixed-lineage replay, controlled repeated optimization, and prospective
confirmation. It does not authorize paid execution and does not turn fixture
results into predictive evidence.

The active objective and method contract is
[`research-program.md`](research-program.md). Earlier task-selection plans remain
valid for their fixed experiments, but their pass-rate-only metric priority does
not govern new work.

## Objective Hierarchy

At repository/time cutoff `t`, let `p_t(a)` be agent `a`'s pass rate on the
predeclared future task cohort, let `delta_t(a,b) = p_t(a) - p_t(b)`, and let
`p_hat_t(a)` and `delta_hat_t(a,b)` be predictions made without that cohort's
outcomes.

New studies have two primary losses:

```text
pass_rate_error(t,a) = abs(p_hat_t(a) - p_t(a))

pass_rate_difference_error(t,a,b) =
  abs(delta_hat_t(a,b) - delta_t(a,b))
```

The target difference must be computed from both agents on the same task and
replicate schedule so pairing and covariance are preserved. An evaluator may
predict `delta_hat_t(a,b)` directly or derive it as
`p_hat_t(a) - p_hat_t(b)`; it must fix that contract in advance. If it emits
both direct pair and marginal predictions, also report
`delta_hat_t(a,b) - (p_hat_t(a) - p_hat_t(b))` as a coherence diagnostic.

The second loss uses a predeclared agent-pair population. All-pair,
frontier-neighbor, parent-child, and incumbent-challenger summaries answer
different questions and may not be substituted after outcomes are opened.

Rank agreement, sign accuracy, recommendation regret, top-1 regret, coverage,
invalid rate, and cost are supporting decision diagnostics. None replaces the
pass-rate or pass-rate-difference loss.

For repeated-optimization evaluation, predeclare budgets `b` in evaluator
queries, candidate count, optimizer rounds, feedback bits, compute, or another
exact budget. Report `pass_rate_mae(b)` and `pass_rate_difference_mae(b)`, plus
their within-method increase from the no-optimization baseline (`b=0`). The
full curve is primary; worst error up to each budget, area under degradation,
and the first crossing of a predeclared within-method degradation tolerance
are summaries. A hack detector score is not a substitute for observed
retention of the two prediction losses.

Keep that longitudinal test separate from method selection. When giving
pass-rate-difference MAE decision priority, name a comparator and require, at
every predeclared evaluation budget, `pass_rate_mae_method(b) -
pass_rate_mae_comparator(b)` to remain within a predeclared non-inferiority
margin. Passing the within-method test from the no-optimization baseline
(`b=0`) does not satisfy this comparator-relative constraint, or vice versa.

## Evaluation And Method-Selection Stages

The project mission is reliable evaluation for self-evolving agents. A method
does not earn that claim merely by beating another method. Assess the following
four stages in order, and preserve the result of each one. A reliability claim
must pass Stages 1 and 2, plus Stage 3 when it covers evaluator-guided
optimization. Stage 4 chooses among methods; it cannot compensate for a failure
or unresolved result at an earlier applicable stage.

### 1. Evidence validity

Before scoring accuracy, verify that the evidence identifies the declared
quantity. At minimum, a run must bind:

- the operational behavior or elicited capability estimand defined
  below, including the complete Agent, task, context, and runtime policy;
- the target task source, inclusion policy, time cutoff, label-maturity rule,
  and the independence of the prospective outcomes from Agent and evaluator
  selection;
- task, check, workspace, runtime, agent snapshot, result, and evaluator
  identities, plus the complete parent-to-child lineage when optimization is
  involved;
- common Task and replicate cells for every Agent comparison;
- the treatment of missing, censored, invalid, abstained, and integrity-failed
  runs;
- the feedback, query, candidate, compute, persistent-state, reset, fork, and
  execution-order contracts for an adaptive study;
- executable-check validity and an execution boundary appropriate to the
  declared tampering threat model.

An integrity violation is an integrity outcome, not an ordinary failed Task.
Operational policy may reject it, but statistical reporting must preserve the
invalid status and show the apparent and verified results separately when both
exist. If any required identity, chronology, denominator, or independence
claim is unresolved, the accuracy result is conditional or descriptive and
does not pass this stage.

### 2. Absolute error limits

Before outcomes are opened, derive two absolute error thresholds from the
deployment decision:

```text
tau_rate        = maximum acceptable pass-rate MAE
tau_difference  = maximum acceptable pass-rate-difference MAE
```

For one deployment decision, these thresholds are fixed across optimization
budgets. A budget-dependent decision is a separately named claim with separately
derived thresholds, not a relaxation within one error curve. The thresholds are
not comparator-relative margins and may not be fitted to the method landscape.
Unless a stricter rule is predeclared for a critical stratum, the same two
thresholds apply to the declared aggregate and to every critical stratum.
Critical strata are chosen from deployment consequences before outcomes, for
example repository families, Agent or harness families, parent-child
transitions, task classes, or integrity-relevant conditions. Post-hoc worst
slices are diagnostics, not confirmatory strata.

For method `m`, budget `b`, and required aggregate or critical stratum `g`, an
absolute-error-limit claim requires simultaneous one-sided upper confidence
bounds `U_rate(m,b,g)` and `U_difference(m,b,g)` satisfying

```text
U_rate(m,b,g)        <= tau_rate
U_difference(m,b,g)  <= tau_difference
```

The uncertainty procedure, family of budgets and strata, dependence unit, and
multiplicity control must be frozen before outcomes. It must preserve paired
Agent outcomes, shared Agents across pairs, task/dependency clusters, optimizer
seeds, and lineages as applicable. A point estimate below a threshold is not a
pass when its uncertainty crosses the threshold. Too few independent units,
an unidentified dependence structure, or an empty critical stratum yields
`unresolved`, not success. Abstention passes this stage only through a
predeclared risk-coverage target and an unconditional fallback policy; it may
not remove difficult strata from the target silently.

### 3. Degradation under optimization

For repeated evaluator-guided optimization, the absolute error limits must
continue to hold at every predeclared budget. Separately define within-method
degradation from the same method's no-optimization value:

```text
degradation_rate_m(b) =
  pass_rate_mae_m(b) - pass_rate_mae_m(0)

degradation_difference_m(b) =
  pass_rate_difference_mae_m(b) - pass_rate_difference_mae_m(0)
```

Predeclare tolerated degradation and simultaneous uncertainty across all
budgets and critical strata. A method that starts inaccurate but degrades
little does not pass the absolute error limits. A method that remains within
those limits but crosses its degradation tolerance may support a bounded static
claim, not a degradation-under-optimization claim. Report the complete curves;
a favorable endpoint cannot erase an earlier crossing.

### 4. Method comparison

Only after reporting every applicable earlier stage compare methods. For a
static `b=0` study, the degradation-under-optimization stage is
explicitly `not_applicable`, not silently passed. Use matched cohorts, common ancestors,
paired optimizer seeds, the same budgets, and a named comparator. Giving
pass-rate-difference MAE
priority requires the predeclared pass-rate-MAE non-inferiority margin at every
budget, with simultaneous uncertainty. Then compare average and
critical-stratum pass-rate-difference MAE. A method can meet the absolute error
limits without being better than its comparator, or beat its comparator while
still being unacceptably inaccurate; report those conclusions separately.

The two primary errors, their absolute thresholds, adaptive degradation,
coverage, cost, and integrity remain separate fields. No weighted or
compensatory aggregate may turn failure of one into a reliability claim.

## Adaptive Allocation And Design Weighting

An allocator that targets informative tasks changes the sampling design. For a
declared finite frame, predeclare one complete estimator contract:

- Horvitz-Thompson uses positive final inclusion probabilities `pi_i`,
  inverse-inclusion weights, and a variance estimator matched to a declared
  unequal-probability without-replacement or Poisson design;
- Hajek uses the same `pi_i` with normalized ratio weights and is labeled with
  its finite-sample ratio bias;
- Hansen-Hurwitz with replacement persists each draw probability and uses
  draw-level inverse-probability weights plus a matching variance estimator;
- sequential without-replacement LURE persists every conditional proposal
  `q_m(i | history)` and uses its step-specific leveled weights, not HT's
  `1/pi_i` weights.

Persist draw scheme, estimator/version, `pi_i` or the full `q_m` history as
applicable, realized weights, and variance protocol. Do not mix their weight or
variance formulas. A deterministically selected subset mean is a property of
that subset; it is not an unbiased estimate of the full frame merely because
the tasks are informative.

For pass-rate-difference estimation, run both agents on each sampled task and
design acquisition around the paired outcome `Y(a,i) - Y(b,i)`. Predicted discordance
`P(Y(a,i) != Y(b,i))` is a natural information proposal, mixed with one-agent
uncertainty, coverage/drift, cost, and a nonzero stratified-random exploration
floor. The response or IRT model proposes tasks; persisted
estimator-specific probabilities and weights protect the target mean over the
predefined task population.

Design weighting does not solve temporal or synthetic-to-real shift. A
historical/generated frame still needs a frozen future-mixture claim and a
temporal validation boundary.

## Time And Cohorts

- Task arrival is `TaskRecord.task_material_available_at`.
- Label maturity is the later of task and Check material availability, subject
  to strict-prospective Task Pool availability.
- An origin's history cohort contains arrivals at or before its as-of cutoff.
  Its future cohort contains arrivals after that cutoff and inside the frozen
  future window.
- A fixed nonnegative maturity lag sets the future label cutoff to
  `future_window.end + maturity_lag_seconds`.
- Arrived refs without a mature label remain right-censored. They stay in the
  Origin and source-event evidence but do not enter training, Agent execution,
  denominators, or MAE.

`strict_prospective` uses what the live system could have known at the origin.
`counterfactual_replay` reconstructs historical material availability and may
predeclare the future cohort, but Runner still freezes every Selection before
opening future Result evidence. Reports must name the mode; the two are not
interchangeable claims.

The batch `evaluate_selectors` Runner supports counterfactual replay with a
predeclared future cohort. Strict-prospective evaluation is two-phase:
`select_benchmark` freezes an Origin with a declared future window but no future
refs, then `evaluate_prospective_selection` links a later immutable Task Pool to
the CellSet. Before supply reads, it reloads Selector, Origin, FeatureSnapshot,
SelectorInput, and Selection, replays deterministic inference, resolves every
frozen pre-origin Result ID/digest, and verifies its Agent/history/cutoff scope
and Feature provenance. It also proves the Result cache identity projects to
the frozen Agent before supply reads. After validating the selection-time pool
and replaying Origin, it verifies Task/Check cache identity and exact
`task_count`/`task_stratum` Feature provenance before opening the later pool.
That pool must preserve the bound repository, stable task-generator behavior, source
protocol, and certification configuration; cover the complete declared future
interval; postdate the Selection; and be observed through the label-maturity
cutoff. It may contain only the later increment or a cumulative history.
Overlapping same-ID Task/Check records must remain unchanged. Run identity,
observed frame, and output inventory may change without changing task-generator
behavior.
Reporting reloads both pools and recomputes mature and censored refs before
supporting a prospective claim. The original Origin and Task Pool are never
rewritten.

For strict-prospective live execution, Result observation time is audit
evidence. Barcarolle-managed Results use the recorded local observation time.
Imported Results default to an import-time floor, preventing late evidence
from entering an earlier Origin. An explicit
`producer_attested_historical_v1` policy may preserve the producer's source
timestamp, but reports label that history as producer-attested; it does not
become a Barcarolle observation-time claim.

That rule governs strict-prospective execution and audit. It is not a
requirement for an offline counterfactual algorithm study. Such a study may
collect Agent outcomes today, order Tasks by their declared historical time,
and expose only history Tasks and the inputs allowed by the experiment at each
rolling Origin. The Result observation timestamp does not enter the estimator.

## Evidence Claim Lattice

Claim strength is a product of independent evidence axes, not one ladder:

- supplied Task Pool bundle and cross-record consistency;
- observed source-frame identity and authority;
- task-generator behavior and source-protocol continuity;
- executable Check certification and hidden-oracle binding;
- Agent/Task/Check/Workspace/Runtime Result identity;
- Result-source and availability provenance;
- rolling-origin chronology, maturity, censoring, and leakage replay;
- downstream field or tuning outcomes.

The machine claim `task_pool_bundle_internal_consistency` proves only the first
axis. A frame-free user pool remains usable, but cannot support a source-frame
or population-coverage claim. A producer-attested frame requires the declared
blind spots and authority; source-authoritative frames additionally require
their authority receipt. An observed frame is an inventory of what was seen,
not proof that the underlying population is complete.

Prediction-error estimates from a generated or user-supplied pool are
conditional on the exact frozen pool and whatever source-frame/protocol
evidence is present. Generalization to natural future traffic additionally
requires a defensible source protocol, prospective behavior continuity, and
enough future Origin blocks. Reporting must not infer those axes from internal
bundle validity.

## Dependence And Stratification

`dependency_cluster_id` is protocol-only metadata for filtering and blocked
history/future evaluation. It is never a Selector feature. A cluster must be
derived from sanitized, reproducible source relations by a concrete adapter;
caller labels without relation evidence are not proof of cluster correctness.

`sampling_stratum` is a separate visible label for coverage, task difficulty,
or future-composition analysis. It may enter a FeatureSnapshot as
`task_stratum`. Every frozen value must replay against its TaskRecord, known-at
time, and Task digest before it can support execution or a report. A stratum is
not evidence of statistical independence.

The fixed Pylint adapter implements the first concrete dependency protocol as
`pylint_trusted_patch_path_components_v1`. It reads trusted certification-side
reference patches, persists only each SourceEvent's patch digest and exact
repository-relative changed paths, creates an undirected edge for exact path
overlap, and assigns deterministic connected-component IDs. The evidence is a
self-digested adapter artifact at `records/adapter-evidence.jsonl`. Generation
provenance binds its ref and digest as run-specific sidecar evidence while
keeping stable behavior inventory-independent. Loading validates the complete
Task Pool bundle, re-derives the artifact from local patches, and checks every
persisted SourceEvent cluster before any paid stage.

Exact path overlap is a conservative, coarse relation: overlap is evidence of
dependence, while no overlap is not proof of independence. Issue/PR links,
reverts, and cherry-picks should be added by a concrete adapter only when its
source data actually supplies those relations. Neither patch text, relation
paths, nor cluster IDs enter Selector features or solver-visible task material.

Report these two dependency views for each applicable pass-rate or
pass-rate-difference target:

1. realistic traffic, where dependency clusters may recur but uncertainty is
   blocked by an appropriate independent unit;
2. unseen-cluster generalization, where future dependency clusters are absent
   from history.

## Comparable Static Evaluator Evidence

Pass-rate-error comparisons accept `future_pass_rate_mae` records that:

- aggregate all Agents;
- are `complete` or `complete_with_exclusions`;
- bind the same Task Pool, budget, metric config, join policy, and denominator
  policy;
- include every registered Selector at every included Origin;
- bind exactly the same future Result evidence for all Selectors at one Origin.

Pass-rate-difference comparisons use `pairwise_gap_mae` computed from the same
selected and future matrices, same Agent set, same Agent-pair weighting, and same common
Task/replicate cells. They must satisfy the same completeness, identity,
denominator, and future-evidence conditions. A new report may not call a
pass-rate-difference summary an equal primary result until Reporting validates
and recomputes that
complete chain; the current pass-rate-only report summary remains an
implementation gap.

Learned-Selector fitting additionally requires one ordered full AgentRecord
digest binding across all training Origins. Every Result used for the fitted
loss must project from its cache identity to that frozen Agent binding; matching
an `agent_id` string alone does not define a stable treatment. The trainer also
loads the common frozen Task Pool, validates every Origin and Snapshot against
its Task/Check records, and requires each Result cache identity to project to
those records before the loss can affect fitted parameters.

Agent separation follows the claim. Predicting one known Agent's performance
on future Tasks should retain that Agent and hold out future Tasks. Claiming
transfer to a previously unseen Agent additionally requires evaluation Agent
identities whose outcomes did not influence algorithm design. Claiming
repository or source transfer requires a corresponding repository or source
split. These are optional stronger claims, not common admission rules for
algorithm development.

Predicting an Agent pass-rate difference additionally requires both Agent
identities to be fixed
before outcome inspection. When the pair represents a parent-child transition,
record lineage and agent-optimizer evidence; when it represents model or Harness
transfer, freeze that crossed claim explicitly. Pairs sharing an Agent are
dependent and cannot be counted as independent sample units.

An Origin's future weight is the number of distinct mature Task/Check refs with
Result cells after common benchmark-owned exclusions. Planned refs with no
scoreable Result do not increase the weight.

For Selector `s` with Origin losses `L(s, o)` and future weights `n(o)`, report:

- macro-Origin MAE: `mean_o L(s, o)`;
- future-task-count-weighted MAE:
  `sum_o n(o) * L(s, o) / sum_o n(o)`;
- for every canonical Selector pair `(a, b)`, paired differences using
  `L(a, o) - L(b, o)` under both weightings. Negative favors `a`.

Here `(a, b)` in the last bullet denotes two evaluator/Selector candidates, not
two tested Agents. To avoid that overloaded notation, new artifacts should call
them `(e1, e2)`. Separately report tested-Agent
`pass_rate_difference_error(t, agent_a,
agent_b)` over the frozen Agent-pair population, with macro-Origin and declared
traffic weighting. Do not confuse evaluator-to-evaluator loss contrasts with
Agent pass-rate-difference prediction error.

The pairwise table lets a report identify a predeclared fallback without adding
fallback identity to Result or Metric records. Choosing a fallback after
looking at the table is exploratory, not confirmatory.

## Multi-Repository Rolling-Origin Evidence

Each Task Pool, Origin, SelectorInput, and Selection remains repository-local.
A multi-repository study is a collection of those local replay chains. It does
not combine Tasks from different repositories into one eligible pool.
This section governs offline research, training, and validation; a normal
Runner invocation still consumes one user repository and one local Task Pool.
Cross-repository aggregation combines effects and evidence, not candidate
Tasks.

For Selector `s`, repository `r`, and Origin `o`, define the paired contrast

`D(s,r,o) = L(s,r,o) - L(full_history,r,o)`,

where negative values favor Selection. Aggregate Origins within each
repository first:

`D(s,r) = mean_o D(s,r,o)`.

The primary portability estimand is the macro-repository mean
`mean_r D(s,r)`. Future-task-count or deployment-volume weighting is secondary
and must retain the per-repository table. Report the number of repositories
with favorable direction and the upper quartile of `D(s,r)` so a good mean does
not imply universal transfer. Origin rows from different
repositories must not be flattened and treated as independent evidence.

Uncertainty is blocked at the highest dependence level supported by the
portfolio. Forks, mirrors, shared task lineages, and mechanically derived
repositories use one declared repository cluster unless independence is
justified. The primary interval resamples those clusters. Origin-block
intervals remain within-repository diagnostics. Report leave-one-cluster-out
sensitivity so one repository family cannot silently determine the result.

A learned policy uses nested held-out-repository evaluation to prove that
offline training did not overfit its research repositories. For outer target
repository `r`, fit the complete policy and choose all hyperparameters using
other repositories and their inner earlier Origins only. Freeze the policy,
then apply it only to eligible local history in `r`; open `r`'s future Results
after its Selection is frozen. This is a validation fold, not a
multi-repository runtime. A target with no eligible local history is a
different cold-start estimand.

The default training loss gives every training repository equal total weight
and weights its Origins equally within the repository. Task-count or
deployment-volume weighting is secondary and may be selected only inside the
training folds.

Report two portfolio views separately:

- a wide view with many independent repositories and few mature Origins,
  measuring portability;
- a deep view with longer histories, measuring temporal drift, horizon
  robustness, and within-repository learnability.

The first comparison fixes the importer or task-generation approach, certification
policy, Agent panel, metric, and budget policy so repository is the primary
varying axis. Held-out-Agent transfer is a separate crossed study. Random
landscape, support, oracle, horizon, and dependency diagnostics are first
computed per repository and only then summarized.

The `0.02` macro-repository margin used by the 2026-07-28 study remains that
study's preregistered promotion rule; it is not a universal suitability or
algorithm threshold. A new study must predeclare a deployment-derived useful
margin before outcomes. Without one, report the paired repository-cluster
interval, leave-one-cluster-out views, and design resolution, but keep the
result descriptive. A later frozen source or strict-prospective campaign is
still required for an external predictive-validity claim.

The current `train_selector` implementation requires every training Origin to
use one Task Pool. Therefore fixed Selectors can be evaluated under this
protocol now, but a globally fitted policy is not executable evidence yet.
When a concrete learned family and enough outer folds exist, the minimal
extension is a sequence of independently validated repository-local training
evidence groups that produces the existing `SelectorRecord`; inference remains
one-Task-Pool, repository-local.

## Repeated-Optimization Evidence

A robustness-under-repeated-optimization claim requires a fixed experiment
tuple:

- declared operational behavior or elicited capability estimand and
  evaluation context;
- initial Agent snapshot and full Agent identity;
- agent-optimizer implementation and version;
- candidate, query, token, time, and compute budgets;
- initial evaluator artifact and its frozen Task, Check, estimator, feedback,
  selection, and update policies;
- what the optimizer sees: aggregate, rounded/thresholded score, per-Task
  result, test output, trace, or another exact channel;
- Agent snapshot, parent, mutation, persistent state, round, branch, and epoch;
- every candidate considered, not only the evaluator winner;
- optimization budgets and stopping rule;
- future real-world task window and maturity rule;
- Agent-pair population, weighting, margins, and analysis code.

An **Agent snapshot** is the immutable state from which one optimization step or
evaluation run starts. It binds the model or provider snapshot, harness and
code revision, persistent or system prompts and skills, tools and permissions,
retrieval material, generation and runtime policies, optimizer-visible memory,
filesystem state, and every other persistent input. Task or user inputs and
temporary cues are recorded as run contexts, not snapshot identity. Large or
secret state may remain in ignored or protected
storage, but its content digest and immutable reference must be recorded.

A **parent-to-child transition** binds one parent snapshot, one proposed child,
the exact mutation or training operation, optimizer seed, evaluator feedback
consumed, budget used, persistent-state change, acceptance decision, and
timestamps. Rejected candidates remain in the archive. The independent unit
for a self-evolving process claim is a complete lineage/process run: one root
snapshot plus its ordered transition and branch history under a frozen process
policy. Siblings, checkpoints, and Agent pairs that share a lineage are
dependent observations, not extra independent runs.

Every study must predeclare these state contracts:

- **persistence**: which conversation, memory, retrieval index, optimizer
  state, caches, files, and external resources survive a Task, round, or epoch;
- **reset**: the exact snapshot restored between replicates and evaluator
  conditions, including cleanup of side effects outside the repository;
- **fork**: all compared branches start from the same verified ancestor
  snapshot, with only the assigned treatment allowed to differ;
- **order**: Task, candidate, feedback, branch, and evaluator-update order is
  frozen or randomized by a persisted schedule;
- **resume**: an interrupted branch resumes only from its recorded snapshot
  and order position, never from the most convenient later state.

State that is intentionally carried forward is part of the Agent or optimizer
treatment. State that leaks across branches violates the comparison rather
than constituting harmless execution noise.

Freeze the evaluator **update policy**, not one evaluator artifact forever.
Within an epoch, the artifact and feedback contract are fixed. At a declared
boundary, the frozen policy may construct, select, or recalibrate a new
artifact using only eligible data. Persist every evaluator version, parent,
training inputs, attack suite, selection outcome, and effective epoch.
Off-schedule updates or changes chosen after viewing outer outcomes invalidate
the confirmatory branch. Open evaluator-selection temporal validation only
after that epoch's Agent search ends. Once validation or test outcomes influence
evaluator generation, attack design, selection, or hyperparameters, they become
development evidence and a new prospective test set is required.

The main controlled comparison forks all evaluator conditions from the same
initial Agent snapshot and holds the agent optimizer, search budget, task
schedule, repository Origins, and outcome policy fixed. Compare at least a
    static baseline, one frozen static comparator that passes the evidence-validity
    preflight, an update-only candidate, and any adversarially updated or
coevolving candidate. Pair optimizer seeds across branches and run enough
independent root lineages to measure process stochasticity.

Use the same hidden future cohort for all branches whenever possible. If
calendar-time deployment makes that impossible, run conditions concurrently on
randomized draws from one declared source frame or retain a contemporaneous
control branch spanning every period. A raw comparison of one evaluator's
early lineage with another evaluator's later lineage confounds evaluator effect
with task, model-supply, and calendar-time change. A time-adjusted analysis must
be frozen in advance and preserve the concurrent controls; a sequential
before/after contrast alone is insufficient.

Report pass-rate and pass-rate-difference loss at every predeclared
optimization budget. Also report accepted transitions whose evaluator score
improves while performance on future real-world tasks or the direction of an
Agent difference worsens, but keep that diagnostic separate from the primary
error curves. No result supports an unbounded "Goodhart-resistant" claim.

Adversarial Tasks and controlled-agent attacks belong to separately labeled
stress strata. Retain a probability sample of newly arriving real-world tasks. An
adversarial slice may affect evaluator promotion only through a frozen rule and
may not silently redefine the natural-work pass-rate target.

## Evaluation-Context Diagnostics

Evaluation awareness is a possible cause of error, not a third primary metric.
When the threat model includes context-sensitive behavior, predeclare two or
more run contexts and randomize them over the same Task, replicate, Agent
snapshot, and runtime schedule. This same-snapshot contrast is valid only when
the contexts vary task or user input and temporary cues allowed by the frozen
agent and runtime policy. A context may include framing and interface cues,
test or scorer visibility, feedback exposure, monitor disclosure, tool names,
workspace layout, and statements about training, evaluation, or deployment.
An intervention that changes persistent configuration or the generation, tool,
or runtime policy is instead a parent-to-child version comparison.

For two contexts `c1` and `c0`, retain the Agent-level context contrast

```text
context_effect_t(a; c1, c0) = p_t(a,c1) - p_t(a,c0)
```

and, for a fixed Agent pair, the difference-in-differences

```text
pairwise_context_interaction_t(a,b; c1,c0) =
    [p_t(a,c1) - p_t(a,c0)]
  - [p_t(b,c1) - p_t(b,c0)]
```

The second quantity detects context effects that do not cancel in an Agent
comparison and can therefore bias pass-rate-difference prediction even when
both Agents change behavior. Preserve common Tasks and replicates and use the
highest supported randomization/dependence unit. Report the interaction by
Agent family, harness, lineage relationship, and optimization budget when
those groups were predeclared.

An overt-evaluation versus deployment-like prompt contrast identifies only the
effect of those constructed cues. It does not establish the true deployment
gap unless the deployment context and sampling process are externally
validated. A large or unresolved context interaction requires a
context-specific prediction, an abstention/fallback, or a narrower claim; it
cannot be averaged into either primary MAE or used to compensate for one.

## Deployment Unit And Estimand

Keep operational behavior and elicited capability as different
estimands.

- **Operational behavior** is the pass rate of one fully specified Agent
  snapshot under the declared deployment harness, tools, permissions,
  prompting policy, persistent state, retry, and runtime policy on future real-world
  Tasks. This is the default primary target for Barcarolle because it predicts
  what that deployed system will do.
- **Elicited capability** is the performance reached by a predeclared family of
  elicitation procedures under a fixed access and search
  budget. The family may include prompting, sampling, demonstrations, tools,
  scaffolds, or weight updates only when those interventions are in scope. It
  is a separate safety or diagnostic claim.

Every elicitation procedure that changes weights, persistent prompts or
configuration, harness, tools, retrieval, generation policy, or runtime policy
produces a new Agent snapshot with a parent link. Varying task or user prompts,
sampling draws, or temporary cues within a frozen policy is a run-context
condition for that snapshot instead. For an elicited capability claim, the
protocol may attribute a child to the declared parent and elicitation budget,
but it may not erase the changed Agent identity. Selecting the best elicitation
on one cohort creates selection bias;
freeze the chosen procedure using inner data and estimate its performance on a
separate future cohort. The observed maximum over an opened search archive is
an oracle diagnostic, not an unbiased capability estimate.

Operational behavior and elicited capability forecasts need separate
predictions, threshold decisions, and claim labels. A successful elicitation
audit does not validate the operational forecast, and failure to elicit a
planted or otherwise known capability is a false negative rather than evidence
that the capability is absent. When weights or training access are unavailable,
the capability claim is explicitly limited to the permitted black-box
elicitation family.

Agent-pair targets must use the same estimand, context, access level, and
elicitation budget for both Agents unless the asymmetric policy is itself the
predeclared deployment target. Do not subtract an operational pass rate for one
agent from an elicited capability rate for another. Report any asymmetric
elicitation success as a diagnostic because it can create a spurious Agent
difference.

The pass-rate-prediction deployment unit is one target Agent and one repository.
The pass-rate-difference deployment unit is one predeclared Agent pair and one
repository. For method `m`, retain the direct pass-rate loss

`L_m(r, o, a) = abs(selected_rate_m(r, o, a) - future_rate(r, o, a))`

before every aggregation. The paired effect is

`d_m(r, o, a) = L_m(r, o, a) - L_full(r, o, a)`.

For Agent pair `(a,b)`, also retain

`G_m(r,o,a,b) = abs(delta_hat_m(a,b) - delta_future(a,b))`.

The prediction `delta_hat_m(a,b)` may come from a direct pair model or from
`p_m(a) - p_m(b)`. When both forms are available, also retain their coherence
residual.

The common Task/replicate design is part of the target. Do not calculate the
two future pass rates from independently selected Task sets and call the result
paired.

The current repository-equal summary is the realized average loss or paired
effect on the exact finite Agent-by-repository-by-Origin panel. It does not by
itself identify the expected loss of a particular Agent-by-repository
deployment unit or of a new Agent or repository population. Such an expectation
requires a declared target distribution and a sampling, stationarity, or
exchangeability assumption.

Every committed development summary must retain Agent-by-repository joint
cells in addition to repository and Agent marginals. For each candidate report
cell origin count, MAE, paired difference, favorable/harmful/tie counts, simple
quantiles, and the worst harm. Repository and Agent marginals can both be
favorable while one joint cell is harmful.

These cell summaries describe heterogeneity on the opened finite panel. Unless
frozen from a target utility before scoring, favorable-cell counts, quantiles,
and worst harm are descriptive diagnostics, not additional promotion gates or
estimates of future deployment-cell effects.

Keep these targets distinct:

- realized next-H fidelity treats the observed next-H block as the target
  cohort. Once observed, its pass rate is not a noisy estimate requiring
  correction; uncertainty concerns performance over other Origins or future
  cohorts;
- latent target-task-distribution pass probability treats next-H as a sample
  from a declared population and requires a separately frozen target
  population, sampling or measurement model, and dependence assumptions.

Do not interpret the first as the second. Under absolute loss, a point forecast
of a random future rate, when the action is an unconstrained scalar, targets a
conditional median. A budgeted Task Selection is a constrained subset action
and need not attain that median. Direct realized next-H pass-rate MAE and direct
Agent-pair pass-rate-difference MAE are the two primary metrics. A variance
model, reliability coefficient,
rank statistic, or latent-rate estimate is diagnostic unless separately named
as a secondary claim.

## Implemented Static Selection Annex

The remainder of this annex documents the implemented or concretely frozen
static rolling-origin task-selection path, including exact code records such as
`Selector`, `SelectorInput`, and `Selection`. It preserves reproducibility for
earlier studies and supplies baselines for the broader evaluator program. It is
not a restriction to task selection, does not give these algorithms research
priority, and does not replace the earlier reliability stages above.
Where a paragraph says a feature is not implemented, that narrower status
still controls.

### Baselines And Landscape Diagnostics

For static task sampling or compression, the primary baseline is every
eligible historical Task/Check ref without task selection. Its benchmark may be
larger and more expensive than the selected benchmark. This is a required
compression baseline, not the definition of the project.

Pass-rate-difference studies compute Full, recent, random, and candidate
predictions on the same Agent pairs. Task-generation studies additionally
compare real-only, passive/random generation, and adversarial generation at
matched execution budgets. Repeated-optimization studies compare static,
update-only, and coevolving evaluator
conditions with the same Agent optimizer and search budget.

Before interpreting a candidate, report whether the Task Pool, Agent panel,
horizon, and aggregation form an informative regime for pass-rate MAE. At
minimum report:

- positive outcome density by Agent and repository;
- the shares of Agent-Origin future blocks with pass rate zero and one;
- always-zero and always-one MAE;
- a fully specified cutoff-safe constant forecast fitted only from evidence
  admitted by the candidate's information contract, using a median when it is
  optimized for absolute loss;
- full-history MAE;
- equal-budget random loss and discrete hindsight-oracle loss.

These controls do not replace full history as the primary no-Selection
baseline. A target-Agent expanding climatology is admissible only in a
cached-target lane; it cannot gate an unseen-target Selector. These diagnostics
determine whether a low absolute MAE reflects nontrivial prediction or only
outcome prevalence and discrete score support.

For every small future horizon, also report:

- H-block score granularity and zero/one block shares;
- Full and trivial MAE at fixed H sensitivities;
- empirical adjacent-block and split-block stability;
- an exact descriptive decomposition of realized future-block variation into
  fitted Agent, repository, Agent-by-repository, and within-cell block
  components on the opened frame;
- a clearly labeled finite-block variance approximation.

These fitted sample-mean components are not population variance estimates,
causal shares, reliability coefficients, or proof of temporal stability.
Do not treat Tasks as IID Bernoulli draws unless the source design establishes
that assumption. A `1/H` variance pattern is evidence consistent with finite
block averaging, not proof that all remaining variation is sampling noise.

Every pairwise control comparison must use identical rows. If a lagged control
is unavailable on early rows, report its coverage and recompute the candidate
or baseline on that matched subset.

Keep method-specific claims separate:

- Task-selection/compression evidence requires candidate pass-rate MAE below full
  history; equal-budget random locates the candidate in the sampling space.
- Nontrivial-prediction evidence requires candidate MAE below a trivial
  estimator admitted by the same information contract.
- Pass-rate-difference evidence requires candidate pass-rate-difference MAE
  below its matched Full/random baselines on the fixed Agent-pair population.
- Repeated-optimization method comparisons require both primary errors to be
  compared with the named baseline at every matched optimization budget.
  Robustness evidence separately requires each method's two error curves to
  stay within their predeclared degradation limits from that method's own
  no-optimization baseline (`b=0`), not merely to achieve a higher final
  evaluator score.

Within the task-selection pass-rate lane, a strong nomination requires the first
two claims. Failure of nontrivial prediction does not erase a separately
labeled candidate-versus-full compression result. A complete evaluator
nomination additionally requires the fixed pass-rate-difference claim;
repeated-optimization nomination additionally requires the error curves by
optimization budget.

When `MAE_full > MAE_oracle`, report

`selection_capture = (MAE_full - MAE_candidate) / (MAE_full - MAE_oracle)`.

When `MAE_trivial > MAE_oracle`, also report

`captured_headroom = (MAE_trivial - MAE_candidate) / (MAE_trivial - MAE_oracle)`.

Keep direct pass-rate and pass-rate-difference MAE as separate primary metrics,
and keep random percentiles separate. Do
not report either ratio when its denominator is nonpositive or when its rows
differ in Task, Check, Agent/pair, Origin, denominator, weighting, budget, or
oracle evidence.

A regime identity includes Task Pool, Agent panel, Selection unit, information
contract, horizon frame, denominator, Origin construction, and aggregation.
Do not label a whole source from one estimator lane. Before
deployment-specific thresholds exist, use descriptive terminal states such as
`descriptive_only`, `not_evaluable`, or `normalization_failed`; do not infer a
universal `failure`, `stress`, or `usable` boundary from one opened panel.

For the current Multi-SWE projection, H5 full history and retained
unseen-target candidates are dominated by always zero under the end-aligned
equal-repository view. H10 has a favorable full-history point estimate whose
sign is sensitive to repository and Origin construction. The corrected claim
boundary is recorded in
[`experiments/2026-07-30-multi-swe-failure-region.md`](experiments/2026-07-30-multi-swe-failure-region.md).

An equal-budget random Selection is calibration, not the primary baseline.
Report its loss distribution or a predeclared seed bank and locate the
candidate within it. State whether Origins draw independently or share a
reproducible seed. When a finite outcome-category model permits an exact
distribution, report its expectation, quantiles, candidate percentile,
as-good-or-better mass, elite means, and expected best-of-draw frontier. A
fixed-seed sensitivity checks whether cross-Origin coupling changes the
conclusion.

Continuous historical support and a discrete hindsight budget oracle are
endpoints. They may open future outcomes to measure representability and search
density, but cannot enter Selection or be reported as learnable algorithms.
Low support loss does not establish that pre-origin features can identify the
corresponding subset.

A future-open reference-Agent Oracle additionally measures contemporaneous
cross-Agent capacity. It does not establish that the reference vector can be
forecast from history or that its macro gain transfers to every
Agent-by-repository cell. Report its joint-cell directions and compare
same-future association with the corresponding pre-Origin lagged association.

A response-matrix or Item Response Theory subset is first a fixed-universe
compression comparator. Fit item parameters only from reference-Agent Results
available before the evaluation boundary, then freeze the subset before
opening disjoint held-out-Agent or later-Origin outcomes. Report held-out
reconstruction of the complete historical benchmark separately from
later-Origin future MAE. Accurate historical score reconstruction cannot by
itself clear the temporal promotion gate.

When the IRT or outcome model drives adaptive allocation, retain positive
sampling probability and design weighting as specified above. Difficulty and
discrimination may vary by time, Agent lineage, model family, harness, and
task generator; differential-item-functioning or comparable residual checks are
required before interpreting them as invariant Task properties.

The earlier `0.02` macro-Origin rule remains a legacy study-specific gate. New
algorithm work must freeze its deployment-derived useful margin and highest
valid dependence unit before outcomes. Random-space position, support, null
controls, rank agreement, and recommendation regret remain separately labeled
diagnostics. Changing a primary metric, Agent-pair population, dependence
unit, or practical margin after outcomes open is exploratory.

Every temporal null must state what it destroys and preserves. A joint-response
circular shift preserves response prevalence, Agent dependence, and almost all
local and long-range adjacency; it tests absolute phase alignment with fixed
Origin cutoffs, not whether chronology contains any predictive structure.
Shuffling complete adjacent H-task blocks destroys block order while preserving
within-block joint responses and instead tests block-level persistence. When
multiple Agents share a block, use one common block order per repository so the
null also preserves same-block cross-Agent dependence. An
unrestricted row permutation asks a still different, stronger
exchangeability question. Report these probabilities separately and do not
use failure of a narrow null to reject mechanisms outside that null.

Predeclare the future-block horizon from the deployment question. When more
than one reasonable horizon exists, report a fixed block-size sensitivity and
dependency-deduplicated view without selecting the most favorable result.
Changing sign across those views is a robustness failure even if one point
estimate is favorable.

### Shrinkage Safe Switch

ALG-001 uses the same complete paired Origin rows. For candidate `s`, fallback
`f`, and `n` prior Origins, define improvement `d_o = L(f,o) - L(s,o)` so
positive values favor the candidate. With prior strength `p`, the shrunk mean is
`sum_o d_o / (n + p)`. The conservative score subtracts
`uncertainty_multiplier * sample_standard_error(d)`.

The current default is `p=2`, at least four Origins, zero improvement margin,
and uncertainty multiplier one. A candidate is eligible only when its
conservative score strictly exceeds the margin; the largest score wins, with
Selector ID as the deterministic final tie-break. No prior history, fewer than
the minimum Origins, or no eligible candidate returns the predeclared fallback.

This gate is a deterministic decision heuristic, not a calibrated confidence
interval. Prior strength, minimum history, margin, and uncertainty multiplier
must be chosen within nested rolling-origin history. Outer Origins compare the
frozen safe switch against fixed experts, raw mean choice, no-shrink, no-gate,
and hindsight-oracle diagnostics.

`future_coverage` and `future_invalid_rate` remain holdout-evidence diagnostics.
They are not Selector prediction losses.

### Drift-Aware EWMA Guard

ALG-004 uses the same complete paired MAE rows and requires their exact training
`RollingOriginRecord` set plus an explicit deployment Origin. All records must
validate and bind the same Task Pool. Each training origin time and cutoff must
strictly precede deployment, its label-maturity cutoff must not exceed the
deployment cutoff, and the training set must use one comparable policy and
distinct materialized `as_of_cutoff` instants. Rows are ordered by those
instants rather than caller order or Origin ID.

For half-life `h > 0`, give the newest prior Origin age zero and an Origin `a`
steps older weight `2^(-a/h)`. Rank every registered Selector by its normalized
weighted mean MAE. If the fallback ranks first, keep it. Otherwise compare only
the ranked candidate and fallback with ALG-001's ordinary unweighted,
full-history safe-switch rule. A candidate that captures a recent trend but
does not clear that gate cannot be deployed.

The implementation does not attach a confidence interpretation to decayed
weights. The default half-life is two Origins. Nested rolling-origin comparison
predeclares half-lives 0.5, 1, 2, and 4 plus the non-decayed history baseline;
the safe-switch parameters are tuned only inside the same prior history. Outer
Origins compare the frozen choice against fixed experts, non-decayed safe
choice, and raw mean choice. Reject the method if its paired outer-origin MAE
does not improve or if the selected half-life is unstable across adjacent
training windows.

### Stratified Forecast And Weighting

ALG-002 operates on Task/Check refs because that is the Selection and primary
MAE denominator. At an Origin, let `c_s` be the count for stratum `s` among the
last `w` eligible refs, let `S` be all strata present in the eligible history,
and let `alpha > 0` be symmetric. The forecast is

`p_s = (c_s + alpha) / (sum_j c_j + alpha * |S|)`.

For budget `B`, start from `floor(B * p_s)`, capped by the number of eligible
refs in each stratum. Assign remaining seats to the available stratum with the
largest current deficit `B * p_s - quota_s`; forecast proportion and stratum
name break ties deterministically. This is ordinary largest remainder when no
capacity binds and deterministic overflow redistribution otherwise. A seeded
digest rank chooses refs within each stratum.

With selected share `q_s > 0`, the raw post-stratification weight is `p_s/q_s`.
The executable weighted variant stores `min(weight_cap, p_s/q_s)` on every
selected ref in stratum `s`; `weight_cap` must be at least one. The exact
unweighted baseline sets `weight_cap=null` and stores weight one. Existing
selection metrics normalize by the total selected weight.

For each outer Origin, report the total-variation distance between future
stratum proportions and (a) the forecast, (b) the unweighted selected mix, and
(c) the capped weighted selected mix. Also report maximum selected weight, cap
activation fraction, and effective sample size
`(sum_i weight_i)^2 / sum_i weight_i^2`. Alpha, trailing-window length, cap,
and seed are hyperparameters selected only inside nested rolling origins. The
required comparison set is random, recency, coverage, and unweighted
stratified selection. No current synthetic test or implementation status is an
empirical accuracy claim.

### Rank-Mixture Simplex Choice

ALG-003 predeclares the ten coverage/random/recency weight triples whose
components are nonnegative thirds summing to one. This grid includes the three
individual experts, the equal-weight point, and all two-expert thirds mixtures.
All points share the same random seed, coverage mapping, feature classes, and
grid-protocol digest. Each point must produce its own frozen Selection and
paired future MAE through the ordinary evaluation path. Individual expert
losses are not a valid substitute for observing the blended rank Selection.

At deployment with `n` prior Origins, use equal weights when `n` is below the
declared minimum (currently four). Otherwise let `m_j` be each grid point's
mean paired MAE. For the lowest-mean point `j*`, compute the sample standard
error of its Origin losses and set `limit = m_j* + SE_j*`. Among points with
`m_j <= limit`, choose the one minimizing squared Euclidean distance to
`(1/3, 1/3, 1/3)`; then prefer lower mean and Selector ID. This is the discrete
one-standard-error rule, not a confidence interval or proof that equal weights
are optimal.

The outer rolling-origin comparison includes equal weights, each expert, the
current inverse-MAE fitted mixture, and the frozen one-SE choice. Reject the
method if gains disappear out of sample or if seed-bank variation dominates
the paired improvement. The grid and four-Origin gate are predeclared starting
points, not empirically calibrated defaults.

### Stochastic Selectors

Random-seed variants form a seed bank only when Selector family, version,
training sources, allowed feature classes, and every non-seed parameter are
identical. The current recognized seed fields are `seed` for `random` and
`stratified_forecast`, and `random_seed` for `rule_mixture`.

For a bank with at least two variants, report the mean and population standard
deviation of each variant's macro-Origin MAE. Do not pool unrelated fitted
weights or feature contracts merely because their family names match.

A small seed bank is not a dense estimate of the random search space. Use an
exact distribution when the outcome structure permits it; otherwise predeclare
enough seeds or simulation draws for the desired tail resolution and report
Monte Carlo uncertainty.

### Uncertainty

The current offline summary treats each non-overlapping rolling Origin future
window as one time block. With fewer than eight complete blocks, report
`insufficient_origin_blocks` and no interval.

With at least eight blocks, use protocol
`paired_origin_block_percentile_bootstrap_v1`:

- 10,000 deterministic resamples;
- seed `20260722`;
- sample Origin indices with replacement and preserve pairing across all
  Selectors;
- report the linear-interpolated 2.5th and 97.5th percentiles for macro-Origin
  MAE and paired macro loss differences.

This interval describes variation across the included Origin blocks. It is not
cluster-robust when dependency clusters cross blocks, and it does not quantify
run-level Agent variation without explicit replicate evidence.

This implemented two-sided static interval is not automatically the
simultaneous one-sided upper-bound procedure required by the absolute-error-limit
layer. Until a study freezes and validates the relevant multiplicity,
critical-stratum, and dependence treatment, this annex cannot clear that layer
by reinterpreting its percentile interval.

Pass-rate-difference uncertainty preserves the paired Task outcomes and
resamples at the
highest supported dependence unit. Agent pairs that share an Agent and Origins
that share Task/dependency blocks are not independent observations. Adaptive
optimization comparisons additionally preserve agent-optimizer seed, agent lineage,
and evaluator condition pairing; a seed-level interval with too few independent
search runs is reported as unresolved rather than replaced by Task-level power.

### Replicates And Nested Fitting

The next paid paired history should randomize Agent-configuration order within
Task and repeat a predeclared stratified 20–30 percent of Tasks two or three
times. Replicates must be explicit experiment evidence; exact-cache lookup must
not silently choose a latest or best duplicate. A stable core replicate identity
will be added only when the first concrete repeated-run workflow establishes
how those records are reused.

The Pylint experiment layer now freezes that first workflow with
`replicate_schedule.py`. Before any Result evidence is opened, it binds the
exact Task Pool members, two Agent records, base Runtime config, campaign ID,
seed, realized stratified subset, total repeat count, Runtime slot identities,
and every cell's serial order in one self-digested schedule. The subset count
must realize 20–30 percent exactly; largest-remainder allocation preserves the
observed sampling-stratum mix, and digest-ranked choices make the declared seed
replayable without depending on input order. Each Task/replicate block contains
both Agents in a seeded order. The two Agent records must describe distinct
execution configurations after ignoring only `agent_id`; duplicate treatments
are rejected before schedule construction.

Selected Tasks have two or three total observations; all other Tasks have one.
Each replicate index derives a campaign-scoped Runtime config by replacing only
`runtime_config_id` and `stochastic_settings_digest`. That existing exact-cache
dimension names the intended stochastic observation slot: resuming the same
slot reuses it, while a new observation requires another slot or campaign. The
schedule does not add a core replicate record, alter Result selection, or
estimate run-level variance by itself.

The experiment-layer resolver first replays the complete schedule, then joins
each cell to the Result Store with that cell's Runtime config and preserves the
frozen serial order. Resume selects only the first exact missing slot; it does
not choose a latest or best observation. The separate campaign executor requires
a self-digested authority ledger that binds the schedule, Task Pool, Agent set,
Workspace and Runtime configs, endpoint digest, budget, schedule-derived call cap,
one campaign-wide maximum estimated cost per call, and ScoringConfig. Before a
call, the remaining total budget must cover that per-call limit. A returned
Result must not exceed either the per-call limit or the cumulative budget. The
executor preflights all remaining cells but executes at most the first missing
slot per invocation. A durable Result can repair an interrupted completion
event; a stopped cell or result-less reservation cannot retry automatically.
The initializer records authority supplied for a new campaign; it does not
derive authority from the completed pilot. Malformed timestamp, endpoint,
scope, accounting, or pricing-source shapes fail before either ledger file is
created. This reservation guard constrains Barcarolle's estimated-cost
authority; preventing a provider call itself from exceeding the declared
per-call limit still depends on the Agent runtime budget. The call cap is
derived from the frozen schedule rather than supplied again.

At deployment Origin `t`, fitting, algorithm choice, hyperparameters, seed-bank
selection, and uncertainty gates may consume only training Origins whose label-
maturity cutoffs precede `t`. Any tuning within that history uses another
rolling-origin split. Outer-Origin future evidence is opened only after the
deployed Selection is frozen.

Every frozen SelectorInput binds one positive selection limit to the canonical
budget digest derived from that limit. Agent and eligible-ref identities are
unique, and the materialized cutoff is canonical UTC; a self-digested record
that violates any of those intrinsic bindings is not admissible evidence.

ALG-005 remains behind an estimand gate. Existing evidence can reconstruct
usage, a declared pricing view, workspace latency, and exact selected cells, but
the protocol has not chosen among per-Cell p90, whole-Selection total resource,
or bounded-concurrency critical-path time. These targets are not interchangeable.
No resource-constrained choice may claim a hard cap until one target, Agent and
Runtime comparability rule, no-feasible action, nested tuning plan, and
unconstrained Pareto baseline are predeclared.

## Current Claim Boundary

The repository can execute and validate static cohort, censoring, common-task
pairing, and pass-rate/pass-rate-difference metric construction offline. Its
evidence-backed summary, fitting, and promotion path remains pass-rate-MAE
centric. It has no implemented records for agent version history or evaluator
feedback, error curves by optimization budget, validated task generator,
adversarial stress tests of evaluators and metrics, or agent–evaluator
coevolution path.

No deployment-derived `tau_rate` and `tau_difference`, simultaneous
critical-stratum upper-bound procedure, or evidence-validity stage over complete
self-evolving lineages has been frozen and validated. Current results therefore
cannot pass the absolute-error-limit or degradation-under-optimization stages
by default.

Existing outcome-open studies may support narrow development comparisons among
Selectors. The repository cannot yet support a prospective production
evaluator, pass-rate-difference-optimized method, repeated-optimization
robustness claim, resistance to Goodhart effects, or calibrated
target-repository interval. Those require complete
reporting of both primary metrics, enough independent blocks and replicates,
predeclared optimization protocols, and new independent temporal test sets.

The paragraphs below preserve the claim boundaries of earlier dated studies.
They are historical evidence, not the active method roadmap.

The 2026-07-27 follow-ups do not relax this boundary. The source-observed SymPy
view remains fully censored. A separate `label_at_task_arrival`
counterfactual replay is valid for development and reuses exact Results, but it
is not source-attested or strict-prospective.

On that opened SymPy scenario, coverage MAE is `0.1833` versus `0.1933` for
full history. The `0.0100` point gain and paired interval
`[-0.0363, +0.0152]` miss the promotion gate. It is a precursor, not an
independent confirmation.

The 2026-07-28 public multi-repository study adds 500 Tasks, three frozen public
Agent result vectors, seven wide repositories, three deep repositories, and 68
repository-local Origins. It averages Origins within repository before
repositories receive equal weight. Candidate-minus-full-history wide
differences are `+0.0189` for recency, `+0.0398` for difficulty coverage,
`-0.0064` for history match, `+0.0016` for cross-repository mean drift,
`+0.0015` for semantic centroid, and `+0.0377` for semantic facility location.
No candidate passes the opened-data nomination gate.

The history-match control is better than 93.75% of 20,000 equal-budget random
draws, while its interval `[-0.0178, +0.0041]` crosses zero and its deep effect
is `-0.0014`. Hindsight support reaches `-0.1589`, with all seven repository
directions favorable. The pool therefore contains representable subsets, but
the tested outcome-safe features and cross-repository corrections do not
identify them before the future Origin.

Repository-level uncertainty replaces nominal Origin power for the transfer
claim. Candidate-specific repository SDs from this screen imply naive sample
counts ranging from roughly 3 to 28 repositories for a `0.02` effect; because
the routes failed and only seven repositories were observed, none is a frozen
confirmatory target. Fix the next sample size only after a nominated route has
a blinded pilot measuring repository dependence, missingness, and cost.

These studies remain counterfactual and panel-conditional. The source Tasks
have historical arrival times, but Check maturity was projected to Task
arrival. They do not establish strict-prospective validity, held-out-Agent
transfer, source-family portability, or a Runner default, and authorize no
campaign.

The 2026-07-30 SWE-bench Full candidate-free audit adds 2,294 Tasks, eleven
checked public result vectors, ten eligible repositories, 408 H5 Origins, and
201 H10 Origins. Full history beats always zero and more than 99.9% of 20,000
equal-budget random draws at both horizons; exact budget-ten oracle MAE is
`0.013093` at H5 and `0.007353` at H10. The primary H5 joint-future-block-order
probability is nevertheless `0.126437`, above its frozen `0.05` admission
gate. No algorithm ran under that conditional plan. The result closes that
plan, not use of Full as an outcome-open development set. Three Full
submissions overlap reserved Verified Agent identities; this affects only a
claim about transfer to previously unseen Agents.
