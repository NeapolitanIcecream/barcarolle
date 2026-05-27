# Fresh Certification Paid Readiness Gate

Paid readiness status: not ready.

What happened: paid readiness was computed from release-eligible counts, not raw candidates or technical certification alone.

Release-eligible counts by repo:

```json
{
  "attrs": 28,
  "boltons": 35,
  "toolz": 5
}
```

Technical certification counts by repo:

```json
{
  "attrs": 31,
  "boltons": 47,
  "humanize": 9,
  "toolz": 6
}
```

Repos meeting 30 release-eligible tasks: `['boltons']`.

Blocking reasons:

```json
[
  "at_least_3_repos_with_30_release_eligible"
]
```
