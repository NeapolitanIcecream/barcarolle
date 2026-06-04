# Proposal Evidence Package Fallback Share

What happened: quantified labeled fallback behavior in the frozen candidate policy manifest.

Why it matters: M4 needs factual fallback share before it sets any fallback threshold or claim-narrowing rule.

Action suggested next: treat the current candidate as composite unless M4 repairs, thresholds, or narrows the fallback claim.

- Overall fallback share: `0.3333`.

| Repo | Selected | Fallback-selected | Fallback share | Fallback reason |
| --- | --- | --- | --- | --- |
| attrs | 6 | 0 | 0.0 | None |
| boltons | 6 | 6 | 1.0 | insufficient_feature_support |
| click | 6 | 0 | 0.0 | None |

Coverage gaps by repo/feature:
| Repo | Feature | Gap value count |
| --- | --- | --- |
| boltons | coarse_task_family | 7 |
| click | coarse_task_family | 2 |

Diagnostic sensitivity:
| Slice | Candidate MAE | Best deterministic baseline | Best MAE | Delta | Relation |
| --- | --- | --- | --- | --- | --- |
| including_all_repos | 0.209 | temporal_recent_baseline | 0.2149 | -0.0059 | candidate_better |
| excluding_fallback_repos | 0.233 | repo_stratified_by_target_profile | 0.2362 | -0.0032 | candidate_better |
| fallback_repos_only | 0.1611 | temporal_recent_baseline | 0.1472 | 0.0139 | candidate_worse |

Boundary:
- M3 does not set a fallback threshold.
- Sensitivity is diagnostic and does not change the frozen candidate policy.
