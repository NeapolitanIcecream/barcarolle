# Proposal Evidence Package Random Baseline Distribution

What happened: generated a deterministic many-seed same-budget random baseline distribution from the existing retrospective universe and committed score tables.

Why it matters: the candidate is compared against a distribution, not only the earlier five-seed random summary.

Action suggested next: use this as traction evidence and as M4 input; it does not establish predictive validity.

- Seed count: `1000`.
- Seed start: `2026060101`.
- Candidate design used for score comparison: `coverage_constrained_unweighted`.
- Candidate policy object for proposal wording: `coverage_constrained_unweighted_v1_with_labeled_fallbacks`.

| Group | Candidate MAE | Random median MAE | Random p05 MAE | Random p95 MAE | Candidate beats/random-ties share % | Miss-rate beats/random-ties share % |
| --- | --- | --- | --- | --- | --- | --- |
| overall:overall | 0.209 | 0.2464 | 0.2056 | 0.2899 | 93.4 | 96.7 |
| adapter:codex_workspace | 0.267 | 0.2917 | 0.2454 | 0.3491 | 80.3 | 98.2 |
| adapter:kilo_workspace | 0.151 | 0.1992 | 0.1399 | 0.2623 | 90.8 | 92.3 |
| repo:attrs | 0.1765 | 0.2553 | 0.1876 | 0.3497 | 98.4 | 100.0 |
| repo:boltons | 0.1611 | 0.1806 | 0.1195 | 0.264 | 68.6 | 74.1 |
| repo:click | 0.2894 | 0.2894 | 0.2339 | 0.3728 | 70.3 | 80.3 |
| window:blocked_split_heldout | 0.1611 | 0.1611 | 0.0944 | 0.2339 | 54.8 | 71.2 |
| window:original_three_repo_split_heldout | 0.157 | 0.2524 | 0.1691 | 0.3497 | 98.2 | 100.0 |
| window:repo_specific_earliest_time_bucket_cutoff | 0.3089 | 0.3089 | 0.2867 | 0.376 | 60.2 | 70.2 |

Boundary:
- Lower MAE and catastrophic miss rate are better.
- Percentiles are descriptive retrospective traction only.
- No paid calls or external review calls were made.
