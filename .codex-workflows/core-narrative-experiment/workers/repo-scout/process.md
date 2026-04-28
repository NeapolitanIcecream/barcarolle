# Process

status: delivered
updated: 2026-04-28T09:40:38+08:00

## Summary

Delivered repo-scout artifacts. Primary recommendation is `pallets/click`;
fallbacks are `psf/black`, `python-attrs/attrs`, and `pallets/flask`.
The primary self-check marks `pallets/click` plausible for 30 RBench tasks and
12 RWork tasks from disjoint anchors.

## Owned Paths

- `experiments/core_narrative/configs/target_repositories.yaml`
- `experiments/core_narrative/reports/repo_scout_notes.md`
- `.codex-workflows/core-narrative-experiment/workers/repo-scout/process.md`

## Files Changed Or Inspected

Inspected:

- `docs/experiments/core-narrative-experiment-plan.md`
- `.codex-workflows/core-narrative-experiment/shared/experiment-brief.md`
- `.codex-workflows/core-narrative-experiment/shared/worker-contract.md`
- `.codex-workflows/core-narrative-experiment/workers/repo-scout/prompt.md`
- `experiments/core_narrative/README.md`
- `experiments/core_narrative/configs/target_repositories.yaml`
- `.gitignore`
- GitHub repository metadata for `pallets/click`, `psf/black`,
  `python-attrs/attrs`, and `pallets/flask`
- GitHub pyproject/license/test-directory pages for the same candidates
- GitHub/Ecosyste.ms issue and pull request count pages used as supply evidence

Changed:

- `.codex-workflows/core-narrative-experiment/workers/repo-scout/process.md`
- `experiments/core_narrative/configs/target_repositories.yaml`
- `experiments/core_narrative/reports/repo_scout_notes.md`
- `experiments/core_narrative/external_repos/` was created as an ignored local
  probe directory; clone probe failed before any repository checkout was written.

Verified:

- `ruby -e 'require "yaml"; YAML.load_file(...)'`
- `ruby` self-check for primary, fallback count, Barcarolle exclusion, and
  primary RBench/RWork self-check presence
- `git diff --check`

## Current Blockers

None for delivery. Local `git clone` feasibility probe could not run because the
sandbox DNS cannot resolve `github.com`; repository evaluation therefore uses
GitHub connector and browser evidence instead of local test timing.

## Git State

branch: codex/core-exp-repo-scout
worktree: /Users/chenmohan/gits/barcarolle-wt-repo-scout
status: delivered artifact commit is present on this branch; post-commit
worktree is expected to be clean except ignored worker `cli.log`

## Handoff

Use `pallets/click` unless reviewer rejects the local-runtime uncertainty.
Next task-builder should clone under
`experiments/core_narrative/external_repos/click`, run the smoke/full pytest
commands from `target_repositories.yaml`, then mine anchors with a temporal
split around `2024-01-01`.
