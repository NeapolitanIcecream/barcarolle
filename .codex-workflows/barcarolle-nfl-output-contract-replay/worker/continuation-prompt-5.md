# Worker Continuation 5 Prompt

You are the worker for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This continuation is a no-new-spend local engineering/experiment pass. Do not run live model calls, retries, extra attempts, broader repos, Click 009+, or anything that consumes LLM/API provider funds. If the only way forward appears to require new provider spend, stop and mark `worker/process.md` as `blocked` with the exact reason.

Do not read worker or reviewer CLI logs. Use the workflow process files and artifacts.

## Starting Context

Reviewer recheck 5 found no issues in continuation 4. The approved next local step is:

1. Replay the three existing Click 005 patch artifacts against the repaired Click 005 verifier.
2. Tighten v3 anchor guidance and Click 008 context packaging before any new live retry.
3. Produce auditable machine-readable artifacts and report updates that make the next live decision clear.

The Click 005 fixture repair already added `test_case_insensitive_choice_returned_exactly` to:
`experiments/core_narrative/tasks/click/rbench/click__rbench__005/verifier/hidden/tests/test_options.py`

The Click 004-008 expansion remains historically recorded as `11 passed`, `5 failed`, `4 invalid_submission`, with Click 005's three failed patch-ready cells treated as verifier-collection artifacts pending repaired-verifier replay.

## Required Work

Keep the work bounded and local.

### A. Replay Existing Click 005 Patch Artifacts

- Locate only the three existing patch-ready Click 005 artifacts from the `codex_nfl_output_contract_v3_click_004_008_20260508` expansion.
- Re-run those existing patches against clean prepared Click 005 task workspaces using the repaired verifier.
- Do not regenerate model output and do not alter historical normalized artifacts.
- Write a machine-readable replay artifact, for example:
  `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_repaired_verifier_replay_20260508.json`
- The artifact must identify each replayed cell, source normalized/raw artifact, patch source, verifier command/result, pass/fail status, and any local-environment caveat.

If exact replay is impossible locally because a required non-LLM dependency/artifact is missing, preserve all evidence, record a precise local blocker in the artifact and process file, and continue with the prompt/context hardening work.

### B. Tighten Prompt / Output Contract / Context Packaging

Use the Click 005/008 triage evidence to make the next live retry less likely to fail for known local reasons:

- Tighten `anchored-search-replace-json-v3` guidance or validation so anchor mismatch and old-occurrence mismatch failures produce clearer diagnostics and stronger instructions for the model.
- Improve Click 008 context packaging or preflight diagnostics so the task context is less likely to omit files needed to reason about `Option(... prompt_required=...)`.
- Keep Gate 1 strict. Do not weaken clean replay, verifier execution, patch application, or invalid-submission classification.
- Add focused tests for any code behavior changed.

Prefer existing runner/helper patterns over new frameworks.

### C. Report And Handoff

Update the existing report:
`experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`

The report must clearly state:
- Click 005 historical box score remains unchanged.
- Repaired-verifier replay result, if successfully run.
- Whether the Click 005 failures should now be treated as verifier fixture defects, model/task failures, or unresolved local replay caveats.
- What was changed for prompt/output-contract/context hardening.
- Whether a new live retry is now justified, and if so, exactly which minimal cells should run next.

Update `worker/process.md` before and after meaningful phases. Final status must be either:
- `delivered` with files changed, artifacts produced, verification, result summary, and reviewer handoff; or
- `blocked` only for a real hard blocker such as missing credentials/API funds/repo auth/user input, or a precise local non-LLM artifact/dependency blocker that prevents the required replay.

## Verification Expectations

Run bounded local checks relevant to the touched scope, such as:
- JSON validation for new result artifacts.
- Syntax checks for changed Python/shell files.
- Focused pytest tests for runner/prompt/context behavior.
- Any local replay verification command used for the Click 005 patch artifacts.

Do not run live model calls.
