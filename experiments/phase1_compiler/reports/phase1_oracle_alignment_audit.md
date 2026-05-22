# Phase 1 Oracle Alignment Audit

Generated: `2026-05-22T03:54:32+00:00`.

| Repo | Aligned | Manual review | Diagnostic-only | Reject | Top risk flags |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | test_edits_only_or_config_heavy_change=3, weak_oracle_risk=3, narrow_test_risk=3, target_fails_hidden_tests=1, wide_test_risk=1 |
| `itsdangerous` | 0 | 4 | 0 | 2 | test_edits_only_or_config_heavy_change=3, large_cross_module_change_risk=1, multi_issue_patch_risk=1, target_fails_hidden_tests=1, wide_test_risk=1, narrow_test_risk=1, weak_oracle_risk=1 |

The audit distinguishes weak-oracle failures from wide and narrow oracle risks. Itsdangerous statements no longer show a repo-name mismatch; remaining blockers are oracle, source-quality, or execution-gate risks.
