# Agent Selection Demo Follow-up Plan 2026-06-13

Status: planning document, not an execution runbook.

Primary inputs:

- `experiments/agent_selection_demo/reports/target_repo_coding_agent_selection_demo_report_zh.md`
- `experiments/agent_selection_demo/results/closeout_summary.json`
- `experiments/agent_selection_demo/results/holdout_check.json`
- `docs/research/agent-selection-demo-execution-proposal-2026-06-12.md`

## Current Result

The `mahmoud/boltons` demo ran end to end:

- 4 candidate Agents;
- 20 selection tasks;
- 10 holdout tasks;
- 80 selection runs and 40 holdout runs;
- clean verifier replay for scored diffs;
- selection recommendation locked before holdout.

The selection set recommended `Codex + GPT mainline`. The holdout check
contradicted that recommendation: `Kilo + GPT mainline` was best on holdout
with `9/10` verified passes, while `Codex + GPT mainline` had `5/10`.

The main lesson is not that one Agent is globally better. The useful result is
that the evaluation system exposed a plausible selection-set recommendation
that did not survive a fresh holdout check.

## Objective

Turn the first demo from "the pipeline ran" into a stronger and cleaner
selection story:

> Target-repo Agent selection needs fresh holdout checks because a plausible
> recommendation can be unstable.

The next work should explain whether the contradiction came from Agent
stochasticity, task-split differences, cost-accounting noise, or a real
repository-specific behavior difference.

## Work Packages

### 1. Post-demo Diagnostics

This is the immediate next step and should not require new paid Agent solving
unless a missing artifact blocks analysis.

Questions:

- How do selection and holdout tasks differ by source, module, task age,
  changed files, test files, size, and oracle shape?
- Did the selection set overrepresent task types where Codex performed well?
- Did the holdout set overrepresent task types where Kilo performed well?
- Were the non-scoreable selection cells concentrated in one Agent or task type?
- Did cost estimation affect the recommendation in a fragile way?

Deliverables:

- `experiments/agent_selection_demo/reports/post_demo_diagnostics_zh.md`
- task-split comparison table;
- per-Agent/per-task outcome matrix;
- short note on whether the recommendation rule should be revised before the
  next paid run.

Acceptance:

- The report can explain the selection/holdout contradiction in plain language,
  or clearly say that current artifacts cannot explain it.
- No new broad claim about predictive validity is made.

### 2. Top-2 Repeatability Check

Run only the two Agents involved in the contradiction:

- `Codex + GPT mainline`;
- `Kilo + GPT mainline`.

Candidate run shape:

- repeat both Agents on the same 10 holdout tasks;
- optionally repeat both on the 20 selection tasks if budget permits;
- keep task text, verifier, endpoint policy, timeout, and recommendation rule
  unchanged;
- do not tune prompts or tools between repeats.

Questions:

- Does Kilo still lead on the holdout repeat?
- Does Codex still tie or lead on selection tasks?
- Are failures stable by task, or do pass/fail outcomes move randomly?

Deliverables:

- repeat score table;
- task-level stability table;
- updated recommendation interpretation.

Acceptance:

- If the same direction repeats, the demo story becomes stronger: the holdout
  contradiction is less likely to be pure noise.
- If the direction changes, the next story becomes stochasticity and repeated
  evaluation, not Agent ranking.

### 3. Cost Accounting Repair

The first demo used observed token usage for 31 runs and conservative estimates
for the rest. This is good enough for a demo, but weak for a production-value
recommendation.

Questions:

- Which harness/model combinations failed to emit parseable usage?
- Can usage be recovered from retained sanitized ledgers without reading raw
  transcripts?
- Can the adapter emit a normalized usage record for every run?
- Does the selection recommendation change if cost is removed as a tie-breaker?

Deliverables:

- usage-coverage audit;
- normalized cost schema or adapter patch plan;
- recommendation sensitivity table with and without cost tie-breakers.

Acceptance:

- Future reports distinguish observed cost, estimated cost, and real billed
  cost.
- The selection rule does not depend on a cost field that is mostly estimated.

### 4. Second Target Repository Gate

Do not jump to a full second-repo paid run before the diagnostics and top-2
repeatability check unless presentation timing requires it.

Candidate repository:

- default fallback: `python-attrs/attrs`;
- alternative may be chosen only if it has a cleaner certified task pool and
  stable verifier setup.

Gate requirements:

- at least 30 locally certified tasks;
- stable checkout and visible test command;
- hidden verifier replay works in clean workspaces;
- model endpoint and secret isolation gates pass;
- no large task-source repair backlog.

Deliverables:

- second-repo gate report;
- split proposal;
- paid-run cost projection;
- go/no-go decision.

Acceptance:

- A second-repo paid run is approved only if the gate is clean and the expected
  result would answer a concrete question that the `boltons` demo cannot answer.

### 5. Rolling-origin Design Prep

Rolling-origin validation remains the path toward predictive validity, but it
should not be the next paid run until the selection-demo diagnostics are
understood.

Prep work:

- define historical windows for one or two repositories;
- decide which Agent set is small enough for repeated windows;
- define simple baselines: recent tasks, random same-budget tasks, and
  repository-stratified selection;
- define prediction target: Agent ranking, pass-rate MAE, or deployment
  recommendation stability;
- estimate task and run budget.

Deliverable:

- rolling-origin design note with windows, baselines, metrics, and budget.

Acceptance:

- The design can be preregistered before paid runs.
- It compares against simple baselines rather than only reporting Barcarolle's
  candidate selector.

## Recommended Order

1. Post-demo diagnostics.
2. Cost-accounting repair plan.
3. Top-2 repeatability check.
4. Second-repo gate.
5. Rolling-origin design prep.

If a near-term presentation is the priority, swap 2 and 3: run the top-2 repeat
first, then repair cost accounting.

## Reporting Policy

Use these terms in presentation-facing materials:

- `selection tasks`;
- `holdout tasks`;
- `Agent`;
- `verified pass`;
- `fresh check`;
- `cost estimate` or `observed cost`, depending on evidence.

Avoid exposing old research-process terms unless they are needed in an
appendix.

## Stop Conditions

Stop and write a blocker report if:

- diagnostics show the split was invalid or leaked future information;
- repeated runs require raw transcripts or uncommitted workspaces to explain
  results;
- cost accounting cannot distinguish observed usage from estimates;
- a second repository cannot produce at least 30 locally certified tasks;
- any paid run would violate `LLM_BASE_URL` / `LLM_API_KEY` endpoint policy.

## Not In Scope For The Next Run

- learned selector implementation;
- Agent tuning loop;
- broad model-family claims;
- full rolling-origin paid validation;
- public leaderboard-style ranking;
- adding more Agent candidates before understanding the current contradiction.

