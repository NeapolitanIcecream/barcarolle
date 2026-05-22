# Workspace Cost Usage Report

Generated at `2026-05-22T11:17:52+00:00`.

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

## Notes

- Kilo `part.cost == 0` rows from the OpenAI-compatible provider are preserved as reported cost but marked untrusted.
- Raw stdout, prompts, completions, patches, and workspaces remain in ignored paths and are not copied into this report or the ledger.
