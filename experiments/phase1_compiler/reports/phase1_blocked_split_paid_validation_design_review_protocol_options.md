# Blocked Split Validation Protocol Options

Status: `complete`.

## What Happened

Five validation protocols were compared under the exploratory claim policy.

## Why It Matters

The selected protocol controls what Barcarolle can honestly claim from reused and future paid cells.

## What Action It Suggests Next

Recommended option: `B`.

## Options

### Option A: `retrospective_only_no_new_paid_cells`

- New paid cells: `0`.
- Reused cells: `72`.
- Total scoreable cells after protocol: `72`.
- Claim boundary: `retrospective_sanity_check_only`.
- Recommendation status: `not_recommended`.
- Click status: `visible_title_only_minor_risk`.

### Option B: `same_budget_missing_cell_supplement`

- New paid cells: `48`.
- Reused cells: `72`.
- Total scoreable cells after protocol: `120`.
- Claim boundary: `exploratory_supplemental_validation_for_post_hoc_blocked_split`.
- Recommendation status: `recommended`.
- Click status: `visible_title_only_minor_risk`.

### Option C: `same_budget_full_rerun`

- New paid cells: `120`.
- Reused cells: `0`.
- Total scoreable cells after protocol: `120`.
- Claim boundary: `cleaner_exploratory_validation_after_blocked_split_freeze`.
- Recommendation status: `acceptable_secondary`.
- Click status: `visible_title_only_minor_risk`.

### Option D: `expanded_full_rerun`

- New paid cells: `180`.
- Reused cells: `0`.
- Total scoreable cells after protocol: `180`.
- Claim boundary: `higher_coverage_exploratory_validation_after_blocked_split_freeze`.
- Recommendation status: `acceptable_secondary`.
- Click status: `visible_title_only_minor_risk`.

### Option E: `stop_for_source_repair_or_third_repo_replacement`

- New paid cells: `0`.
- Reused cells: `0`.
- Total scoreable cells after protocol: `0`.
- Claim boundary: `no_paid_validation_until_click_risk_or_repo_mix_changes`.
- Recommendation status: `not_recommended`.
- Click status: `treated_as_blocker_for_this_option`.

No option claims predictive validity. Adapter-level reporting remains required before pooled summaries.
