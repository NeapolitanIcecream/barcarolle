# M2 Patch-Or-Files Gap Acquisition

Date: 2026-05-10

## Target Gap

- Source matrix: `experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_20260510.json`.
- Source report: `experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition.md`.
- Historical run: `codex_nfl_m2_patch_or_files_20260509__cheap-click-specialist__click__rwork__006__attempt1`.
- Cell: `cheap-click-specialist x click__rwork__006`.
- Contract: `patch-or-files-v1`.
- Gap: normalized result and prompt snapshot existed, but the historical raw response artifact was absent and classified as `missing_raw_response_artifact`.

## Acquisition Result

- Pre-call gate: passed in `experiments/core_narrative/results/m2_patch_or_files_gap_acquisition_budget_gate_20260510.json`.
- Live calls made: `1`.
- Acquisition batch: `experiments/core_narrative/results/m2_patch_or_files_gap_acquisition_20260510.json`.
- Acquisition run: `m2_patch_or_files_gap_acquisition_20260510__cheap-click-specialist__click__rwork__006__attempt1`.
- Raw input acquired: yes, at `experiments/core_narrative/results/raw/m2_patch_or_files_gap_acquisition_20260510__cheap-click-specialist__click__rwork__006__attempt1/provider_response.redacted.json`.
- Stable category: `model_output_invalid_submission`.
- Failure owner/class: `model_output` / `unsafe_generated_text`.
- Verifier-ready persisted patch artifact: `false`.
- Nonpersistent verifier attempt: `false`.
- Infra failure: `false`.
- Cleanup blocker: `false`.
- Cost ledger append: `0.033658` USD estimated/provider-usage basis; new cumulative estimated cost `38.217436` USD.

## Updated Matrix

- Updated matrix: `experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap_20260510.json`.
- Updated report: `experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap.md`.
- Patch-or-files live fixed denominator: `6`.
- Patch-or-files acquisition input records: `1`.
- Historical patch-or-files missing raw artifacts: `1`.
- Remaining patch-or-files raw input gaps after acquisition: `0`.
- Aggregate category counts: `{'missing_raw_artifact': 1, 'model_output_invalid_submission': 14, 'nonpersistent_verifier_attempt': 2, 'verifier_ready_persisted_patch_artifact': 6}`.
- Blockers: none recorded.

The historical missing raw artifact remains recorded as historical evidence. The new acquisition row closes the remaining cell-level raw-input gap without rewriting the old run.

## Reproduction

```bash
PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/llm_budget_gate.py \
  --ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --projected-cost-usd 1 \
  --acut-id cheap-click-specialist \
  --split rwork \
  --attempt 1 \
  --output experiments/core_narrative/results/m2_patch_or_files_gap_acquisition_budget_gate_20260510.json

PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/codex_nfl_experiment_runner.py \
  --run-prefix m2_patch_or_files_gap_acquisition_20260510 \
  --task-split rwork \
  --tasks click__rwork__006 \
  --acuts cheap-click-specialist \
  --attempt 1 \
  --mode live \
  --submission-contract patch-or-files-v1 \
  --llm-ledger experiments/core_narrative/results/cost_ledger.jsonl \
  --output experiments/core_narrative/results/m2_patch_or_files_gap_acquisition_20260510.json \
  --runner-timeout-seconds 360 \
  --install-timeout-seconds 240 \
  --max-context-chars 50000

PYTHONPATH=experiments/core_narrative/tools python3 experiments/core_narrative/tools/m2_stable_nonpersistent_replay_matrix.py \
  --m2-summary experiments/core_narrative/results/m2_scoreability_summary_20260509.json \
  --patch-replay experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_patch_or_files_replay_20260510.json \
  --patch-acquisition-batch patch_or_files_gap_acquisition fixed_grid_acquisition_live experiments/core_narrative/results/m2_patch_or_files_gap_acquisition_20260510.json \
  --anchored-batch anchored_contract_live_smoke historical_live experiments/core_narrative/results/m2_anchored_contract_live_smoke_20260509.json \
  --anchored-batch anchored_occurrence_repair_live_smoke historical_live experiments/core_narrative/results/m2_anchored_occurrence_repair_live_smoke_20260510.json \
  --anchored-batch unsafe_artifact_repair_live_smoke historical_live experiments/core_narrative/results/m2_unsafe_artifact_repair_live_smoke_20260510.json \
  --anchored-batch nonpersistent_channel_replay no_model_replay experiments/core_narrative/results/m2_nonpersistent_verifier_channel_replay_20260510.json \
  --anchored-batch nonpersistent_channel_live_smoke historical_live experiments/core_narrative/results/m2_nonpersistent_verifier_channel_live_smoke_20260510.json \
  --anchored-batch fixed_grid_acquisition_generic fixed_grid_acquisition_live experiments/core_narrative/results/m2_anchored_fixed_grid_acquisition_generic_20260510.json \
  --anchored-batch fixed_grid_acquisition_specialist fixed_grid_acquisition_live experiments/core_narrative/results/m2_anchored_fixed_grid_acquisition_specialist_20260510.json \
  --output experiments/core_narrative/results/m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap_20260510.json \
  --report experiments/core_narrative/reports/2026-05-10_m2_stable_nonpersistent_replay_matrix_fixed_grid_acquisition_patch_or_files_gap.md
```

## Claim Boundaries

This acquisition does not claim M2 passed, ranking reversal, task-solving improvement, capability uplift, G_score predictivity, G0-G5 outcomes, license, admission, or authorization.
