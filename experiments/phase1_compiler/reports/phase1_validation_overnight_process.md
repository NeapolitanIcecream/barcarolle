# Phase 1 Overnight Validation Process

Generated: `2026-05-21T15:38:56Z`.

## Step 0 Preflight

- Branch: `codex/restart-benchmark-compiler`.
- Starting HEAD: `9fc424ff529ca2f72f7a2e837ff764038a57a6dd`.
- Python: `Python 3.9.6`.
- uv: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`.
- Codex CLI: `codex-cli 0.132.0`.
- Kilo CLI: `7.3.1`.
- Endpoint environment check after sourcing `~/.zshrc`: present.

Phase 1 MVP state:

- `phase1_mvp_closeout.predictive_validity_established`: `false`.
- `phase1_mvp_closeout.evidence_status`:
  `mvp_compiler_artifacts_built_insufficient_for_predictive_validation`.
- `phase1_mvp_release.status`: `pilot_grade`.

Cost baseline from `workspace_cost_reconciliation.json`:

- Prior workspace call count: `77`.
- Usage observed rate: `0.9221`.
- Observed-or-conservative estimated spend: `22.5529578` USD.

Hygiene:

- `git diff --check`: passed.
- Phase 0 tools tests: `62 passed`.
- Phase 1 compiler tests: `13 passed`.
- Phase 1 compiler validate: `status=valid`.
- Raw results, solver workspaces, external repos, virtualenvs, and Python
  caches are ignored and not tracked.

Current budget position:

- Overnight smoke projection: `4 * 0.50 = 2.00` USD.
- Projected cumulative after smoke: `24.5529578` USD.
- Main Humanize holdout projection: `12 * 0.50 = 6.00` USD.
- Projected cumulative after smoke plus main: `30.5529578` USD.
- These projections are below the `140` USD pre-batch stop threshold and the
  `160` USD unattended stop threshold.

## Step 1 Overnight Plan

Created:

- `experiments/phase1_compiler/configs/phase1_validation_overnight.yaml`
- `experiments/phase1_compiler/results/phase1_validation_overnight_plan.json`

Planned Humanize internal unseen ACUT holdout tasks:

- Smoke: `humanize__hist__002`, `humanize__hist__010`.
- Main: `humanize__hist__003`, `humanize__hist__004`,
  `humanize__hist__007`, `humanize__hist__008`,
  `humanize__hist__012`, `humanize__hist__015`.
- Already solved and excluded: `humanize__hist__005`,
  `humanize__hist__006`, `humanize__hist__013`,
  `humanize__hist__014`.

The plan includes both `B_real` and `W_real` coverage and keeps the evidence
label at `internal_unseen_acut_holdout_not_future_holdout`.
