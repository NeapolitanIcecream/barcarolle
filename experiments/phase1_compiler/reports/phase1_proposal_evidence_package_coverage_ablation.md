# Proposal Evidence Package Coverage Ablation

What happened: compared the coverage candidate against unweighted, stratified, temporal, and many-seed random baselines.

Why it matters: this tests whether the coverage objective adds traction beyond simple heuristics, while preserving limitations.

Action suggested next: M4 should decide whether the limited ablation is enough for candidate-policy hardening or whether a factorial selector family is needed later.

| Component | Role | MAE | Miss rate | Candidate - comparator MAE | Interpretation |
| --- | --- | --- | --- | --- | --- |
| coverage_constrained_unweighted | candidate_score_comparison | 0.209 | 0.5556 | 0.0 | reference candidate in the retrospective score-join artifacts |
| repo_unweighted_same_budget | deterministic_simple | 0.2242 | 0.6667 | -0.0152 | candidate_better |
| repo_stratified_by_target_profile | deterministic_simple | 0.2343 | 0.5556 | -0.0253 | candidate_better |
| temporal_recent_baseline | deterministic_simple | 0.2149 | 0.5556 | -0.0059 | candidate_better |
| many_seed_random_same_budget | many_seed_random_distribution_median | 0.2464 | 0.6667 | -0.0374 | candidate_better |

Adapter diagnostics:
| Adapter | Candidate MAE | Best baseline | Best baseline MAE | Delta | Relation |
| --- | --- | --- | --- | --- | --- |
| codex_workspace | 0.267 | temporal_recent_baseline | 0.2417 | 0.0253 | candidate_worse |
| kilo_workspace | 0.151 | repo_unweighted_same_budget | 0.1807 | -0.0297 | candidate_better |

Limitation:

Current artifacts compare whole selector designs. They do not isolate coverage, unweighted budgeting, fallback, and temporal recency as orthogonal randomized factors.
