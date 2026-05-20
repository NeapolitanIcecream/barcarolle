# Overnight Research Report

Status: `complete`.

## Run Context

- Runbook: `docs/experiments/phase-0-to-phase-1-overnight-runbook.md`.
- Branch: `codex/restart-benchmark-compiler`.
- HEAD before closeout report: `23a2ebad`.
- Chosen branch: `generic_comparator_repaired`.
- Primary endpoint ACUT model: `gpt-5.4-mini`.
- Endpoint authentication path: `LLM_BASE_URL` plus `LLM_API_KEY`; no Codex subscription fallback.

## What Completed

- Step 0/1: preflight passed and active measured-endpoint artifacts were clarified.
- Step 2: repaired the Click `G_mini` generic comparator protocol with `4` active same-protocol packages.
- Step 3A: ran measured endpoint Matrix A by reusing `4` compatible calibration cells and adding `6` paid cells.
- Step 4: initialized the Phase 1 compiler skeleton and imported the current Phase 0 release into a draft Phase 1 manifest.

## Cost And Usage

- Measured endpoint calls recorded: `12`.
- Paid task-solving calls: `10`.
- Usage observed rate: `1.0`.
- Input tokens: `85467`.
- Cached input tokens: `0`.
- Output tokens: `4858`.
- Estimated endpoint spend: `USD 0.329271`.
- Overnight incremental endpoint spend: `USD 0.217941`.
- Provider-billed actual cost: `null`; billing dollars were not exposed by the endpoint response.
- Overnight projected-cost artifact: `experiments/phase0_headroom/results/overnight_projected_cost_ledger.jsonl`.

## Task And Cell Counts

- Certified same-repo `toolz` tasks: `6`.
- Repaired same-protocol `G_mini` packages: `4`.
- Matrix A task-solving cells: `10`.
- Scoreable Matrix A cells: `2`.
- Invalid or harness-error Matrix A cells: `8`.
- Verified-pass cells: `0`.
- Verified-fail cells: `2`.
- Scoreable `G_mini` Matrix A cells: `0`.

## Certification Yield

- Certified: `6`.
- Rejected: `10`.
- Rejection reasons:
  - `reference_pass`: `6`.
  - `no_op_fail`: `4`.

## Decision

Phase 0 remains `proceed_regression_benchmark`. The generic comparator protocol was repaired, but Matrix A was too harness-sensitive: all newly added cells failed at patch-application/output-contract time. This is not enough to move to `proceed_predictive`.

No second ACUT and no optional Matrix B are approved from this evidence.

## Phase 1 Skeleton

Phase 1 skeleton exists at `experiments/phase1_compiler/`.

- Draft release: `experiments/phase1_compiler/results/toolz_phase1_draft_release.json`.
- Weighted score summary: `experiments/phase1_compiler/results/toolz_phase1_weighted_score.json`.
- Weighted score status: `insufficient_evidence`.
- Tests: `uv run --project experiments/phase1_compiler pytest -q` passed.

## Changed Artifacts

- `experiments/phase0_headroom/configs/measured_endpoint_matrix.yaml`.
- `experiments/phase0_headroom/generic_comparator/click_r0/`.
- `experiments/phase0_headroom/results/generic_comparator_protocol.json`.
- `experiments/phase0_headroom/results/generic_comparator_dry_run.json`.
- `experiments/phase0_headroom/results/measured_cost_ledger.jsonl`.
- `experiments/phase0_headroom/results/measured_cost_summary.json`.
- `experiments/phase0_headroom/results/headroom_matrix.json`.
- `experiments/phase0_headroom/results/headroom_metrics.json`.
- `experiments/phase0_headroom/results/headroom_score_table.csv`.
- `experiments/phase0_headroom/results/overnight_research_decision.json`.
- `experiments/phase0_headroom/reports/overnight_research_process.md`.
- `experiments/phase0_headroom/reports/phase0_decision_memo.md`.
- `experiments/phase0_headroom/reports/measured_cost_report.md`.
- `experiments/phase0_headroom/reports/headroom_analysis.md`.
- `experiments/phase1_compiler/`.

## Next Smallest Useful Runbook

Write a targeted output-contract repair runbook before any broader paid residual-validation run. The next run should compare the current diff-only prompt against a stricter patch contract on `4` to `6` cells, and should scale only if patch application produces scoreable cells above the Matrix A baseline.
