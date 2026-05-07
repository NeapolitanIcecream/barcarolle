# Empty Patch Gate Review

You are the focused reviewer for the Barcarolle core narrative experiment
post-pilot-004 adapter hardening.

Reviewer repository:
`/Users/chenmohan/gits/barcarolle-wt-empty-patch-gate-reviewer`

Implementation commit under review: `1504e5e`

Read first:

1. `.codex-workflows/core-narrative-experiment/coordinator.md`
2. `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/process.md`
3. `.codex-workflows/core-narrative-experiment/workers/pilot-004-execution/process.md`
4. `.codex-workflows/core-narrative-experiment/workers/pilot-004-reviewer/process.md`

Do not inspect any `cli.log` file in any worktree. Do not start any ACUT
attempt, retry, second attempt, additional specialist ACUT run, broad execution,
live BARCAROLLE model call, or large model-call batch.

## Review Scope

Review only the empty-patch harness hardening and its no-model smoke:

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_empty_patch_gate.md`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- `.codex-workflows/core-narrative-experiment/coordinator.md`

Write only:

- `.codex-workflows/core-narrative-experiment/reviews/empty-patch-gate-review.md`
- `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/process.md`

## What To Check

1. If the inner patch-generation command exits `0` but the resulting patch/git
   diff is empty, `acut_patch_adapter.py` records adapter status and ledger event
   `no_patch_generated`, not `command_completed`.
2. The same empty-patch condition writes normalized status `infra_failed` and
   does not create a verifier-ready/scorable result.
3. Non-empty successful patches can still be classified as `command_completed`.
4. Timeout, unsafe patch rejection, and non-zero command failure paths remain
   behaviorally distinct.
5. The regression/no-model smoke exercises an exit-0 empty-diff command and
   asserts the adapter status, ledger event, patch size, and normalized
   `infra_failed` result.
6. No live BARCAROLLE model call, ACUT attempt, retry, second attempt,
   additional specialist run, broad execution, or large batch was started by
   the hardening or by this review.
7. Artifacts and workflow files do not record credential values, bearer tokens,
   resolved secrets, full base URLs, hostnames, or IP addresses. Exclude
   `cli.log` from all scans and do not inspect it.

You may run no-model tests and static checks only. Do not run any command that
would contact BARCAROLLE or start an ACUT attempt.

## Output

Write `.codex-workflows/core-narrative-experiment/reviews/empty-patch-gate-review.md`:

```markdown
# Empty Patch Gate Review

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
`.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/process.md`
with `status: no_issues`, `status: issues_found`, or `status: blocked`, a
short summary, checks run, and handoff. If you find no issues, say explicitly
that the coordinator may integrate the review artifact before deciding any next
bounded pilot step.
