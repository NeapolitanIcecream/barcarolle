# Phase 1 Oracle Alignment Audit

Generated: `2026-05-22T06:02:33+00:00`.

| Repo | Aligned | Manual review | Diagnostic-only | Reject | Top risk flags |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | test_edits_only_or_config_heavy_change=3, weak_oracle_risk=3, narrow_test_risk=3, target_fails_hidden_tests=1, wide_test_risk=1 |
| `boltons` | 11 | 5 | 10 | 6 | target_fails_hidden_tests=5, narrow_test_risk=3, weak_oracle_risk=3, test_edits_only_or_config_heavy_change=3, maintenance_or_dependency_update_risk=2, large_cross_module_change_risk=1, multi_issue_patch_risk=1, wide_test_risk=1 |

The audit distinguishes weak-oracle failures from wide and narrow oracle risks. Itsdangerous statements no longer show a repo-name mismatch; remaining blockers are oracle, source-quality, or execution-gate risks.
