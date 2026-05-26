# Phase 1 Pre-Paid Replication Decision

Final decision: `ready_for_pilot_paid_replication`.

Primary release candidate: `barcarolle_weighted_time_family_matched`.
Baselines: `repo_unweighted_same_budget`, `repo_stratified_by_target_profile`, `prior_statement_hardened_release_as_historical_reference`.

No paid ACUT replication was run. No paid LLM statement-prep calls were made.

## Research Questions

- `RQ1`: The next replication uses a preregistered per-repo or repo-family absolute predictive gap threshold of <= 0.15, with 100% scoreability or preregistered non-scoreable handling, zero policy/harness/invalid-output violations, and Wilson or beta-binomial precision labels.
- `RQ2`: The target profile for attrs and boltons is estimated from pre-holdout metadata: task time, module, source kind, implementation/test file counts, task family, statement/source surface features, and candidate-pool metadata. H_future pass/fail outcomes are explicitly excluded.
- `RQ3`: The prior mismatch is explained by time-window, task-family/module, source-kind, and statement-source differences. The next release matches and weights those strata before paid validation and labels sparse strata insufficient.
- `RQ4`: attrs and boltons local reservoirs are usable for a two-repo pilot after excluding already-paid tasks. humanize, itsdangerous, and toolz remain excluded from this paid candidate pool until a third-repo target profile and source/provenance hardening are preregistered.
- `RQ5`: The frozen primary candidate is barcarolle_weighted_time_family_matched. Baselines are repo_unweighted_same_budget, repo_stratified_by_target_profile, and prior_statement_hardened_release_as_historical_reference.
- `RQ6`: The final state is ready for pilot paid replication, not precision-target replication. The main remaining risk is underpowered precision/sparse strata, not statement quality or policy readiness.

## Closeout

The package is pilot-grade ready. Precision-target predictive validity remains underpowered and must not be claimed from this package alone.
