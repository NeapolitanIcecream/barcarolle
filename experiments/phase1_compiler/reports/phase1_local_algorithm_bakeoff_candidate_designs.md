# Local Bakeoff Candidate Designs

Status: `pass`.

| Design | Kind | Tasks | Weight mode | Status |
| --- | --- | --- | --- | --- |
| repo_unweighted_same_budget | baseline_existing_unweighted | 16 | uniform | evaluated |
| repo_stratified_by_target_profile | baseline_existing_stratified | 16 | uniform | evaluated |
| seeded_random_same_budget | seeded_random_same_budget | 16 | uniform | evaluated |
| temporal_recent_baseline | temporal_recent_baseline | 16 | uniform | evaluated |
| coverage_constrained_unweighted | coverage_constrained_unweighted | 16 | uniform | evaluated |
| block_randomized_stratified | block_randomized_stratified | 16 | uniform | evaluated |
| old_weighted_target_profile | old_weighted_target_profile_reference | 16 | existing_pre_paid_release_weights | evaluated |
| block_plus_shrinkage_weighted | block_plus_shrinkage_weighted | 16 | capped_shrinkage_pending | evaluated |
| optional_block_plus_prior_difficulty | skipped_optional_prior_difficulty | 0 | not_applicable | skipped |

All evaluated candidate designs record empty `outcome_fields_used_for_selection`; the old weighted design is retained only as a baseline reference.
