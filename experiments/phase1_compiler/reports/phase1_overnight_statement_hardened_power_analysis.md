# Statement-Hardened Power Analysis

The current 16 cells per split have useful scoreability evidence but are underpowered for a 0.15 predictive gap rule; adapter correlation makes the effective sample closer to tasks than cells.

Cells per split needed for approximate 0.15 half-width: `78`.
Recommended minimum task-level tasks per split: `40`.

## Designs

| Design | Repos | Tasks/repo/split | Adapters | Cells/split | Approx 95 half-width | Power for 0.30 gap | Meets 0.15 precision |
| --- | --- | --- | --- | --- | --- | --- | --- |
| current_design | 2 | 4 | 2 | 16 | 0.3305 | 0.4244 | False |
| expanded_tasks | 2 | 8 | 2 | 32 | 0.2337 | 0.7209 | False |
| expanded_repos | 3 | 4 | 2 | 24 | 0.2699 | 0.5912 | False |
| expanded_repos_and_tasks | 3 | 8 | 2 | 48 | 0.1908 | 0.8812 | False |
| single_adapter_current | 2 | 4 | 1 | 8 | 0.4674 | 0.2301 | False |
| adapter_averaged_current_task_units | 2 | 4 | 1 | 8 | 0.4674 | 0.2301 | False |
