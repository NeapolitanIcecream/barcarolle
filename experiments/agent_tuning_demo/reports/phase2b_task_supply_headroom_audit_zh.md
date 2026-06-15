# Agent Tuning Phase 2b task-supply and headroom audit

Generated at: `2026-06-15T03:20:26+00:00`.

Paid cells run in this package: `0`.

Readiness decision: `pass_time_ordered_single_window`.
Recommended Agent/surface: `kilo_gpt_5_4_mini` / `repo_AGENTS_md`.
Rolling-origin multi-window claim feasible now: `False`.
Time-ordered future validation feasible now: `True`.

## Candidate windows

| Window | Selected | Train | Dev | Future | Dev pass | Future pass | Paid cells | Decision |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltons_time_ordered_w1_train2015_2018_dev2019_2020_future2022_2023 | True | 10 | 6 | 10 | 0.6667 | 0.6 | 38 | best single-window default path: dev pass rate is inside target range and future Holdout pass rate is 6/10 |
| boltons_time_ordered_train12_dev4_future_holdout | False | 12 | 4 | 10 | 0.75 | 0.6 | 32 | rejected: dev baseline is above the preferred headroom range |
| boltons_time_ordered_train16_dev4_future_holdout | False | 16 | 4 | 10 | 1.0 | 0.6 | 32 | rejected: dev baseline is saturated after excluding an unscoreable row |

Future task IDs are not listed here; only counts, time ranges, and SHA-256 digests are committed before artifact freeze.

## Inventory notes

- `mahmoud/boltons` with Kilo low-cost has 20 Selection rows and 10 Holdout rows; Holdout baseline headroom is `6/10`.
- `python-attrs/attrs` and `click` have Phase 1 task supply and generic adapter evidence, but they are not selected for this paid path because the Phase 2 artifact-injection runner and Kilo AGENTS.md action preflight are prepared for the boltons package map.
- Limitation: Current Kilo low-cost boltons supply supports one strong time-ordered future-validation window, not a two-window rolling-origin claim. Later middle slices are saturated or too sparse.
