# Phase 1 Blocked Split Candidate Universe

## What Happened

Loaded only `experiments/phase1_compiler/results/phase1_source_context_statement_hardening_split_feature_table.json` and selected rows with `release_eligible_for_split_design=true`.
The candidate universe has 95 tasks: attrs=30, boltons=35, click=30.
Excluded rows: 58. Exclusion reasons: `{'ambiguous_scope': 1, 'missing_public_problem_context': 57}`.

No paid outcome files were loaded in this step. No pass/fail, adapter outcome, hidden verifier, raw trace, prompt, completion, raw diff, or test patch fields were used.

## Why It Matters

The redesign starts from source-hardening eligibility only. Blocked rows, diagnostic-only rows, and rows missing public context are not silently included.

Click remains eligible but caveated: every eligible click task has `source_context_type_bucket=title_only` and `source_quality_bucket=minor_risk`. That means click can be balanced within click, but it cannot support the same clean-source claim as attrs or boltons.

## What Action It Suggests Next

Use this 95-task universe to define deterministic block schema and feature-balance constraints. Keep repo as a hard stratum and keep click title-only minor risk explicit in every later gate.

## Visible Feature Counts

- Source quality: `{'clean': 65, 'minor_risk': 30}`
- Source context type: `{'issue_or_pr': 65, 'title_only': 30}`
- Statement specificity: `{'acceptable': 92, 'specific': 3}`
- Context length: `{'medium': 3, 'short': 30, 'unknown': 62}`
- Editable scope: `{'multi_module': 8, 'project_wide': 1, 'single_module': 86}`
- Time bucket: `{'legacy_2018_or_earlier': 28, 'middle_2019_2022': 38, 'recent_2023_or_later': 29}`
- Rare or unknown feature flag: `{'False': 94, 'True': 1}`
