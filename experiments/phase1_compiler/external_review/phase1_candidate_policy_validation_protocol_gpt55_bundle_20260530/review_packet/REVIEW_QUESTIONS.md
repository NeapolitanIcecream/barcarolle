# Review Questions

1. Is `coverage_constrained_unweighted_v1` a defensible near-term mainline candidate given the current evidence, or is it too close to a simple coverage heuristic to carry the Barcarolle compiler claim?
2. Does the proposed rolling-origin or future-holdout protocol actually test predictive validity, or does it still leave a post-hoc or transductive loophole?
3. Are the baselines strong enough, especially `temporal_recent_baseline`, `repo_unweighted_same_budget`, `repo_stratified_by_target_profile`, and seeded random same-budget?
4. Are the success criteria too weak, too strong, or vulnerable to a single repo or adapter driving the conclusion?
5. Does adapter-stratified reporting correctly treat Codex and Kilo as ACUT configurations rather than model-only comparisons?
6. Is the proposal narrative better stated as predictive benchmark compiler, auditable repo-specific benchmark construction with early predictive signal, or something narrower?
