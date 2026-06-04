# Validation Protocol

What happened: froze the future validation protocol before any future paid ACUT calls.

Why it matters: future results can be interpreted against preregistered baselines, metrics, adapter handling, and failure rules.

Action suggested next: adversarially review this protocol before authorizing any future paid validation.

Primary candidate: `coverage_constrained_unweighted_v1`.
Preferred study mode: `true_future_holdout`.
Fallback study mode: `preregistered_rolling_origin_or_pseudo_future_replay`.
Primary reporting: adapter-stratified MAE and catastrophic miss rate.
No paid run is authorized by this runbook.
