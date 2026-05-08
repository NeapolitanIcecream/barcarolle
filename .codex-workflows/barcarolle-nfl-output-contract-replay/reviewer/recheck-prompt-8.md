# Reviewer Recheck 8 Prompt

You are the reviewer for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This is a review-only pass for worker continuation 7. Do not edit task artifacts. Do not read worker or reviewer CLI logs. Coordinate only through `reviewer/process.md` and `reviewer/review-to-worker.md`.

## Context

Worker continuation 7 claims it completed a no-spend Click 008 failure-analysis pass:
- Scope stayed limited to existing Click 008 attempt-1/attempt-2 normalized/raw artifacts, prompt snapshots, runner/verifier outputs, task fixtures, and relevant runner code/tests.
- No live model calls, retries, extra attempts, broader repos, Click 009+ work, historical artifact mutation, or CLI log reads were run.
- Key finding: Click 008 attempt-2 is not clean evidence that prompt/context hardening failed because no-op verification ran in the same workspace later used for prompt packaging, and the Click 008 verifier copied hidden tests into that workspace before the model prompt was built.
- Local fix: no-op verification now uses a separately prepared `run_id__noop` workspace before any model prompt packaging.
- Changed files:
  - `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
  - `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`
  - `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json`
  - `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- Worker says no further live spend is justified until no-model prompt-packaging verification proves separate no-op and runner workspaces, focused `Option` context present, and hidden verifier test names/SHA absent from the prompt package.

## Review Scope

Inspect delivered artifacts and relevant files only as needed:
- `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`
- `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- `experiments/core_narrative/tools/codex_nfl_experiment_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`
- Existing Click 008 attempt-1/attempt-2 normalized/raw artifacts and prompt snapshots only as needed to validate the claims.

Do not reopen previously closed decisions except where continuation 7 contradicts them.

## Checks To Perform

1. Confirm the no-spend Click 008 analysis artifact is machine-readable and includes included cells, source artifacts, attempt-1 vs attempt-2 comparison, invalid-submission classes, verifier evidence, context-packaging evidence, root-cause classification, and recommended next action.
2. Confirm the root-cause claim is evidence-based: no-op verification could contaminate the prompt workspace with hidden verifier tests before prompt packaging.
3. Confirm the local fix isolates no-op verification into a separate workspace and does not weaken Gate 1, clean replay, verifier execution, patch validation, or invalid-submission classification.
4. Confirm the regression test covers this contamination path and would fail without the fix.
5. Confirm historical attempt artifacts were not modified and no new live calls/spend occurred.
6. Confirm the report explains the Click 008 story in plain language and recommends no further live spend until no-model prompt-packaging verification passes.
7. Decide whether the next useful local step is the no-model prompt-packaging verification named by the worker, a worker revision, or PR packaging.

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

Use `status: no_issues` only if continuation 7 is ready for supervisor continuation or PR packaging. Use `issues_found` for concrete fixable gaps. Use `blocked` only for missing credentials, inaccessible required files, or hard infrastructure blockers.
