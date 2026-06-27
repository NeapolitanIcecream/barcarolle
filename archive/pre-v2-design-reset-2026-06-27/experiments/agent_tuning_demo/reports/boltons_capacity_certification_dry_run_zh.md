# Boltons bounded certification dry run

Generated at: `2026-06-15T05:08:30+00:00`. Paid cells run: `0`.

## Conversion Estimate

| Metric | Value |
| --- | --- |
| Gross boltons attempts | 80 |
| Gross release conversion | 0.4375 |
| New-attempt denominator | 58 |
| New release conversion | 0.3793 |
| 20-row slice release conversion | 0.35 |
| Dominant bottleneck | source_context_repair_for_commit_message_only_rows; no incremental recent release-eligible tasks were found beyond current release-table commits |

This package reuses the committed no-paid fresh-certification execution rows instead of rerunning paid or broad tooling. The existing boltons wave is larger than the suggested 10-20 dry-run size: `80` attempted candidates. For a bounded view, the JSON also records a 20-row slice biased toward middle/recent new candidates.

Gross release conversion was `0.4375`. After excluding target commits already present in the current release table, release conversion was `0.3793` (`22/58`).

## Bottleneck

The dominant bottleneck is source context, not raw mining. Technical-certified commit-message-only rows are not release-eligible without source repair, and the deterministic non-leaky issue/PR pool has already been attempted. The incremental release rows add legacy and middle coverage; they do not add new recent 2023+ release-eligible tasks beyond current release-table commits.
