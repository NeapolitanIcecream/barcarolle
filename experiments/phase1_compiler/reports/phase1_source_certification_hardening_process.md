# Phase 1 Source Certification Hardening Process

Status: preflight complete.

Generated: `2026-05-22T03:14:41Z`.

## Scope

This runbook hardens source provenance and certification interpretation before
any new paid ACUT scale-up. No paid ACUT task-solving cells or paid LLM calls
were run during preflight.

## Starting State

| Item | Value |
| --- | --- |
| Branch | `codex/restart-benchmark-compiler` |
| HEAD | `65971fb03852b43bf40f9f1c0442b3fbd3eb8b9d` |
| Python | `python` unavailable on PATH; `python3` is `Python 3.9.6`; project commands use `uv run` |
| uv | `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)` |
| Initial tracked git status | clean |

## Expected Evidence

| Check | Observed |
| --- | --- |
| Phase 1 decision | `phase1_operational_validation_pilot_complete` |
| Predictive validity established | `false` |
| Humanize source provenance | `humanize_source_provenance_fallback_confirmed` |
| Third repo release status | `diagnostic_only` |

## Hygiene Checks

| Command | Result |
| --- | --- |
| `git diff --check` | pass |
| `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` | `62 passed` |
| `uv run --project experiments/phase1_compiler pytest -q` | `13 passed` |
| `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` | `status=valid` |
| raw/workspace/external-repo/venv/cache tracking check | no tracked files |

Ignored local paths are present for `.venv`, `.pytest_cache`, external repos,
raw results, workspaces, and `__pycache__`; these remain untracked and are not
part of the hardening artifacts.
