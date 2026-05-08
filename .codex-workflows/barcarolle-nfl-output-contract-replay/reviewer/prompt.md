# Reviewer Task

You are the REVIEWER agent. Work in `/Users/chenmohan/gits/barcarolle`.

Do not edit task artifacts, source files, docs, or experiment outputs. Review the worker's delivered work and provide concise, actionable feedback.

## Task Under Review

Repair the Codex NFL output contract / patch replay path that blocked Gate 1, keep Gate 1 clean-replay strict, add regression coverage for ambiguous search/replace on Click task 003 style failures, run a targeted frontier-click-specialist x click__rbench__003 rerun after the fix, and produce a PR-ready report explaining whether Gate 1 can now pass and whether Click 004-008 expansion is justified.

## Work Type

implementation+experiment

## Expected Deliverable

Focused code/tests/artifacts/report for the output-contract replay repair and targeted live rerun, with local reviewer closure and PR-ready evidence.

## Inputs

- Read `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`.
- Inspect the files or artifacts the worker says changed.
- Run read-only checks or tests when useful and safe.
- Judge whether the delivered work satisfies the requested task.

## Review Focus

Verify that Gate 1 was not weakened, ambiguous model-output failures are handled by robust diagnostics or a replayable patch contract, tests cover the failure mode, live spend is minimal and cost-accounted, and the report supports next-step expansion decisions without overclaiming.

Also preserve user-approved assumptions and existing ownership boundaries. Do not reopen by-design decisions as findings.

## Process File Contract

Maintain `.codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/process.md`.

Keep it compressed. It must include:

- current status: `working`, `delivered`, or `blocked`;
- short summary;
- files inspected;
- checks or tests run;
- findings count;
- if blocked, what is missing.

## Review Handoff Contract

Write `.codex-workflows/barcarolle-nfl-output-contract-replay/reviewer/review-to-worker.md`.

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
