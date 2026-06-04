# Validation Protocol Claim Modes

What happened: M4 separates future validation modes from retrospective replay.

Why it matters: the same numeric table can support different claims depending on when the policy, baselines, seeds, and outcomes were frozen.

| Mode | Can claim | Cannot claim | Freeze artifact |
| --- | --- | --- | --- |
| true_future_holdout | Predictive-validity evidence for the named scope only if every frozen gate passes. | Cannot generalize beyond named repos, adapters, task supply, source reservoirs, and release schema. | benchmark release manifest plus protocol freeze JSON committed before future outcomes are collected or joined |
| preregistered_rolling_origin | Predictive-validity evidence for preregistered cutoffs only when candidate, baselines, seeds, estimand, invalid-cell handling, support thresholds, and gate are frozen before outcomes are joined. | Cannot use cutoffs chosen after seeing joined outcomes; cannot hide failed cutoffs in a pooled-only summary. | rolling-origin preregistration manifest with outcome-blind digest and seed list |
| pseudo_future_replay | Traction, debugging, and protocol stress-testing. | Cannot carry the north-star validity claim because outcomes or outcome-derived design choices may already be visible. | retrospective replay manifest and traction-only report |
| current_m3_retrospective_evidence | Proposal traction: candidate MAE was 0.209 versus 0.2149 for the best simple aggregate baseline, with visible limitations. | Cannot be treated as current predictive-validity evidence or as a paid-readiness result. | phase1_proposal_evidence_package_decision.json and M3 supporting reports |

M3 interpretation:
- Label: `traction_only`.
- Candidate MAE: `0.209`.
- Best simple baseline: `temporal_recent_baseline` at MAE `0.2149`.
- Delta: `-0.0059`.

Boundary:
- Pseudo-future replay supports traction and debugging only.
- The north-star claim remains future work.
- Paid-validation authorization remains `false`.
