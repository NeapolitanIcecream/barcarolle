# Phase 1 Source Context Statement Hardening Process

Status: Step 0 preflight complete.

## What Happened

This run is hardening source context and solver-facing task statement quality for
the frozen attrs, boltons, and click Phase 1 paid pilot supply. The paid pilot
result stays frozen. This run does not make paid LLM calls and does not run paid
ACUT solver cells.

The current branch is `codex/restart-benchmark-compiler` at commit `09501600`
(`Add source context statement hardening runbook`). The dirty tree contains one
known unrelated untracked external-review bundle under
`experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/`.
That bundle was not staged.

All explicitly required committed input files are present. The optional
`*_source_context*.jsonl` certified-task glob has no matching files in the
current checkout; this is recorded as an availability fact, not a blocker,
because the runbook says to use those inputs when present.

## Why It Matters

The paid pilot was clean, but release eligibility and task-statement quality need
to be checked separately from technical certification. The known weak area is
title-only or commit-message-only context, especially where a task may look
certified while still giving the solver a thin problem description.

## Action This Suggests

Continue with a deterministic inventory of the frozen three-repo paid package and
the directly relevant review queues. Keep the external-review bundle untracked
and keep paid outcome labels out of promotion decisions.

## Step Evidence

- `git status --short --untracked-files=all` showed 106 untracked paths, all
  under the known external-review bundle prefix.
- `git log --oneline -5` showed `09501600` as the latest commit.
- Paid calls made by this run: 0.
- Completed paid result changed: false.

## Step 1 Inventory Evidence

What happened: a deterministic inventory tool was added and run for the frozen
paid package plus directly relevant attrs, boltons, and click source-review
queue rows. The inventory covers 96 paid-package tasks and 57 source-review
queue tasks.

Why it matters: the inventory keeps release eligibility separate from technical
certification. It records 96 release-eligible rows before overlay and 153
technical-certified rows in scope.

Action this suggests: send the 31 title-only rows and 57 commit-message-only
rows into the repair queue. Paid outcomes remain excluded from promotion and
priority rules.

## Step 2 Repair Queue Evidence

What happened: the repair queue was generated with 91 rows: 31 title-only paid
tasks, 57 commit-message-only source-review rows, and 3 preexisting attrs public
context repairs kept in the review path for consistency.

Why it matters: the queue is ordered deterministically and records that H_future
outcomes, adapter pass/fail labels, and other paid outcome labels cannot promote
or demote a task.

Action this suggests: create sanitized statement packets for every queued row.
Rows without public problem context should be blocked rather than guessed.

## Step 3 Statement Packet Evidence

What happened: 91 sanitized statement packets were generated. Thirty-four are
ready for review: 31 title-context packets and 3 preexisting attrs public-context
repairs. Fifty-seven commit-message-only packets are blocked for missing public
problem context.

Why it matters: every packet separates solver-visible problem summaries from
non-solver-visible review notes, and none commits raw public API responses, raw
prompts, raw completions, raw diffs, target commit hashes, or hidden oracle
material.

Action this suggests: review each ready or blocked packet for leakage,
ambiguity, and scope, then write the overlay for future split-design
eligibility.

## Step 4 Review And Overlay Evidence

What happened: 91 review records were written. The verdicts were 33
`keep_release_eligible`, 1 `reject_ambiguous_scope`, and 57
`reject_missing_public_problem_context`. The overlay keeps click at 30
release-eligible rows, boltons at 35, and attrs at 30 after excluding
`attrs__v2__056` from future split-design eligibility.

Why it matters: the overlay repairs the title-only weakness without changing the
completed paid task list or paid decision. Commit-message-only rows stay blocked
unless a future run finds non-leaky public problem context.

Action this suggests: build the low-dimensional feature table from the overlay,
with click title-only rows carried as explicit minor risk.
