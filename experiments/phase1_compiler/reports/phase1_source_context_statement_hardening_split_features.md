# Source Quality Split Feature Table

## What Happened

The split feature table has 153 rows and 95 rows eligible for future split design after overlay.

Eligible counts by repo:
- attrs: 30
- boltons: 35
- click: 30

## Why It Matters

Future split redesign can use coarse, auditable buckets instead of raw statement text or high-cardinality public context.

## Action This Suggests

The fields ready for blocked split design are repo, source context type, source quality, statement specificity, context length, editable scope, leakage risk, ambiguity risk, certification risk, task family, and time bucket.

Weak fields remain explicit: click title-only tasks carry minor risk, and commit-message-only queue tasks are blocked from split-design eligibility.
