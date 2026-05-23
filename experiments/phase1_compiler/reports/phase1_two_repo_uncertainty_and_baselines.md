# Phase 1 Two-Repo Uncertainty And Baselines

Generated: `2026-05-23T11:30:46+00:00`.

## Wilson Intervals

| Group | Pass/scoreable | Pass rate | Wilson 95% interval |
|---|---:|---:|---:|
| `pooled_b_eval` | `14/16` | `0.875000` | `[0.639772, 0.965023]` |
| `pooled_h_future` | `8/15` | `0.533333` | `[0.301170, 0.751905]` |
| `boltons_b_eval` | `7/8` | `0.875000` | `[0.529112, 0.977583]` |
| `boltons_h_future` | `7/8` | `0.875000` | `[0.529112, 0.977583]` |
| `attrs_b_eval` | `7/8` | `0.875000` | `[0.529112, 0.977583]` |
| `attrs_h_future` | `1/7` | `0.142857` | `[0.025680, 0.513128]` |
| `codex_workspace_b_eval` | `7/8` | `0.875000` | `[0.529112, 0.977583]` |
| `codex_workspace_h_future` | `3/8` | `0.375000` | `[0.136844, 0.694258]` |
| `kilo_workspace_b_eval` | `7/8` | `0.875000` | `[0.529112, 0.977583]` |
| `kilo_workspace_h_future` | `5/7` | `0.714286` | `[0.358934, 0.917781]` |

## Baseline Errors

- Pooled B_eval to pooled H_future absolute error: `0.341667`.
- Repo-specific B_eval to same-repo H_future MAE: `0.366071`.
- Adapter-specific B_eval to same-adapter H_future MAE: `0.330357`.
- Unweighted all-B_eval predictor to H_future repo/adapter MAE: `0.416667`.
- Preserved preregistered pooled MAE: `0.479167`.

## Interpretation

The pilot is both negative and underpowered. The point estimates do not
support predictive validity: pooled B_eval overpredicts pooled H_future,
and attrs B_eval badly overpredicts attrs H_future. At the same time, the
sample has only two repos and 15 H_future scoreable cells, so the Wilson
intervals remain wide. The policy violation remains non-scoreable and
predictive validity remains `false`.
