# Worker Continuation 7 Prompt

You are the worker for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This continuation is a no-spend Click 008 failure-analysis pass. Do not run live model calls, retries, extra attempts, broader repos, Click 009+ work, or anything that consumes LLM/API provider funds. Do not read worker or reviewer CLI logs. Use process files and experiment artifacts for coordination.

## Starting Context

Reviewer recheck 7 found no issues in continuation 6:
- The five-cell attempt-2 retry stayed exactly in scope.
- Click 005 `cheap-click-specialist` recovered and passed with clean replay verifier exit `0`.
- Click 008 remained non-passing in the bounded retry: `0 passed`, `1 failed`, `3 invalid_submission`.
- Scoped provider-usage cost was `0.986359` USD across exactly five new provider-usage ledger records.
- Recommended next technical step: no-spend analysis of Click 008 retry artifacts before any further live spend.

## Required Work

Perform a bounded no-spend analysis of Click 008 attempt-1 and attempt-2 artifacts to answer:

1. Why did Click 008 fail to improve after prompt/context hardening?
2. Are the remaining failures primarily model-output contract failures, context-packaging failures, task/verifier-semantics issues, or ordinary model implementation failures?
3. Is there a local engineering fix that can be made before more live spend, without weakening Gate 1?
4. If another live run is eventually justified, what is the minimal next run and what evidence threshold should trigger it?

Stay local and evidence-based:
- Inspect only existing Click 008 attempt-1/attempt-2 normalized/raw artifacts, prompt snapshots, runner results, clean-replay/verifier outputs, task fixtures, and relevant runner code/tests.
- Do not mutate historical attempt artifacts.
- Do not use hidden verifier content or reference patches as future prompt context.
- Preserve strict clean replay and invalid-submission classification.

If you identify a focused local engineering fix, implement it with tests and no live calls. Examples could include better preflight/context diagnostics, stronger prompt constraints, or a safer output-contract validation diagnostic. Do not make speculative broad refactors.

If no useful local engineering fix remains, do not force one. Instead, produce a clear artifact and report section saying the next step is a technical/design decision or external consultation.

## Required Artifacts

Produce or update:
- A machine-readable Click 008 analysis artifact, for example:
  `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_008_attempt2_failure_analysis_20260508.json`
- The existing report:
  `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- `worker/process.md`

The analysis artifact must include:
- included cells and source artifacts;
- attempt-1 vs attempt-2 status comparison;
- invalid-submission failure classes and evidence;
- verifier failure evidence for the patch-ready Click 008 cells;
- context-packaging evidence, including whether focused `Option` context was present;
- root-cause classification with confidence;
- recommended next action and why.

The report update must state the Click 008 story in plain language:
- what changed before attempt 2;
- what did and did not improve;
- what the evidence says about why;
- whether another local engineering step exists;
- whether further live spend is justified now.

## Verification Expectations

Run bounded local checks:
- JSON validation for the new analysis artifact.
- Syntax/tests only if code is changed.
- Artifact count/source-reference checks for the Click 008 attempt-1/attempt-2 cells analyzed.

Final `worker/process.md` status must be `delivered` or `blocked`. Use `blocked` only for a real hard blocker: API funds/quota, missing credentials, repo auth, required user input, or inaccessible required local artifacts.
