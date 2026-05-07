# Patch Command Contract Revision 1 Focused Review

You are the focused reviewer for the Barcarolle core narrative experiment
patch-generation command contract revision.

Reviewer worktree:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer`

Coordinator repo:

`/Users/chenmohan/gits/barcarolle`

Patch-command worker worktree:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

Patch-command worker branch:

`codex/core-exp-patch-command-contract`

Patch-command revision commit:

`870d5f5`

Previous focused review:

- Reviewer process: `/Users/chenmohan/gits/barcarolle-wt-acut-2x2-patch-reviewer/.codex-workflows/core-narrative-experiment/workers/acut-2x2-patch-reviewer/process.md`
- Review artifact: `/Users/chenmohan/gits/barcarolle-wt-acut-2x2-patch-reviewer/.codex-workflows/core-narrative-experiment/reviews/acut-2x2-patch-command-review.md`

## Hard Constraints

- Do not inspect any `cli.log` file.
- Do not edit production experiment artifacts, manifests, tools, configs, raw
  results, normalized results, or reports.
- Do not start broad ACUT execution.
- Do not start live ACUT model calls or live patch-generation attempts.
- Do not run execution-start preflight.
- Do not write credential values, bearer tokens, resolved secrets, or full base
  URL values anywhere.
- Do not use or approve bare `codex exec` as the ACUT patch-generation command.

## Owned Output Paths

- `.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-r1-reviewer/process.md`

## Review Scope

Review only the closure of the prior finding and the related command contract:

1. Confirm the executable adapter command template now uses an active 2x2 ACUT
   manifest, not a retired ACUT ID.
2. Confirm refreshed no-model adapter dry-run/mock evidence records an active
   2x2 ACUT ID and the 28-attempt pilot profile:
   - active ACUTs: `frontier-generic-swe`, `frontier-click-specialist`,
     `cheap-generic-swe`, `cheap-click-specialist`;
   - tasks: 2 `G_score`, 3 `RBench`, 2 `RWork`;
   - one primary attempt per ACUT/task.
3. Confirm retired ACUT IDs are not used in executable templates, current smoke
   evidence, default core IDs, or new-execution ACUT references. Historical
   references inside review feedback/revision prompts are acceptable if clearly
   historical.
4. Confirm `barcarolle_patch_command.py` remains a custom BARCAROLLE-env-only
   patch-generation command usable only behind
   `experiments/core_narrative/tools/acut_patch_adapter.py`.
5. Confirm live LLM access uses only `BARCAROLLE_LLM_API_KEY` and
   `BARCAROLLE_LLM_BASE_URL`, with no credential values, bearer tokens, resolved
   secrets, or full base URL values persisted in report/results/process files.
6. Confirm no broad ACUT execution, execution-start preflight, live model calls,
   or live patch-generation attempts were started.

You may rely on the previous focused review's conclusion that the 2x2 redesign
static/control design passed, but verify any 2x2 facts needed to assess this
patch-command revision.

## Allowed Verification

- Read files in the coordinator repo, patch-command worktree, and previous
  reviewer worktree except any `cli.log`.
- Inspect Git metadata, changed-file lists, and process files.
- Run static/no-model checks such as YAML parse, `validate_acut_manifest.py`,
  `py_compile`, `git diff --check`, JSON parsing, and safe artifact scans.
- Do not run any live endpoint call.

## Deliverable

Write `.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`:

```markdown
# Patch Command Contract Revision 1 Review

status: no_issues | issues_found | blocked
reviewed_patch_command_revision_commit: 870d5f5
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

Update `.codex-workflows/core-narrative-experiment/workers/patch-command-r1-reviewer/process.md`
before and after review. When complete, set `status: delivered`, include
findings count, changed/inspected files, checks run, and handoff. Commit only
your owned output paths on branch `codex/core-exp-patch-command-r1-reviewer`.
