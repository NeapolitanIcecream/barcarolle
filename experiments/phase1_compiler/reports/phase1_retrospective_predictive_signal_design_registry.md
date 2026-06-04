# Retrospective Predictive-Signal Design Registry

What happened: registered required baselines, candidates, negative controls, and diagnostic designs before score outcomes were joined.

Why it matters: no task selection, weight, seed, cutoff, or design inclusion can move after outcomes are loaded.

Action suggested next: join committed score tables against the frozen selections.

| Design | Role | Claim boundary | Seeds |
| --- | --- | --- | --- |
| repo_unweighted_same_budget | baseline | eligible_for_exploratory_comparison | deterministic |
| repo_stratified_by_target_profile | baseline | eligible_for_exploratory_comparison | deterministic |
| temporal_recent_baseline | baseline | eligible_for_exploratory_comparison | deterministic |
| seeded_random_same_budget | baseline | eligible_for_exploratory_comparison | 2026053001,2026053002,2026053003,2026053004,2026053005 |
| coverage_constrained_unweighted | candidate | eligible_for_exploratory_comparison | deterministic |
| block_randomized_stratified | candidate | eligible_for_exploratory_comparison | deterministic |
| block_plus_shrinkage_weighted | candidate | eligible_for_exploratory_comparison | deterministic |
| old_weighted_target_profile | negative_control | reference_only_not_promotable | deterministic |
| completed_blocked_split_supplement | diagnostic | diagnostic_only_post_hoc | deterministic |

Freeze summary:
- Selection rows: `117`.
- Selected rows: `102`.
- Outcome fields used for selection: `[]`.
- Completed blocked split supplement is diagnostic only.
- Old weighted target-profile is reference-only and not promotable.
