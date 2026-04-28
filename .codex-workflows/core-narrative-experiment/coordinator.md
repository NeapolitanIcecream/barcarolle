# Core Narrative Experiment Coordinator

status: execution_ready_stop_policy_defer
updated: 2026-04-28T16:18:03+08:00
today_stop_state: pre_soft_stop_active
phase: Phase 0 - Experiment Bootstrap
base_commit: 47046e7754d2402b7177a4b80f631ab6b0bcd97c
coordinator_repo: /Users/chenmohan/gits/barcarolle
coordinator_branch: codex/core-narrative-experiment

## Objective

Execute `docs/experiments/core-narrative-experiment-plan.md` with tmux-managed Codex CLI workers. Coordinate through this file and worker `process.md` files only. Do not inspect `cli.log` files unless debugging is explicitly requested.

## Worker Status

| Worker | Phase | Status | Session | Branch | Worktree | Owned Paths |
| --- | --- | --- | --- | --- | --- | --- |
| repo-scout | Wave 0 | delivered; worker commit `9b5dbbe`, integrated as `dc58f8d` | exited | codex/core-exp-repo-scout | /Users/chenmohan/gits/barcarolle-wt-repo-scout | `experiments/core_narrative/configs/target_repositories.yaml`, `experiments/core_narrative/reports/repo_scout_notes.md` |
| schema-toolsmith | Wave 0 | delivered; worker commit `a9824ba`, integrated as `d337c78` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| acut-matrix | Wave 0 | delivered; worker commit `dcbdc1e`, integrated as `512be8a` | exited | codex/core-exp-acut-matrix | /Users/chenmohan/gits/barcarolle-wt-acut-matrix | `experiments/core_narrative/configs/acuts/**`, `experiments/core_narrative/reports/acut_matrix_notes.md` |
| general-benchmark | Wave 0 | delivered; worker commit `54a07ae`, integrated as `7215d3e` | exited | codex/core-exp-general-benchmark | /Users/chenmohan/gits/barcarolle-wt-general-benchmark | `experiments/core_narrative/configs/general_benchmark.yaml`, `experiments/core_narrative/reports/general_benchmark_notes.md` |
| wave0-reviewer | Wave 0 review | delivered; issues_found; commit `a2aef12` integrated | exited | codex/core-exp-wave0-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md` |
| schema-toolsmith-r1 | Wave 0 revision | delivered; worker commit `b79d369`, integrated as `6c41c2d` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| acut-matrix-r1 | Wave 0 revision | delivered; worker commit `583600c`, integrated as `cb2831a` | exited | codex/core-exp-acut-matrix | /Users/chenmohan/gits/barcarolle-wt-acut-matrix | `experiments/core_narrative/configs/acuts/**`, `experiments/core_narrative/reports/acut_matrix_notes.md` |
| wave0-r1-reviewer | Wave 0 revision review | delivered; issues_found; commit `607d8a2` integrated | exited | codex/core-exp-wave0-r1-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r1-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md` |
| schema-toolsmith-r2 | Wave 0 revision | delivered; worker commit `de7a126`, integrated as `0c1fb36` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| llm-budget-gate | Revised-plan gate | implemented and reviewed; no_issues in Wave 0 r5 review | n/a | codex/core-narrative-experiment | /Users/chenmohan/gits/barcarolle | `experiments/core_narrative/configs/llm_access.yaml`, `experiments/core_narrative/results/cost_ledger.jsonl`, shared workflow contract |
| schema-toolsmith-r3 | Revised-plan gate tooling | delivered; worker commits `c7a01b2`, `34b0677`, integrated as `de47618`, `8575eb6` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/tools/**` |
| wave0-r3-reviewer | Wave 0 revision review | delivered; issues_found; commit `1689032` integrated | exited | codex/core-exp-wave0-r3-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r3-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md` |
| schema-toolsmith-r4 | Revised-plan gate tooling | delivered; worker commit `61833bf`, integrated as `2f804e9` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/tools/**` |
| wave0-r4-reviewer | Wave 0 revision review | delivered; issues_found; worker commit `b5312b5`, integrated as `4b767bd` | exited | codex/core-exp-wave0-r4-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r4-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r4-review.md` |
| schema-toolsmith-r5 | Revised-plan gate tooling | delivered; worker commits `df16bdb`, `11ce367`, integrated as `3b14e8a`, `a3c90f9` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/tools/**` |
| wave0-r5-reviewer | Wave 0 revision review | delivered; no_issues; worker commit `386a6e1`, integrated as `1d07e2e` | exited | codex/core-exp-wave0-r5-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r5-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r5-review.md` |
| repo-runtime-lock | Pre-run lock | delivered; worker commit `029fbdf`, integrated as `08064a5` | exited | codex/core-exp-repo-runtime-lock | /Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock | `experiments/core_narrative/configs/target_repositories.yaml`, `experiments/core_narrative/reports/repo_scout_notes.md` |
| general-benchmark-lock | Pre-run lock | delivered; worker commit `88acbad`, integrated as `d9f8f8e` | exited | codex/core-exp-general-lock | /Users/chenmohan/gits/barcarolle-wt-general-lock | `experiments/core_narrative/configs/general_benchmark.yaml`, `experiments/core_narrative/reports/general_benchmark_notes.md` |
| pre-run-lock-reviewer | Pre-run lock review | delivered; no_issues; worker commit `9c1c9a7`, integrated as `13404bc` | exited | codex/core-exp-pre-run-lock-reviewer | /Users/chenmohan/gits/barcarolle-wt-pre-run-lock-reviewer | `.codex-workflows/core-narrative-experiment/reviews/pre-run-locks-review.md` |
| execution-planner | Execution planning | delivered; run manifest prepared | exited | codex/core-narrative-experiment | /Users/chenmohan/gits/barcarolle | `experiments/core_narrative/configs/core_subset_run_manifest.yaml` |
| task-manifests | No-model preflight | delivered; worker commit `1cdcbba`, integrated as `4a89984` | exited | codex/core-exp-task-manifests | /Users/chenmohan/gits/barcarolle-wt-task-manifests | `experiments/core_narrative/configs/tasks/**`, `experiments/core_narrative/reports/task_manifest_notes.md` |
| task-manifests-reviewer | No-model preflight review | delivered; no_issues; worker commit `8869a07`, integrated as `7ad9462` | exited | codex/core-exp-task-manifests-reviewer | /Users/chenmohan/gits/barcarolle-wt-task-manifests-reviewer | `.codex-workflows/core-narrative-experiment/reviews/task-manifests-review.md`, `.codex-workflows/core-narrative-experiment/workers/task-manifests-reviewer/process.md` |

## Active Tmux Sessions

None.

## Decisions

- Use dedicated worktrees for all Wave 0 workers to keep write ownership isolated.
- Run Codex CLI workers in sandboxed non-interactive mode with `--full-auto`; do not use `--dangerously-bypass-approvals-and-sandbox`.
- Track the core narrative workflow files in Git, while ignoring CLI logs and large local artifacts.
- Created heartbeat automation `core-narrative-experiment-coordinator` to wake this thread every 10 minutes for bounded coordination steps.
- Adopt revised-plan LLM access contract: ACUT execution may use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`; credential values, bearer tokens, resolved secrets, and full base URL values must not be written to Git, process files, logs, run results, or reports.
- Adopt revised-plan budget contract: USD `$240` soft stop, USD `$300` hard cap, and no ACUT model call may start without cost ledgering.
- Default execution is budget-constrained to the core ACUT subset: `general-benchmark-optimized`, `repo-context-heavy`, `retrieval-sparse-symbolic`, and `lower-budget-fast-path`; 6 `G_score`, 8 `RBench`, 6 `RWork`, and one primary attempt per ACUT/task.
- Defer `higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline` unless the core subset finishes below the soft stop and the coordinator records spare budget.
- Adopt today's local stop strategy for 2026-04-28 in `Asia/Shanghai`: soft stop at `17:30`, hard stop at `17:50`.

## Today Stop Strategy

- timezone: `Asia/Shanghai`
- soft_stop_at: `2026-04-28T17:30:00+08:00`
- hard_stop_at: `2026-04-28T17:50:00+08:00`
- current_stop_state: `pre_soft_stop_active`
- current_pause_or_wind_down_status: Reviewed task manifests are integrated and no worker is active. Broad ACUT execution remains not started. Because the default core run is broad and cannot be guaranteed to close cleanly before the `17:50` hard stop, defer broad execution for today's remaining window.
- before_soft_stop_policy: Continue the current plan, but do not start a new long task that is unlikely to be reviewed, handed off, or cleanly paused before the hard stop.
- soft_stop_window_policy: From `17:30` through `17:50`, only continue or start short, low-risk, easy-to-close coordination tasks such as `process.md` updates, review cleanup, artifact integration, small no-model-call preflights, and status summaries.
- post_soft_stop_bans: After `17:30`, do not start broad ACUT execution, large batches of ACUT model calls, or new long-running workers.
- hard_stop_policy: After `17:50`, do not start new Codex CLI workers, do not continue ACUT model calls, and do not continue consuming LLM budget. If any worker is still running, require it to write a clear `process.md` handoff and stop the corresponding tmux session.
- workflow_contract: Coordinate only through `coordinator.md` and worker `process.md` files, do not inspect `cli.log` unless explicitly debugging, and do not overwrite unrelated user changes.
- resume_entry: On resume, first read this `coordinator.md` and the latest relevant worker `process.md`. Continue from the recorded handoff: if `task-manifests-reviewer` delivered `no_issues`, integrate the reviewed task manifests and review; if it found issues, start a focused revision only if the current stop window allows it; if it is still working after hard stop, request handoff and stop its tmux session before any further execution.

## Blockers

None currently recorded. Broad ACUT execution has not been started.

## Execution Readiness Bookkeeping

- checked_at: `2026-04-28T16:18:03+08:00`
- readiness_state: `ready_for_explicit_execution_start_after_resume_or_sufficient_runway`
- active_workers: none recorded
- reviewed_inputs_ready:
  - LLM access and budget gate: reviewed in `wave0-r5-reviewer` with `no_issues`
  - repo runtime lock: reviewed and integrated
  - general benchmark lock: reviewed and integrated
  - core subset run manifest: prepared, not started
  - concrete `RBench` and `RWork` task manifests: reviewed and integrated
- broad_execution_started: false
- model_calls_started: false
- today_execution_decision: Do not start broad ACUT execution or large model-call batches in the remaining 2026-04-28 window unless a future coordinator step can explicitly prove it will close cleanly before `17:50`.
- resume_entry: On the next real execution window, read this coordinator and the latest relevant worker `process.md` files, re-confirm required LLM env presence and writable ledger without recording values, then explicitly record execution start before launching any ACUT worker.

## Review Queue

- Wave 0 review found issues. Review artifact is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md`.
- Targeted revisions for `schema-toolsmith` and `acut-matrix` delivered. `acut-matrix` commit blocker was resolved by the coordinator.
- Focused `wave0-r1-reviewer` found one remaining contract issue and its review is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md`.
- Started `schema-toolsmith-r2` to align `execution_mode` and `adapter_or_harness_basis` with the scalar ACUT manifest contract and run the validator against all seven manifests.
- `schema-toolsmith-r2` delivered and the coordinator resolved its Git metadata commit blocker.
- Started `schema-toolsmith-r3` to implement the LLM access and cost ledger gate tooling required by the revised plan.
- `schema-toolsmith-r3` delivered gate and ledger append tooling, updated `run_task.py` to enforce the gate before ACUT command execution, and reported passing self-checks.
- Focused `wave0-r3-reviewer` found one remaining credential-boundary issue and its review is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md`.
- Started `schema-toolsmith-r4` to make `run_task.py` reject or redact secret-looking command arguments and full URLs before writing result artifacts.
- `schema-toolsmith-r4` delivered the command/result redaction fix and reported passing focused self-checks.
- Focused `wave0-r4-reviewer` found one remaining patch artifact credential-boundary issue and its review is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-r4-review.md`.
- Started `schema-toolsmith-r5` to prevent `submission.patch` and related runner artifacts from persisting resolved required LLM env values or other unsafe credential/full-URL content from tracked-file mutations.
- `schema-toolsmith-r5` delivered the patch artifact credential-boundary fix and reported passing focused self-checks.
- Started focused `wave0-r5-reviewer` before integrating worker branches.
- Focused `wave0-r5-reviewer` delivered `no_issues`; LLM access, cost ledger, command/result redaction, and patch artifact credential-boundary gates are implemented and reviewed.
- Integrated reviewed Wave 0 worker artifacts into the coordinator branch.
- Started `repo-runtime-lock` to verify local target repository runtime feasibility or select a fallback.
- Started `general-benchmark-lock` to materialize the revised six-task `G_score` concrete instance lock.
- `repo-runtime-lock` rerun delivered: `pallets/click` locked locally at commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2`; smoke and full local pytest commands passed.
- `general-benchmark-lock` rerun delivered: pinned SWE-Bench Pro parquet hash matched and six `G_score` IDs were materialized from the recorded selection rule.
- Started focused `pre-run-lock-reviewer` before integrating the rerun lock commits.
- Focused `pre-run-lock-reviewer` delivered `no_issues`; repo runtime and general benchmark pre-run locks are reviewed.
- Integrated the reviewed pre-run lock commits and review artifact.
- Broad ACUT execution has not been started; execution planning gate is ready for the budget-constrained core subset.
- Non-secret execution-start preflight recorded at `2026-04-28T15:02:08+08:00`: `BARCAROLLE_LLM_API_KEY` present, `BARCAROLLE_LLM_BASE_URL` present, and `experiments/core_narrative/results/cost_ledger.jsonl` exists and is writable. Values were not printed or recorded.
- Prepared `experiments/core_narrative/configs/core_subset_run_manifest.yaml` without starting broad ACUT execution or model calls.
- Started `task-manifests` to prepare concrete 8 `RBench` and 6 `RWork` task manifests plus no-model-call preflights.
- `task-manifests` delivered concrete 8 `RBench` and 6 `RWork` manifests for focused review. Broad ACUT execution and model calls remain not started.
- Started focused `task-manifests-reviewer` before integrating task manifests.
- Focused `task-manifests-reviewer` delivered `no_issues`.
- Integrated reviewed task manifests and the review artifact. Broad ACUT execution and model calls remain not started.

## Pre-Run Gates

- `repo-scout`: closed and reviewed. `pallets/click` is locked at commit `8bd8b4a074c55c03b6eb5666edc44a9c43df38a2` with local Python 3.12 install, smoke, and full local pytest timings recorded.
- `general-benchmark`: closed and reviewed. Six `G_score` task IDs are locked from the pinned SWE-Bench Pro parquet and recorded in `experiments/core_narrative/configs/general_benchmark.yaml`.
- LLM access: `experiments/core_narrative/configs/llm_access.yaml` must remain value-free and record only environment variable names, redaction policy, and budget caps.
- Cost ledger: `experiments/core_narrative/results/cost_ledger.jsonl` must exist and every ACUT model call or patch-generation attempt must append token, estimated/actual cost, and cumulative estimated cost fields.
- Execution block: ACUT execution workers must mark `status: blocked` before any model call if either LLM environment variable is missing, if the ledger is missing/unwritable, if ledgering is not implemented, or if projected spend would exceed `$300`.
- Broad execution workers are not started yet; next execution-start record must confirm required LLM env presence, writable cost ledger, and the active budget-constrained default slice.

## Execution Planning Gate

- gate_status: ready_for_execution_planning
- checked_at: 2026-04-28T15:02:08+08:00
- llm_env_presence:
  - `BARCAROLLE_LLM_API_KEY`: present, value not inspected or recorded
  - `BARCAROLLE_LLM_BASE_URL`: present, value not inspected or recorded
- cost_ledger: `experiments/core_narrative/results/cost_ledger.jsonl` exists and is writable
- budget_caps: USD `$240` soft stop, USD `$300` hard cap
- active_default_slice:
  - acuts: `general-benchmark-optimized`, `repo-context-heavy`, `retrieval-sparse-symbolic`, `lower-budget-fast-path`
  - tasks: 6 `G_score`, 8 `RBench`, 6 `RWork`
  - attempts: one primary attempt per ACUT/task
- deferred_acuts: `higher-budget-repo-depth`, `retrieval-history-augmented`, `minimal-context-baseline`
- broad_execution_started: false
- run_manifest: `experiments/core_narrative/configs/core_subset_run_manifest.yaml`
- next_allowed_step: prepare concrete RBench/RWork task manifests and any no-model-call preflight checks; do not start model calls until the coordinator records explicit execution start.

## Acceptance Gate

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes local workspaces, caches, cloned repositories, large artifacts, raw logs, and CLI logs.

## Next Heartbeat Action

Apply today's stop strategy before taking the next step. The task manifests are reviewed and integrated, no worker is active, and broad ACUT execution remains not started. For the remaining 2026-04-28 window, only perform short readiness bookkeeping or status summaries. After `17:30`, do not start broad ACUT execution, large ACUT model-call batches, or new long-running workers. After `17:50`, pause the workflow unless a running worker unexpectedly appears; if one does, request a `process.md` handoff and stop its tmux session. Do not start broad ACUT execution or model calls until the coordinator explicitly records execution start. Do not inspect `cli.log` unless debugging is explicitly requested.
