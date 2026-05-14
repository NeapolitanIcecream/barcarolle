# Rich Task-Admission Readiness

Status: `rich_task_admission_readiness_completed`
Generated at: `2026-05-14T17:29:39.679248Z`

## Scan Boundary

- This scan deduplicates commits by normalized subject before counting task-design rows.
- Direct smoke-ready requires source changes, test changes, and extractable pytest nodes from the target diff.
- Source-only rows remain task-design candidates, but require Golden-Oracle verifier construction before admission.
- C is scanned from `2025-04-14` to `2025-11-13`; older C can still be used if calibration supply is thin.

## Summary

| Window | Design candidates | Direct smoke-ready | Source-only needing Golden-Oracle | Direct tests without nodes | Families | 40-pool gap |
|---|---:|---:|---:|---:|---:|---:|
| `C` | 20 | 6 | 13 | 1 | 6 | 20 |
| `R` | 37 | 12 | 25 | 0 | 6 | 3 |
| `W_star` | 23 | 8 | 14 | 1 | 5 | 17 |

## Verdict

- R has 20-primary design supply: `True`
- R has 40-candidate pool supply: `False`
- W* has 20-primary design supply: `True`
- W* has 20-primary plus 5-reserve design supply: `False`
- W* has 40-candidate pool supply: `False`
- W* direct smoke-ready candidates: `8`
- W* Golden-Oracle candidates needed for 20 primary: `12`
- W* Golden-Oracle candidates needed for 20 primary + 5 reserve: `17`

Primary R/W* model attempts remain unauthorized. This readiness scan does not run no-op/reference smoke.
