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

## Step 2 Source Provenance Audit

Created:

- `experiments/phase1_compiler/tools/phase1_source_provenance_audit.py`
- `experiments/phase1_compiler/results/phase1_source_provenance_audit.json`
- `experiments/phase1_compiler/reports/phase1_source_provenance_audit.md`

Audit result:

- Toolz: `6/6` certified tasks have issue/PR-derived usable context.
- Humanize: `0/12` certified tasks have issue/PR-derived usable context.
- Humanize: `12/12` certified tasks remain commit-message fallback only.
- GitHub commit-to-PR metadata lookup was attempted and found `0` pull request
  metadata matches for the 12 certified Humanize target commits.

Decision:

- Humanize source provenance status:
  `humanize_source_provenance_fallback_confirmed`.
- This is acceptable for an operational pilot, but not for validation-grade
  claims.

## Step 3 Adapter And Cost Gates

Adapter preflight commands were run with `source ~/.zshrc` before invocation.
The workspace preflight tool writes one `{result_prefix}_preflight` artifact, so
the second adapter run overwrites the first. Both command outputs were checked:

| Adapter | Status | Endpoint proof | Missing env | Blockers |
| --- | --- | --- | --- | --- |
| `codex_workspace` | `ready` | `codex_eligible` | `[]` | `[]` |
| `kilo_workspace` | `ready` | `kilo_eligible` | `[]` | `[]` |

The committed preflight artifact currently reflects the final `kilo_workspace`
run for prefix `phase1_validation_humanize_holdout_smoke`.

Smoke projection:

- Cells: `4`.
- Conservative cost: `2.00` USD.
- Projected cumulative cost: `24.5529578` USD.

Cost gate:

- Projected cumulative cost remains below the `140` USD pre-batch stop
  threshold.
- Prior usage observed rate is `0.9221`, above the `0.85` stop threshold.

## Step 4 Humanize Holdout Smoke

Paid ACUT smoke cells were run sequentially:

- Codex: `humanize__hist__002`, `humanize__hist__010`.
- Kilo: `humanize__hist__002`, `humanize__hist__010`.

Smoke outcome:

- Cells: `4`.
- Scoreable cells: `4`.
- Terminal statuses: `verified_fail=4`.
- Policy violations: `0`.
- Usage observed rate for smoke prefix: `1.0`.
- Observed-or-conservative smoke cost: `1.2234708` USD.

Cumulative cost reconciliation was refreshed with all prior Phase 0 prefixes
plus `phase1_validation_humanize_holdout_smoke`:

- Cumulative calls: `81`.
- Cumulative usage observed rate: `0.9259`.
- Cumulative observed-or-conservative estimated spend: `23.7764286` USD.

Decision:

- Smoke passes the scoreability, policy, usage, and cost gates.
- The verified failures are valid experimental signal, not a harness blocker.
- Continue to the main Humanize holdout batch.
