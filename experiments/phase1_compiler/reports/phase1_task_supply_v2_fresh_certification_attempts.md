# Fresh Certification Attempts

What happened: `160` selected candidates have fresh local execution evidence. `31` are technically certified and `28` are release-eligible under source-context policy.

Why it matters: technical certification is counted separately from release eligibility, so weak source context cannot silently inflate paid-readiness supply.

Deferred or not selected before execution: `345`. Unattempted selected candidates: `324`.

Terminal execution subgates:

```json
{
  "collect_failed": 44,
  "install_failed": 63,
  "noop_assert_failed": 7,
  "reference_assert_failed": 15,
  "technical_certified": 31
}
```

Runtime by repo:

```json
{
  "attrs": {
    "attempt_count": 160,
    "median_duration_seconds": 1.634,
    "total_duration_seconds": 450.592
  }
}
```

Raw stdout and stderr were written only under ignored scratch paths and are not committed.
