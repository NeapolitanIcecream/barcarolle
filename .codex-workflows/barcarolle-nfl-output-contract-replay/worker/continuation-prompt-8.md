# Worker Continuation 8 Prompt

You are the worker for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This continuation is a no-model/no-spend Click 008 prompt-packaging verification pass. Do not run live model calls, retries, extra attempts, broader repos, Click 009+ work, or anything that consumes LLM/API provider funds. Do not read worker or reviewer CLI logs. Use process files and experiment artifacts for coordination.

## Starting Context

Reviewer recheck 8 found no issues in continuation 7:
- Click 008 attempt 2 is not clean evidence that prompt/context hardening failed because same-workspace no-op verification could copy hidden verifier tests into the prompt-packaging workspace before model prompting.
- The local runner fix isolates no-op verification in `run_id__noop` without weakening Gate 1, clean replay, verifier execution, patch validation, or invalid-submission classification.
- The next useful local step is no-model prompt-packaging verification proving:
  1. no-op verification uses a separate `noop_workspace`;
  2. direct runner prompt packaging uses a separate runner workspace;
  3. focused `Option` source context is present;
  4. hidden verifier test names and hidden `tests/test_termui.py` SHA are absent from the prompt package.

## Required Work

Run a bounded no-model Click 008 prompt-packaging verification after the continuation 7 fix.

Required scope:
- Click 008 only.
- No model/provider calls.
- No live retry, no attempt 3, no new provider ledger records.
- No mutation of historical attempt-1 or attempt-2 artifacts.
- Use existing runner/no-model/dry-run paths where possible.

Verification must demonstrate:
- The no-op verifier command and direct runner prompt-packaging command use different workspaces.
- The no-op workspace may contain copied hidden verifier tests, but the runner prompt workspace does not.
- The prompt package still includes focused `src/click/core.py` `class Option(Parameter):` context.
- The prompt package excludes hidden verifier test names such as `test_prompt_required_with_required` and `test_prompt_required_false`.
- The prompt package excludes the hidden `tests/test_termui.py` SHA recorded in continuation 7.
- `cost_ledger.jsonl` receives no new records from this pass.

If verification fails, implement a focused local fix with regression coverage and rerun the no-model verification. Do not make broad speculative refactors.

## Required Artifacts

Produce or update:
- A machine-readable verification artifact, for example:
  `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json`
- The existing report:
  `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- `worker/process.md`

The verification artifact must include:
- commands or runner invocations used;
- workspace paths for no-op and prompt packaging;
- evidence that workspaces are separate;
- evidence for focused `Option` context presence;
- evidence that hidden verifier test names/SHA are absent from the prompt package;
- ledger before/after counts;
- pass/fail decision and next action recommendation.

The report update must state whether the Click 008 packaging fix is now locally verified and whether any further live spend is justified.

## Verification Expectations

Run bounded local checks:
- JSON validation for the new verification artifact.
- Syntax/tests if code changes are made.
- Cost ledger before/after count check.
- Prompt-content checks for Option context and hidden verifier name/SHA absence.

Final `worker/process.md` status must be `delivered` or `blocked`. Use `blocked` only for a real hard blocker: API funds/quota, missing credentials, repo auth, required user input, or inaccessible required local artifacts.
