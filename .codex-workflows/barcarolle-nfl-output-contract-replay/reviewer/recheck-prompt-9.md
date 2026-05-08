# Reviewer Recheck 9 Prompt

You are the reviewer for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This is a review-only pass for worker continuation 8. Do not edit task artifacts. Do not read worker or reviewer CLI logs. Coordinate only through `reviewer/process.md` and `reviewer/review-to-worker.md`.

## Context

Worker continuation 8 claims it completed a no-model/no-spend Click 008 prompt-packaging verification pass after the continuation 7 no-op workspace isolation fix:
- Scope stayed limited to Click 008 local dry-run verification and prompt-content checks.
- No live model/provider calls, live retries, attempt 3, broader repos, Click 009+ work, historical attempt artifact mutation, or CLI log reads were run.
- No-op verification used a separate `__noop` workspace containing the copied hidden `tests/test_termui.py` SHA.
- Direct runner prompt packaging used a separate runner workspace retaining the base `tests/test_termui.py` SHA.
- The prompt package kept focused `src/click/core.py` `class Option(Parameter):` context.
- The prompt package excluded hidden verifier test names `test_prompt_required_with_required` and `test_prompt_required_false`, and excluded the hidden `tests/test_termui.py` SHA.
- Real `experiments/core_narrative/results/cost_ledger.jsonl` stayed unchanged at 72 records.
- Worker says no further local fix is required for hidden-test contamination. Future live spend is technically defensible only as explicitly approved, bounded Click 008 attempt 3 across the four core ACUTs; no broader Click 009+ or speculative spend is justified.

## Review Scope

Inspect delivered artifacts and relevant files only as needed:
- `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`
- `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_prompt_packaging_verification_20260508.json`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- The new no-model raw/normalized dry-run artifacts named in worker/process.md
- `experiments/core_narrative/results/cost_ledger.jsonl`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`

Do not reopen previously closed decisions except where continuation 8 contradicts them.

## Checks To Perform

1. Confirm the verification artifact is machine-readable and includes commands/invocations, workspace paths, workspace separation evidence, Option-context evidence, hidden verifier absence evidence, ledger before/after counts, pass/fail decision, and next action recommendation.
2. Confirm the no-op workspace and direct prompt workspace are separate, and only the no-op workspace contains hidden verifier contamination.
3. Confirm the prompt package contains focused `class Option(Parameter):` context and excludes hidden verifier test names/SHA.
4. Confirm the real cost ledger was not appended and no live model/provider call occurred.
5. Confirm no historical attempt-1/attempt-2 artifacts were modified.
6. Confirm the report accurately states the Click 008 packaging fix is locally verified and clearly distinguishes technically defensible future live spend from already-approved spend.
7. Decide whether any clear local next step remains before PR packaging. If not, say so explicitly.

Run bounded checks/tests when useful. If you run commands, report them. Do not run live model calls.

## Required Output

Update `reviewer/process.md` with:
- `status: delivered`
- updated timestamp
- concise summary
- files inspected
- checks/tests run
- findings count
- handoff summary

Write `reviewer/review-to-worker.md` exactly in this format:

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

Use `status: no_issues` only if continuation 8 is ready for supervisor continuation or PR packaging. Use `issues_found` for concrete fixable gaps. Use `blocked` only for missing credentials, inaccessible required files, or hard infrastructure blockers.
