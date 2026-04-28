# Core Narrative Experiment Coordinator

status: wave_0_review_running
updated: 2026-04-28T09:45:49+08:00
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
| wave0-reviewer | Wave 0 review | session_running; process initialized | bcx-wave0-reviewer | codex/core-exp-wave0-reviewer | /Users/chenmohan/gits/barcarolle-wt-wave0-reviewer | `.codex-workflows/core-narrative-experiment/reviews/wave0-review.md` |

## Active Tmux Sessions

- `bcx-wave0-reviewer`

## Decisions

- Use dedicated worktrees for all Wave 0 workers to keep write ownership isolated.
- Run Codex CLI workers in sandboxed non-interactive mode with `--full-auto`; do not use `--dangerously-bypass-approvals-and-sandbox`.
- Track the core narrative workflow files in Git, while ignoring CLI logs and large local artifacts.
- Created heartbeat automation `core-narrative-experiment-coordinator` to wake this thread every 10 minutes for bounded coordination steps.

## Blockers

None currently recorded.

## Review Queue

- `wave0-reviewer` is running and will inspect delivered Wave 0 artifacts from worker worktrees before coordinator merges or cherry-picks any worker branch.

## Acceptance Gate

- Coordinator can list all workers and owned paths.
- Coordinator can list worker branches and worktrees.
- No two workers have overlapping write ownership except through explicit review feedback files.
- `.gitignore` excludes local workspaces, caches, cloned repositories, large artifacts, raw logs, and CLI logs.

## Next Heartbeat Action

Read `wave0-reviewer` `process.md`. If review is delivered with no blocking issues, inspect the review and integrate accepted worker branches. If issues are found, write targeted feedback into the owning worker directory and start the corresponding revision worker. Do not inspect `cli.log` unless debugging is explicitly requested.
