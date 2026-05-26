# Phase 1 Pre-Paid Replication Threshold Preregistration

Threshold version: `phase1_pre_paid_replication_thresholds_20260526`.

Primary rule: `For each preregistered repo or repo-family stratum, abs(B_eval_predicted_pass_rate - H_future_observed_pass_rate) <= 0.15.`

Primary gates are scoreability, zero policy/harness/invalid-output violations, and preregistered precision labeling.

Previous paid evidence may motivate this threshold and local redesign, but it cannot validate this redesigned release or make the design look prospectively chosen.

H_future is validation data, not the target profile.
