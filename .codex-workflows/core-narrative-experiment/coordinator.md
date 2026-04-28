# Core Narrative Experiment Coordinator

status: pre_run_locks_review_running
updated: 2026-04-28T14:35:56+08:00
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
| repo-runtime-lock | Pre-run lock | delivered; worker commit `029fbdf`, review pending | exited | codex/core-exp-repo-runtime-lock | /Users/chenmohan/gits/barcarolle-wt-repo-runtime-lock | `experiments/core_narrative/configs/target_repositories.yaml`, `experiments/core_narrative/reports/repo_scout_notes.md` |
| general-benchmark-lock | Pre-run lock | delivered; worker commit `88acbad`, review pending | exited | codex/core-exp-general-lock | /Users/chenmohan/gits/barcarolle-wt-general-lock | `experiments/core_narrative/configs/general_benchmark.yaml`, `experiments/core_narrative/reports/general_benchmark_notes.md` |
| pre-run-lock-reviewer | Pre-run lock review | session_running; process initialized | bcx-pre-run-lock-reviewer | codex/core-exp-pre-run-lock-reviewer | /Users/chenmohan/gits/barcarolle-wt-pre-run-lock-reviewer | `.codex-workflows/core-narrative-experiment/reviews/pre-run-locks-review.md` |

## Active Tmux Sessions

- `bcx-pre-run-lock-reviewer`

## Decisions

- Use dedicated worktrees for all Wave 0 workers to keep write ownership isolated.
- Run Codex CLI workers in sandboxed non-interactive mode with `--full-auto`; do not use `--dangerously-bypass-approvals-and-sandbox`.
- Track the core narrative workflow files in Git, while ignoring CLI logs and large local artifacts.
- Created heartbeat automation `core-narrative-experiment-coordinator` to wake this thread every 10 minutes for bounded coordination steps.
- Adopt revised-plan LLM access contract: ACUT execution may use only `BARCAROLLE_LLM_API_KEY` and `BARCAROLLE_LLM_BASE_URL`; credential values, bearer tokens, resolved secrets, and full base URL values must not be written to Git, process files, logs, run results, or reports.
- Adopt revised-plan budget contract: USD `$240` soft stop, USD `$300` hard cap, and no ACUT model call may start without cost ledgering.
- Default execution is budget-constrained to the core ACUT subset: `general-benchmark-optimized`, `repo-context-heavy`, `retrieval-sparse-symbolic`, and `lower-budget-fast-path`; 6 `G_score`, 8 `RBench`, 6 `RWork`, and one primary attempt per ACUT/task.
- Defer `higher-budget-repo-depth`, `retrieval-history-augmented`, and `minimal-context-baseline` unless the core subset finishes below the soft stop and the coordinator records spare budget.

## Blockers

None currently recorded. Broad ACUT execution remains paused until pre-run lock review and integration finish.

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
- Do not start broad ACUT execution workers until pre-run lock review and integration finish.

## Pre-Run Gates

- `repo-scout`: delivered by worker rerun; review pending before integration.
- `general-benchmark`: delivered by worker rerun; review pending before integration.
- LLM access: `experiments/core_narrative/configs/llm_access.yaml` must remain value-free and record only environment variable names, redaction policy, and budget caps.
- Cost ledger: `experiments/core_narrative/results/cost_ledger.jsonl` must exist and every ACUT model call or patch-generation attempt must append token, estimated/actual cost, and cumulative estimated cost fields.
- Execution block: ACUT execution workers must mark `status: blocked` before any model call if either LLM environment variable is missing, if the ledger is missing/unwritable, if ledgering is not implemented, or if projected spend would exceed `$300`.
- Broad execution workers remain blocked until the `repo-scout` and `general-benchmark` pre-run locks are closed.

## Acceptance Gate

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes local workspaces, caches, cloned repositories, large artifacts, raw logs, and CLI logs.

## Next Heartbeat Action

Read `pre-run-lock-reviewer` `process.md`. If review is delivered with `no_issues`, integrate `repo-runtime-lock`, `general-benchmark-lock`, and the review artifact, then update coordinator status before considering any broad ACUT execution worker. If issues remain, route focused feedback to the owning lock worker. Do not inspect `cli.log` unless debugging is explicitly requested.
