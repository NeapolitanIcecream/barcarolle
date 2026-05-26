# Phase 1 Pre-Paid Replication Strata Matching

Recommended design: `barcarolle_weighted_time_family_matched`.

| Design | Mean L1 to target | B/H metadata gap | Post hoc calibrated |
| --- | --- | --- | --- |
| barcarolle_weighted_time_family_matched | 0.583 | 0.1875 | False |
| repo_stratified_by_target_profile | 0.6903 | 0.4688 | False |
| repo_unweighted_same_budget | 0.7701 | 0.8125 | False |

Selection uses pre-outcome metadata only; historical paid terminal outcomes are excluded from new release selection.
