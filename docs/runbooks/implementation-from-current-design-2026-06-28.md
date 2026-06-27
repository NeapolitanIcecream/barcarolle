# Runbook: Implement From Current Design

Status: ready for execution, 2026-06-28.

## Purpose

Implement Barcarolle module by module from the current design documents, with a
per-module worker/reviewer loop. The goal is to reach a small, auditable
implementation that preserves the benchmark evidence chain.

## Authority

The design documents are the only source of truth for intended behavior:

- `docs/design/README.md`
- `docs/design/system-design.md`
- `docs/design/data-flow.md`
- `docs/design/source-alignment-check.md`
- `docs/design/modules/records.md`
- `docs/design/modules/task-pool.md`
- `docs/design/modules/verification.md`
- `docs/design/modules/workspace.md`
- `docs/design/modules/result-store.md`
- `docs/design/modules/selection.md`
- `docs/design/modules/reporting.md`
- `docs/design/modules/runner.md`
- `PROCESS.md`

If this runbook, existing code, archived material, or an agent's assumptions
conflict with the design documents, the design documents win. Do not import
archived abstractions, old module names, or alternate vocabulary as active API
concepts.

## Review Stop Line

Use the `PROCESS.md` design review stop line for all implementation reviews.
Review findings must focus on gaps that can break the trustworthy evidence
chain:

- stale paid results can be reused;
- Selectors can see future results or future-derived features;
- Task, Check, or oracle records can mismatch;
- selected or future denominators become unauditable;
- frozen selections, results, or metrics can be changed after the fact;
- reports lose traceability to cell, matrix, or result evidence.

Do not fail review merely because a schema could be more expressive, a feature
or metric taxonomy could be richer, a report could have more views, or a
validator could cover more future field combinations.

## Module Order

Implement in this order unless the design documents require a narrower
dependency step:

1. Records
2. Task Pool
3. Verification
4. Workspace
5. Result Store
6. Selection
7. Reporting
8. Runner

Keep each module small. Prefer direct functions and plain record contracts over
frameworks or new abstractions.

## Per-Module Loop

For each module, run a worker/reviewer loop based on the
`codex-design-review-loop` pattern:

1. Create a workflow under `.codex-workflows/<module-slug>/`.
2. Start a worker Codex CLI session to implement only that module and the tests
   needed for its design boundary.
3. The worker must update `worker/process.md` before and after meaningful phases.
4. When the worker reports `status: delivered`, start an independent reviewer
   Codex CLI session.
5. The reviewer must inspect the implementation against the design documents and
   this runbook, then write `reviewer/review-to-worker.md`.
6. If the reviewer reports `issues_found`, hand the review back to the worker and
   repeat the revision/recheck loop.
7. Move to the next module only after the reviewer reports `no_issues`.

Do not read worker or reviewer CLI logs for coordination. Use `process.md` and
review handoff files. Logs are for debugging only.

## Worker Prompt Requirements

Each worker prompt must state:

- the repository path;
- the module being implemented;
- the exact design files to read before editing;
- that design documents are the only source of truth;
- that implementation must preserve current module vocabulary;
- that new concepts, module names, or broad frameworks are not allowed unless a
  design document requires them;
- that focused tests should be added or updated where risk justifies them;
- that `uv` should be used for repo-local Python tooling;
- that `git diff --check` and relevant tests must be run before delivery when
  feasible.

Workers must not run paid benchmark Agent-solving calls. If a step appears to
require paid benchmark execution, stop and write a blocker report. Any explicit
paid LLM or Agent call must obey `PROCESS.md` and use only `LLM_BASE_URL` and
`LLM_API_KEY`.

## Reviewer Prompt Requirements

Each reviewer prompt must prohibit editing implementation files. The reviewer
must check:

- whether the module implements the function boundaries, inputs, outputs, and
  effects from its design document;
- whether record identities and digests are used where the design requires them;
- whether append-only evidence records cannot be mutated in place;
- whether cache identity, leakage prevention, Task/Check linkage, denominator
  policy, and report traceability remain intact;
- whether the implementation introduced unnecessary vocabulary, concepts,
  storage layers, framework abstractions, or behavior not present in the design;
- whether relevant tests or verification were run, or whether skipped
  verification is clearly justified.

Reviewer findings should be concise and actionable. Do not reopen design choices
that are already accepted in `docs/design/` and `PROCESS.md`.

## Module Completion Criteria

A module is complete when:

- worker reports `status: delivered`;
- reviewer reports `status: no_issues`;
- relevant tests pass or skipped tests are justified;
- `git diff --check` passes;
- changed files are limited to the module, its tests, and necessary integration
  points;
- no new first-class concepts or module names were introduced outside the design.

## Runbook Completion Criteria

This runbook is complete when all eight modules pass their reviewer loop and the
Runner can execute the designed end-to-end path far enough to produce claim-safe
records or a documented blocker for any external dependency that cannot be
exercised locally.
