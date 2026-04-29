# Patch Command Contract Revision 1

You are the focused revision worker for the Barcarolle core narrative
experiment. Work in:

`/Users/chenmohan/gits/barcarolle-wt-patch-command-contract`

Branch:

`codex/core-exp-patch-command-contract`

## Context

The prior patch-command delivery commit `db68a50` implemented
`experiments/core_narrative/tools/barcarolle_patch_command.py`, and the
reviewer found that the command implementation appears custom and
BARCAROLLE-env-only. The active ACUT design changed after that delivery to the
2x2 pilot:

- `frontier-generic-swe`
- `frontier-click-specialist`
- `cheap-generic-swe`
- `cheap-click-specialist`

The old active IDs are retired for new execution:

- `general-benchmark-optimized`
- `repo-context-heavy`
- `retrieval-sparse-symbolic`
- `lower-budget-fast-path`

The focused reviewer delivered `issues_found` because the patch-command report,
handoff template, and no-model adapter evidence still target retired ACUT IDs.

## Inputs To Read

Read these files first:

- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/review-feedback-1.md`
- `.codex-workflows/core-narrative-experiment/coordinator.md`
- `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
- `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- active ACUT manifests under `experiments/core_narrative/configs/acuts/`

Do not read any `cli.log` file.

## Task

Close the review finding without starting execution:

1. Update patch-command report and process handoff templates so the executable
   adapter command uses an active 2x2 ACUT manifest. Prefer
   `cheap-click-specialist` for the no-model mock probe unless the existing
   test fixture makes another active 2x2 manifest cleaner.
2. Refresh no-model adapter dry-run/mock probe evidence through the integrated
   post-redesign `experiments/core_narrative/tools/acut_patch_adapter.py` and
   `experiments/core_narrative/tools/barcarolle_patch_command.py`.
3. Ensure structured evidence records an active 2x2 ACUT ID and the 28-attempt
   pilot profile from `experiments/core_narrative/configs/core_subset_run_manifest.yaml`.
4. Keep retired ACUT IDs only in historical redesign notes or explicit
   historical review context. They must not appear in executable templates,
   current smoke evidence, default core IDs, or new-execution ACUT references.
5. Re-run relevant no-model checks and artifact scans. Do not make live model
   calls.
6. Update `.codex-workflows/core-narrative-experiment/workers/patch-command-contract/process.md`
   with status, checks, changed files, and handoff. Set `status: delivered` only
   when done.
7. Commit only your owned paths.

## Constraints

- Do not start broad ACUT execution, execution-start preflight, live ACUT model
  calls, or live patch-generation attempts.
- Never record credential values, bearer tokens, resolved secrets, or full base
  URL values.
- The custom command must use only `BARCAROLLE_LLM_API_KEY` and
  `BARCAROLLE_LLM_BASE_URL` for live LLM access.
- The command must remain wrapped by `experiments/core_narrative/tools/acut_patch_adapter.py`
  so env, budget, ledger, and redaction gates stay in force.
- Do not use bare `codex exec` as the ACUT patch-generation command.
- Do not inspect any `cli.log` files.

## Expected Output

- Updated patch-command report/process handoff and refreshed no-model evidence.
- Passing no-model checks recorded in `process.md`.
- A commit on `codex/core-exp-patch-command-contract`.
