# Phase 0 Headroom Analysis

Status: `scored_underpowered`.

This matrix is underpowered directional evidence only. It uses one ACUT, six certified `toolz` same-repo tasks, and no same-protocol `G_mini` cells.

## Split Metrics

| Split | Cells | Scoreable | Pass | Fail | Pass Rate |
|---|---:|---:|---:|---:|---:|
| `B_real` | `3` | `3` | `1` | `2` | `0.3333` |
| `W_real` | `3` | `3` | `1` | `2` | `0.3333` |

## Cell Outcomes

| Task | Split | Terminal Status | Scoreable |
|---|---|---:|---:|
| `toolz__hist__001` | `B_real` | `verified_fail` | `True` |
| `toolz__hist__002` | `B_real` | `verified_fail` | `True` |
| `toolz__hist__003` | `B_real` | `verified_pass` | `True` |
| `toolz__hist__004` | `W_real` | `verified_fail` | `True` |
| `toolz__hist__010` | `W_real` | `verified_pass` | `True` |
| `toolz__hist__016` | `W_real` | `verified_fail` | `True` |

MAE, RMSE, Brier score, and residual-style predictive metrics are `not_applicable_underpowered` for a one-ACUT matrix.
