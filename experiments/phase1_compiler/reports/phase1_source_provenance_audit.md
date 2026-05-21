# Phase 1 Source Provenance Audit

Generated: `2026-05-21T15:43:36+00:00`.

- GitHub metadata attempted: `true`.
- Humanize provenance status: `humanize_source_provenance_fallback_confirmed`.
- Humanize PR metadata count: `0`.
- No raw GitHub responses were committed.
- No paid LLM call was made.

| Repo | Certified | Issue/PR context | Commit fallback only | Missing context | Statement exposure risk |
| --- | ---: | ---: | ---: | ---: | ---: |
| `toolz` | 6 | 6 | 0 | 0 | 0 |
| `humanize` | 12 | 0 | 12 | 0 | 12 |

## Interpretation

Toolz remains issue-derived through the repaired source adapter. Humanize remains commit-message-fallback provenance unless GitHub commit-to-PR metadata supplies at least six non-fallback matches. This audit is sufficient for an operational pilot but not for validation-grade claims.
