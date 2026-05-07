# Review Feedback 2

source_review: `/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer/.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`
review_status: `issues_found`
updated: 2026-04-29T12:08:00+08:00

## Required Closure

The patch-command revision 1 artifacts closed the prior retired-ID issue for
`patch_command_contract*` evidence, but focused re-review found one remaining
related command-contract issue: the older `acut_adapter_smoke*` report/results
are still presented as current smoke evidence and still record retired ACUT IDs
and the retired default execution profile.

Refresh or clearly supersede the pre-redesign `acut_adapter_smoke*` report and
result artifacts so current smoke evidence no longer advertises retired ACUT IDs
or the retired `budget-constrained-core-v1` default profile.

Historical references can remain only if explicitly labeled historical or
superseded and not used as executable templates, current smoke evidence, default
core IDs, or new-execution ACUT references.

## Standing Constraints

- Do not inspect any `cli.log` file.
- Do not start broad ACUT execution.
- Do not run execution-start preflight.
- Do not run live ACUT model calls or live patch-generation attempts.
- Do not record credential values, bearer tokens, resolved secrets, or full base
  URL values.
- Keep any adapter or command probes no-model-call only.
