# Current Project Story

Status: current narrative snapshot, 2026-06-04.

This document records the reader-facing story after the proposal and deck
iterations. It is the narrative companion to
`docs/research/project-state-after-proposal.md`. Use it when explaining what the
project is, why it matters, what evidence exists, and what the next work should
prove.

## One-Sentence Position

Barcarolle is a target-repository benchmark compiler: given a repository,
candidate task sources, an Agent family, and a cutoff, it compiles auditable
benchmark releases that are meant to predict how that Agent will perform on
later real work in the same repository.

## Problem

General coding-agent benchmarks do not answer the question a team has before
deploying or tuning an Agent in one repository: will this complete Agent setup
work on future work in this codebase?

The gap has two parts:

- task distribution mismatch: general benchmark tasks differ from a target
  repository's work;
- time mismatch: past tasks do not automatically represent future work.

SWE-bench-style work, live benchmarks, and generated task supply each address
parts of this problem. Barcarolle's specific claim is that repo-specific
predictive validity should be the design target.

## Method

Barcarolle compiles benchmark releases from certified task supply.

The compiler has these jobs:

- collect candidate tasks from repo history and other task-source adapters;
- certify tasks with public context checks, changed-test or oracle material,
  and leakage controls;
- select a release under a stated policy and budget;
- run complete Agents, meaning model, harness, prompt or skills, tools,
  retrieval, runtime policy, and budget;
- report score, uncertainty, cost, failure labels, and claim boundaries.

Task generation is supply infrastructure. The central research problem is
choosing and validating benchmark releases that predict future Agent
performance.

## Current Evidence

What the evidence supports:

- workspace Agent execution is feasible: the three-repo paid pilot completed
  `120` scoreable cells with endpoint compliance and no policy violations;
- task selection matters: the old weighted target-profile selector badly
  misled on the paid pilot, while simple baselines were better;
- selection likely has optimization room: a coverage-constrained candidate beat
  or tied `93.4%` of same-budget random samples on overall MAE in retrospective
  comparison.

What the evidence does not support:

- predictive validity is not proven;
- the current candidate selector is not established as generally better than
  simple baselines;
- public benchmark rank is not shown to predict later target-repo work.

## Current Reader Story

The project is valuable before predictive validity is proven because it has
identified a concrete missing layer between task generators and Agent tuning: a
compiler that turns repository-specific task supply into auditable benchmark
releases with explicit claim boundaries.

The near-term project should build that compiler and use future holdout or
rolling-origin validation to test whether selected releases predict later Agent
behavior better than simple baselines.

## Related Work Position

Public benchmarks measure broad competence. Live benchmarks reduce temporal
leakage. Synthetic or generated task systems expand task supply. Barcarolle
uses these ideas as inputs where useful, while focusing on a different layer:
repo-specific benchmark compilation under predictive-validity constraints.

This means Barcarolle should keep task-source adapters open. Internal
repo-history mining remains useful, and external generators can be plugged in
when they produce certifiable tasks.

## Product Direction

Agent Tuning is the nearer product route. A validated compiler can provide
benchmark releases, failure labels, reward signals, and before/after reports for
tuning loops.

Agent License is a lighter future packaging route. It can summarize evidence
about whether an Agent is ready for a repository, but it should depend on
benchmark validity.

## Relationship To Proposal V5

`docs/research/barcarolle-proposal-report-v5.md` is a frozen proposal-stage
report. It remains useful for audit, evidence context, and funding history. It
is not the live source for the current story.

Use this document for the current narrative. Use
`docs/research/project-state-after-proposal.md` for factual state and repository
layout. Use the evidence manifest for path-level traceability.
