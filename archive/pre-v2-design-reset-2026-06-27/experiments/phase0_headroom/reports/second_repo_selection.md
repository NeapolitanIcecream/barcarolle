# Second Repo Selection

Selected repository: `humanize`.

## Repository

- GitHub URL: `https://github.com/python-humanize/humanize.git`.
- Local clone: `experiments/phase0_headroom/external_repos/humanize`.
- Local HEAD: `bde649fc2927c022dd2a9eedba2a1ed677b97902`.
- HEAD subject: `Performance improvements: 1.07x - 8.4x (#315)`.
- Package shape: Hatch/pyproject package with `src/humanize` and `tests`.
- Test command candidate:
  `uv run --project experiments/phase0_headroom --with freezegun --with "pytest>=9" python -m pytest -q {test_files}`.

## Entry Scan

The deterministic history scan used commits since `2020-01-01` and rejected
docs-only, CI-only, release metadata, formatting, linting, lockfile,
dependency-bump, translation-only, and test-only cleanup commits.

Entry result:

- Plausible code-plus-test anchors after rejection: `52`.
- Minimum required plausible anchors: `12`.
- External service risk: low.
- Test environment risk: bounded local Python tests with `freezegun` and
  `pytest` supplied through `uv run --with`.

## Decision

`humanize` is selected without fallback. It is small enough for bounded local
certification, has a clear `src/` package layout, and has enough historical
code-plus-test anchors to attempt a pilot release.

Fallback repositories were not used.

## ACUT Boundary

The selected pilot keeps the existing workspace ACUT protocol unchanged:
Barcarolle prepares clean solver/verifier workspaces, invokes the existing
Codex and Kilo workspace adapters, captures git diff, rejects test and
out-of-scope edits, and injects hidden oracle material only in verifier
workspaces.
