# Review Feedback 1

source_review: `.codex-workflows/core-narrative-experiment/reviews/acut-2x2-patch-command-review.md`
review_status: `issues_found`
updated: 2026-04-29T11:42:00+08:00

## Required Closure

Refresh the patch-command delivery against the reviewed 2x2 ACUT redesign before
execution-start promotion.

- Replace executable command templates and current handoff text that reference
  retired ACUT IDs with an active 2x2 ACUT manifest:
  `frontier-generic-swe`, `frontier-click-specialist`,
  `cheap-generic-swe`, or `cheap-click-specialist`.
- Rerun only no-model adapter dry-run/mock evidence through the post-redesign
  `acut_patch_adapter.py`, `barcarolle_patch_command.py`, and
  `_llm_budget.py` so structured evidence records active 2x2 ACUT IDs and the
  28-attempt pilot profile.
- Keep retired ACUT IDs only as historical redesign notes, not as executable
  templates, current smoke evidence, default core IDs, or new-execution ACUT
  references.

## Standing Constraints

- Do not inspect any `cli.log` file.
- Do not start broad ACUT execution.
- Do not run live ACUT model calls or live patch-generation attempts.
- Do not record credential values, bearer tokens, resolved secrets, or full base
  URL values.
- The patch-generation command must remain a custom BARCAROLLE-env-only command
  wrapped by `experiments/core_narrative/tools/acut_patch_adapter.py`.
