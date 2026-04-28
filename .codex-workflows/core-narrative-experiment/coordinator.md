# Core Narrative Experiment Coordinator

status: wave_0_revision_review_running
updated: 2026-04-28T10:12:14+08:00
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
| wave0-r1-reviewer | Wave 0 revision review | session_running; process initialized | bcx-wave0-r1-reviewer | codex/core-exp-wave0-r1-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-r1-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-r1-review.md` |

## Active Tmux Sessions

- `bcx-wave0-r1-reviewer`

## Decisions

- Use dedicated worktrees for all Wave 0 workers to keep write ownership isolated.
- Run Codex CLI workers in sandboxed non-interactive mode with `--full-auto`; do not use `--dangerously-bypass-approvals-and-sandbox`.
- Track the core narrative workflow files in Git, while ignoring CLI logs and large local artifacts.
- Created heartbeat automation `core-narrative-experiment-coordinator` to wake this thread every 10 minutes for bounded coordination steps.

## Blockers

None currently recorded.

## Review Queue

- Wave 0 review found issues. Review artifact is integrated at `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md`.
- Targeted revisions for `schema-toolsmith` and `acut-matrix` delivered. `acut-matrix` commit blocker was resolved by the coordinator.
- Focused `wave0-r1-reviewer` is running before integrating revised artifact branches.
- Do not start task-builder, leakage-auditor, verifier-auditor, or ACUT execution workers until the clean-room workspace leakage and ACUT schema/manifest mismatch are closed.

## Pre-Run Gates

- `repo-scout`: clone and run a local `pallets/click` smoke/full-suite timing check, or select a fallback if local runtime is not viable.
- `general-benchmark`: materialize and record locked SWE-Bench Pro instance IDs and any pre-run infrastructure replacements before ACUT patch-generation runs.

## Acceptance Gate

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes local workspaces, caches, cloned repositories, large artifacts, raw logs, and CLI logs.

## Next Heartbeat Action

Read `wave0-r1-reviewer` `process.md`. If review is delivered with no blocking issues, inspect the review and integrate accepted worker branches. If issues remain, write targeted feedback into the owning worker directory and start the next revision. Do not inspect `cli.log` unless debugging is explicitly requested.
