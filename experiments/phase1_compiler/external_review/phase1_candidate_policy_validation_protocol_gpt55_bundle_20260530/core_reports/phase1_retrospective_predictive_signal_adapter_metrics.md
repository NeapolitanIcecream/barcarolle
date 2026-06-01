# Retrospective Predictive-Signal Adapter Metrics

What happened: computed B_eval-to-H_future prediction error separately for Codex and Kilo workspace adapters.

Why it matters: adapter differences are ACUT-configuration evidence, so the primary readout keeps them separate.

Action suggested next: compare candidates against simple baselines with uncertainty labels.

| Adapter | Design | Slices | MAE | RMSE | Catastrophic miss rate |
| --- | --- | --- | --- | --- | --- |
| codex_workspace | repo_unweighted_same_budget | 9 | 0.2677 | 0.316 | 0.5556 |
| codex_workspace | repo_stratified_by_target_profile | 9 | 0.2714 | 0.3175 | 0.5556 |
| codex_workspace | temporal_recent_baseline | 9 | 0.2417 | 0.2949 | 0.4444 |
| codex_workspace | seeded_random_same_budget | 45 | 0.2954 | 0.3377 | 0.7333 |
| codex_workspace | coverage_constrained_unweighted | 9 | 0.267 | 0.3159 | 0.5556 |
| codex_workspace | block_randomized_stratified | 9 | 0.3473 | 0.3816 | 0.7778 |
| codex_workspace | block_plus_shrinkage_weighted | 9 | 0.3423 | 0.3784 | 0.8889 |
| codex_workspace | completed_blocked_split_supplement | 3 | 0.1815 | 0.2007 | 0.3333 |
| kilo_workspace | repo_unweighted_same_budget | 9 | 0.1807 | 0.2097 | 0.7778 |
| kilo_workspace | repo_stratified_by_target_profile | 9 | 0.1973 | 0.2449 | 0.5556 |
| kilo_workspace | temporal_recent_baseline | 9 | 0.1881 | 0.2147 | 0.6667 |
| kilo_workspace | seeded_random_same_budget | 45 | 0.2095 | 0.2557 | 0.7333 |
| kilo_workspace | coverage_constrained_unweighted | 9 | 0.151 | 0.185 | 0.5556 |
| kilo_workspace | block_randomized_stratified | 9 | 0.2241 | 0.2568 | 0.7778 |
| kilo_workspace | block_plus_shrinkage_weighted | 9 | 0.2364 | 0.2594 | 0.7778 |
| kilo_workspace | completed_blocked_split_supplement | 3 | 0.1 | 0.1291 | 0.3333 |

Boundary:
- Adapter-level metrics are primary.
- Equal-mix pooled metrics are secondary diagnostics only.
- Known invalid-output sensitivity is labeled on affected slices, not coerced to pass or fail.
