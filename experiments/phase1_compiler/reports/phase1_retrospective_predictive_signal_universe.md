# Retrospective Predictive-Signal Universe

What happened: built an outcome-blind universe from the repaired attrs, boltons, and click candidate supply.

Why it matters: the downstream replay uses task metadata and coverage only until selections are frozen.

Action suggested next: use this universe for fixed windows and selections, then join score tables later.

| Repo | Eligible | Any score row | Both adapters | Time buckets |
| --- | --- | --- | --- | --- |
| attrs | 30 | 25 | 25 | legacy_2018_or_earlier:4, middle_2019_2022:26 |
| boltons | 35 | 30 | 30 | legacy_2018_or_earlier:24, middle_2019_2022:8, recent_2023_or_later:3 |
| click | 30 | 28 | 28 | middle_2019_2022:4, recent_2023_or_later:26 |

Boundary:
- Terminal outcomes loaded before selection freeze: `false`.
- Pass/fail fields present in universe rows: `false`.
- Click repair overlay used only public-context review metadata and did not change historical paid outcomes.
