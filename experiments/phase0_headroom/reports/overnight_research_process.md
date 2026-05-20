# Overnight Research Process

Generated UTC: `2026-05-20T14:35:07Z`.

## Step 0 Preflight And Evidence Sync

- Objective runbook: `docs/experiments/phase-0-to-phase-1-overnight-runbook.md`.
- Branch: `codex/restart-benchmark-compiler`.
- HEAD at preflight: `766f57bf`.
- Python: `Python 3.9.6`.
- `uv`: `uv 0.11.1 (Homebrew 2026-03-24 aarch64-apple-darwin)`.
- `LLM_BASE_URL` present after sourcing shell config: `true`.
- `LLM_API_KEY` present after sourcing shell config: `true`.
- Endpoint fallback policy: local Codex/ChatGPT subscription disabled; provider-specific fallback keys not used.
- Current measured endpoint calls: `6`.
- Usage observed rate: `1.0`.
- Estimated measured endpoint spend before overnight work: `USD 0.11133`.
- Generic comparator status before overnight work: `blocked_metadata_only`.
- Same-protocol `G_mini` tasks before overnight work: `0`.
- Raw/workspace/cache paths tracked by git: `0`.
- `git diff --check`: passed.
- `uv run --project experiments/phase0_headroom pytest -q experiments/phase0_headroom/tools`: `22 passed`.

## Step 1 Remove Immediate Ambiguity

- `configs/headroom_matrix.yaml` was still shaped as the older Codex CLI matrix. It is now explicitly marked `historical_codex_cli_default_disabled`.
- `configs/measured_endpoint_matrix.yaml` is the canonical active measured-endpoint matrix config for any future paid Phase 0 run.
- `reports/phase0_decision_memo.md` already points to `results/measured_cost_ledger.jsonl` and states that `G_mini` is blocked.
- `results/headroom_matrix.json` and `results/headroom_score_table.csv` reflect the measured endpoint calibration, not the old Codex CLI run.

## Step 2 Bounded Generic Comparator Repair

- Current release `G_mini` candidates: `click__rbench__001`, `click__rbench__002`, `click__rbench__003`, `click__rbench__004`.
- Archive evidence found: Click R0 task manifests, ACUT-visible statements, hidden verifiers, audit provenance, release hygiene metadata, and admission results.
- Active package root: `experiments/phase0_headroom/generic_comparator/click_r0/`.
- Same-protocol scoreable `G_mini` tasks after repair: `4`.
- Required same-protocol scoreable `G_mini` tasks: `3`.
- Paid calls used for comparator repair: `0`.
- Step 2 decision: `run_measured_endpoint_comparator_matrix`.

## Step 3A Measured Endpoint Matrix A

- Matrix branch taken because Step 2 produced `4` same-protocol scoreable `G_mini` packages.
- Existing compatible calibration cells reused: `4`.
- New paid Matrix A cells run: `6`.
- Toolz cells added: `toolz__hist__002`, `toolz__hist__016`.
- G_mini cells added: `click__rbench__001`, `click__rbench__002`, `click__rbench__003`, `click__rbench__004`.
- Usage observed rate after Matrix A: `1.0`.
- Estimated endpoint spend after Matrix A: `USD 0.329271`.
- Matrix A terminal statuses: `invalid_output=8`, `verified_fail=2`.
- Scoreable Matrix A cells: `2`.
- Scoreable G_mini Matrix A cells: `0`.
- Scale-up approved after Matrix A: `false`.
- Step 3A decision: stay diagnostic and initialize the Phase 1 compiler skeleton.

## Step 4 Phase 1 Compiler Skeleton

- Workspace initialized with `uv`: `experiments/phase1_compiler/`.
- Schemas implemented as dataclasses plus a schema catalog.
- Phase 0 importer wrote `experiments/phase1_compiler/results/toolz_phase1_draft_release.json`.
- Weighted score summary wrote `experiments/phase1_compiler/results/toolz_phase1_weighted_score.json`.
- Current weighted score status: `insufficient_evidence`.
- `uv run --project experiments/phase1_compiler pytest -q`: `4 passed`.
- Skeleton boundary: implemented compiler scaffolding only; no Phase 1 predictive validation claimed.
