# Boltons no-paid generator capacity audit

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Summary

| Metric | Value |
| --- | --- |
| V2 raw candidates | 233 |
| Existing no-paid attempts | 80 |
| Gross release-eligible from attempts | 35 |
| Incremental release-eligible excluding current release commits | 22 |
| Technical-certified but source-context repair needed | 7 |
| Cap-deferred commit-message-only candidates | 100 |
| Conservative projected boltons release tasks | 57 |

The existing v2 generator can mine boltons anchors, but the near-term release-eligible increment is modest. The committed no-paid certification wave already attempted `80` boltons candidates. It found `35` gross release-eligible rows, but only `22` are incremental after excluding current release-table commits.

## Reservoir Split

Classification counts: `{'already_used_in_phase2b_scoreable_pool': 30, 'attempted_not_certified_collect_failed': 5, 'attempted_not_certified_install_failed': 5, 'attempted_not_certified_noop_assert_failed': 10, 'attempted_not_certified_reference_assert_failed': 9, 'blocked_missing_oracle_or_changed_tests': 32, 'blocked_source_context_leakage_risk': 8, 'new_release_eligible_from_no_paid_dry_run': 22, 'previously_certified_but_unused_or_smoke': 5, 'raw_cap_deferred_commit_message_only': 100, 'technical_certified_needs_source_context_repair': 7}`.

Source-context counts: `{'commit_message_only_context': 165, 'material_leakage_risk': 8, 'non_leaky_issue_or_pr_context': 60}`. Oracle counts: `{'oracle_available': 201, 'oracle_missing': 32}`.

The important distinction is between technical capacity and paid-demo capacity. The `100` cap-deferred candidates are all commit-message-only. They may support future source repair, but they do not support a near-term rolling-origin paid demo without additional source-context work.

## Incremental Estimate

Conservative projection: current `35` release tasks + `22` incremental release-eligible v2 rows = `57`.

Optimistic small-repair projection: add `7` technical-certified rows that need source-context repair, reaching `64`. This is not the conservative default because source repair is the dominant non-deterministic bottleneck.
