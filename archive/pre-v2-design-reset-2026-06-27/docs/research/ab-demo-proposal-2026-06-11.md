# AB Demo Proposal 2026-06-11

Status: draft for discussion.

Related note: `docs/research/presentation-feedback-2026-06-11.md`.

## Purpose

Build an AB demo that helps reviewers understand the project as a useful system,
not only as a research claim about task selection.

The demo should show that a target-repository Agent evaluation system can:

1. run complete Coding Agents on repo-specific tasks;
2. verify their diffs with hidden tests in an isolated verifier workspace;
3. produce a readable comparison report;
4. support a practical decision, such as Agent selection or Agent tuning.

This demo should not depend on fully solving predictive validity. It should
create a credible bridge from the current prototype assets to a product-facing
system story.

## Strategic Position

The demo should serve two presentation needs.

First, it should make Agent selection visible. Agent tuning remains important,
but reviewers pointed out that Agent selection may be the broader and more
common use case. A team often needs to decide which Agent configuration can be
used in a specific repository before it invests in deeper tuning.

Second, it should avoid over-binding project value to SKVM or DSPy. Those
systems may be useful demo targets, but the project should not sound valuable
only if SKVM or DSPy is already valued internally. The demo should make the
system value visible even when the target Agent is SKVM, DSPy, Hermes Agent, or
another Coding Agent.

The proposed framing:

> Use target-repo tasks and hidden verification to compare or improve real
> Agent configurations, then validate the decision on independent holdout tasks.

## Demo Claim Boundary

The demo can credibly claim:

- the evaluation loop runs end to end;
- the system can produce a useful Agent comparison or tuning report;
- a rule-based benchmark can support a small-scale decision;
- independent holdout tasks can be used to check whether that decision was
  directionally correct.

The demo should not claim:

- predictive validity is proven;
- the task selector is better than all simple baselines;
- the result generalizes to new repositories or Agent families;
- SKVM, DSPy, or any specific Agent is broadly improved by this project.

If results are strong, the stronger phrasing can be:

> On this target repository and this Agent pair, the system's benchmark selected
> the same winner as the independent holdout and produced a readable failure and
> cost report.

## Design Principle: Clean Demo Layer

The strict top-level goal is to build a useful AB demo. The implementation
strategy is not fixed in this proposal.

Future Codex sessions should decide how much old code to reuse after inspecting
the repository. The expected direction is to minimize concept burden, reduce
abstract terminology, and keep the demo surface clean. If reusing old assets
makes the demo clearer and faster, reuse them. If old assets force confusing
concepts into the user-facing path, wrap, rename, or replace them.

The previous code assets are valuable, but they were built during research
exploration and may carry concept history: phases, runbooks, ACUT wording,
release terminology, candidate-policy wording, weighted selector artifacts, and
proposal-evidence scaffolding.

The demo should use a clean, independent layer with low terminology cost.

Use these user-facing concepts:

- `target_repo`
- `task_pool`
- `benchmark`
- `agent_run`
- `holdout`
- `feedback_report`

Avoid exposing these concepts in demo-facing filenames, reports, and slide text
unless technically necessary:

- phase names;
- ACUT;
- release;
- candidate policy;
- adapter fairness;
- weighted target profile;
- proposal evidence package;
- runbook/process artifacts.

Possible directory:

```text
demo/predictive_agent_eval/
```

Alternative:

```text
experiments/predictive_agent_eval_demo/
```

These paths are suggestions, not requirements. The next implementation session
should choose the path that gives the cleanest demo and least abstraction tax.

The boundary is that demo inputs, outputs, command names, and reports should
follow the new simplified story.

## Reuse Strategy

This proposal does not prescribe a strict reuse plan. Treat old code as a
source of implementation assets, not as a required architecture.

Likely reusable assets include:

- workspace creation;
- Agent invocation wrappers where endpoint compliance is clear;
- diff capture;
- verifier replay;
- hidden-test injection pattern;
- task certification checks;
- score table and cost accounting ideas;
- retained sanitized task and result data;
- lessons from the failed weighted selector and paid validation.

Assets that may need wrapping, renaming, or replacement if they leak old
concepts into the demo:

- proposal evidence generation scripts;
- old weighted selector reports;
- phase-specific report generators;
- process/runbook closeout files;
- scripts whose output forces old terminology into the demo report.

The practical direction:

> Build the cleanest demo that can run credibly. Reuse proven experiment assets
> where they reduce risk, but let the implementation session choose the exact
> reuse boundary.

## Demo Pipeline

Use a small number of explicit steps. The exact command names may change if the
implementation session finds a cleaner interface.

```text
1. build_task_pool
2. certify_tasks
3. select_benchmark
4. run_agents
5. verify_diffs
6. compare_agents
7. write_report
```

Possible artifacts:

```text
task_pool.json
certified_tasks.json
benchmark.json
agent_results.csv
holdout_results.csv
agent_comparison_report.md
```

These names are suggestions, not requirements. The report should be written in
plain Chinese by default, with an optional English appendix if needed.

## Primary Demo: Agent Selection AB

This should be the first demo target because it does not depend on SKVM or DSPy
being accepted as valuable tuning products.

Question:

> Given two or three Agent configurations, can the system choose the one that
> performs better on independent target-repo holdout tasks?

Setup:

- choose one target repository;
- prepare certified tasks;
- split tasks into benchmark tasks and holdout tasks;
- run 2-3 Agent configurations on benchmark tasks;
- choose the winner using benchmark score plus failure/cost report;
- run the same Agents on holdout tasks;
- check whether the benchmark-selected winner is also better on holdout.

Possible Agent differences:

- model;
- harness;
- prompt/hooks;
- tool access;
- retrieval policy;
- runtime budget;
- SKVM/DSPy/Hermes-style tuned vs untuned configuration.

Minimum success criteria:

- scoreable cell rate >= 95%;
- no hidden-test leakage;
- no endpoint or policy violation;
- generated comparison report is readable;
- benchmark winner and holdout winner have the same direction, or failures are
  clearly explained.

Stretch success criteria:

- benchmark prediction error beats a recent-task or random benchmark baseline;
- selected Agent improves future holdout pass rate by 5-10 percentage points;
- cost per solved holdout task does not regress materially;
- regression or failure labels explain the observed gap.

## Secondary Demo: Agent Tuning AB

This is more attractive if it works, but it has higher risk because the effect
depends on the tuning system and on the quality of benchmark feedback.

Question:

> Can feedback from the target-repo benchmark improve an Agent configuration and
> show better results on independent holdout tasks?

Setup:

- run baseline Agent on benchmark tasks;
- summarize failure labels and cost;
- use SKVM, DSPy, Hermes Agent, or a manual tuning pass to modify prompt,
  skills, tools, workflow, or budget;
- rerun the tuned Agent on benchmark tasks;
- validate the tuned Agent on holdout tasks.

Minimum success criteria:

- before/after report is generated;
- tuned Agent does not regress on holdout;
- failure labels show at least one understandable improvement area.

Stretch success criteria:

- holdout pass rate improves by 5-10 percentage points;
- regression rate remains below 5%;
- cost per validated improvement drops by 20% or more;
- the system can identify which feedback drove the tuning change.

## Selector Strategy For The Demo

Use a rule-based selector first.

This is not a weak placeholder. It should be the first reliable system
baseline and the fallback for later learned selectors.

Initial rules:

- cover important target-repo modules;
- include recent tasks;
- balance task sources when possible;
- filter low-confidence or flaky tasks;
- respect a task-count or cost budget;
- reserve a small random audit slice if the task pool is large enough.

Do not require a mature learned selector for the first demo. Learned or
adaptive selection can become the next iteration once the clean demo loop is
working.

Recommended wording:

> The demo uses an interpretable rule-based benchmark first. Later versions will
> use historical rolling validation to learn better weights and update the
> selector safely.

## Metrics

Execution metrics:

- scoreable cell rate;
- verifier replay success rate;
- hidden-test leakage count;
- endpoint or policy violations;
- invalid or flaky cell rate;
- cost per scoreable cell;
- latency per task.

Decision metrics:

- benchmark winner vs holdout winner;
- benchmark pass-rate gap vs holdout pass-rate gap;
- selection accuracy across Agent pairs if multiple pairs are tested;
- future holdout MAE if enough cells exist;
- catastrophic miss count.

Tuning metrics:

- before/after holdout pass-rate change;
- regression rate;
- cost per validated improvement;
- failure-label shift;
- unchanged or improved scoreable-cell rate.

Story metrics:

- report readability for non-specialist reviewers;
- number of concepts exposed in the demo report;
- whether a reviewer can explain the demo in one sentence.

## Risks And Mitigations

Risk: the demo depends too much on mature predictive benchmark optimization.

Mitigation: make the first demo an execution and decision demo, not a full
predictive-validity proof. Use rule-based selection first.

Risk: old code concepts leak into the demo and make it hard to explain.

Mitigation: create a clean demo layer with simplified artifacts and reports.
Treat old code as implementation support, not as the product surface.

Risk: SKVM or DSPy does not produce a visible gain.

Mitigation: make Agent selection the primary demo. Treat tuning as a secondary
or stretch demo. Allow Hermes Agent or another internal Coding Agent as the
target.

Risk: no concrete business sponsor is available.

Mitigation: produce a strong prototype result and prepare a separate internal
community post to find potential users.

Risk: task supply is too small.

Mitigation: choose a target repository with enough existing certified or
certifiable tasks. If necessary, narrow the demo claim to one repository and one
Agent pair.

Risk: the result is not directionally correct on holdout.

Mitigation: report it honestly as a selector failure, keep the execution demo
value, and use the failure to motivate learned selector work.

## Deliverables

Minimum deliverables:

- clean demo pipeline;
- one target repository;
- one benchmark task set and one holdout task set;
- 2-3 Agent configurations;
- one Agent comparison report;
- one slide-friendly Chinese summary;
- raw local logs kept out of Git;
- sanitized metrics committed only if safe.

Optional deliverables:

- Agent tuning before/after report;
- internal community post draft;
- short demo video or screenshot sequence;
- GPT-5.5-Pro review of demo target selection and experiment design.

## GPT-5.5-Pro Research Prompt

Use this prompt if we want an external model to help choose the AB demo target
and experiment design.

```text
You are advising on an AB demo for a repo-specific predictive Agent evaluation
system.

Context:
We are building a system that evaluates complete Coding Agents on a target
repository. A complete Agent includes model, harness, tools, prompt/hooks,
retrieval, runtime policy, and budget. The system constructs repo-specific
tasks, runs the Agent in an isolated solver workspace, captures the final diff,
replays the diff in a verifier workspace with hidden tests, and produces score,
failure labels, cost, latency, and comparison reports.

We need a demo for internal reviewers. The demo should be easy to explain,
avoid excessive terminology, and not depend on proving full predictive validity.
It should show that the system can support either Agent selection or Agent
tuning on a real Coding Agent setting.

Constraints:
- We want a clean independent demo layer, not a direct exposure of old research
  scripts or old terminology.
- We can reuse proven assets internally: workspace setup, diff capture,
  verifier replay, task certification, score tables, and cost accounting.
- The first selector should probably be rule-based: module coverage, recency,
  source balance, oracle confidence, budget cap, and possibly a random audit
  slice.
- Learned or adaptive selectors are future work unless the demo design clearly
  justifies them.
- The demo should avoid making project value depend solely on whether SKVM or
  DSPy is already considered valuable internally.

Candidate demo directions:
1. Agent selection AB:
   Compare 2-3 Agent configurations on a target-repo benchmark, choose a
   winner, and verify the choice on independent holdout tasks.
2. Agent tuning AB:
   Use benchmark feedback to tune an Agent with SKVM, DSPy, Hermes Agent, or a
   manual tuning pass, then validate before/after on holdout tasks.

Please advise on:
1. Which demo direction should be primary and why.
2. How to choose the target repository.
3. How to choose Agent configurations so the demo is meaningful but not
   artificially easy.
4. How to split tasks into benchmark and holdout without overclaiming.
5. What minimum task counts are needed for a credible demo.
6. What metrics should be shown to reviewers.
7. What result would be considered a successful execution demo, decision demo,
   and stretch performance demo.
8. How to avoid leakage, overfitting, and misleading before/after claims.
9. How to keep the demo language low-terminology and understandable to
   non-specialist reviewers.
10. What would make the demo look investable even without a concrete business
    sponsor.

Please produce a practical recommendation with a preferred demo design,
fallback design, risks, and a short execution plan.
```
