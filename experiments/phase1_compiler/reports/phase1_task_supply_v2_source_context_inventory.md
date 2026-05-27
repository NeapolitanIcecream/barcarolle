# Source Context Inventory

The source-context pass counts issue/PR-like context separately from commit-message-only context. Commit-message-only candidates do not silently count as high-quality issue supply.

| Repo | Context Quality Counts |
| --- | --- |
| attrs | {'commit_message_only_context': 160, 'material_leakage_risk': 18, 'non_leaky_issue_or_pr_context': 120, 'pr_title_only_context': 2} |
| boltons | {'commit_message_only_context': 165, 'material_leakage_risk': 8, 'non_leaky_issue_or_pr_context': 60} |
| humanize | {'commit_message_only_context': 92} |
| toolz | {'commit_message_only_context': 198, 'non_leaky_issue_or_pr_context': 6} |
