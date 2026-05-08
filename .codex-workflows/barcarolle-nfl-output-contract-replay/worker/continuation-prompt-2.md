# Worker Continuation 2

You are the WORKER agent continuing the Barcarolle NFL output-contract replay workflow in `/Users/chenmohan/gits/barcarolle`.

Do not read worker or reviewer CLI logs. Use and update `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md` as the progress channel. Preserve unrelated user changes, especially `docs/draft/barcarolle-leadership-report.md`.

## Current Reviewed State

Local reviewer recheck 1 reported `status: no_issues`. Revision 1 closed the evidence-quality issue by replaying the captured `frontier-click-specialist x click__rbench__003` response through the final repaired code path with no new spend. The canonical replay now emits `invalid_unified_diff`, `failure_owner: model_output`, `patch_ready: false`, and strict Gate 1 remains failed. Click 004-008 were correctly skipped.

## Supervisor Continuation Goal

Do not stop at report packaging while there is a clear local next step. The next useful step is to advance Gate 1 readiness beyond diagnostics: try one bounded engineering/experiment iteration to make `frontier-click-specialist x click__rbench__003` produce a verifier-ready clean replay, or prove that the next failure mode is still model-output after the stronger contract.

## Required Work

1. Keep Gate 1 strict. Do not weaken `all_runs_have_clean_patch_replay`; do not expand to Click 004-008 unless clean replay is actually recovered and justified.
2. Improve the model-output contract/prompt path for the targeted frontier-click task 003 failure. Prefer repo-local, testable changes such as stricter response schema, explicit unified-diff validity constraints, exact anchor requirements, or pre-submit response validation messaging. Avoid broad refactors.
3. Add or update focused tests for the new contract behavior before or alongside implementation. Existing regression coverage for atomic search/replace and invalid unified diff must stay green.
4. Run the relevant local test suite.
5. Run the smallest useful targeted experiment after the change:
   - First use no-new-spend replay/smoke where it can validate the local parser/diagnostics.
   - If local evidence supports a new live attempt and no hard blocker exists, run at most one new targeted live cell: `frontier-click-specialist x click__rbench__003`.
   - Reconcile cost and ledger exactly. Stop and mark blocked only for API funds/quota exhaustion, missing credentials, repo auth failure, or necessary user input.
6. Update machine-readable artifacts and the experiment report/Gate decision. If clean replay is recovered, explain the next justified step; if not, clearly classify the remaining failure and keep Click 004-008 skipped.

## Completion

When done, set `worker/process.md` to `status: delivered` with files changed, artifacts produced, verification, cost status, and a concise reviewer handoff.
