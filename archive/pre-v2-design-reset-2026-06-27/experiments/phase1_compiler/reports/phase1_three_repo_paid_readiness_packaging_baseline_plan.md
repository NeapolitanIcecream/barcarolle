# Three-Repo Baseline Plan

What happened: the primary design, baselines, and diagnostics were frozen before paid outcomes.

Why it matters: old weighted scoring must not become the main claim after seeing outcomes.

Primary design: `repo_stratified`.

Frozen comparators:
- `repo_unweighted_same_budget`: baseline.
- `repo_stratified_same_budget`: baseline.
- `temporal_recent_baseline`: baseline.
- `block_randomized_stratified_candidate`: secondary.
- `old_weighted_design`: diagnostic_only.

Old weighted design primary: `False`.
Post-hoc promotion rule: `none`.
