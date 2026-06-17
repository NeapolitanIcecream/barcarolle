# Sphinx certification-expanded manifest

生成时间：`2026-06-17T11:35:30+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certified task manifest 包含 `16` 个 Sphinx tasks；threshold state: `below_minimum`；stop reason: `recent_conversion_below_0_30_and_not_clearly_repairable`。

## 输入与扩展

- candidate inventory: `experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json`
- existing certification wave: `experiments/agent_tuning_demo/results/sphinx_certification_wave.json`
- prior wave attempts/pass: `24` / `16`
- additional no-paid attempts/pass: `30` / `0`
- additional failure labels: `{'reference_target_test_failure': 27, 'target_worktree_failed': 3}`

## 覆盖

- time buckets: `{'2022_2023': 6, '2024_plus': 7, 'pre_2022': 3}`
- module families: `{'builders': 4, 'config': 2, 'directives': 1, 'domains': 2, 'extensions': 7}`
- verifier duration: `{'count': 16, 'median_seconds': 9.502, 'p95_seconds': 20.469, 'max_seconds': 24.333}`

## Certified rows

| Task | Bucket | Family | Profile | Seconds | Provenance |
| --- | --- | --- | --- | --- | --- |
| sphinx__hist__0044 | pre_2022 | extensions | py39_2018_2021_editable | 7.076 | sphinx_certification_wave |
| sphinx__hist__0052 | pre_2022 | extensions | py39_2018_2021_editable | 8.484 | sphinx_certification_wave |
| sphinx__hist__0061 | pre_2022 | extensions | py39_2018_2021_editable | 11.624 | sphinx_certification_wave |
| sphinx__hist__0064 | 2022_2023 | domains | py39_2018_2021_editable | 12.071 | sphinx_certification_wave |
| sphinx__hist__0080 | 2022_2023 | extensions | py39_2018_2021_editable | 7.008 | sphinx_certification_wave |
| sphinx__hist__0098 | 2022_2023 | builders | py39_2018_2021_editable | 24.333 | sphinx_certification_wave |
| sphinx__hist__0134 | 2022_2023 | extensions | py310_2022_2023_editable | 5.187 | sphinx_certification_wave |
| sphinx__hist__0160 | 2022_2023 | config | py310_2022_2023_editable | 10.24 | sphinx_certification_wave |
| sphinx__hist__0178 | 2022_2023 | directives | py310_2022_2023_editable | 4.446 | sphinx_certification_wave |
| sphinx__hist__0195 | 2024_plus | config | py312_2024_editable | 20.469 | sphinx_certification_wave |
| sphinx__hist__0228 | 2024_plus | builders | py312_2024_editable | 12.814 | sphinx_certification_wave |
| sphinx__hist__0312 | 2024_plus | extensions | py312_2024_editable | 13.715 | sphinx_certification_wave |
| sphinx__hist__0359 | 2024_plus | domains | py312_2024_editable | 5.898 | sphinx_certification_wave |
| sphinx__hist__0391 | 2024_plus | builders | py314_current_editable | 6.75 | sphinx_certification_wave |
| sphinx__hist__0424 | 2024_plus | extensions | py314_current_editable | 18.26 | sphinx_certification_wave |
| sphinx__hist__0471 | 2024_plus | builders | py314_current_editable | 8.763 | sphinx_certification_wave |

## Artifact hygiene

manifest 只保留 sanitized task metadata、profile、duration、provenance 和 evidence digest；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
