# Sphinx certification wave

生成时间：`2026-06-17T10:48:21+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

bounded no-paid certification/replay wave 为 `16/24` 通过，conversion rate `0.6667`。

## 覆盖

- time buckets: `{'2022_2023': 8, '2024_plus': 8, 'pre_2022': 8}`
- module families: `{'builders': 6, 'config': 2, 'directives': 1, 'domains': 4, 'extensions': 11}`
- sample policy: 24 deterministic spread-sample candidates across pre_2022, 2022_2023, and 2024_plus where available; normal-risk rows preferred before wider risk labels.

## Verifier speed

`{'count': 24, 'median_seconds': 7.78, 'p95_seconds': 24.333, 'max_seconds': 42.758}`

## Failure labels

`{'reference_target_test_failure': 5, 'base_passed_changed_tests_not_meaningful': 2, 'reference_dependency_mismatch_or_install_failed': 1}`

## Rows

| Task | Bucket | Family | Status | Label | Profile | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| sphinx__hist__0001 | pre_2022 | extensions | failed | reference_target_test_failure |  | 0.427 |
| sphinx__hist__0009 | pre_2022 | domains | failed | reference_target_test_failure |  | 0.398 |
| sphinx__hist__0017 | pre_2022 | extensions | failed | reference_target_test_failure |  | 0.979 |
| sphinx__hist__0025 | pre_2022 | domains | failed | reference_target_test_failure |  | 1.294 |
| sphinx__hist__0036 | pre_2022 | extensions | failed | reference_target_test_failure |  | 1.121 |
| sphinx__hist__0044 | pre_2022 | extensions | passed |  | py39_2018_2021_editable | 7.076 |
| sphinx__hist__0052 | pre_2022 | extensions | passed |  | py39_2018_2021_editable | 8.484 |
| sphinx__hist__0061 | pre_2022 | extensions | passed |  | py39_2018_2021_editable | 11.624 |
| sphinx__hist__0064 | 2022_2023 | domains | passed |  | py39_2018_2021_editable | 12.071 |
| sphinx__hist__0080 | 2022_2023 | extensions | passed |  | py39_2018_2021_editable | 7.008 |
| sphinx__hist__0098 | 2022_2023 | builders | passed |  | py39_2018_2021_editable | 24.333 |
| sphinx__hist__0116 | 2022_2023 | builders | failed | base_passed_changed_tests_not_meaningful | py39_2018_2021_editable | 42.758 |
| sphinx__hist__0134 | 2022_2023 | extensions | passed |  | py310_2022_2023_editable | 5.187 |
| sphinx__hist__0160 | 2022_2023 | config | passed |  | py310_2022_2023_editable | 10.24 |
| sphinx__hist__0178 | 2022_2023 | directives | passed |  | py310_2022_2023_editable | 4.446 |
| sphinx__hist__0194 | 2022_2023 | extensions | failed | base_passed_changed_tests_not_meaningful | py310_2022_2023_editable | 3.817 |
| sphinx__hist__0195 | 2024_plus | config | passed |  | py312_2024_editable | 20.469 |
| sphinx__hist__0228 | 2024_plus | builders | passed |  | py312_2024_editable | 12.814 |
| sphinx__hist__0260 | 2024_plus | builders | failed | reference_dependency_mismatch_or_install_failed |  | 24.223 |
| sphinx__hist__0312 | 2024_plus | extensions | passed |  | py312_2024_editable | 13.715 |
| sphinx__hist__0359 | 2024_plus | domains | passed |  | py312_2024_editable | 5.898 |
| sphinx__hist__0391 | 2024_plus | builders | passed |  | py314_current_editable | 6.75 |
| sphinx__hist__0424 | 2024_plus | extensions | passed |  | py314_current_editable | 18.26 |
| sphinx__hist__0471 | 2024_plus | builders | passed |  | py314_current_editable | 8.763 |

## Artifact hygiene

只提交 sanitized CSV/JSON/report。未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
