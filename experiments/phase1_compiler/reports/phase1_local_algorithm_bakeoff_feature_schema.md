# Local Bakeoff Feature Schema

Status: `pass`.
H_future outcomes used for features: `False`.

## Feature Dimensions

| Name | Source | Description |
| --- | --- | --- |
| repo_id | candidate_inventory.repo_id | Target repository id. |
| work_cluster | module_or_package_list/module_or_package | Coarsened module root with rare_or_unknown merging. |
| difficulty_band | constant_unknown | Unknown by default because no leakage-safe prior model is available. |
| source_quality | statement_quality_status | clean, minor_risk, or risky from statement quality status. |
| locality | implementation_file_count | single_file or multi_file from implementation file count. |
| time_recency | task_time | older or recent within repo by task time ordering. |
| source_kind_group | source_kind | issue, pull_request, commit, or other. |
| statement_quality_group | statement_quality_status | clean, minor_risk, or risky from statement quality status. |

## Eligible Feature Rows

| Repo | Rows |
| --- | --- |
| attrs | 10 |
| boltons | 12 |
