# Runbook: Implement From Current Design

Status: completed, 2026-06-28.

## Purpose

Implement Barcarolle module by module from the current design documents. The
Agent executing this runbook is the worker for each module; an independent
Reviewer Codex CLI session audits the worker's delivered changes after each
module. The goal is to reach a small, auditable implementation that preserves
the benchmark evidence chain.

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

`PROCESS.md` is not a source of truth for this implementation run. It may be
stale and must not override or complete the design documents. Use it only as
historical/process context when it is consistent with the design documents and
this runbook.

If this runbook, `PROCESS.md`, existing code, archived material, or an agent's
assumptions conflict with the design documents, the design documents win. Do not
import archived abstractions, old module names, or alternate vocabulary as
active API concepts.

## Archive-First Reset

Before implementing modules, verify that legacy implementation code and old
design documents are under `archive/`. If active, non-archived legacy code or
old design material remains outside the current design set, archive it first in
a focused step with a short manifest.

Make this check from the Git-tracked/source perspective. Old source files,
tracked docs, or active configuration that still define the previous system
belong in `archive/`. Ignored local residue such as `__pycache__`, `.cache`,
`.hypothesis`, `outputs/`, raw CLI logs, raw prompts, transcripts, and other
large or generated artifacts must not be archived or committed; delete them or
leave them ignored.

New production code should be written from a clean starting point against the
current design documents. Do not copy old implementation modules forward as the
starting structure. Archived code may be inspected only as historical reference
after identifying the current owner module and design contract it would need to
satisfy.

## Review Stop Line

Use this review stop line for all implementation reviews. Review findings must
focus on gaps that can break the trustworthy evidence chain:

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

1. Archive-first reset
2. Records
3. Task Pool
4. Verification
5. Workspace
6. Result Store
7. Selection
8. Reporting
9. Runner

Keep each module small. Prefer direct functions and plain record contracts over
frameworks or new abstractions.

## Per-Module Loop

For each module, run a worker/reviewer loop inspired by the
`codex-design-review-loop` review discipline, but do not delegate worker duties
to a separate Codex session. The Agent executing this runbook is the worker.

1. Create a workflow under `.codex-workflows/<module-slug>/`.
2. As the worker, implement only that module and the tests needed for its design
   boundary.
3. As the worker, update `worker/process.md` before and after meaningful phases.
4. When the worker writes `status: delivered`, start an independent reviewer
   Codex CLI session.
5. The reviewer must inspect the implementation against the design documents and
   this runbook, then write `reviewer/review-to-worker.md`.
6. If the reviewer reports `issues_found`, the runbook Agent resumes worker
   duties, fixes the issues, updates `worker/process.md`, and repeats the
   reviewer check.
7. Move to the next module only after the reviewer reports `no_issues`.

Do not start an independent Worker Codex CLI session. Do not read reviewer CLI
logs for coordination. Use `process.md` and review handoff files. Logs are for
debugging only. `.codex-workflows/` is coordination state and must not be
committed.

Reviewer Codex CLI sessions are repository-maintenance review sessions. They
should use the user's local Codex CLI authentication/subscription. Do not route
Reviewer sessions through `LLM_BASE_URL` or `LLM_API_KEY` unless the user
explicitly asks for that execution mode.

## Worker Prompt Requirements

The runbook Agent's worker notes for each module must state:

- the repository path;
- the module being implemented;
- the exact design files to read before editing;
- that design documents are the only source of truth;
- that `PROCESS.md` is not a source of truth and must not override the design
  documents;
- that new production code must start from the current design, not from archived
  or legacy implementation structure;
- that implementation must preserve current module vocabulary;
- that new concepts, module names, or broad frameworks are not allowed unless a
  design document requires them;
- that focused tests should be added or updated where risk justifies them;
- that `uv` should be used for repo-local Python tooling;
- that `git diff --check` and relevant tests must be run before delivery when
  feasible.

The worker must not run paid benchmark Agent-solving calls. If a step appears to
require paid benchmark execution, stop and write a blocker report. Any explicit
benchmark/evidence-producing paid LLM or Agent call must obey `AGENTS.md` and
use only `LLM_BASE_URL` and `LLM_API_KEY`. This restriction does not apply to
Reviewer Codex CLI sessions, which are repository-maintenance review sessions
and should use the user's local Codex CLI authentication/subscription.

## Reviewer Prompt Requirements

Each reviewer prompt must prohibit editing implementation files. The reviewer
must check:

- whether the module implements the function boundaries, inputs, outputs, and
  effects from its design document;
- whether record identities and digests are used where the design requires them;
- whether append-only evidence records cannot be mutated in place;
- whether cache identity, leakage prevention, Task/Check linkage, denominator
  policy, and report traceability remain intact;
- whether the implementation was built from the current design rather than
  copy-forward legacy code;
- whether the implementation introduced unnecessary vocabulary, concepts,
  storage layers, framework abstractions, or behavior not present in the design;
- whether relevant tests or verification were run, or whether skipped
  verification is clearly justified.

Reviewer findings should be concise and actionable. Do not reopen design choices
that are already accepted in `docs/design/`.

## Module Completion Criteria

A module is complete when:

- worker reports `status: delivered`;
- reviewer reports `status: no_issues`;
- relevant tests pass or skipped tests are justified;
- `git diff --check` passes;
- changed files are limited to the module, its tests, and necessary integration
  points;
- active legacy implementation or old design material has been archived before
  new module code is introduced;
- no new first-class concepts or module names were introduced outside the design.

## Runbook Completion Criteria

This runbook is complete when all eight modules pass their reviewer loop and the
Runner can execute the designed end-to-end path far enough to produce claim-safe
records or a documented blocker for any external dependency that cannot be
exercised locally.
