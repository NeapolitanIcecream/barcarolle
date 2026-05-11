# Core Narrative Experiment

This directory contains the small, auditable experiment scaffold for validating the Barcarolle core narrative:

> General coding-agent benchmark rank is not enough evidence for repository-specific work quality.

The experiment follows `docs/experiments/core-narrative-experiment-plan.md`. It intentionally starts with protocolized artifact construction, minimal schemas, and runner/verifier glue before any platform productization.

## Current Phase

Phase 0 bootstrap is in progress. Wave 0 workers are responsible for:

- selecting a primary target repository;
- drafting the minimal schemas and tools;
- freezing the ACUT matrix;
- recording the general benchmark basis;
- enforcing the LLM access and budget contract before any ACUT execution.

Large or volatile artifacts stay out of Git. See `.gitignore` for the local workspace, clone, cache, and log paths.

## Execution Budget

ACUT execution is budget-constrained by default. LLM access must use only the environment variables named in `configs/llm_access.yaml`; credential values must never be written to repository artifacts. Cost records are appended to `results/cost_ledger.jsonl`. Broad execution remains blocked until the ledger gate is implemented and reviewed.

## Workspace-Mode Execution

`tools/workspace_mode_runner.py` is the minimal ACUT execution interface. For each ACUT and task, it creates an isolated run workspace from the task base commit and writes only ACUT-visible task material into that workspace. The ACUT works in the repo normally: it can read files, edit files, create files, and run commands without returning a structured patch or JSON response.

After the ACUT command ends, Barcarolle extracts the candidate patch from the final workspace state with the recorded `BASE_REF`, not from the ending `HEAD`. Harness-owned untracked paths such as `.core_narrative/`, `.venv/`, `.pytest_cache/`, `__pycache__/`, and install metadata are excluded. Regular untracked source files are added to the patch deterministically; untracked files that cannot be included are recorded as rejected artifacts.

Verification runs in a fresh workspace prepared from the same task base commit. The runner checks the fresh workspace base tree against the run workspace `BASE_TREE`; a mismatch returns `base_tree_mismatch` before patch replay or hidden verifier execution. On a matching tree, the runner applies the candidate patch and then runs the existing hidden verifier. Hidden verifier files, target commits, and reference patches are never copied into the ACUT run workspace. ACUT stdout, stderr, exit code, duration, and any local tests it ran are auxiliary evidence only; the final status comes from fresh replay plus the hidden verifier.
