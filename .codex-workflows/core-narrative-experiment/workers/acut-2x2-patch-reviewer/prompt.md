# ACUT 2x2 And Patch Command Focused Review

You are the focused reviewer for the Barcarolle core narrative experiment pre-execution redesign and patch command contract.

Repository context:

- Reviewer worktree: `/Users/chenmohan/gits/barcarolle-wt-acut-2x2-patch-reviewer`
- Coordinator repo: `/Users/chenmohan/gits/barcarolle`
- Coordinator branch: `codex/core-narrative-experiment`
- Redesign commit on coordinator branch: `9409244`
- Patch command worker worktree: `/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`
- Patch command worker branch: `codex/core-exp-patch-command-contract`
- Patch command worker delivered commit: `db68a50`

Hard workflow constraints:

- Do not inspect any `cli.log` file.
- Do not edit production experiment artifacts, manifests, tools, configs, raw results, normalized results, or reports.
- Do not start broad ACUT execution.
- Do not start live ACUT model calls or live patch-generation attempts.
- Do not run execution-start preflight.
- Do not write credential values, bearer tokens, resolved secrets, or full base URL values anywhere.

Owned output paths:

- `.codex-workflows/core-narrative-experiment/reviews/acut-2x2-patch-command-review.md`
- `.codex-workflows/core-narrative-experiment/workers/acut-2x2-patch-reviewer/process.md`

Review scope:

1. Review the 2x2 ACUT redesign on the coordinator branch:
   - active ACUTs are exactly `frontier-generic-swe`, `frontier-click-specialist`, `cheap-generic-swe`, and `cheap-click-specialist`;
   - old active ACUTs are retired for new execution;
   - deferred ACUTs remain `higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline`;
   - all four active ACUTs share harness, task budget, turn cap, test cap, retry policy, network policy, and one-primary-attempt policy;
   - within each model tier, generic vs Click-specialist changes only policy/context specialization;
   - Click-specialist policy allows only pre-generated, task-agnostic, reproducible Click repo/docs/symbol/convention/deterministic retrieval context;
   - RBench/RWork gold patches, hidden human hints, post-hoc tuning, and undeclared history mining remain forbidden.
2. Review the pilot execution manifest:
   - default pilot is 4 ACUT x (2 G_score + 3 RBench + 2 RWork) = 28 primary attempts;
   - budget-tight fallback is exactly `frontier-generic-swe`, `frontier-click-specialist`, and `cheap-click-specialist`;
   - full core subset is not allowed until pilot review and explicit coordinator promotion.
3. Review related gate/profile updates:
   - `experiments/core_narrative/configs/llm_access.yaml`;
   - `experiments/core_narrative/tools/_llm_budget.py`;
   - `.codex-workflows/core-narrative-experiment/shared/llm-access-budget-contract.md`;
   - `.codex-workflows/core-narrative-experiment/coordinator.md`;
   - `.codex-workflows/core-narrative-experiment/workers/acut-2x2-redesign/process.md`.
4. Review the delivered patch command worker commit `db68a50`:
   - it implements a custom BARCAROLLE-env-only patch-generation command path;
   - it is usable behind `experiments/core_narrative/tools/acut_patch_adapter.py`;
   - it uses only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL` for LLM access;
   - it does not accept/persist credential values, bearer tokens, resolved secrets, or full base URL values;
   - no-model smoke coverage is sufficient;
   - it does not use bare `codex exec` as the ACUT patch-generation command;
   - its command template and ACUT references are compatible with the new 2x2 active ACUT IDs.

Allowed verification:

- Read files in the coordinator repo and delivered patch command worktree except `cli.log`.
- Inspect Git metadata, changed-file lists, and process files.
- Run static/no-model checks such as YAML parse, `validate_acut_manifest.py`, `py_compile`, `git diff --check`, JSON parsing, and safe artifact scans.
- Do not run any live endpoint call.

Deliverable format:

Write `.codex-workflows/core-narrative-experiment/reviews/acut-2x2-patch-command-review.md`:

```markdown
# ACUT 2x2 And Patch Command Review

status: no_issues | issues_found | blocked
reviewed_redesign_commit: 9409244
reviewed_patch_command_commit: db68a50
updated: <Asia/Shanghai timestamp>

## Summary
...

## Findings
1. ...

## Required Closure
...

## Checks Run
- ...
```

If there are no findings, write `None.` under Findings and Required Closure.

Update `.codex-workflows/core-narrative-experiment/workers/acut-2x2-patch-reviewer/process.md` before and after review. When complete, set `status: delivered`, include findings count, changed/inspected files, checks run, and handoff. Commit only your owned output paths on branch `codex/core-exp-acut-2x2-patch-reviewer`.
