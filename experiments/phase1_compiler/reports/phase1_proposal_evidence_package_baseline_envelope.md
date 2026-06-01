# Proposal Evidence Package Baseline Envelope

What happened: compared the candidate against the best available simple comparator overall, by adapter, by repo, and by window.

Why it matters: M4 can harden success gates using slice-level baseline evidence rather than a single aggregate.

Action suggested next: keep adapter-level rows primary and treat pooled rows as secondary diagnostics.

| Group | Candidate MAE | Best baseline | Best baseline MAE | Candidate - baseline MAE | Relation | Evidence label |
| --- | --- | --- | --- | --- | --- | --- |
| overall:overall | 0.209 | temporal_recent_baseline | 0.2149 | -0.0059 | candidate_better | proposal_traction |
| adapter:codex_workspace | 0.267 | temporal_recent_baseline | 0.2417 | 0.0253 | candidate_worse | diagnostic_negative_evidence |
| adapter:kilo_workspace | 0.151 | repo_unweighted_same_budget | 0.1807 | -0.0297 | candidate_better | proposal_traction |
| repo:attrs | 0.1765 | repo_stratified_by_target_profile | 0.183 | -0.0065 | candidate_better | proposal_traction |
| repo:boltons | 0.1611 | temporal_recent_baseline | 0.1472 | 0.0139 | candidate_worse | diagnostic_negative_evidence |
| repo:click | 0.2894 | temporal_recent_baseline | 0.2339 | 0.0555 | candidate_worse | diagnostic_negative_evidence |
| window:blocked_split_heldout | 0.1611 | temporal_recent_baseline | 0.1056 | 0.0555 | candidate_worse | diagnostic_negative_evidence |
| window:original_three_repo_split_heldout | 0.157 | repo_stratified_by_target_profile | 0.1746 | -0.0176 | candidate_better | proposal_traction |
| window:repo_specific_earliest_time_bucket_cutoff | 0.3089 | temporal_recent_baseline | 0.3006 | 0.0083 | candidate_worse | diagnostic_negative_evidence |

Boundary:
- This envelope does not set a final success threshold.
- The random comparator uses the median seed summary for the envelope; the full distribution is reported separately.
