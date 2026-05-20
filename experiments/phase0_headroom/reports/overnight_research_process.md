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
