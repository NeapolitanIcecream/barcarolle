# Phase 0 Headroom Analysis

Status: `measured_endpoint_calibration_complete`.

The measured endpoint run replaces the earlier Codex-subscription cost estimate for Phase 0 calibration. It remains underpowered and diagnostic only.

## Calibration Cells

| Task | Split | Terminal Status | Scoreable |
|---|---|---:|---:|
| `toolz__hist__001` | `B_real` | `invalid_output` | `False` |
| `toolz__hist__003` | `B_real` | `verified_fail` | `True` |
| `toolz__hist__004` | `W_real` | `verified_fail` | `True` |
| `toolz__hist__010` | `W_real` | `invalid_output` | `False` |

Predictive metrics remain `not_applicable_underpowered` because `G_mini` is not same-protocol scoreable and the calibration matrix is small.
