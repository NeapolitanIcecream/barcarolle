# Fresh Certification Attempts

What happened: `484` selected candidates have fresh local execution evidence. `93` are technically certified and `68` are release-eligible under source-context policy.

Why it matters: technical certification is counted separately from release eligibility, so weak source context cannot silently inflate paid-readiness supply.

Deferred or not selected before execution: `345`. Unattempted selected candidates: `0`.

Terminal execution subgates:

```json
{
  "collect_failed": 125,
  "import_failed": 1,
  "install_failed": 197,
  "noop_assert_failed": 22,
  "reference_assert_failed": 46,
  "technical_certified": 93
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
  "boltons": {
    "attempt_count": 80,
    "median_duration_seconds": 0.619,
    "total_duration_seconds": 301.261
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
