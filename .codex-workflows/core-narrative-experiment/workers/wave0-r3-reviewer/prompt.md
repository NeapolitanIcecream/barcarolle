You are a focused reviewer for Wave 0 revision 3 in the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Reviewer repo: /Users/chenmohan/gits/barcarolle-wt-wave0-r3-reviewer
Reviewer branch: codex/core-exp-wave0-r3-reviewer
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment
Process file: /Users/chenmohan/gits/barcarolle-wt-wave0-r3-reviewer/.codex-workflows/core-narrative-experiment/workers/wave0-r3-reviewer/process.md

Do not edit production experiment artifacts. Inspect delivered files and worker process files. Write your review only to:
- .codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md
- .codex-workflows/core-narrative-experiment/workers/wave0-r3-reviewer/process.md

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Update your process.md at start, after meaningful phases, and before exit. Mark status: delivered only when the review is complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.

Do not inspect any `cli.log` file.

Prior reviews:
- /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-review.md
- /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md

Revision deliveries to inspect:
- schema-toolsmith revision 2 and 3: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith at commits `de7a126`, `c7a01b2`, and `34b0677`
- acut-matrix revision: /Users/chenmohan/gits/barcarolle-wt-acut-matrix at commit `583600c`
- coordinator LLM budget artifacts: `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/llm_access.yaml`, `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/results/cost_ledger.jsonl`, and `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`

Task:
1. Read the plan, coordinator.md, worker contract, LLM access/budget contract, prior reviews, and the relevant worker process.md files.
2. Inspect the revised schema/tool artifacts, ACUT manifests, and coordinator LLM budget artifacts. Do not inspect any `cli.log`.
3. Verify whether these gates are closed:
   - ACUT schema/manifest validator passes the seven manifests;
   - clean-room workspace leakage fix still appears intact;
   - W-score mergeability-grade numeric rubric support remains intact;
   - LLM access uses only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`;
   - credential values and resolved secrets are not written to Git/process/log/result/report artifacts by the new tooling;
   - missing env vars, missing/unwritable ledger, hard-cap overflow, and soft-stop approval are enforced before ACUT command execution;
   - cost ledger append records tokens, estimated/actual cost, and cumulative estimated cost;
   - default execution profile remains the four core ACUTs, 6 `G_score`, 8 `RBench`, 6 `RWork`, one primary attempt each.
4. Check for obvious regressions that would block integrating the revised branches as Wave 0 scaffold work.
5. Write `.codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md` in this format:

```markdown
# Wave 0 Revision 3 Review

status: no_issues | issues_found | blocked

## Summary
...

## Findings
1. ...

## Integration Recommendation
...

## Required Closure
...
```

6. Self-check that your review file exists and process.md is current.
7. Commit only your review/process changes on `codex/core-exp-wave0-r3-reviewer`. Do not push.
