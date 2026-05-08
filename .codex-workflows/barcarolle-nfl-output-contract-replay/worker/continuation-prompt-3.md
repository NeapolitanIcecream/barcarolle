# Worker Continuation 3

You are the WORKER agent continuing the Barcarolle NFL output-contract replay workflow in `/Users/chenmohan/gits/barcarolle`.

Do not read worker or reviewer CLI logs. Use and update `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md` as the progress channel. Preserve unrelated user changes, especially `docs/draft/barcarolle-leadership-report.md`.

## Current Reviewed State

Reviewer recheck 2 reported `status: no_issues`. Continuation 2 recovered strict clean replay for `frontier-click-specialist x click__rbench__003` with `anchored-search-replace-json-v3`. Gate 1 was not weakened. The old captured response remains a no-new-spend `invalid_unified_diff` diagnostic. The report says Click 004-008 are now justified as the next controlled expansion subject to normal budget/expansion controls.

## Supervisor Continuation Goal

Do not stop at report packaging while there is a clear local next step. The next useful step is the controlled Click 004-008 expansion using the v3 output contract.

## Required Work

1. Keep Gate 1 and budget controls strict. Do not bypass existing budget/credential/gate checks. Stop only for actual API funds/quota exhaustion, missing LLM credentials, repo auth failure, or necessary user input.
2. Before live expansion, run the cheapest local sanity checks needed to confirm the v3 contract path and task materialization for Click 004-008.
3. Run the controlled expansion on Click 004-008 using the v3 contract and the four core ACUTs:
   - `cheap-generic-swe`
   - `frontier-generic-swe`
   - `cheap-click-specialist`
   - `frontier-click-specialist`
4. Record every run with existing raw/redacted artifacts, normalized results, and cost ledger semantics. Keep raw provider responses redacted according to existing policy.
5. Summarize Click 004-008 outcomes, reconcile provider-usage cost, update the experiment report, and create/update machine-readable decision artifacts. If the expansion creates a clear next local step, state it in `process.md` so the supervisor can continue.

## Scope Discipline

- Do not run broad non-Click families.
- Do not run extra attempts unless a local gate/report explicitly justifies them and budget allows; prefer delivering the controlled expansion evidence first.
- Do not change scoring semantics to make failures look better. Classify model-output, verifier/task, infra, and clean-replay results as the existing repaired pipeline dictates.

## Completion

When done, set `worker/process.md` to `status: delivered` with files changed, artifacts produced, verification, cost status, expansion summary, and a concise reviewer handoff.
