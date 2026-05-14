# Repository-Local Benchmark Admission

Status: `repository_admission_completed`
Generated at: `2026-05-14T14:25:54.936281Z`

## Split

- T0: `2026-05-14`
- C/calibration: `<= 2025-11-13`
- R/repository benchmark: `2025-11-14` to `2026-02-13`
- W*/criterion work set: `2026-02-14` to `2026-05-14`
- If task supply is thin, only C/R may extend earlier; W* must stay recent.

## Repository Summary

| Repo | Ready | Strict R design | Extended R design | W* design | W* direct oracle | W* families | Notes |
|---|---:|---:|---:|---:|---:|---:|---|
| `click` | `False` | 2 | 53 | 14 | 11 | 4 | w_star_task_design_candidate_count_below_20, strict_r_window_needs_allowed_earlier_extension |
| `rich` | `True` | 47 | 74 | 25 | 9 | 5 | none |
| `black` | `False` | 20 | 46 | 16 | 12 | 4 | w_star_task_design_candidate_count_below_20 |

## Recommendation

- Primary repo: `None`
- Recommended execution repo: `rich`
- Replication repo: `rich`
- Fallback replication repo: `None`

## Boundary

This scan does not admit tasks and does not run models. It checks whether repositories have enough history to justify task admission under the C/R/W* design, separating direct oracle candidates from source-only task-design candidates.
