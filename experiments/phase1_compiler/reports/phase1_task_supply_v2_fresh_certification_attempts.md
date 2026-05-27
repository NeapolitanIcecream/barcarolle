# Fresh Certification Attempts

What happened: `404` selected candidates have fresh local execution evidence. `46` are technically certified and `33` are release-eligible under source-context policy.

Why it matters: technical certification is counted separately from release eligibility, so weak source context cannot silently inflate paid-readiness supply.

Deferred or not selected before execution: `345`. Unattempted selected candidates: `80`.

Terminal execution subgates:

```json
{
  "collect_failed": 118,
  "install_failed": 192,
  "noop_assert_failed": 12,
  "reference_assert_failed": 36,
  "technical_certified": 46
}
```

Runtime by repo:

```json
{
  "attrs": {
    "attempt_count": 160,
    "median_duration_seconds": 1.634,
    "total_duration_seconds": 450.592
  },
  "humanize": {
    "attempt_count": 84,
    "median_duration_seconds": 1.603,
    "total_duration_seconds": 175.512
  },
  "toolz": {
    "attempt_count": 160,
    "median_duration_seconds": 0.166,
    "total_duration_seconds": 71.33
  }
}
```

Raw stdout and stderr were written only under ignored scratch paths and are not committed.
