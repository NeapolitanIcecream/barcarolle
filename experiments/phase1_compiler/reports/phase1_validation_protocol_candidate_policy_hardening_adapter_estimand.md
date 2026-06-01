# Adapter Estimand And Reporting Rule

Primary estimand: `per_named_acut_configuration`.

A claim for a named adapter requires that adapter to pass the joint gate. A cross-adapter claim requires every named adapter in scope to pass.

An equal-mixture pooled metric may be reported only as a preregistered secondary diagnostic; it cannot rescue a named-adapter failure.

| Adapter | Candidate MAE | Best baseline | Delta | Passes margin | Passes tolerance |
| --- | --- | --- | --- | --- | --- |
| codex_workspace | 0.267 | temporal_recent_baseline | 0.0253 | False | False |
| kilo_workspace | 0.151 | repo_unweighted_same_budget | -0.0297 | True | True |

M3 cross-adapter status: `fails_because_codex_does_not_pass_and_pooled_summary_is_secondary`.

M5 primary table:
- adapter-stratified baseline envelope with candidate, best baseline, MAE delta, catastrophic miss rate, fallback status, and support status by named ACUT configuration.

Boundary:
- Codex and Kilo are ACUT-configuration evidence; do not collapse differences into a model-only finding unless harness differences have been ruled out.
- Paid-validation authorization remains `false`.
