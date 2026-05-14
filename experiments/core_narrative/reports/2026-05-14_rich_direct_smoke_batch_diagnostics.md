# Rich Direct-Smoke Batch Diagnostics

Status: `completed`

## Summary

The Rich W* direct-smoke batch accepted 5 of 8 current direct-oracle candidates. The 3 rejected candidates fall into two actionable categories:

| Category | Count | Meaning |
|---|---:|---|
| `non_discriminating_existing_tests` | 2 | Extracted target tests passed on the base tree, so they cannot serve as hidden verifiers. |
| `noop_timeout_or_hanging_verifier` | 1 | The no-op verifier timed out and needs node pruning or replacement. |

## Candidate Actions

| Batch index | No-op | Reference | Action |
|---:|---|---|---|
| 6 | `passed_unexpected` | `passed` | Build Golden-Oracle verifier or reject. |
| 7 | `blocked_timeout` | `passed` | Prune/replace verifier nodes, then re-smoke; otherwise reject. |
| 8 | `passed_unexpected` | `passed` | Build Golden-Oracle verifier or reject. |

## Boundary

This diagnostic uses redacted batch output and ignored private smoke artifacts. It publishes no raw source commits, reference patches, hidden verifier files, or target diffs. Primary ACUT runs remain unauthorized.
