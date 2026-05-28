# Third Repo Raw Anchor Inventory

What happened: bounded repo-history v2 mining produced sanitized candidate rows for the repos advanced by the cheap screen.

Why it matters: raw anchors are inventory only. Only `oracle_usable` candidates can enter local certification.

| Repo | Raw Candidates | Inventory Statuses | Reservoir Mix |
| --- | --- | --- | --- |
| cachetools | 108 | {'oracle_missing_inventory_only': 21, 'oracle_usable': 87} | {'repo_history_v2_commit_with_tests': 34, 'repo_history_v2_issue_without_changed_tests': 21, 'repo_history_v2_pr_issue_with_tests': 53} |
| click | 298 | {'oracle_missing_inventory_only': 25, 'oracle_usable': 273} | {'repo_history_v2_commit_with_tests': 235, 'repo_history_v2_issue_without_changed_tests': 25, 'repo_history_v2_pr_issue_with_tests': 38} |
| jinja2 | 292 | {'oracle_missing_inventory_only': 50, 'oracle_usable': 242} | {'repo_history_v2_commit_with_tests': 215, 'repo_history_v2_issue_without_changed_tests': 50, 'repo_history_v2_pr_issue_with_tests': 27} |
| packaging | 300 | {'oracle_missing_inventory_only': 119, 'oracle_usable': 181} | {'repo_history_v2_commit_with_tests': 68, 'repo_history_v2_issue_without_changed_tests': 119, 'repo_history_v2_pr_issue_with_tests': 113} |
