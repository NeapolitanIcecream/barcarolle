# Nonzero-Exit Normalization Review

You are the focused no-model/static reviewer for the Barcarolle core narrative
experiment `nonzero-exit-normalization` harness repair.

Reviewer repository:
`/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization-reviewer`

Delivered worker worktree under review:
`/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization`

Implementation commit under review: `4b26c7a`

## Coordination Contract

Read first:

1. `.codex-workflows/core-narrative-experiment/coordinator.md` in this reviewer
   repository.
2. `/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization/.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/process.md`
3. `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization-reviewer/process.md`
4. `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-r1-reviewer/process.md`
5. `.codex-workflows/core-narrative-experiment/workers/codex-cli-failure-capture-r1-reviewer/process.md`
6. `.codex-workflows/core-narrative-experiment/workers/pilot-006-reviewer/process.md`

Do not inspect any `cli.log` file in any worktree. Do not start any ACUT
attempt, retry, second attempt, additional specialist ACUT run, broad
execution, live BARCAROLLE model call, further pilot attempt, or large
model-call batch.

Never record credential values, bearer tokens, resolved secrets, hostnames, IP
addresses, or full base URL values.

## Review Scope

Review only the delivered worker owned paths in
`/Users/chenmohan/gits/barcarolle-wt-nonzero-exit-normalization`:

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_nonzero_exit_normalization.md`
- `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization/process.md`

Write only these files in this reviewer repository:

- `.codex-workflows/core-narrative-experiment/reviews/nonzero-exit-normalization-review.md`
- `.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization-reviewer/process.md`

## What To Check

1. Non-timeout nonzero inner-command failures with no verifier-ready patch
   produce normalized `infra_failed` output.
2. The raw adapter status and cost-ledger event remain `command_failed`; the
   repair must not reclassify this path as `no_patch_generated`.
3. Exit-0 empty diff remains `no_patch_generated`; unsafe patch rejection and
   timeout remain distinct.
4. Existing successful verifier-eligible patch behavior remains intact.
5. Regression tests cover the nonzero-exit/no-patch path and preserve the
   empty-diff and unsafe-patch distinctions.
6. The repair did not modify pilot 004/005/006 artifacts or append to
   `experiments/core_narrative/results/cost_ledger.jsonl`.
7. Scoped artifacts and process files do not contain credential values, bearer
   tokens, resolved secrets, full base URLs, hostnames, or IP addresses. Exclude
   `cli.log` from all scans and do not inspect it.

You may run no-model tests and static checks only. Do not run any command that
would contact BARCAROLLE or start an ACUT attempt.

## Output

Write `.codex-workflows/core-narrative-experiment/reviews/nonzero-exit-normalization-review.md`:

```markdown
# Nonzero-Exit Normalization Review

status: no_issues | issues_found | blocked

## Summary
...

## Findings
...

## Evidence
...

## Required Closure
...
```

Update
`.codex-workflows/core-narrative-experiment/workers/nonzero-exit-normalization-reviewer/process.md`
with `status: no_issues`, `status: issues_found`, or `status: blocked`, a
short summary, checks run, and handoff. If you find no issues, say explicitly
that the coordinator may integrate the repair and review artifact before
deciding any later bounded execution hypothesis.
