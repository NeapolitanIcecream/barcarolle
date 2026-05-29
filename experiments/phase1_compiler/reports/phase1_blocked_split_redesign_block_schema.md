# Phase 1 Blocked Split Block Schema

## What Happened

Defined deterministic, within-repo blocks of size 2. Each block assigns one task to `B_eval` and one task to `H_future`.
Budgets evaluated locally: `['same_budget_20_per_repo', 'expanded_30_per_repo']`.
`same_budget_20_per_repo` feasible: `True`.
`expanded_30_per_repo` feasible: `True`.

## Why It Matters

The schema names the visible features that can influence split selection before any paid outcomes are read. Repo remains a hard stratum, so attrs, boltons, and click are balanced separately rather than hidden inside a cross-repo average.

Click is a required caveat. Click tasks stay eligible, but their source context is title-only and their source quality is `minor_risk`; this must remain visible in reports and gates.

## What Action It Suggests Next

Generate seeded candidate splits under this schema and choose by feature-imbalance score only. Do not load paid score tables until the selected split is frozen.

## Selection Inputs

- Allowed visible features: `['source_context_type_bucket', 'source_quality_bucket', 'statement_specificity_bucket', 'context_length_bucket', 'editable_scope_bucket', 'ambiguity_risk_bucket', 'leakage_risk_bucket', 'certification_risk_bucket', 'coarse_task_family', 'time_bucket', 'rare_or_unknown_feature_flag']`
- Blocking priority: `['source_quality_bucket', 'source_context_type_bucket', 'coarse_task_family', 'time_bucket', 'editable_scope_bucket']`
- Hard constraints: `{'repo_count_balance': 'exact', 'split_count_per_repo': 'exact', 'duplicate_task_ids': 'prohibited', 'non_eligible_task_selected': 'prohibited', 'blocked_source_quality_selected': 'prohibited', 'diagnostic_only_source_quality_selected': 'prohibited', 'missing_selected_seed': 'prohibited', 'unstable_deterministic_order': 'prohibited', 'outcome_fields_loaded_before_freeze': 'prohibited'}`
- Soft penalty weights: `{'coarse_task_family': 5, 'time_bucket': 4, 'editable_scope_bucket': 3, 'statement_specificity_bucket': 2, 'rare_or_unknown_feature_flag': 5, 'context_length_bucket': 1}`
