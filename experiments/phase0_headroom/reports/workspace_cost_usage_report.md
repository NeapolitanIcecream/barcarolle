# Workspace Cost Usage Report

Generated at `2026-05-28T07:25:04+00:00`.

Provider-billed dollars remain unavailable for these workspace ACUT runs. The canonical spend estimate is therefore the observed-token estimate priced through `experiments/phase0_headroom/configs/model_pricing.yaml`; missing usage, if any, is shown separately as the previous conservative fallback.

| Result prefix | Cells | Usage observed | Conservative USD | Observed-token USD | Observed-or-conservative USD | Missing usage | Median latency s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| codex_kilo_workspace | 20 | 0.7000 | 10.00000000 | 4.68420780 | 7.68420780 | 6 | 85.562 |
| codex_kilo_workspace_followup_smoke | 6 | 1.0000 | 3.00000000 | 1.53421560 | 1.53421560 | 0 | 54.188 |
| codex_kilo_workspace_followup | 20 | 1.0000 | 10.00000000 | 5.64126960 | 5.64126960 | 0 | 45.57 |
| kilo_completion_probe | 3 | 1.0000 | 1.50000000 | 0.61331400 | 0.61331400 | 0 | 19.065 |
| codex_kilo_workspace_stability | 20 | 1.0000 | 10.00000000 | 4.70140020 | 4.70140020 | 0 | 38.895 |
| humanize_pre_phase1_workspace | 8 | 1.0000 | 4.00000000 | 2.37855060 | 2.37855060 | 0 | 67.388 |
| phase1_validation_humanize_holdout_smoke | 4 | 1.0000 | 2.00000000 | 1.22347080 | 1.22347080 | 0 | 83.18 |
| phase1_validation_humanize_holdout | 12 | 1.0000 | 6.00000000 | 3.12707340 | 3.12707340 | 0 | 61.058 |
| phase1_validation_humanize_holdout_stability | 16 | 1.0000 | 8.00000000 | 4.12293300 | 4.12293300 | 0 | 48.897 |
| phase1_validation_boltons_paid_smoke | 8 | 0.8750 | 4.00000000 | 3.17627580 | 3.67627580 | 1 | 37.453 |
| phase1_validation_boltons_paid_extension | 6 | 1.0000 | 3.00000000 | 2.94453240 | 2.94453240 | 0 | 43.003 |
| phase1_future_holdout_b_eval | 8 | 1.0000 | 4.00000000 | 4.47608820 | 4.47608820 | 0 | 58.155 |
| phase1_future_holdout_h_future | 8 | 1.0000 | 4.00000000 | 4.86423240 | 4.86423240 | 0 | 57.154 |
| phase1_two_repo_future_holdout_attrs_b_eval | 8 | 1.0000 | 4.00000000 | 6.48330180 | 6.48330180 | 0 | 52.398 |
| phase1_two_repo_future_holdout_attrs_h_future | 8 | 1.0000 | 4.00000000 | 8.71208040 | 8.71208040 | 0 | 81.379 |
| phase1_statement_hardened_after_canonical_repair_attrs_b_eval | 8 | 1.0000 | 4.00000000 | 2.03351640 | 2.03351640 | 0 | 50.74 |
| phase1_statement_hardened_after_canonical_repair_attrs_h_future | 8 | 1.0000 | 4.00000000 | 3.54503700 | 3.54503700 | 0 | 86.239 |
| phase1_statement_hardened_after_canonical_repair_boltons_b_eval | 8 | 1.0000 | 4.00000000 | 2.53346760 | 2.53346760 | 0 | 69.148 |
| phase1_statement_hardened_after_canonical_repair_boltons_h_future | 8 | 1.0000 | 4.00000000 | 1.81149420 | 1.81149420 | 0 | 44.552 |
| phase1_three_repo_paid_validation_batch_1_smoke_codex_workspace | 3 | 1.0000 | 1.50000000 | 1.38578220 | 1.38578220 | 0 | 140.973 |
| phase1_three_repo_paid_validation_batch_1_smoke_kilo_workspace | 3 | 1.0000 | 1.50000000 | 0.61068000 | 0.61068000 | 0 | 32.418 |
| phase1_three_repo_paid_validation_batch_2_small_pilot_complete_codex_workspace | 15 | 1.0000 | 7.50000000 | 8.24846280 | 8.24846280 | 0 | 114.906 |
| phase1_three_repo_paid_validation_batch_2_small_pilot_complete_kilo_workspace | 15 | 1.0000 | 7.50000000 | 4.33731060 | 4.33731060 | 0 | 43.07 |
| phase1_three_repo_paid_validation_batch_3_attrs_remainder_codex_workspace | 14 | 1.0000 | 7.00000000 | 8.85764700 | 8.85764700 | 0 | 115.504 |
| phase1_three_repo_paid_validation_batch_3_attrs_remainder_kilo_workspace | 14 | 1.0000 | 7.00000000 | 5.06814420 | 5.06814420 | 0 | 60.419 |
| phase1_three_repo_paid_validation_batch_4_boltons_remainder_codex_workspace | 14 | 1.0000 | 7.00000000 | 6.89520720 | 6.89520720 | 0 | 94.404 |
| phase1_three_repo_paid_validation_batch_4_boltons_remainder_kilo_workspace | 14 | 1.0000 | 7.00000000 | 4.36723500 | 4.36723500 | 0 | 56.899 |
| phase1_three_repo_paid_validation_batch_5_click_remainder_codex_workspace | 14 | 1.0000 | 7.00000000 | 6.83599080 | 6.83599080 | 0 | 116.378 |
| phase1_three_repo_paid_validation_batch_5_click_remainder_kilo_workspace | 14 | 1.0000 | 7.00000000 | 4.66087320 | 4.66087320 | 0 | 48.77 |

## Per-Harness Observed Cost

### codex_kilo_workspace
- `codex_workspace`: `USD 3.67590780`.
- `kilo_workspace`: `USD 1.00830000`.
- Missing usage rows: `6`.

### codex_kilo_workspace_followup_smoke
- `codex_workspace`: `USD 0.90653460`.
- `kilo_workspace`: `USD 0.62768100`.

### codex_kilo_workspace_followup
- `codex_workspace`: `USD 2.93106060`.
- `kilo_workspace`: `USD 2.71020900`.

### kilo_completion_probe
- `kilo_workspace`: `USD 0.61331400`.

### codex_kilo_workspace_stability
- `codex_workspace`: `USD 2.51145480`.
- `kilo_workspace`: `USD 2.18994540`.

### humanize_pre_phase1_workspace
- `codex_workspace`: `USD 1.35034440`.
- `kilo_workspace`: `USD 1.02820620`.

### phase1_validation_humanize_holdout_smoke
- `codex_workspace`: `USD 0.68859360`.
- `kilo_workspace`: `USD 0.53487720`.

### phase1_validation_humanize_holdout
- `codex_workspace`: `USD 1.90032120`.
- `kilo_workspace`: `USD 1.22675220`.

### phase1_validation_humanize_holdout_stability
- `codex_workspace`: `USD 2.78837700`.
- `kilo_workspace`: `USD 1.33455600`.

### phase1_validation_boltons_paid_smoke
- `codex_workspace`: `USD 2.31634440`.
- `kilo_workspace`: `USD 0.85993140`.
- Missing usage rows: `1`.

### phase1_validation_boltons_paid_extension
- `codex_workspace`: `USD 1.89612180`.
- `kilo_workspace`: `USD 1.04841060`.

### phase1_future_holdout_b_eval
- `codex_workspace`: `USD 2.52736680`.
- `kilo_workspace`: `USD 1.94872140`.

### phase1_future_holdout_h_future
- `codex_workspace`: `USD 2.86099500`.
- `kilo_workspace`: `USD 2.00323740`.

### phase1_two_repo_future_holdout_attrs_b_eval
- `codex_workspace`: `USD 4.78243440`.
- `kilo_workspace`: `USD 1.70086740`.

### phase1_two_repo_future_holdout_attrs_h_future
- `codex_workspace`: `USD 4.57916100`.
- `kilo_workspace`: `USD 4.13291940`.

### phase1_statement_hardened_after_canonical_repair_attrs_b_eval
- `codex_workspace`: `USD 1.19963460`.
- `kilo_workspace`: `USD 0.83388180`.

### phase1_statement_hardened_after_canonical_repair_attrs_h_future
- `codex_workspace`: `USD 1.95904800`.
- `kilo_workspace`: `USD 1.58598900`.

### phase1_statement_hardened_after_canonical_repair_boltons_b_eval
- `codex_workspace`: `USD 1.38313680`.
- `kilo_workspace`: `USD 1.15033080`.

### phase1_statement_hardened_after_canonical_repair_boltons_h_future
- `codex_workspace`: `USD 1.17057180`.
- `kilo_workspace`: `USD 0.64092240`.

### phase1_three_repo_paid_validation_batch_1_smoke_codex_workspace
- `codex_workspace`: `USD 1.38578220`.

### phase1_three_repo_paid_validation_batch_1_smoke_kilo_workspace
- `kilo_workspace`: `USD 0.61068000`.

### phase1_three_repo_paid_validation_batch_2_small_pilot_complete_codex_workspace
- `codex_workspace`: `USD 8.24846280`.

### phase1_three_repo_paid_validation_batch_2_small_pilot_complete_kilo_workspace
- `kilo_workspace`: `USD 4.33731060`.

### phase1_three_repo_paid_validation_batch_3_attrs_remainder_codex_workspace
- `codex_workspace`: `USD 8.85764700`.

### phase1_three_repo_paid_validation_batch_3_attrs_remainder_kilo_workspace
- `kilo_workspace`: `USD 5.06814420`.

### phase1_three_repo_paid_validation_batch_4_boltons_remainder_codex_workspace
- `codex_workspace`: `USD 6.89520720`.

### phase1_three_repo_paid_validation_batch_4_boltons_remainder_kilo_workspace
- `kilo_workspace`: `USD 4.36723500`.

### phase1_three_repo_paid_validation_batch_5_click_remainder_codex_workspace
- `codex_workspace`: `USD 6.83599080`.

### phase1_three_repo_paid_validation_batch_5_click_remainder_kilo_workspace
- `kilo_workspace`: `USD 4.66087320`.

## Notes

- Kilo `part.cost == 0` rows from the OpenAI-compatible provider are preserved as reported cost but marked untrusted.
- Raw stdout, prompts, completions, patches, and workspaces remain in ignored paths and are not copied into this report or the ledger.
