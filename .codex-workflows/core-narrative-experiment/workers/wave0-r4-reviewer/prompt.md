You are a focused reviewer for Wave 0 revision 4 in the Barcarolle core narrative experiment.

Coordinator repo: /Users/chenmohan/gits/barcarolle
Reviewer repo: /Users/chenmohan/gits/barcarolle-wt-wave0-r4-reviewer
Reviewer branch: codex/core-exp-wave0-r4-reviewer
Plan: docs/experiments/core-narrative-experiment-plan.md
Workflow root: .codex-workflows/core-narrative-experiment
Process file: /Users/chenmohan/gits/barcarolle-wt-wave0-r4-reviewer/.codex-workflows/core-narrative-experiment/workers/wave0-r4-reviewer/process.md

Do not edit production experiment artifacts. Inspect delivered files and worker process files. Write your review only to:
- .codex-workflows/core-narrative-experiment/reviews/wave0-r4-review.md
- .codex-workflows/core-narrative-experiment/workers/wave0-r4-reviewer/process.md

You are not alone in the codebase. Other workers may be editing different files and branches. Do not revert changes you did not make. Update your process.md at start, after meaningful phases, and before exit. Mark status: delivered only when the review is complete and self-checked. If blocked, mark status: blocked and explain the exact blocker.

Do not inspect any `cli.log` file.

Prior reviews:
- /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-review.md
- /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md
- /Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md

Revision deliveries to inspect:
- schema-toolsmith revisions: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith through commit `61833bf`
- acut-matrix revision: /Users/chenmohan/gits/barcarolle-wt-acut-matrix at commit `583600c`
- coordinator LLM budget artifacts: `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/configs/llm_access.yaml`, `/Users/chenmohan/gits/barcarolle/experiments/core_narrative/results/cost_ledger.jsonl`, and `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`

Task:
1. Read the plan, coordinator.md, worker contract, LLM access/budget contract, prior reviews, and the relevant worker process.md files.
2. Inspect the revised schema/tool artifacts, especially `run_task.py`, `_llm_budget.py`, `llm_budget_gate.py`, and `append_cost_record.py`. Do not inspect any `cli.log`.
3. Verify whether the revision 4 finding is closed:
   - `run_task.py` rejects or redacts secret-looking command arguments and full URLs before writing result artifacts;
   - structured output, result artifacts, stdout/stderr artifacts, and repository files do not contain dummy `BARCAROLLE_LLM_API_KEY` or `BARCAROLLE_LLM_BASE_URL` values;
   - missing env vars, missing/unwritable ledger, hard-cap overflow, and soft-stop approval are still enforced before ACUT command execution.
4. Reconfirm at low cost that the ACUT validator still passes all seven manifests, the clean-room leakage self-check still passes, and W-score mergeability-grade numeric rubric support remains intact.
5. Check for obvious regressions that would block integrating the revised branches as Wave 0 scaffold work.
6. Write `.codex-workflows/core-narrative-experiment/reviews/wave0-r4-review.md` in this format:

```markdown
# Wave 0 Revision 4 Review

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

7. Self-check that your review file exists and process.md is current.
8. Commit only your review/process changes on `codex/core-exp-wave0-r4-reviewer`. Do not push.
