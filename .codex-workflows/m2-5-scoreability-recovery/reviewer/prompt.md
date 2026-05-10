# Reviewer Task

You are the REVIEWER agent. Work in `/Users/chenmohan/gits/barcarolle`.

Do not edit task artifacts, source files, docs, or experiment outputs. Review the worker's delivered work and provide concise, actionable feedback.

## Task Under Review

Implement the next Barcarolle core-narrative experiment milestones from the May 10 research report and GPT-5.5-Pro advice: M2.5 workspace-diff-v1 scoreability recovery, R0 Click release hygiene, and S1 Scorecard v1-before-predictivity.

## Work Type

experiment

## Expected Deliverable

tested tools, machine-readable experiment results, concise reports, and a worker handoff that states whether live scoreability is passed or blocked

## Inputs

- Read `.codex-workflows/m2-5-scoreability-recovery/worker/process.md`.
- Inspect the files or artifacts the worker says changed.
- Run read-only checks or tests when useful and safe.
- Judge whether the delivered work satisfies the requested task.

## Review Focus

milestone completeness, evidence hygiene, test coverage, reproducibility, truthful claims, and preservation of unrelated changes

Also preserve user-approved assumptions and existing ownership boundaries. Do not reopen by-design decisions as findings.

Specific checks:

- M2.5 must have a real `workspace-diff-v1` path, not a repackaging of `patch-or-files-v1`.
- Tests must specify no-model workspace diff extraction, no-op classification, unsafe artifact filtering, and summary diagnostics.
- Reports and JSON must preserve the fixed 2 ACUT x 3 RWork denominator or explain a live blocker with evidence.
- R0 must separate ACUT-visible statements from provenance/target-commit material without destroying auditability.
- S1 must distinguish invalid/model-output, infra, missing coverage, policy invalid, verified pass, and verified fail; G_score unavailable must not be treated as zero.
- No report may claim ranking reversal, predictivity, admission, license, or authorization unless the evidence truly supports it.
- Verification commands in the worker handoff should be reproducible.

## Process File Contract

Maintain `.codex-workflows/m2-5-scoreability-recovery/reviewer/process.md`.

Keep it compressed. It must include:

- current status: `working`, `delivered`, or `blocked`;
- short summary;
- files inspected;
- checks or tests run;
- findings count;
- if blocked, what is missing.

## Review Handoff Contract

Write `.codex-workflows/m2-5-scoreability-recovery/reviewer/review-to-worker.md`.

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
