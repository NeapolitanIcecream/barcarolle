# Workspace Cost Usage Report

Generated at `2026-05-21T12:18:20+00:00`.

Provider-billed dollars remain unavailable for these workspace ACUT runs. The canonical spend estimate is therefore the observed-token estimate priced through `experiments/phase0_headroom/configs/model_pricing.yaml`; missing usage, if any, is shown separately as the previous conservative fallback.

| Result prefix | Cells | Usage observed | Conservative USD | Observed-token USD | Observed-or-conservative USD | Missing usage | Median latency s |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| codex_kilo_workspace | 20 | 0.7000 | 10.00000000 | 4.68420780 | 7.68420780 | 6 | 85.562 |
| codex_kilo_workspace_followup_smoke | 6 | 1.0000 | 3.00000000 | 1.53421560 | 1.53421560 | 0 | 54.188 |
| codex_kilo_workspace_followup | 20 | 1.0000 | 10.00000000 | 5.64126960 | 5.64126960 | 0 | 45.57 |
| kilo_completion_probe | 3 | 1.0000 | 1.50000000 | 0.61331400 | 0.61331400 | 0 | 19.065 |
| codex_kilo_workspace_stability | 20 | 1.0000 | 10.00000000 | 4.70140020 | 4.70140020 | 0 | 38.895 |
| humanize_pre_phase1_workspace | 4 | 1.0000 | 2.00000000 | 0.97443360 | 0.97443360 | 0 | 67.388 |

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
- `codex_workspace`: `USD 0.59868480`.
- `kilo_workspace`: `USD 0.37574880`.

## Notes

- Kilo `part.cost == 0` rows from the OpenAI-compatible provider are preserved as reported cost but marked untrusted.
- Raw stdout, prompts, completions, patches, and workspaces remain in ignored paths and are not copied into this report or the ledger.
