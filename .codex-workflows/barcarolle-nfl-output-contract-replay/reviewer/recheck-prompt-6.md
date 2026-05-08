# Reviewer Recheck 6 Prompt

You are the reviewer for the Barcarolle NFL output-contract replay workflow.

Repo: `/Users/chenmohan/gits/barcarolle`
Workflow: `.codex-workflows/barcarolle-nfl-output-contract-replay`

This is a review-only pass for worker continuation 5. Do not edit task artifacts. Do not read worker or reviewer CLI logs. Coordinate only through `reviewer/process.md` and `reviewer/review-to-worker.md`.

## Context

Worker continuation 5 claims it completed a no-new-spend local engineering/experiment pass:
- Replayed the three existing Click 005 patch-ready artifacts from `codex_nfl_output_contract_v3_click_004_008_20260508` against the repaired Click 005 verifier.
- All three repaired-verifier replays passed with verifier exit code `0`.
- Historical Click 004-008 normalized artifacts remain unchanged.
- The three historical patch-ready Click 005 verifier failures are now classified as verifier fixture defects.
- The Click 005 `cheap-click-specialist` invalid submission remains a model-output contract failure.
- Hardened v3 anchored-edit guidance and machine-readable mismatch diagnostics without weakening Gate 1.
- Improved Click 008 prompt-required context packaging with focused `Option` excerpts, without hidden verifier content or reference patches.
- Recommended the next live spend, if approved later, as only five attempt-2 cells: `click__rbench__005/cheap-click-specialist` and all four `click__rbench__008` core ACUTs.

## Review Scope

Inspect delivered artifacts and relevant source/tests only as needed:
- `.codex-workflows/barcarolle-nfl-output-contract-replay/worker/process.md`
- `experiments/core_narrative/reports/2026-05-08_codex_nfl_output_contract_replay_repair_report.md`
- `experiments/core_narrative/results/codex_nfl_output_contract_v3_click_005_repaired_verifier_replay_20260508.json`
- The three replay-specific normalized artifacts under `experiments/core_narrative/results/normalized/`
- The three replay-specific raw artifact directories under `experiments/core_narrative/results/raw/`
- `experiments/core_narrative/tools/openclaw_direct_runner.py`
- `experiments/core_narrative/tools/test_openclaw_direct_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_direct_runner.py`
- `experiments/core_narrative/tools/test_codex_nfl_experiment_runner.py`

Do not reopen previously closed decisions except where continuation 5 contradicts them.

## Checks To Perform

1. Confirm the repaired-verifier replay artifact has clear provenance, identifies the three expected Click 005 cells, records patch sources, verifier commands/results, and has no local caveats hiding failures.
2. Confirm historical Click 004-008 normalized artifacts are not rewritten and the report clearly separates historical box score from repaired-verifier replay.
3. Confirm the classification is justified: three Click 005 patch-ready failures are verifier fixture defects after repaired replay; `cheap-click-specialist` Click 005 remains an invalid model-output contract case.
4. Confirm Gate 1 strictness is preserved: bad anchors and old-occurrence mismatches remain invalid submissions; diagnostics became clearer but not permissive.
5. Confirm Click 008 context packaging exposes relevant `Option` context without using hidden verifier content or reference patches.
6. Confirm no new live model calls, retries, extra attempts, broader repos, or Click 009+ artifacts were created.
7. Confirm the recommended next live retry set is minimal and supported by the evidence.

Run bounded checks/tests when useful. If you run commands, report them.

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

Use `status: no_issues` only if continuation 5 is ready for supervisor continuation or PR packaging. Use `issues_found` for concrete fixable gaps. Use `blocked` only for missing credentials, inaccessible required files, or hard infrastructure blockers.
