# Core Narrative Experiment Coordinator

status: wave0_r3_review_starting
updated: 2026-04-28T11:03:26+08:00
phase: Phase 0 - Experiment Bootstrap
base_commit: 47046e7754d2402b7177a4b80f631ab6b0bcd97c
coordinator_repo: /Users/chenmohan/gits/barcarolle
coordinator_branch: codex/core-narrative-experiment

## Objective

Execute `docs/experiments/core-narrative-experiment-plan.md` with tmux-managed Codex CLI workers. Coordinate through this file and worker `process.md` files only. Do not inspect `cli.log` files unless debugging is explicitly requested.

## Worker Status

| Worker | Phase | Status | Session | Branch | Worktree | Owned Paths |
| --- | --- | --- | --- | --- | --- | --- |
| repo-scout | Wave 0 | delivered; commit `9b5dbbe` | exited | codex/core-exp-repo-scout | /Users/chenmohan/gits/barcarolle-wt-repo-scout | `experiments/core_narrative/configs/target_repositories.yaml`, `experiments/core_narrative/reports/repo_scout_notes.md` |
| schema-toolsmith | Wave 0 | delivered; commit `a9824ba` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| acut-matrix | Wave 0 | delivered; commit `dcbdc1e` | exited | codex/core-exp-acut-matrix | /Users/chenmohan/gits/barcarolle-wt-acut-matrix | `experiments/core_narrative/configs/acuts/**`, `experiments/core_narrative/reports/acut_matrix_notes.md` |
| general-benchmark | Wave 0 | delivered; commit `54a07ae` | exited | codex/core-exp-general-benchmark | /Users/chenmohan/gits/barcarolle-wt-general-benchmark | `experiments/core_narrative/configs/general_benchmark.yaml`, `experiments/core_narrative/reports/general_benchmark_notes.md` |
| wave0-reviewer | Wave 0 review | delivered; issues_found; commit `a2aef12` integrated | exited | codex/core-exp-wave0-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md` |
| schema-toolsmith-r1 | Wave 0 revision | delivered; commit `b79d369` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| acut-matrix-r1 | Wave 0 revision | delivered; commit `583600c` | exited | codex/core-exp-acut-matrix | /Users/chenmohan/gits/barcarolle-wt-acut-matrix | `experiments/core_narrative/configs/acuts/**`, `experiments/core_narrative/reports/acut_matrix_notes.md` |
| wave0-r1-reviewer | Wave 0 revision review | delivered; issues_found; commit `607d8a2` integrated | exited | codex/core-exp-wave0-r1-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r1-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md` |
| schema-toolsmith-r2 | Wave 0 revision | delivered; commit `de7a126` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/schemas/**`, `experiments/core_narrative/tools/**` |
| llm-budget-gate | Revised-plan gate | recorded; tool enforcement delivered by schema worker; review pending | n/a | codex/core-narrative-experiment | /Users/chenmohan/gits/barcarolle | `experiments/core_narrative/configs/llm_access.yaml`, `experiments/core_narrative/results/cost_ledger.jsonl`, shared workflow contract |
| schema-toolsmith-r3 | Revised-plan gate tooling | delivered; commits `c7a01b2`, `34b0677` | exited | codex/core-exp-schema-toolsmith | /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith | `experiments/core_narrative/tools/**` |
| wave0-r3-reviewer | Wave 0 revision review | initialized | pending | codex/core-exp-wave0-r3-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r3-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r3-review.md` |

## Active Tmux Sessions

None. `schema-toolsmith-r3` has exited after delivery.

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

None currently recorded.

## Review Queue

- Wave 0 review found issues. Review artifact is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md`.
- Targeted revisions for `schema-toolsmith` and `acut-matrix` delivered. `acut-matrix` commit blocker was resolved by the coordinator.
- Focused `wave0-r1-reviewer` found one remaining contract issue and its review is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md`.
- Started `schema-toolsmith-r2` to align `execution_mode` and `adapter_or_harness_basis` with the scalar ACUT manifest contract and run the validator against all seven manifests.
- `schema-toolsmith-r2` delivered and the coordinator resolved its Git metadata commit blocker.
- Started `schema-toolsmith-r3` to implement the LLM access and cost ledger gate tooling required by the revised plan.
- `schema-toolsmith-r3` delivered gate and ledger append tooling, updated `run_task.py` to enforce the gate before ACUT command execution, and reported passing self-checks. Start focused review before integrating worker branches.
- Do not start task-builder, leakage-auditor, verifier-auditor, or ACUT execution workers until the clean-room workspace leakage and ACUT schema/manifest mismatch are closed.

## Pre-Run Gates

- `repo-scout`: clone and run a local `pallets/click` smoke/full-suite timing check, or select a fallback if local runtime is not viable.
- `general-benchmark`: materialize and record locked SWE-Bench Pro instance IDs and any pre-run infrastructure replacements before ACUT patch-generation runs.
- LLM access: `experiments/core_narrative/configs/llm_access.yaml` must remain value-free and record only environment variable names, redaction policy, and budget caps.
- Cost ledger: `experiments/core_narrative/results/cost_ledger.jsonl` must exist and every ACUT model call or patch-generation attempt must append token, estimated/actual cost, and cumulative estimated cost fields.
- Execution block: ACUT execution workers must mark `status: blocked` before any model call if either LLM environment variable is missing, if the ledger is missing/unwritable, if ledgering is not implemented, or if projected spend would exceed `$300`.
- Broad execution workers remain blocked until the LLM access contract and ledger gate are implemented and reviewed.

## Acceptance Gate

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes local workspaces, caches, cloned repositories, large artifacts, raw logs, and CLI logs.

## Next Heartbeat Action

Read `wave0-r3-reviewer` `process.md`. If review is delivered with no blocking issues, integrate the reviewed worker branches and keep broad execution blocked until the remaining pre-run repository and general-benchmark locks are closed. If issues remain, write targeted feedback into the owning worker directory and start the next revision. Do not inspect `cli.log` unless debugging is explicitly requested.
