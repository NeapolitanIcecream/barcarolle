# Phase 1 Oracle Alignment Audit

Generated: `2026-05-22T03:29:58+00:00`.

| Repo | Aligned | Manual review | Diagnostic-only | Reject | Top risk flags |
| --- | ---: | ---: | ---: | ---: | --- |
| `toolz` | 6 | 0 | 0 | 0 | none |
| `humanize` | 0 | 0 | 16 | 0 | test_edits_only_or_config_heavy_change=3, weak_oracle_risk=3, narrow_test_risk=3, target_fails_hidden_tests=1, wide_test_risk=1 |
| `itsdangerous` | 0 | 1 | 1 | 9 | statement_source_mismatch=11, target_fails_hidden_tests=7, test_edits_only_or_config_heavy_change=7, wide_test_risk=5, maintenance_or_dependency_update_risk=4, weak_oracle_risk=3, narrow_test_risk=2, large_cross_module_change_risk=1 |

The audit distinguishes weak-oracle failures from wide and narrow oracle risks. Itsdangerous statements currently contain a repo-name mismatch that requires certification repair before benchmark use.
