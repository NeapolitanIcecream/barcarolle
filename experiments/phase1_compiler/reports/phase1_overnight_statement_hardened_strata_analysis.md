# Statement-Hardened Strata Analysis

Pooled B_eval to H_future gap: `0.3125`.
Repo gaps: `{'attrs': 0.25, 'boltons': 0.375}`.
H_future drop same direction across attrs and boltons: `True`.

The strongest plausible explanation is future-holdout hardness with time-window and task-family shift under small-N evidence. The main uncertainty is that statement source, task family, and time are confounded in the small boltons H_future slice.

## Repo/Split Strata

| Repo split | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| attrs/B_eval | 8 | 4 | 6 | 2 | 0.75 |
| attrs/H_future | 8 | 4 | 4 | 4 | 0.5 |
| boltons/B_eval | 8 | 4 | 7 | 1 | 0.875 |
| boltons/H_future | 8 | 4 | 4 | 4 | 0.5 |

## Adapter Strata

| Adapter | Cells | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- |
| codex_workspace | 16 | 11 | 5 | 0.6875 |
| kilo_workspace | 16 | 10 | 6 | 0.625 |

## Task Family Strata

| Family | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| attrs:attr._make | 10 | 5 | 6 | 4 | 0.6 |
| attrs:attr._next_gen | 2 | 1 | 0 | 2 | 0.0 |
| attrs:attr:multi_file | 4 | 2 | 4 | 0 | 1.0 |
| boltons:boltons.cacheutils | 2 | 1 | 0 | 2 | 0.0 |
| boltons:boltons.iterutils | 6 | 3 | 3 | 3 | 0.5 |
| boltons:boltons.setutils | 4 | 2 | 4 | 0 | 1.0 |
| boltons:boltons.tbutils | 2 | 1 | 2 | 0 | 1.0 |
| boltons:boltons.timeutils | 2 | 1 | 2 | 0 | 1.0 |

## Statement Source Strata

| Statement source | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| new_codex_loop | 8 | 4 | 3 | 5 | 0.375 |
| reused_codex_loop | 24 | 12 | 18 | 6 | 0.75 |

## Source Kind Strata

| Source kind | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| issue | 18 | 9 | 16 | 2 | 0.8889 |
| pull_request | 14 | 7 | 5 | 9 | 0.3571 |

## Time Bucket Strata

| Time bucket | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| 2020H1 | 14 | 7 | 11 | 3 | 0.7857 |
| 2020H2 | 6 | 3 | 2 | 4 | 0.3333 |
| 2021H1 | 4 | 2 | 4 | 0 | 1.0 |
| 2022H2 | 2 | 1 | 2 | 0 | 1.0 |
| 2023H1 | 4 | 2 | 2 | 2 | 0.5 |
| 2023H2 | 2 | 1 | 0 | 2 | 0.0 |

## File Count Strata

| Implementation files | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| 1 | 28 | 14 | 17 | 11 | 0.6071 |
| 2 | 2 | 1 | 2 | 0 | 1.0 |
| 3 | 2 | 1 | 2 | 0 | 1.0 |
| Test files | Cells | Tasks | Pass | Fail | Pass rate |
| --- | --- | --- | --- | --- | --- |
| 1 | 30 | 15 | 19 | 11 | 0.6333 |
| 2 | 2 | 1 | 2 | 0 | 1.0 |

## Split Repair Check

- manifest_status: `frozen`.
- inventory_current_split_used_for_selection: `False`.
- manifest_selected_counts: `{'attrs/B_eval': 4, 'attrs/H_future': 4, 'boltons/B_eval': 4, 'boltons/H_future': 4}`.
- old_mapping_bug_reintroduced: `False`.
