# Retrospective Predictive-Signal Window Plan

What happened: froze two held-out pseudo-future windows and one sparse time-cutoff diagnostic.

Why it matters: the primary analysis has enough held-out score coverage, while rolling-origin support is too thin for a formal claim.

Action suggested next: report pseudo-future signal and keep true rolling-origin as a future preregistration need.

| Window | Mode | Repo | B_eval pool | H_future pool | Status |
| --- | --- | --- | --- | --- | --- |
| blocked_split_heldout | retrospective_pseudo_future | attrs | 10 | 10 | accepted |
| blocked_split_heldout | retrospective_pseudo_future | boltons | 10 | 10 | accepted |
| blocked_split_heldout | retrospective_pseudo_future | click | 10 | 10 | accepted |
| original_three_repo_split_heldout | retrospective_pseudo_future | attrs | 16 | 15 | accepted |
| original_three_repo_split_heldout | retrospective_pseudo_future | boltons | 18 | 17 | accepted |
| original_three_repo_split_heldout | retrospective_pseudo_future | click | 15 | 15 | accepted |
| repo_specific_earliest_time_bucket_cutoff | true_rolling_origin_diagnostic | attrs | 4 | 26 | diagnostic_sparse |
| repo_specific_earliest_time_bucket_cutoff | true_rolling_origin_diagnostic | boltons | 24 | 11 | diagnostic_sparse |
| repo_specific_earliest_time_bucket_cutoff | true_rolling_origin_diagnostic | click | 4 | 26 | diagnostic_sparse |

Boundary:
- Terminal outcomes loaded before this plan: `false`.
- Primary mode: `retrospective_pseudo_future`.
- True rolling-origin support: `too_sparse_for_primary_claim`.
