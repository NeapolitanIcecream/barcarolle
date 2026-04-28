# Process

status: delivered
updated: 2026-04-28T10:07:59+08:00

## Summary

Delivered review-feedback-1 revisions. `prepare_workspace.py` now builds ACUT workspaces from a base-commit tree archive into a fresh synthetic Git repository, so post-base refs and target commit objects are not visible. ACUT and run-result schemas are aligned to the reviewed minimal contracts, and dependency-light leakage and ACUT validation self-checks are available.

## Owned Paths

- `experiments/core_narrative/schemas/**`
- `experiments/core_narrative/tools/**`
- `.codex-workflows/core-narrative-experiment/workers/schema-toolsmith/process.md`

## Files Changed Or Inspected

- Inspected `.codex-workflows/core-narrative-experiment/workers/schema-toolsmith/process.md`
- Inspected delivered process state from `HEAD`
- Inspected `docs/experiments/core-narrative-experiment-plan.md`
- Inspected `.codex-workflows/core-narrative-experiment/shared/worker-contract.md`
- Inspected `.codex-workflows/core-narrative-experiment/workers/schema-toolsmith/review-feedback-1.md`
- Inspected delivered ACUT manifests in `/Users/chenmohan/gits/barcarolle-wt-acut-matrix/experiments/core_narrative/configs/acuts/` for shape compatibility only; no edits made there
- Added `experiments/core_narrative/tools/check_workspace_leakage.py`
- Added `experiments/core_narrative/tools/validate_acut_manifest.py`
- Modified `experiments/core_narrative/tools/prepare_workspace.py`
- Modified `experiments/core_narrative/schemas/acut.schema.json`
- Modified `experiments/core_narrative/schemas/run_result.schema.json`

## Current Blockers

None.

## Git State

branch: codex/core-exp-schema-toolsmith
worktree: /Users/chenmohan/gits/barcarolle-wt-schema-toolsmith
start status:
- `?? .codex-workflows/core-narrative-experiment/workers/schema-toolsmith/review-feedback-1.md`
- `?? .codex-workflows/core-narrative-experiment/workers/schema-toolsmith/revision-prompt-1.md`
- `?? .codex-workflows/core-narrative-experiment/workers/schema-toolsmith/run_revision_1.sh`
pre-commit status:
- Modified owned files: process.md, `acut.schema.json`, `run_result.schema.json`, `prepare_workspace.py`
- New owned files: `check_workspace_leakage.py`, `validate_acut_manifest.py`
- Untracked coordinator-provided revision files remain unstaged: `review-feedback-1.md`, `revision-prompt-1.md`, `run_revision_1.sh`
final state after commit: owned tracked revision changes committed on `codex/core-exp-schema-toolsmith`; coordinator-provided untracked revision files intentionally not committed

## Handoff

Self-checks passed:
- `PYTHONPYCACHEPREFIX=/tmp/barcarolle-core-narrative-pycache python3 -m py_compile experiments/core_narrative/tools/*.py`
- `for f in experiments/core_narrative/schemas/*.schema.json; do python3 -m json.tool "$f" >/tmp/$(basename "$f").pretty.json; done`
- `for tool in prepare_workspace run_task apply_and_verify summarize_results check_workspace_leakage validate_acut_manifest; do python3 "experiments/core_narrative/tools/$tool.py" --help >/tmp/$tool.help.txt; done`
- `python3 experiments/core_narrative/tools/check_workspace_leakage.py`
- `python3 experiments/core_narrative/tools/validate_acut_manifest.py --self-check`
- `python3 experiments/core_narrative/tools/summarize_results.py experiments/core_narrative/results/normalized`
- `git diff --check`

Leakage self-check result: passed with one synthetic workspace commit and one local ref; the supplied target commit was absent from refs, the object database, reachable history, and the ACUT-visible task package.

Validation note: the inspected ACUT matrix manifests currently use the pre-review nested `model`/`operator` shape and `frozen_date`/`prompt_or_policy_digest` names. They were not edited in this worktree; `validate_acut_manifest.py` is ready for the ACUT matrix worker to run after those manifests are revised to the canonical top-level contract.
