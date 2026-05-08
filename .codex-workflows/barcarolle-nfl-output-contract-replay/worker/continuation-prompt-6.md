# Worker Continuation 6 Prompt

You are the worker for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This continuation is a tightly bounded live retry experiment after reviewer-approved no-spend repair work. Do not broaden scope. Do not read worker or reviewer CLI logs. Use process files and artifacts for coordination.

## Starting Context

Reviewer recheck 6 found no issues in continuation 5:
- The three existing Click 005 patch-ready artifacts replayed against the repaired verifier and passed `3/3`.
- Click 005 historical patch-ready failures are now classified as verifier fixture defects.
- Click 005 `cheap-click-specialist` remains an invalid model-output contract case.
- Click 008 context packaging and v3 anchor diagnostics were hardened while preserving Gate 1 strictness.
- The minimal supported next live retry set is exactly five attempt-2 cells:
  - `click__rbench__005` x `cheap-click-specialist`
  - `click__rbench__008` x `cheap-generic-swe`
  - `click__rbench__008` x `frontier-generic-swe`
  - `click__rbench__008` x `cheap-click-specialist`
  - `click__rbench__008` x `frontier-click-specialist`

The user has asked the supervisor to keep pushing step-by-step unless blocked by real API funds/quota, missing credentials, repo auth, or required user input.

## Required Scope

Run only the five attempt-2 cells above using the current repaired/hardened runner path.

Before any live call:
- Run the existing budget/funds/credential preflight path used by this experiment stack.
- If budget, provider quota/funds, or required credentials are unavailable, mark `worker/process.md` as `blocked` with exact evidence and stop.

During the experiment:
- Do not run any other ACUTs, tasks, attempts, repos, or Click 009+ cells.
- Do not rerun passing Click 004/006/007 cells.
- Do not weaken Gate 1, clean replay, patch validation, invalid-submission classification, or verifier execution.
- Record provider usage in the cost ledger using the established provider-reported usage path.
- Preserve historical attempt-1 artifacts unchanged.

Suggested run prefix:
`codex_nfl_output_contract_v3_click_005_008_attempt2_20260508`

## Required Artifacts

Produce machine-readable artifacts consistent with prior runs, including:
- live batch summary JSON;
- normalized per-cell artifacts;
- normalized summary JSON;
- cost reconciliation JSON;
- decision/interpretation JSON if the existing tooling supports it;
- raw redacted provider responses and prompt snapshots for all five cells;
- report update in `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`.

The report update must state:
- the repaired attempt-1 interpretation after Click 005 replay;
- the five-cell attempt-2 result table;
- whether the Click 005 invalid-submission repair succeeded;
- whether Click 008 improved after context hardening;
- updated provider-usage cost for the attempt-2 retry;
- whether the next step should be more live retries, no-spend analysis, or PR packaging.

## Verification Expectations

Run bounded checks after the live retry:
- JSON validation for new artifacts.
- Artifact count checks for exactly 5 normalized results and 5 redacted provider responses under the new prefix.
- Cost ledger/reconciliation check for exactly 5 new provider-usage records under the new prefix.
- Focused runner tests if any code changes are made.

Do not leave `worker/process.md` vague. It must end with `status: delivered` or `status: blocked`, updated timestamp, files changed, artifacts produced, verification, result summary, cost status, and reviewer handoff.
