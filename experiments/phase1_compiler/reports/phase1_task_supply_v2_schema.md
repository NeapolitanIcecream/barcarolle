# TaskSourceCandidate v2 Schema

TaskSourceCandidate v2 is the normalized row shape for supply candidates. It keeps source provenance, public context, oracle status, environment profile, leakage flags, and solver-exposure policy in one JSON-serializable object.

| Field | Status |
| --- | --- |
| schema_version | required |
| candidate_id | required |
| repo_id | required |
| repo_url | required |
| language | required |
| source_system | required |
| source_system_version | required |
| source_reservoir | required |
| source_license | required |
| upstream_task_id | required |
| base_commit | required |
| target_commit_optional | required |
| task_time | required |
| source_time | required |
| problem_statement | required |
| problem_statement_provenance | required |
| public_context_refs | required |
| oracle | required |
| environment | required |
| changed_files | required |
| implementation_files | required |
| test_files | required |
| reference_patch_digest_optional | required |
| gold_patch_available_to_barcarolle | required |
| gold_patch_exposed_to_solver | required |
| leakage_flags | required |
| ambiguity_flags | required |
| candidate_labels | required |
| source_confidence | required |
| raw_artifact_paths_uncommitted | required |

The validator enforces required ids, base commits, allowed source reservoirs, oracle shape, environment shape, `gold_patch_exposed_to_solver == false`, and raw artifact paths under ignored scratch prefixes.

Allowed source reservoirs:

- external_swe_bench_live_feasibility
- external_swe_bench_plus_plus_feasibility
- external_swe_smith_feasibility
- manual_or_customer_future_direction
- repo_history_v1_commit_with_tests
- repo_history_v2_commit_with_tests
- repo_history_v2_issue_without_changed_tests
- repo_history_v2_pr_issue_with_tests
- synthetic_or_generated_oracle_future_direction
