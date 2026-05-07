# Empty Patch Gate Revision 1

You are the focused revision worker for the Barcarolle core narrative
experiment empty-patch adapter gate.

Worker repository: `/Users/chenmohan/gits/barcarolle-wt-empty-patch-gate-r1`

Read first:

1. `.codex-workflows/core-narrative-experiment/coordinator.md`
2. `.codex-workflows/core-narrative-experiment/reviews/empty-patch-gate-review.md`
3. `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-r1/process.md`
4. `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-reviewer/process.md`
5. `.codex-workflows/core-narrative-experiment/workers/pilot-004-execution/process.md`

Do not inspect any `cli.log` file in any worktree. Do not start any ACUT
attempt, retry, second attempt, additional specialist ACUT run, broad execution,
live BARCAROLLE model call, or large model-call batch.

## Revision Scope

Fix the issue found by the focused review:

- A true empty-patch classification should apply only when the inner command
  exits `0`, does not time out, does not trigger unsafe patch rejection, and the
  resulting patch/git diff is empty.
- Unsafe patch rejection must remain a distinct outcome. It must not record
  adapter or ledger metadata as `no_patch_generated: true`, and it must not use
  the empty-patch normalized message.
- Normalized empty-patch output should be guarded by the final adapter status
  being `no_patch_generated`, not only by the raw patch artifact size.

Keep the existing valid behavior:

- Exit-0 empty diff: adapter status and ledger event `no_patch_generated`,
  normalized status `infra_failed`, no verifier-ready/scorable result.
- Exit-0 non-empty safe diff: `command_completed`.
- Non-zero command failure: `command_failed`.
- Timeout: `timeout`.
- Unsafe patch rejection: `unsafe_patch_rejected` /
  `command_completed_unsafe_patch_rejected`.

## Owned Paths

Edit only:

- `experiments/core_narrative/tools/acut_patch_adapter.py`
- `experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `experiments/core_narrative/reports/acut_adapter_empty_patch_gate.md`
- `.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-r1/process.md`

## Required Checks

Run no-model/static checks only:

- `python3 experiments/core_narrative/tools/test_acut_patch_adapter.py`
- `python3 -m py_compile experiments/core_narrative/tools/acut_patch_adapter.py experiments/core_narrative/tools/test_acut_patch_adapter.py`
- A scoped no-secret scan over changed files, excluding any `cli.log`
- `git diff --check`

Add a no-model regression for unsafe patch rejection that asserts the adapter
status/event remain unsafe-specific and adapter/ledger metadata do not mark
`no_patch_generated: true`.

## Output

Update
`.codex-workflows/core-narrative-experiment/workers/empty-patch-gate-r1/process.md`
with:

- `status: delivered`, `status: blocked`, or `status: working`
- summary
- changed files
- checks run
- handoff

If delivered, include the worker commit hash. If blocked, state whether user
input is required. Do not include secrets, full base URLs, hostnames, IP
addresses, or bearer tokens.
