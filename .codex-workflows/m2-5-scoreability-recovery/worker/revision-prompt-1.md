# Worker Revision 1

You are the WORKER agent for `/Users/chenmohan/gits/barcarolle`.

The reviewer found two closure issues in `.codex-workflows/m2-5-scoreability-recovery/worker/review-feedback-1.md`. Address those issues only. Do not broaden the experiment, do not spend new live model calls unless a deterministic regeneration command already requires it and the existing budget/env gates allow it, and do not claim M2.5 passed.

## Required Fixes

1. Fix M2.5 normalized metadata consistency.
   - Patch availability and persistence must come from the workspace-diff collection, not verifier outcome.
   - Clean replay attempted must come from whether `verify_patch()` was invoked.
   - Replay failure must be represented separately from patch availability.
   - Preserve adapter unsafe-patch attribution in normalized output when a live adapter rejects a patch before the second workspace collection sees an empty workspace.
   - Add a regression test for a non-empty workspace diff whose clean replay returns `invalid_submission`.

2. Fix M2.5 report reproduction commands.
   - Generated reports must include exact delivered flags such as `--force`.
   - The noop report must include `--skip-noop-check`.
   - If live reruns are budget/env-gated, say that explicitly while still giving the exact delivered command.

## Verification

Run the focused new/changed tests and any relevant existing M2.5/R0/S1 tests. Regenerate affected JSON and Markdown artifacts so source, results, and reports are internally consistent.

## Process Contract

Update `.codex-workflows/m2-5-scoreability-recovery/worker/process.md` before and after the revision. When complete, set `status: delivered`, list changed files/artifacts, verification commands, and a concise reviewer handoff.
