# Reviewer Task

You are the REVIEWER agent. Work in `/Users/chenmohan/gits/barcarolle`.

Do not edit task artifacts, source files, docs, or experiment outputs. Review the worker's delivered work and provide concise, actionable feedback.

## Task Under Review

Run the next Barcarolle Codex NFL follow-up experiments: fill frontier-click-specialist attempt 1 on Click 001-003, run attempt 2 for the four-ACUT 2x2 on Click 001-003, gate on stability, then expand to Click 004-008 when justified; produce an experiment report and PR-ready evidence.

## Work Type

experiment

## Expected Deliverable

Experiment artifacts, normalized summaries, evidence package/report, local review closure, and a PR-ready branch.

## Inputs

- Read `.codex-workflows/barcarolle-nfl-followup-experiments/worker/process.md`.
- Inspect the files or artifacts the worker says changed.
- Run read-only checks or tests when useful and safe.
- Judge whether the delivered work satisfies the requested task.

## Review Focus

Check that the paid live experiment plan was executed or defensibly gated, results are reproducible, cost accounting is accurate, and the report supports the NFL story without overclaiming.

Specifically verify:

- `frontier-click-specialist` attempt 1 was run on Click `001`-`003`, or a hard blocker is documented.
- attempt 2 was run for all four ACUTs on Click `001`-`003`, or a hard blocker is documented.
- the expansion decision followed `next_experiment_decision_gates.md`.
- if the gate passed, Click `004`-`008` were run for all four ACUTs; if not, the report explains why spending stopped.
- normalized summaries and reports are internally consistent with raw/runner artifacts.
- cost accounting separates ledger estimates, provider-reported usage cost, and actual billed-cost caveats.
- any facility fixes are focused and have relevant tests.
- the final report supports the Barcarolle NFL narrative without claiming more than the data can support.

Also preserve user-approved assumptions and existing ownership boundaries. Do not reopen by-design decisions as findings.

## Process File Contract

Maintain `.codex-workflows/barcarolle-nfl-followup-experiments/reviewer/process.md`.

Keep it compressed. It must include:

- current status: `working`, `delivered`, or `blocked`;
- short summary;
- files inspected;
- checks or tests run;
- findings count;
- if blocked, what is missing.

## Review Handoff Contract

Write `.codex-workflows/barcarolle-nfl-followup-experiments/reviewer/review-to-worker.md`.

Use this format:

```markdown
# Review To Worker

status: issues_found | no_issues | blocked

## Summary
...

## Findings
1. ...

## Required Closure
...
```

If there are no issues, write `status: no_issues` and briefly explain why the work is acceptable.

When the review handoff is ready, update `reviewer/process.md` with `status: delivered`.
