# Patch Command Contract Revision 2 Focused Review

You are the focused reviewer for the Barcarolle core narrative experiment
patch-generation command contract revision 2.

Reviewer worktree:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-r2-reviewer`

Coordinator repo:

`/Users/chenmohan/gits/barcarolle`

Patch-command worker worktree:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

Patch-command worker branch:

`codex/core-exp-patch-command-contract`

Patch-command revision 2 commit:

`0d27f26`

Prior re-review:

- Reviewer process: `/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer/.codex-workflows/core-narrative-experiment/workers/patch-command-r1-reviewer/process.md`
- Review artifact: `/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer/.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`

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

- `.codex-workflows/core-narrative-experiment/reviews/patch-command-r2-review.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-r2-reviewer/process.md`

## Review Scope

Review closure of the prior finding and the nearby command contract:

1. Confirm current `acut_adapter_smoke*` report/results no longer advertise
   retired ACUT IDs or the retired `budget-constrained-core-v1` profile as
   current smoke evidence.
2. Confirm current adapter smoke evidence uses an active 2x2 ACUT ID,
   preferably `cheap-click-specialist`, and records:
   - active ACUTs: `frontier-generic-swe`, `frontier-click-specialist`,
     `cheap-generic-swe`, `cheap-click-specialist`;
   - profile `budget-constrained-2x2-pilot-v2`;
   - tasks: 2 `G_score`, 3 `RBench`, 2 `RWork`;
   - one primary attempt per ACUT/task;
   - 28 pilot primary attempts.
3. Confirm any retired ACUT IDs that remain are clearly historical/superseded
   and are not used as executable templates, current smoke evidence, default
   core IDs, or new-execution ACUT references.
4. Confirm patch-command revision 1's clean state remains intact:
   `patch_command_contract*` evidence uses active 2x2 IDs and the executable
   adapter template routes through `acut_patch_adapter.py` with the custom
   `barcarolle_patch_command.py`.
5. Confirm the command path remains BARCAROLLE-env-only for live LLM access:
   only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`.
6. Confirm no credential values, bearer tokens, resolved secrets, or full base
   URL values are persisted in report/results/process artifacts.
7. Confirm no broad ACUT execution, execution-start preflight, live model calls,
   or live patch-generation attempts were started.

You may rely on previous focused reviews for issues outside this closure scope,
but verify any facts needed to decide whether execution-start preflight may be
unblocked after integration.

## Allowed Verification

- Read files in the coordinator repo, patch-command worktree, previous reviewer
  worktree, and this reviewer worktree except any `cli.log`.
- Inspect Git metadata, changed-file lists, and process files.
- Run static/no-model checks such as YAML parse, `validate_acut_manifest.py`,
  `py_compile`, `git diff --check`, JSON parsing, JSONL parsing, retired-ID
  scans, and credential/full-URL scans.
- Do not run any live endpoint call.

## Deliverable

Write `.codex-workflows/core-narrative-experiment/reviews/patch-command-r2-review.md`:

```markdown
# Patch Command Contract Revision 2 Review

status: no_issues | issues_found | blocked
reviewed_patch_command_revision_commit: 0d27f26
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

Update `.codex-workflows/core-narrative-experiment/workers/patch-command-r2-reviewer/process.md`
before and after review. When complete, set `status: delivered`, include
findings count, changed/inspected files, checks run, and handoff. Commit only
your owned output paths on branch `codex/core-exp-patch-command-r2-reviewer`.
