# Agent Selection Demo Predictive-validity Completion Runbook 2026-06-13

Status: mandatory long-running runbook for finishing the demo with the
predictive-validity story, rolling-origin infrastructure, and supporting data.

This runbook supersedes the previous Agent-selection-only completion runbooks
when the user asks to finish the whole demo. The earlier strict completion
runbook completed the target-repo Agent-selection layer; this runbook adds the
north-star predictive-validity layer.

## Reader-facing Research Problem

Target readers are internal technical decision-makers who understand coding
Agents but may not care about Barcarolle's process history.

Problem:

- Generic benchmarks and one-off selection sets do not tell a repo owner whether
  an Agent will perform well on that repo's future work.
- The completed `mahmoud/boltons` demo already showed that a plausible
  selection-set recommendation can be contradicted by fresh holdout tasks.
- What remains missing is a disciplined way to ask whether a repo-specific
  benchmark predicts future Agent performance better than simple alternatives.

Demo-level response:

> Barcarolle is a target-repo predictive Agent evaluation system. It can run
> complete Agents, verify their diffs, and now must demonstrate a rolling-origin
> validation path that measures whether selected benchmark tasks predict later
> target-repo outcomes better than simple baselines.

The goal is not to prove predictive validity conclusively in one pass. The goal
is to finish the demo with:

- a precise predictive-validity estimand;
- rolling-origin infrastructure;
- no-paid retrospective results from existing paid/sanitized outcomes;
- a preregistered bounded paid-pilot path if the no-paid evidence is
  insufficient and gates pass;
- a final story that says exactly what is supported, what failed, and what still
  needs future validation.

## Non-negotiable Completion Criteria

Do not mark this run complete until every package below is completed or has a
specific blocker report with attempted fixes and evidence.

Mandatory packages:

1. Predictive-validity state audit and evidence ledger.
2. Estimand, metrics, baselines, and claim-boundary protocol.
3. Rolling-origin window and data feasibility builder.
4. Rolling-origin evaluation infrastructure with tests.
5. No-paid retrospective rolling-origin analysis using committed sanitized
   outcomes.
6. Bounded paid-pilot decision and execution if gates pass and data are still
   insufficient.
7. Predictive-validity story package integrated with the current demo.
8. Final closeout and `PROCESS.md` update.

Document-only completion is not acceptable unless infrastructure or experiment
execution is blocked by a documented external condition.

## Paid-call Boundary

Default: use existing committed sanitized outcomes first.

Approved paid work inside this runbook, only after preregistration and gates:

- at most 40 new paid Agent cells total;
- only for filling a preregistered rolling-origin pilot gap;
- only with stable Agent configurations whose adapter gate passes;
- no second-repo paid matrix unless it is explicitly part of the preregistered
  rolling-origin pilot and fits the 40-cell total;
- no Kilo paid cells unless Kilo timeout gates pass first.

If Kilo remains blocked, the agent must not spend paid cells trying to prove
Kilo stable. Use existing Kilo evidence as historical evidence only and run any
new paid pilot on stable Agent paths.

All paid calls must use `LLM_BASE_URL` and `LLM_API_KEY`. If endpoint, model,
secret-isolation, artifact-hygiene, or scoreability gates fail, write a no-paid
blocker and continue non-paid packages.

## Blocker Standard

A package may be marked blocked only after the agent has:

- identified the exact data, command, code path, or external dependency that
  blocks progress;
- made a concrete local implementation or repair attempt when the issue is in
  repo code;
- added or updated tests when the code path is testable;
- recorded why further progress would require exceeding the paid-call boundary,
  violating artifact hygiene, changing the experiment contract, or waiting for
  an external provider/tool.

If one package is blocked, continue the other packages.

## Package 1: Predictive-validity State Audit And Evidence Ledger

Read:

- `AGENTS.md`
- `PROCESS.md`
- `docs/research/project-state-after-proposal.md`
- `docs/research/current-project-story.md`
- `docs/research/research-inputs-and-related-work-reference.md`
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`
- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`
- `experiments/phase1_compiler/reports/phase1_future_holdout_decision.md`
- `experiments/phase1_compiler/reports/phase1_future_holdout_prediction_metrics.md`
- `experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_decision.md`
- `experiments/phase1_compiler/reports/phase1_two_repo_future_holdout_prediction_metrics.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_decision.md`
- `experiments/phase1_compiler/reports/phase1_retrospective_predictive_signal_baseline_comparison.md`

Produce:

```text
experiments/agent_selection_demo/reports/predictive_validity_state_audit_zh.md
experiments/agent_selection_demo/results/predictive_validity_evidence_ledger.json
```

Required ledger fields:

- evidence source path;
- repos covered;
- Agents/adapters covered;
- task windows or cutoffs;
- task counts and scoreable-cell counts;
- whether outcomes are paid, no-paid, retrospective, future holdout, or demo
  holdout;
- whether raw artifacts are needed;
- which claim each artifact can and cannot support.

Acceptance:

- the audit explicitly states that current demo evidence supports the importance
  of predictive validity but does not prove it;
- the ledger identifies all existing usable outcomes before any new paid calls.

Commit after this package.

## Package 2: Estimand, Metrics, Baselines, And Protocol

Define the measurement target before running new analyses.

Required output:

```text
experiments/agent_selection_demo/reports/predictive_validity_protocol_zh.md
experiments/agent_selection_demo/results/predictive_validity_protocol.json
```

Required definitions:

- Agent unit: complete Agent = model + harness + prompt/tools/runtime policy.
- Primary estimand: how well a benchmark selection predicts a complete Agent's
  future target-repo verified pass rate.
- Primary metric: pass-rate MAE, averaged over preregistered `(repo, origin,
  Agent)` slices where both benchmark and future outcomes are scoreable.
- Secondary metrics:
  - signed error;
  - RMSE;
  - rank agreement where at least two Agents are scoreable in the same slice;
  - recommendation regret: future pass-rate loss from choosing the selection
    recommendation instead of the future-best Agent;
  - catastrophic miss rate using a preregistered threshold.
- Baselines:
  - temporal recent same-budget baseline;
  - random same-budget baseline with many seeds;
  - repo-stratified/simple same-budget baseline;
  - best-simple-baseline envelope;
  - Barcarolle candidate selector or coverage-constrained selector if available.
- Minimum reporting:
  - every result must be compared to simple baselines;
  - report uncertainty or seed distribution, not only the best run;
  - report Agent-stratified results rather than pooling away Agent instability.

Acceptance:

- protocol says what would count as directional traction versus no signal;
- protocol says what would be required to claim predictive validity in the
  future;
- protocol is frozen before Package 5 analysis and Package 6 paid calls.

Commit after this package.

## Package 3: Rolling-origin Window And Data Feasibility Builder

Build a no-paid feasibility tool that inventories possible rolling-origin
windows from committed task metadata and committed score tables.

Suggested CLI:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools \
  uv run --project experiments/phase1_compiler \
  python experiments/agent_selection_demo/tools/agent_selection_demo.py \
  predictive-validity-feasibility \
  --output experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md
```

The agent may implement this in `agent_selection_demo.py`, a new focused module,
or a phase1 helper, but it must leave a documented command.

Required behavior:

- find candidate repos from committed artifacts, at minimum `boltons` and
  `attrs`, and include `click` if existing sanitized outcomes are usable;
- identify task dates/cutoffs and possible origin windows;
- join task metadata to existing scoreable outcomes without reading raw
  prompts/completions/transcripts/workspaces;
- count scoreable cells by repo, origin, Agent, and stage;
- identify which windows can support:
  - pass-rate prediction only;
  - Agent ranking agreement;
  - recommendation-regret analysis;
  - no analysis because cells are missing or non-scoreable.

Required outputs:

```text
experiments/agent_selection_demo/reports/predictive_validity_feasibility_zh.md
experiments/agent_selection_demo/results/predictive_validity_window_inventory.json
```

Acceptance:

- at least one viable no-paid rolling-origin slice is identified, or the report
  explains exactly why existing artifacts are insufficient;
- no paid calls are made in this package;
- focused tests cover the window inventory or score join logic.

Commit after this package.

## Package 4: Rolling-origin Evaluation Infrastructure

Implement evaluation code that turns a frozen window inventory into prediction
metrics.

Suggested CLI:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools \
  uv run --project experiments/phase1_compiler \
  python experiments/agent_selection_demo/tools/agent_selection_demo.py \
  rolling-origin-eval \
  --protocol experiments/agent_selection_demo/results/predictive_validity_protocol.json \
  --window-inventory experiments/agent_selection_demo/results/predictive_validity_window_inventory.json \
  --output experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
```

Required behavior:

- compute pass-rate MAE by `(repo, origin, Agent)` slice;
- compute signed error, RMSE, and catastrophic miss rate;
- compute rank agreement and recommendation regret where slice data allow;
- compare Barcarolle/candidate selectors against the simple baselines from the
  frozen protocol;
- handle missing or non-scoreable cells explicitly;
- emit both markdown and machine-readable JSON/CSV.

Required outputs:

```text
experiments/agent_selection_demo/reports/rolling_origin_eval_zh.md
experiments/agent_selection_demo/results/rolling_origin_eval.json
experiments/agent_selection_demo/results/rolling_origin_eval_slices.csv
```

Acceptance:

- focused tests cover MAE averaging, baseline comparison, missing-cell policy,
  and recommendation-regret calculation;
- results are reproducible from committed sanitized artifacts;
- no broad predictive-validity claim is made from retrospective data alone.

Commit after this package.

## Package 5: No-paid Retrospective Rolling-origin Analysis

Run the rolling-origin evaluation on existing committed outcomes.

Required report sections:

- what windows were analyzed;
- which repos and Agents were included;
- which results came from existing paid artifacts versus no-paid metadata;
- baseline comparison;
- whether Barcarolle-style selection beats simple baselines, ties them, or
  loses;
- what the result means for the demo story.

Interpretation rules:

- If Barcarolle/candidate selectors beat the best simple baseline, call it
  directional retrospective traction only.
- If they do not beat baselines, call it a useful negative result showing why
  predictive-validity optimization remains the project core.
- If data are too sparse, do not fabricate a result; produce a paid-pilot
  readiness gap in Package 6.

Required outputs may reuse Package 4 outputs, but add:

```text
experiments/agent_selection_demo/reports/predictive_validity_retrospective_result_zh.md
```

Acceptance:

- the report includes at least one numeric predictive metric, or a documented
  data insufficiency reason;
- all metrics are tied back to the frozen protocol;
- no raw artifacts are required.

Commit after this package.

## Package 6: Bounded Paid-pilot Decision And Execution

Run this package only after Packages 1-5.

First decide whether existing no-paid data are enough for the demo story. If the
story already has supporting data, do not run paid cells. Instead produce a paid
pilot preregistration for later.

If existing data are insufficient and gates pass, run at most 40 new paid cells
to fill one preregistered rolling-origin pilot gap.

Required decision output:

```text
experiments/agent_selection_demo/reports/predictive_validity_paid_pilot_decision_zh.md
experiments/agent_selection_demo/results/predictive_validity_paid_pilot_plan.json
```

If running paid cells, the plan must freeze before execution:

- repos;
- origins/cutoffs;
- task IDs;
- Agent configurations;
- endpoint/model proof;
- visible context;
- hidden verifier;
- scoreability gate;
- baseline comparison;
- success threshold;
- stop conditions.

Paid execution stop conditions:

- endpoint compliance fails;
- secret isolation fails;
- Kilo timeout gate fails and Kilo was included;
- scoreable-cell rate cannot reach the preregistered threshold;
- raw artifacts would need to be committed;
- total new paid cells would exceed 40.

If paid execution occurs, required outputs:

```text
experiments/agent_selection_demo/reports/predictive_validity_paid_pilot_result_zh.md
experiments/agent_selection_demo/results/predictive_validity_paid_pilot_result.json
```

Acceptance:

- either a clear no-paid decision with preregistered future pilot plan, or a
  completed bounded paid pilot;
- paid cells count is explicit;
- results are joined back into rolling-origin metrics where possible;
- no claim exceeds the achieved evidence.

Commit after this package.

## Package 7: Predictive-validity Story Package

Create a final reader-facing story package that integrates the Agent-selection
demo with the predictive-validity layer.

Required output:

```text
experiments/agent_selection_demo/reports/predictive_validity_demo_story_zh.md
```

Required structure:

1. One-page plain-language summary.
2. Problem: target-repo future performance is what users care about.
3. Existing demo result: selection recommendation failed a fresh holdout check.
4. Method: rolling-origin asks, at historical origin `T`, whether a benchmark
   compiled from earlier tasks predicts later tasks.
5. Metrics: MAE, rank agreement, recommendation regret in simple terms.
6. Baselines: random, recent, repo-stratified/simple.
7. Data: no-paid retrospective and any bounded paid-pilot results.
8. Claim boundary: what is proven, what is only directional, what remains
   future validation.
9. Product relevance: Agent selection and Agent tuning both need predictive
   feedback, not just pass/fail dashboards.

Required style:

- Chinese, readable by non-specialist technical reviewers;
- low terminology burden;
- no stale `phase`, `ACUT`, `release`, `M1-M6`, or process-runbook vocabulary
  in the main text;
- do not hide negative or blocked results.

Acceptance:

- the story includes actual numeric data or a documented insufficiency result;
- it makes predictive validity the north-star concept;
- it clearly distinguishes demo evidence from future proof.

Commit after this package.

## Package 8: Final Closeout And Process Update

Update:

- `PROCESS.md`;
- `experiments/agent_selection_demo/reports/final_agent_selection_demo_package_zh.md`;
- `experiments/agent_selection_demo/reports/demo_completion_closeout_zh.md`;
- `experiments/agent_selection_demo/results/closeout_summary.json`.

Required closeout answers:

1. What predictive-validity estimand was frozen?
2. What rolling-origin infrastructure exists and what command runs it?
3. What no-paid retrospective data were produced?
4. Were any paid cells run? If yes, how many and why?
5. Did Barcarolle/candidate selection beat simple baselines, tie them, lose, or
   remain underpowered?
6. What claim can be made in the demo now?
7. What cannot be claimed?
8. What is the next experiment required to move from directional evidence to
   predictive-validity proof?
9. Which tests and hygiene checks passed?

Commit after this package.

## Required Validation

Run at minimum:

```text
PYTHONPATH=experiments/agent_selection_demo/tools:experiments/phase1_compiler/tools uv run --project experiments/phase1_compiler pytest experiments/agent_selection_demo/tests -q
git diff --check
git ls-files experiments/agent_selection_demo | rg '(__pycache__|\\.pyc$|raw|transcript|workspace|\\.DS_Store|\\.pytest_cache|\\.venv)'
```

Run phase1 focused tests if rolling-origin code reuses or modifies phase1
predictive-signal tooling.

Artifact hygiene rule: committed outputs may include sanitized manifests,
tables, summaries, and digests only. Do not commit raw prompts, raw completions,
transcripts, solver workspaces, verifier workspaces, cloned repos, provider
logs, secrets, `.pyc`, or cache files.

## Final Response Checklist

The executing agent's final report must answer:

- which packages completed;
- which packages remain blocked and why;
- the exact rolling-origin commands;
- numeric predictive-validity metrics produced;
- baseline comparison result;
- paid cells used;
- final demo claim;
- remaining route to a real predictive-validity proof;
- tests and hygiene checks.

Only mark the goal complete when this checklist is answered.
