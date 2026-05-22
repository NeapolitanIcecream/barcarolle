# Phase 1 Source Certification Hardening Process

## Step 0 Preflight

Generated: 2026-05-22T11:14:21+08:00.

| Field | Value |
| --- | --- |
| Branch | `codex/restart-benchmark-compiler` |
| HEAD | `65971fb03852b43bf40f9f1c0442b3fbd3eb8b9d` |
| Python | `python` not on PATH; `python3 --version` returned `Python 3.9.6` |
| uv | `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)` |
| Paid ACUT calls | `disabled` |
| Paid LLM calls | `disabled` |

Starting evidence matched the runbook:

| Check | Observed |
| --- | --- |
| Overnight decision | `phase1_operational_validation_pilot_complete` |
| Predictive validity | `false` |
| Humanize source provenance | `humanize_source_provenance_fallback_confirmed` |
| Itsdangerous release status | `diagnostic_only` |

Pre-change hygiene:

| Command | Result |
| --- | --- |
| `git diff --check` | pass |
| `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools` | `62 passed in 1.76s` |
| `uv run --project experiments/phase1_compiler pytest -q` | `13 passed in 0.04s` |
| `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_compiler.py validate --config experiments/phase1_compiler/configs/phase1_mvp.yaml` | `status=valid` |
| raw/workspace/external-repo/venv/cache tracked-file check | no tracked files |

Scoped status only reported ignored raw, workspace, external-repo, venv, and
cache paths. No paid calls were made during preflight.
