# Barcarolle Handoff

Last updated: 2026-08-30.

Start with these documents:

1. [`docs/research-program.md`](docs/research-program.md) — first principle,
   reliability contract, metrics, candidate methods, and experiment sequence;
2. [`docs/implementation-status.md`](docs/implementation-status.md) — what the
   current code does and does not implement;
3. [`docs/research-improvement-backlog.md`](docs/research-improvement-backlog.md)
   — current work packages and earlier evidence;
4. [`docs/literature-review.md`](docs/literature-review.md) — annotated
   literature, transfer limits, and open questions.

The dated material under
`docs/briefings/2026-08-13-future-grounded-evaluation/` is an archive of an
earlier discussion. It is useful background, but its terminology, metric
priority, and task-selection-first roadmap are no longer authoritative.

## First Principle And Research Questions

Barcarolle's first principle is to provide reliable evaluation methods for
self-evolving agents. Repository-level coding agents are the first concrete
domain. A self-evolving agent retains behavior-changing updates across tasks,
including changes to its model, harness, persistent prompts, memory, skills,
tools, or other persistent state.

Reliability is bounded by the declared task population, outcome definition,
agent lineage and optimizer, evaluator feedback, optimization budget, threat
model, time horizon, and decision. Subject evolution is the core context;
making the evaluator coevolve is an optional candidate method.

The three primary empirical objectives are:

1. minimize pass-rate mean absolute error (MAE) on future real-world tasks;
2. minimize pass-rate-difference MAE between agents on those tasks;
3. minimize the increase in both errors as the predeclared budget for repeated
   evaluator-guided optimization grows.

The first two are separate primary metrics. Apply four stages in order:

- evidence validity: were the future tasks, outcomes, and information
  boundaries independent and fit for the claim;
- absolute error limits: do both errors meet deployment-derived limits with
  adequate coverage and uncertainty;
- degradation under optimization: how does the same evaluation method change
  from `b=0` as it supplies more queries, feedback, candidate trials, or
  optimization steps;
- method comparison: which method is better under matched conditions.

A reliability claim must pass the first two stages and the third when it covers
evaluator-guided optimization. The fourth stage cannot repair an earlier
failure.

Give pass-rate-difference MAE decision priority only if, at every predeclared
evaluation budget, the method's pass-rate MAE is no more than a predeclared
margin worse than a named comparator. Separately predeclare tolerated
within-method degradation from `b=0`. Neither rule is an absolute error limit.

The default target is **operational behavior**—what an exact agent actually
does under a declared deployment-like harness and runtime policy. Performance
under a separate, predeclared capability-elicitation protocol is a different
target. A change to persistent agent configuration or its generation, tool, or
runtime policy creates a new version; task inputs and temporary cues allowed by a frozen
policy are run contexts for that version. For a self-evolving study, preserve
the frozen snapshots, parent-to-child transitions, and complete agent lineage,
not only the final winner.

Task selection is only one candidate method. The method space includes task
generation, task sampling and weighting, statistical outcome models,
calibration and abstention, evaluator feedback policies, evaluator updating,
adversarial stress testing of evaluators and metrics, and agent–evaluator
coevolution.

All methods must ultimately be tested on an independent set of future
real-world tasks that remained hidden while optimizing the agent, updating or
choosing the evaluator, designing attacks, and setting claim thresholds.
Generated or adversarial tasks can be useful probes, training data, or
evaluation components, but their raw pass rates cannot stand in for future
real-world pass rates without empirical calibration.

## Current State

The implementation already provides:

- auditable `Task`, `Check`, `Workspace`, and `Result` records;
- hidden-check verification and exact result identity;
- static rolling-origin evaluation, meaning backtests across successive time
  cutoffs;
- pass-rate MAE (`future_pass_rate_mae`) and aggregate pass-rate-difference MAE
  (`pairwise_gap_mae`) computation;
- evidence-backed reporting for the current static path.

It does not yet provide:

- a durable self-evolving-agent lineage that records behavior-changing model,
  harness, prompt, memory, skill, tool, and persistent-state updates;
- training or reporting that treats pass-rate-difference MAE as an equal
  primary metric;
- a built-in forecast-based or adversarial task generator with evidence that
  generated responses predict responses on future real-world tasks;
- parent links between agent versions, evaluator versions, evaluator feedback,
  query counts, rounds, or epochs;
- error curves over increasing optimization budgets;
- complete reliability-claim evidence, including deployment-derived
  error limits, coverage, and uncertainty;
- an independent prospective evidence stream for changing agent and evaluator
  versions under a frozen evaluation method, distinct from the existing static
  prospective-selection path;
- evidence that separates general capability improvement from behavior specific
  to the evaluator or exploit-only changes;
- adversarial stress testing of evaluators and metrics, or agent–evaluator
  coevolution.

## Existing Evidence

The earlier task-selection studies remain useful baselines. On one previously
analyzed, fixed mini-SWE-agent v2 development panel, `consensus_rate_match`
improved repository-equal pass-rate MAE for the next 5 and 10 tasks after each
time cutoff (H5 and H10), but the result reversed when each time cutoff received
equal weight and failed two transfer checks on different agent systems or
harnesses. Do not tune it again on the same five-repository development score,
call it a production-ready evaluator, or treat it as evidence that task
selection is the only promising direction.

Prior work supports several components of the new program:

- active testing, item response theory (IRT), and outcome models can reduce
  the cost of static evaluation;
- time-based validation and continuous task collection can measure some forms
  of temporal change;
- repeated proxy optimization and direct scorer exploitation are real failure
  modes;
- dynamic and adversarial data collection can expose blind spots;
- adversarial data can also distort the target distribution, destabilize
  rankings, or hurt out-of-domain performance;
- red teaming, controlled agents with deliberately implanted behaviors,
  reward-model ensembles, and coevolving training systems provide adjacent
  methods.

The review did not locate a published result establishing that a coevolving
coding-agent evaluator preserves either of Barcarolle's prediction errors. In
particular, the located literature rarely studies numerical error in the
predicted difference between two agents. These are open research questions,
not implemented or validated capabilities.

## Candidate Methods

Keep these method families active until a discriminating result retires them:

- paired task sampling and weighting for agent comparisons;
- hierarchical IRT, matrix-completion, and calibrated outcome models;
- forecasts of future task categories followed by multiple independent task
  instantiations;
- joint allocation across real and generated tasks;
- detection of cases where the available data do not support a reliable
  prediction, with abstention and an explicit fallback policy;
- query limits, coarser feedback, and evaluator updating at fixed epochs;
- adversarial tests of tasks, hidden checks, scorers, feedback, metrics, and
  agent variants;
- portfolios or agent–evaluator coevolution, selected using an
  independent set of future real-world tasks.

Keep task generation intended to approximate future real-world tasks separate
from adversarial task generation intended to expose failures. A task is not
representative of future work merely because it is difficult or breaks the
current agent.

## Next Work Cycle

1. Define the minimum closed-loop evidence for agent versions, changes to
   persistent behavior, agent optimizers, evaluator versions, feedback,
   query counts, budgets, and prospective-cohort consumption.
2. Make pass-rate MAE and pass-rate-difference MAE equally visible in research
   summaries and reports, including absolute-error-limit and uncertainty
   status.
3. Re-score existing public panels under both metrics. Include full-history,
   recent, random, common-task, IRT, models using coding-task features,
   calibrated marginal outcome models, direct paired-outcome models, and
   comparison-aware sampling baselines.
4. Replay best-of-`N` selection over fixed lineages of agent versions before
   paying for a live repeated evaluator-guided optimization experiment.
5. Prototype forecast-based task generation with at least two independent task
   instantiation methods, then test whether generated agent outcomes predict
   outcomes on temporally held-out future real-world tasks.
6. Run adversarial stress tests with held-out attack families, workspace
   integrity logging, and coverage- or mutation-guided check strengthening.
   Retain attacks that predict errors on unseen attack families or future
   real-world tasks, not attacks that merely lower a score.
7. Add paired evaluation-context and capability-elicitation audits using
   controlled agents with known behavior, while keeping those diagnostics out
   of the primary pass-rate estimate.
8. Use those results to predeclare the first controlled repeated-optimization
   experiment with the same agent optimizer and budget across evaluator
   conditions. A frozen static baseline is sufficient to validate the protocol;
   the first instrumented pilot does not require an opened-data static winner.

This cycle may add small experiment schemas or concrete generation code when an
experiment against the prediction targets requires them. It does not authorize
a generic framework or a paid agent campaign by itself.

## Paid Calls And Claims

No paid benchmark or research-evidence call was made for the 2026-08-13
briefing or the 2026-08-30 documentation work. Existing public outcomes are
sufficient for the first static and fixed-archive studies.

Any later evidence-producing paid call must follow `AGENTS.md`, including the
`OPENAI_BASE_URL` and `OPENAI_API_KEY` rule. Before the first call, freeze the
initial agent, agent optimizer, candidate evaluator, future task window,
optimization budget, feedback policy, agent-pair population, absolute error
limits, metrics, independent prospective evidence source and reference standard,
stopping rule, and artifact policy.

Current evidence supports an auditable benchmark execution and verification
boundary, plus static calculation of the two requested errors. It does not
support claims of a production-ready evaluator, validated generated-task
distribution, optimized pass-rate-difference estimator, robustness under
repeated evaluator-guided optimization, resistance to Goodhart effects, or
successful agent–evaluator coevolution.
