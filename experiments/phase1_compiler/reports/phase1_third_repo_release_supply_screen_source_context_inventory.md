# Third Repo Source Context Inventory

What happened: every raw candidate received a source-context class.

Why it matters: commit-message-only context is not counted as release eligible without separate review.

| Repo | Context Counts | Release-Ready Before Cert | Technical+Review Upper Bound |
| --- | --- | --- | --- |
| cachetools | {'commit_message_only_context': 34, 'pr_title_only_context': 74} | 53 | 87 |
| click | {'commit_message_only_context': 235, 'pr_title_only_context': 63} | 38 | 273 |
| jinja2 | {'commit_message_only_context': 215, 'pr_title_only_context': 77} | 27 | 242 |
| packaging | {'commit_message_only_context': 68, 'pr_title_only_context': 232} | 113 | 181 |

Repos selected for environment probe: `['packaging', 'cachetools', 'click']`.
