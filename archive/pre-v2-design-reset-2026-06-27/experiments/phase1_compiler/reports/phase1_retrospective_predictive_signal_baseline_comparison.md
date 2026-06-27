# Retrospective Predictive-Signal Baseline Comparison

What happened: compared candidate MAE and catastrophic miss rate against simple baselines on overlapping slices.

Why it matters: the question is whether Barcarolle-style selection predicts held-out outcomes better than simple alternatives.

Action suggested next: treat any improvement as directional traction only unless a future run is preregistered.

Best simple baseline: `temporal_recent_baseline` with MAE `0.2149`.
Best Barcarolle candidate: `coverage_constrained_unweighted` with MAE `0.209`.
Best diagnostic candidate: `completed_blocked_split_supplement` with MAE `0.1407`.
Candidate beats best simple baseline: `True`.

| Design | MAE | Catastrophic miss rate | Slices |
| --- | --- | --- | --- |
| repo_stratified_by_target_profile | 0.2343 | 0.5556 | 18 |
| repo_unweighted_same_budget | 0.2242 | 0.6667 | 18 |
| temporal_recent_baseline | 0.2149 | 0.5556 | 18 |
| seeded_random_same_budget | 0.2525 | 0.7333 | 90 |
| coverage_constrained_unweighted | 0.209 | 0.5556 | 18 |
| block_randomized_stratified | 0.2857 | 0.7778 | 18 |
| block_plus_shrinkage_weighted | 0.2894 | 0.8333 | 18 |
| completed_blocked_split_supplement | 0.1407 | 0.3333 | 6 |
