# General Benchmark Lock Prompt

You are the general-benchmark-lock worker for the Barcarolle core narrative experiment.

Repo path: `/Users/chenmohan/gits/barcarolle-wt-general-lock`
Branch: `codex/core-exp-general-lock`

Do not inspect any `cli.log` file. Do not make ACUT model calls. Do not write credential values, bearer tokens, resolved secrets, or full base URL values into Git, process files, logs, reports, or results.

## Read First

- `.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`
- `/Users/chenmohan/gits/barcarolle/.codex-workflows/core-narrative-experiment/coordinator.md`
- `/Users/chenmohan/gits/barcarolle-wt-general-benchmark/.codex-workflows/core-narrative-experiment/workers/general-benchmark/process.md`

Then inspect only the repository/config/report files needed to close this lock.

## Task

Close the `general-benchmark` pre-run gate by materializing concrete `G_score` task IDs for the revised default:

- 6 `G_score` tasks.
- One primary attempt per ACUT/task.
- No broad ACUT execution.
- No model calls.

Use the already delivered general benchmark basis as the authority unless it is internally inconsistent. Materialize the exact SWE-Bench Pro Public instance IDs, dataset snapshot/revision, data hash or equivalent reproducibility proof, evaluator revision, and any replacement needed if the originally proposed infrastructure is unavailable.

If the dataset or infrastructure cannot be accessed, set `status: blocked` in `process.md` and record the exact blocker and the smallest next action needed to close it. Do not invent IDs.

## Output Requirements

Update:

- `experiments/core_narrative/configs/general_benchmark.yaml`
- `experiments/core_narrative/reports/general_benchmark_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/general-benchmark-lock/process.md`

Do not edit LLM access config or the cost ledger. Do not start broad ACUT execution.

## Process And Delivery

Update `process.md` before meaningful phases and at delivery. At the end, set:

- `status: delivered` if the concrete six-task `G_score` lock is closed.
- `status: blocked` if materialization cannot be completed.

Commit only owned tracked changes. Leave caches unstaged. Do not push.
