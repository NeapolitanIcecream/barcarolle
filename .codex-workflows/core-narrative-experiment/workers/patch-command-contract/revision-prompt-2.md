# Patch Command Contract Revision 2

You are the focused revision worker for the Barcarolle core narrative
experiment. Work in:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

Branch:

`codex/core-exp-patch-command-contract`

## Context

Revision 1 commit `870d5f5` refreshed the patch-command report/templates and
`patch_command_contract*` no-model evidence against the active 2x2 pilot using
`cheap-click-specialist`. Focused re-review commit `e5c7db1` found one remaining
related issue: older `acut_adapter_smoke*` report/results are still presented as
current smoke evidence and still record retired ACUT IDs/default profile values.

## Inputs To Read

Read these files first:

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-2.md`
- `/Users/chenmohan/gits/barcarolle-wt-patch-command-r1-reviewer/.codex-workflows/core-narrative-experiment/reviews/patch-command-r1-review.md`
- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- active ACUT manifests under `experiments/core_narrative/configs/acuts/`

Do not read any `cli.log` file.

## Task

Close the remaining review finding without starting execution:

1. Refresh or clearly supersede the pre-redesign `acut_adapter_smoke*`
   report/results so current smoke evidence no longer advertises retired ACUT
   IDs or the retired `budget-constrained-core-v1` default profile.
2. If refreshing evidence, use only no-model adapter/command probes and an
   active 2x2 ACUT manifest such as `cheap-click-specialist`.
3. Ensure current adapter smoke evidence records the active 2x2 core IDs,
   profile `budget-constrained-2x2-pilot-v2`, 2 `G_score` / 3 `RBench` /
   2 `RWork`, one primary attempt per ACUT/task, and 28 pilot primary attempts.
4. Historical retired-ID references may remain only when explicitly labeled as
   historical or superseded and not used as executable templates, current smoke
   evidence, default core IDs, or new-execution ACUT references.
5. Re-run relevant no-model checks, JSON/JSONL parses, retired-ID scans, and
   credential/full-URL scans.
6. Update `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
   with status, checks, changed files, and handoff. Set `status: delivered` only
   when done.
7. Commit only your owned paths.

## Owned Paths For This Revision

- `experiments/core_narrative/reports/acut_adapter_smoke.md`
- `experiments/core_narrative/results/normalized/acut_adapter_smoke*.json`
- `experiments/core_narrative/results/raw/acut_adapter_smoke*/**`
- existing patch-command report/results if needed to cross-reference the
  supersession cleanly
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/**`

## Constraints

- Do not start broad ACUT execution, execution-start preflight, live ACUT model
  calls, or live patch-generation attempts.
- Never record credential values, bearer tokens, resolved secrets, or full base
  URL values.
- Any command path used for probe evidence must remain behind
  `experiments/core_narrative/tools/acut_patch_adapter.py`.
- Do not use bare `codex exec` as an ACUT patch-generation command.
- Do not inspect any `cli.log` files.

## Expected Output

- Current adapter smoke report/results refreshed or explicitly superseded for
  the active 2x2 pilot.
- Passing no-model checks recorded in `process.md`.
- A commit on `codex/core-exp-patch-command-contract`.
