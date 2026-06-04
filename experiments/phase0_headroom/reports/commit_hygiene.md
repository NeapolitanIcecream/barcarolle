# Phase 0 Commit Hygiene

Post-proposal mainline retention:

- Keep configs, scripts, tests, small manifests, summary tables, reports,
  `pyproject.toml`, `uv.lock`, and the sanitized
  `results/workspace_usage_ledger.jsonl` used by later analyses.
- Do not commit `.venv/`, pytest caches, cloned repositories, raw pytest tails,
  solver/verifier workspaces, cost ledgers, submissions, raw transcripts, raw
  prompts, or raw completions.
- The older `results/raw_artifact_manifest.json` digest file is not retained in
  the active mainline because the raw artifacts themselves are not retained.

This directory is historical support for the current compiler evidence. New
paid validation should be recorded through `experiments/phase1_compiler/` using
the repository-wide artifact hygiene rules.
