# Quantitative Support Thresholds

| Threshold | Value | Supports | Blocks if not met |
| --- | --- | --- | --- |
| minimum_repos | `{"broader_method_claim": 5, "narrow_target_repo_claim": 3}` | Narrow multi-repo validation if at least three repos pass; broader method claims need more independent repos. | Primary predictive-validity claim for the intended scope. |
| future_tasks_per_repo | 20 | Enough H_future support to estimate future target-repo performance beyond six selected tasks. | Primary claim for a repo with sparse future outcomes. |
| candidate_pool_support | at least 2x selected budget per repo after source-quality filters | Outcome-blind selection with meaningful alternatives. | Coverage-policy claim for that repo; route to repair or narrowing. |
| named_acut_configurations | 2 | Cross-adapter claim if every named configuration passes. | Adapter-general wording; one adapter can support only adapter-specific wording. |
| rolling_origin_cutoffs | 2 | Rolling-origin claim with temporal replication. | Rolling-origin claim; true-future holdout may still proceed if separately frozen. |
| fallback_share | `{"overall_max": 0.1, "per_repo_max": 0.1667}` | Primary coverage-policy claim without composite-selector caveat. | Primary coverage-policy wording; report composite selector or repair support. |
| invalid_non_scoreable_share | `{"invalid_overall_max": 0.02, "non_scoreable_overall_max": 0.1, "non_scoreable_slice_max": 0.15}` | Stable primary metrics and sensitivity analysis. | Primary claim unless rerun/repair is preregistered and completed. |
| independent_source_reservoirs | 2 | Source-mix claim and reduced single-reservoir overfitting risk. | Source-quality or source-diversity claim for affected repo. |
| source_quality_certification_fields | provenance digest, license status, oracle-source type, leakage check, environment status, statement digest | Release auditability and hidden-oracle protection. | Release inclusion for the affected task. |

Current M3 status:
- Blocks primary future claim: `True`.
- Reasons:
  - retrospective replay
  - fallback caps fail
  - adapter/repo support is fragile

Boundary:
- Staffing, duration, and any paid budget ceiling remain user-owned decisions.
- Paid-validation authorization remains `false`.
