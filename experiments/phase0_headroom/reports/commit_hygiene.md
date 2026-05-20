# Phase 0 Commit Hygiene

Step 9 checks before commit:

- `git status --short --ignored experiments/phase0_headroom .gitignore` showed only staged small artifacts plus ignored `experiments/phase0_headroom/external_repos/` and `experiments/phase0_headroom/results/raw/`.
- `git diff --cached --check` passed.
- Staged artifacts are configs, scripts, tests, small manifests, tables, reports, `pyproject.toml`, `uv.lock`, and `results/cost_ledger.jsonl`.
- Raw pytest tails, `.venv/`, and cloned repositories are not staged.
- Raw artifact digests are recorded in `experiments/phase0_headroom/results/raw_artifact_manifest.json`.

The committed `cost_ledger.jsonl` is empty because no paid model calls were made.
