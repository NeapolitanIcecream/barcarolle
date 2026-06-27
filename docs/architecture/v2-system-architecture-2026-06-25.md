# Barcarolle System Architecture

Status: draft architecture for the current system, 2026-06-25.

This document describes the intended architecture of Barcarolle. It is not a
migration plan for the previous experiment code. The old codebase remains
useful as evidence, examples, and data provenance, but the current system should
be designed from the current understanding of the project.

## Goal

Barcarolle is a target-repository benchmark compiler for coding Agents.

Given a target repository, task supply, Agent candidates, and a time cutoff, it
should compile and evaluate a benchmark that estimates how those Agents will
perform on later work in that repository.

The north star is predictive validity:

```text
Does the selected benchmark predict future target-repository Agent performance?
```

Agent tuning is a downstream use case. It matters because a predictive
benchmark can provide useful feedback for tuning, but tuning success must not
be confused with benchmark predictive validity.

## Design Principles

- Keep the system small enough to explain.
- Prefer direct data contracts over invented concepts.
- Treat related work task generators as input methods to reuse, not ideas to
  rename.
- Keep Agent execution outside Barcarolle. The Agent owns model, harness,
  prompt, tools, retrieval, runtime config, and retry behavior.
- Keep verification separate from solving. Hidden oracle material appears only
  in verifier workspaces.
- Make every selector decision replayable from frozen task metadata and past
  outcomes.
- Treat rolling-origin evaluation as the main development protocol for
  predictive validity.
- Keep Goodhart risk explicit: do not judge a benchmark only by Agents already
  optimized against that benchmark.

## Core Objects

The system should have only a small number of first-class objects.

### Task

A task is the problem given to an Agent.

It contains the target repository, base commit, time, solver-visible statement,
allowed context, and metadata used for selection. A task may come from history,
an external generator, an LLM-assisted generator, a user import, or a synthetic
generator.

### Check

A check is the task's acceptance method.

Most checks will be tests or verifier scripts, but the system should allow
other forms: GUI screenshot evaluation, domain-specific scripts, human-reviewed
or LLM-judged checks, or customer-provided regressions.

Generator output should be thought of as:

```text
Task + Check
```

not just a problem statement.

### Workspace

A workspace is an isolated checkout used for either solving or verification.

The solver workspace contains only solver-visible material. The verifier
workspace receives the captured diff and hidden check material.

### Result

A result records one Agent on one task:

```text
agent_id, task_id, status, pass/fail/invalid, cost, latency, failure label,
captured diff digest, verifier metadata
```

Selectors and reports should consume result tables, not raw transcripts.

### Selector

A selector chooses a benchmark from the available history pool under a budget.

Selectors must not see future holdout outcomes. They may use task metadata and
past Agent outcomes that would have been available at the origin time.

### Rolling Origin

Rolling origin is the evaluation protocol:

```text
origin time t
history pool = all eligible tasks before t
selected benchmark = selector(history pool, budget)
future holdout = next task/time window after t
compare selected benchmark performance with future holdout performance
```

The same protocol is used to train, validate, and compare selectors.

## Decoupled Assets And Execution Optimizations

The system must not assume a single linear flow where Barcarolle first selects a
benchmark and only then pays to run Agents on that benchmark.

Three assets must be independent and joinable:

```text
Task Pool
  generated or imported tasks, checks, metadata, certification records

Benchmark Selection
  selector version, origin, history pool, selected task IDs, weights, budget

Agent Results
  cached Agent-task outcomes under a specific environment, with cost and verifier status
```

This separation is required for selector research. If a task pool has already
been fully or partially paid for across a set of Agents, the selector should be
able to choose virtual benchmarks from the cached result table and compute
prediction error without paying for those same Agent-task runs again.

This is not a set of separate workflows. It is one flow with two cost-saving
optimizations:

- cache reuse: do not rerun an Agent-task pair when an identical reusable result
  already exists;
- lazy Agent execution: when results are sparse, select a benchmark first and
  then run only selected Agent-task pairs whose results are missing.

In both cases, the result cache should prevent duplicate paid execution for an
identical `(task, Agent, environment, config)` combination.

A thin Runner module should own this cross-module orchestration. Runner is a
code owner for command flow, not a new research object: it calls Task Pool,
Results, Selection, Workspace, and Reporting without taking over their logic.

### Cache Reuse

Use this optimization for offline selector development and rolling-origin
research. It allows repeated selector training, ablation, and error analysis
without repeatedly paying for the same task outcomes.

### Lazy Agent Execution

Use this optimization when the task pool is large and Agent outcomes are
expensive.

```text
certified task pool
  -> selector chooses benchmark under budget
  -> run only selected Agent-task runs whose results are missing
  -> verify, cache, and report
```

This is the expected operational path when a user wants a budgeted benchmark
release.

The system should treat paid Agent results as durable assets.

## Minimal System Flow

The minimal flow is therefore not one fixed pipeline. It is a set of
composable steps over the three assets above:

```text
generate or import Task + Check
  -> certify into a frozen Task Pool
  -> optionally run Agents to fill the Result Cache
  -> define rolling-origin windows
  -> selectors choose Benchmarks from pre-origin Task Pools
  -> join Benchmark selections with cached or newly run Agent Results
  -> compare selected-benchmark performance with future-window performance
  -> report prediction error, ranking, regret, uncertainty, cost, and coverage
```

The first vertical slice should implement this with one repository, one
certified task source, one result-cache schema, and a few simple selectors
before adding more generator families or learned selectors.

## Task Supply And Generator Replication

Task supply is not the central claim, but it sets the ceiling for predictive
validity. If the task pool misses important future work types, even a strong
selector will have systematic prediction bias.

The system should support several task-source families. Built-in generators
should be treated as replications or adaptations of related-work methods, not
as free-form inventions. Before implementing a generator family, a worker
should read the relevant paper or repository, identify the method's data inputs,
oracle construction, filtering gates, and failure modes, then document what is
being reproduced and what is deliberately changed.

### Related Work Targets

These are the initial generator families to study and adapt. The list is not
closed.

| Work | Generator idea to inspect | What Barcarolle should learn |
| --- | --- | --- |
| SWE-bench | GitHub issue/PR-derived tasks, issue text as statement, repository checkout as context, fail-to-pass and pass-to-pass tests as checks. | The baseline real-history task format and changed-test oracle pattern. |
| SWE-bench Verified | Human-reviewed subset for clarity, correct tests, and solvability. | Certification gates for statement quality, oracle quality, and solvability. |
| SWE-bench Live | Continuously updated SWE-bench-like task collection with reproducible execution. | Freshness, anti-contamination, and origin-aware task freezing. |
| SWE-Bench Pro | More difficult long-horizon, realistic tasks across many active repositories. | Task difficulty, enterprise-style scope, and richer repository/task diversity. |
| SWE-Bench++ / SWE-Bench Atlas-style work | Automated large-scale generation of repository-level coding tasks from open-source projects. | Scalable task harvesting and broader task supply beyond small curated sets. |
| SWE-smith | Toolkit for turning repositories into SWE-style task environments and generating many training/evaluation tasks. | Large-supply synthetic or semi-synthetic tasks and environment construction. |
| SWE-Future | Forecast-conditioned repository-specific task synthesis using separated forecast, validation, and generation time points. | Future-oriented task synthesis without simply replaying realized future PRs. |
| SWE-EVO and long-horizon evolution benchmarks | Release-note or software-requirement-driven tasks spanning many files and steps. | Whether Barcarolle needs a task type beyond single issue/PR repair. |

Each related-work replication should answer:

- what source data it consumes;
- how it writes or derives the task statement;
- how it builds the `Check`;
- whether LLMs are used for statement synthesis, ambiguity review, or oracle
  assistance;
- what certification gates are required;
- what task metadata it emits for selector features;
- whether the generated tasks improve future prediction or only increase count.

### Repository-History Generators

These should reproduce the SWE-bench-style pattern:

- identify historical code changes;
- link changes to issue, PR, commit, and test context where possible;
- build a solver-visible task statement from issue text, PR body, commit
  message, and, when necessary, LLM-assisted diff summarization;
- build a hidden check from changed tests, regression tests, or verifier
  scripts;
- validate that the base commit fails and the reference change passes;
- reject ambiguous, flaky, unreplayable, over-broad, or leaking tasks.

This is the conservative default because it is closest to real repository work.

### Quality-Filtered Historical Generators

Inspired by work such as SWE-bench Verified, these generators add review or
filtering gates:

- statement clarity;
- oracle validity;
- environment reproducibility;
- leakage risk;
- task boundary clarity;
- expected solve scope.

The implementation can begin with deterministic filters and later add
LLM-assisted review when useful.

### Live Or Future-Oriented Generators

SWE-bench Live motivates continual refresh. The system should support task
pools that are updated over time and frozen at explicit origins.

The key requirement is not just freshness. The system must preserve what was
known at each origin so that rolling-origin validation remains honest.

SWE-Future-style methods should also be investigated: instead of replaying
future PRs directly, they use forecasts of repository evolution as conditioning
signals for future-oriented task synthesis. This may become important when the
available history pool is too small or too backward-looking.

### Large-Supply Synthetic Or Semi-Synthetic Generators

SWE-Bench++, SWE-smith-like, and future related methods are relevant because
they may increase task supply and coverage. The system should investigate these
methods as generator adapters, especially when repository history does not
provide enough certified tasks.

Synthetic tasks must still pass certification. More tasks are useful only when
they improve future prediction or coverage without introducing misleading
distribution shift.

When a generator uses an LLM to write statements, judge ambiguity, infer
developer intent from diffs, or propose checks, the committed artifact should be
the sanitized task/check manifest and a digest of the generation process. Do not
commit raw prompts or completions.

### User-Provided Task Pools

Some users will already have task pools or custom regressions. The system
should allow direct import:

```text
task pool + checks + metadata
```

without forcing the user through Barcarolle's built-in generators.

### Custom Verification Methods

Users may need checks beyond normal tests. For example, a GUI framework task may
need to run a demo app, capture screenshots, and judge visual output.

The check interface should therefore be simple:

```text
prepare verifier workspace
apply candidate diff
run check
return pass/fail/invalid + evidence summary
```

Barcarolle should standardize execution, isolation, and reporting, not dictate
that every oracle is a unit test.

## Certification

Certification decides whether a generated task can enter the frozen pool.

Minimum gates:

- base commit can be checked out;
- dependencies can be installed or restored;
- reference or expected solution passes the check;
- known-bad or base state fails when appropriate;
- verifier is bounded in time and resources;
- task statement does not expose hidden oracle material;
- task is not obviously ambiguous or impossible;
- repeated check runs are stable enough for the intended use.

Certification should produce a small manifest with rejection reasons. Rejection
data is useful for improving generators.

## Workspace And Agent Execution

Workspace code should stay boring.

Responsibilities:

- create clean solver workspace at base commit;
- provide task statement and allowed files;
- invoke the configured Agent harness;
- capture final diff;
- create fresh verifier workspace;
- apply the diff;
- inject hidden check material;
- run the check;
- record sanitized result metadata.

Non-responsibilities:

- implementing the Agent's search or edit loop;
- rewriting the Agent's prompt stack except through an explicit tuning artifact;
- reading raw transcripts for selector logic;
- leaking hidden oracle material into solver workspaces.

## Result Store

The result store can start as explicit JSONL/CSV/Parquet files with stable
schemas. A database is optional later.

The important property is joinability:

```text
tasks table
checks table
agents table
runs table
rolling-origin windows
selector decisions
prediction metrics
```

Selector research should be able to run from these tables without replaying
workspaces or reading raw Agent traces.

The result store should enforce cache identity. A cached result is reusable only
when the task, check version, base commit, Agent identity, environment, runtime
config, and scoring config match. If any of these change, the old result remains
provenance but is not the same reusable `Result`.

## Selector System

The selector is the core research claim.

Selection should expose three module-level entry points:

1. train a persistent Selector from historical data;
2. evaluate a specified Selector on historical data;
3. use a specified or adaptively chosen Selector to produce a benchmark for a
   frozen origin.

Rolling-origin splitting is internal to training and evaluation. External
callers provide historical windows, Agents, budgets, configs, and optionally a
specified Selector; Selection returns either a persistent Selector, metrics, or
a Benchmark Selection.

It receives:

- history pool before an origin;
- task metadata;
- past outcome tables that would have been available then;
- budget;
- candidate Agent set or Agent family;
- objective and constraints.

It outputs:

- persistent selector records;
- selected benchmark task IDs;
- optional weights;
- reason summary;
- expected uncertainty;
- features and selector version used.

### Rule-Based Selectors

Rule-based selectors should be direct and auditable. They are not just weak
baselines; they are useful fallbacks.

Examples:

- recency-biased selection;
- module or path coverage;
- task-type coverage;
- difficulty balancing;
- Agent-disagreement selection;
- failure-mode coverage;
- cost-bounded coverage;
- hybrid recency plus coverage.

They should remain simple enough that a reader can understand why tasks were
selected.

### Learned Selectors

Learned selectors should be trained and evaluated with rolling-origin splits.

The first generation should favor data-efficient, interpretable methods:

- linear or generalized linear models;
- pairwise ranking models;
- tree ensembles if the data volume supports them;
- learned mixtures over rule-based selectors;
- uncertainty-aware selectors;
- online updates as new windows arrive.

The learned selector should optimize prediction of future Agent performance,
not just fit historical task labels.

### Adaptive Selector Controller

The adaptive layer should not become a vague new subsystem. Its job is:

- compare selectors on recent rolling-origin evidence;
- decide whether to use one selector or a mixture;
- detect stale selectors when recent errors drift;
- fall back to rule-based selectors when learned models are unstable;
- record why a selector was trusted at a given origin.

In the simplest version, this can be model selection over a small set of
selectors using recent rolling-origin error and uncertainty.

When lazy Agent execution produces new Results for a selected benchmark, Runner
should pass the resulting metrics back to Selection. Selection may then update
the persistent Selector or its trust metadata using only recorded metrics and
allowed historical outcomes.

## Metrics

Primary metric:

- future pass-rate prediction error, initially MAE.

Important supporting metrics:

- top-rank agreement;
- top-tier agreement;
- recommendation regret;
- calibration bias;
- catastrophic miss rate;
- robustness across origins, repos, Agent subsets, and task budgets;
- scoreable/invalid rate;
- cost and latency;
- task diversity and coverage.

The goal is not to make every metric improve. The research target is to reduce
prediction error while keeping robustness and operational metrics within
acceptable bounds.

## Goodhart Safeguards

The system must keep these claims separate:

- benchmark predictive validity: whether a benchmark predicts future performance
  of Agents available at the origin;
- tuning utility: whether benchmark feedback improves a later tuned Agent.

Practical safeguards:

- freeze generator, selector, task IDs, and metrics before joining future
  outcomes;
- keep true future holdouts out of selector and tuner decisions;
- record which Agents or artifacts have been exposed to which benchmark;
- use rolling-origin for development, but reserve fresh holdouts for stronger
  claims;
- compare to random, temporal, and simple stratified baselines;
- report negative or regressed tuning results honestly.

## Proposed Repository Layout

This is a starting point, not a mandate:

```text
barcarolle/
  tasks/
    schema.py
    generators/
      history.py
      issue_pr.py
      synthetic.py
      import_pool.py
    certification.py
  checks/
    base.py
    pytest_check.py
    script_check.py
    visual_check.py
  workspace/
    checkout.py
    solver.py
    verifier.py
    diff.py
  results/
    schema.py
    store.py
  selection/
    rolling_origin.py
    selectors/
      random.py
      recency.py
      coverage.py
      disagreement.py
      learned.py
      adaptive.py
    metrics.py
  reporting/
    prediction_report.py
    run_report.py
  cli.py
```

The exact package name can change. The important point is that task supply,
checks, workspace execution, results, and selection remain separate.

## Relationship To Existing Code

The current codebase should be treated as:

- evidence of what worked or failed;
- a source of reusable small functions if they are clean;
- provenance for already-paid results;
- a source of tests and fixtures after review.

It should not dictate current abstractions.

Specific guidance:

- keep historical reports and committed result summaries for audit;
- port only code that has a clear owner module and contract;
- do not port experiment-specific names into core APIs;
- prefer new minimal tests over adapting broad experiment tests;
- preserve paid-result schemas or write one-time converters rather than making
  the current system depend on old experiment modules.

## First Vertical Slice

The first implementation milestone should prove only the core path:

1. Import or generate a small certified task pool for one repository.
2. Define one check type.
3. Store the task pool and checks independently of any benchmark selection.
4. Run one or two Agents through isolated solver/verifier workspaces.
5. Store normalized result rows in a reusable result cache.
6. Build rolling-origin windows.
7. Run random, recency, and one coverage selector repeatedly from the same
   cached results.
8. Report MAE, rank agreement, regret, scoreable rate, cost, and cache reuse.

Do not implement learned selectors in the first skeleton unless the basic path
is already clean.

## References To Inspect Before Generator Work

- SWE-bench: <https://www.swebench.com/original.html>
- SWE-bench Verified: <https://www.swebench.com/verified.html>
- SWE-bench Live: <https://arxiv.org/html/2505.23419>
- SWE-Bench Pro: <https://arxiv.org/html/2509.16941>
- SWE-Bench++: <https://arxiv.org/html/2512.17419>
- SWE-smith: <https://swesmith.com/> and
  <https://github.com/SWE-bench/SWE-smith>
- SWE-Future: <https://arxiv.org/html/2606.18733>
- SWE-EVO: <https://arxiv.org/html/2512.18470>

## Open Questions

- What is the smallest task/check schema that can cover both SWE-style tasks
  and user custom checks?
- Which related-work generators should be replicated first, and which should be
  left as adapters?
- How should LLM-assisted task statement generation be audited without storing
  raw prompts and completions in Git?
- What feature set is safe for learned selectors without leaking future
  outcomes?
- How much paid data is required before a learned selector can beat strong
  rule-based baselines convincingly?
- What are the minimum fresh-holdout requirements for a strong predictive
  validity claim?
