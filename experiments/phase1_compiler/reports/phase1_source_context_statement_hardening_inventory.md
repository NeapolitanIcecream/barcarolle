# Source Context Statement Hardening Inventory

## What Happened

The inventory covers 96 frozen paid-package tasks and 57 directly relevant source-review queue tasks for attrs, boltons, and click.

Release-eligible before this overlay: 96. Technical-certified rows in scope: 153. These counts are separate.

Title-only context rows: 31. Commit-message-only context rows: 57.

## Why It Matters

Title-only and commit-message-only source context can make a task look usable while still leaving the solver with a weak problem statement. The inventory makes that risk explicit before any future split design consumes the pool.

## Counts By Repo And Source Quality

- attrs: {'non_leaky_issue_or_pr_context': 27, 'pr_title_only_context': 1, 'public_context_repaired': 3}
- boltons: {'commit_message_only_context': 12, 'non_leaky_issue_or_pr_context': 35}
- click: {'commit_message_only_context': 45, 'pr_title_only_context': 30}

## Action This Suggests

Build a deterministic repair queue from title-only and commit-message-only rows. Keep completed paid outcomes out of repair priority and promotion decisions.

## Hygiene

- Diagnostic paid outcomes were not joined into the inventory rows.
- Raw hidden oracle material committed: false.
- Raw target diffs committed: false.
