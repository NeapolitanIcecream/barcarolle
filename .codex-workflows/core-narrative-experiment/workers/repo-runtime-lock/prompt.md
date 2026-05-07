# Repo Runtime Lock Prompt

You are the repo-runtime-lock worker for the Barcarolle core narrative experiment.

Repo path: `/Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock`
Branch: `codex/core-exp-repo-runtime-lock`

Do not inspect any `cli.log` file. Do not make ACUT model calls. Do not write credential values, bearer tokens, resolved secrets, or full base URL values into Git, process files, logs, reports, or results.

## Read First

- `.codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle-wt-repo-scout/.codex-workflows/core-narrative-experiment/workers/repo-scout/process.md`

Then inspect only the repository/config/report files needed to close this lock.

## Task

Close the `repo-scout` pre-run gate:

- Primary target is `pallets/click` unless local runtime evidence proves it is not viable.
- Clone the target under `experiments/core_narrative/external_repos/` or another ignored local probe path.
- Record the target repository commit, Python/runtime version, install command, smoke command, full-suite or representative command, elapsed times, and whether the repository is viable for the revised default `RBench`/`RWork` slice.
- The revised default needs only 8 `RBench` tasks and 6 `RWork` tasks, one primary attempt each, under the budget-constrained four-core-ACUT execution profile.
- If `pallets/click` is not locally viable, evaluate the existing fallbacks from the repo-scout handoff in order and lock one fallback with the same evidence.

## Output Requirements

Update:

- `experiments/core_narrative/configs/target_repositories.yaml`
- `experiments/core_narrative/reports/repo_scout_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/repo-runtime-lock/process.md`

Do not edit LLM access config or the cost ledger. Do not start broad ACUT execution.

## Process And Delivery

Update `process.md` before meaningful phases and at delivery. At the end, set:

- `status: delivered` if the pre-run repo lock is closed.
- `status: blocked` if local runtime cannot be verified or no fallback can be selected.

Commit only owned tracked changes. Leave ignored local clones and caches unstaged. Do not push.
