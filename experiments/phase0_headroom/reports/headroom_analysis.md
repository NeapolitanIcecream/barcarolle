# Phase 0 Headroom Analysis

Status: `measured_endpoint_matrix_a_complete`.

Matrix A uses the measured endpoint path with the current `gpt-5.4-mini` model. It reuses compatible calibration cells and adds the missing `toolz` cells plus the repaired Click `G_mini` comparator cells.

## Matrix Cells

| Task | Split | Terminal Status | Scoreable |
|---|---|---:|---:|
| `toolz__hist__001` | `B_real` | `invalid_output` | `False` |
| `toolz__hist__003` | `B_real` | `verified_fail` | `True` |
| `toolz__hist__004` | `W_real` | `verified_fail` | `True` |
| `toolz__hist__010` | `W_real` | `invalid_output` | `False` |
| `toolz__hist__002` | `B_real` | `invalid_output` | `False` |
| `toolz__hist__016` | `W_real` | `invalid_output` | `False` |
| `click__rbench__001` | `G_mini` | `invalid_output` | `False` |
| `click__rbench__002` | `G_mini` | `invalid_output` | `False` |
| `click__rbench__003` | `G_mini` | `invalid_output` | `False` |
| `click__rbench__004` | `G_mini` | `invalid_output` | `False` |

Predictive metrics remain `not_applicable_underpowered`; the run is a protocol and harness diagnostic, not a final predictive-validity estimate.
