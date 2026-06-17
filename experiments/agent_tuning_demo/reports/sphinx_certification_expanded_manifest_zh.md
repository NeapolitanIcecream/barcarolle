# Sphinx certification-expanded manifest

生成时间：`2026-06-17T14:40:19+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certified task manifest 包含 `100` 个 Sphinx tasks；threshold state: `preferred_met`；stop reason: `preferred_threshold_reached`。

## 输入与扩展

- candidate inventory: `experiments/agent_tuning_demo/results/sphinx_candidate_inventory.json`
- existing certification wave: `experiments/agent_tuning_demo/results/sphinx_certification_wave.json`
- prior wave attempts/pass: `24` / `16`
- additional no-paid attempts/pass: `153` / `84`
- additional failure labels: `{'reference_target_test_failure': 34, 'base_passed_changed_tests_not_meaningful': 18, 'target_worktree_failed': 10, 'reference_dependency_mismatch_or_install_failed': 4, 'base_worktree_failed': 1, 'changed_test_oracle_missing': 1, 'reference_import_failed': 1}`

## 覆盖

- time buckets: `{'2022_2023': 43, '2024_plus': 37, 'pre_2022': 20}`
- module families: `{'builders': 20, 'config': 6, 'core_or_other': 10, 'directives': 7, 'domains': 14, 'environment': 2, 'extensions': 36, 'util': 5}`
- verifier duration: `{'count': 100, 'median_seconds': 8.332, 'p95_seconds': 24.333, 'max_seconds': 86.196}`

## Certified rows

| Task | Bucket | Family | Profile | Seconds | Provenance |
| --- | --- | --- | --- | --- | --- |
| sphinx__hist__0040 | pre_2022 | core_or_other | py39_2018_2021_editable | 8.394 | sphinx_certification_expansion |
| sphinx__hist__0043 | pre_2022 | domains | py39_2018_2021_editable | 8.878 | sphinx_certification_expansion |
| sphinx__hist__0044 | pre_2022 | extensions | py39_2018_2021_editable | 7.076 | sphinx_certification_wave |
| sphinx__hist__0045 | pre_2022 | builders | py39_2018_2021_editable | 10.252 | sphinx_certification_expansion |
| sphinx__hist__0046 | pre_2022 | extensions | py39_2018_2021_editable | 8.549 | sphinx_certification_expansion |
| sphinx__hist__0047 | pre_2022 | extensions | py39_2018_2021_editable | 8.966 | sphinx_certification_expansion |
| sphinx__hist__0048 | pre_2022 | extensions | py39_2018_2021_editable | 9.392 | sphinx_certification_expansion |
| sphinx__hist__0049 | pre_2022 | extensions | py39_2018_2021_editable | 10.856 | sphinx_certification_expansion |
| sphinx__hist__0050 | pre_2022 | extensions | py39_2018_2021_editable | 7.886 | sphinx_certification_expansion |
| sphinx__hist__0051 | pre_2022 | domains | py39_2018_2021_editable | 8.665 | sphinx_certification_expansion |
| sphinx__hist__0052 | pre_2022 | extensions | py39_2018_2021_editable | 8.484 | sphinx_certification_wave |
| sphinx__hist__0053 | pre_2022 | util | py39_2018_2021_editable | 8.475 | sphinx_certification_expansion |
| sphinx__hist__0054 | pre_2022 | core_or_other | py39_2018_2021_editable | 6.646 | sphinx_certification_expansion |
| sphinx__hist__0055 | pre_2022 | domains | py39_2018_2021_editable | 8.876 | sphinx_certification_expansion |
| sphinx__hist__0056 | pre_2022 | core_or_other | py39_2018_2021_editable | 17.045 | sphinx_certification_expansion |
| sphinx__hist__0057 | pre_2022 | domains | py39_2018_2021_editable | 8.291 | sphinx_certification_expansion |
| sphinx__hist__0058 | pre_2022 | extensions | py39_2018_2021_editable | 8.301 | sphinx_certification_expansion |
| sphinx__hist__0059 | pre_2022 | util | py39_2018_2021_editable | 8.867 | sphinx_certification_expansion |
| sphinx__hist__0060 | pre_2022 | core_or_other | py39_2018_2021_editable | 25.66 | sphinx_certification_expansion |
| sphinx__hist__0061 | pre_2022 | extensions | py39_2018_2021_editable | 11.624 | sphinx_certification_wave |
| sphinx__hist__0062 | 2022_2023 | extensions | py39_2018_2021_editable | 12.024 | sphinx_certification_expansion |
| sphinx__hist__0064 | 2022_2023 | domains | py39_2018_2021_editable | 12.071 | sphinx_certification_wave |
| sphinx__hist__0066 | 2022_2023 | extensions | py39_2018_2021_editable | 4.52 | sphinx_certification_expansion |
| sphinx__hist__0075 | 2022_2023 | extensions | py39_2018_2021_editable | 4.929 | sphinx_certification_expansion |
| sphinx__hist__0078 | 2022_2023 | util | py39_2018_2021_editable | 5.949 | sphinx_certification_expansion |
| sphinx__hist__0080 | 2022_2023 | extensions | py39_2018_2021_editable | 7.008 | sphinx_certification_wave |
| sphinx__hist__0082 | 2022_2023 | extensions | py39_2018_2021_editable | 5.651 | sphinx_certification_expansion |
| sphinx__hist__0084 | 2022_2023 | builders | py39_2018_2021_editable | 7.37 | sphinx_certification_expansion |
| sphinx__hist__0089 | 2022_2023 | config | py39_2018_2021_editable | 22.844 | sphinx_certification_expansion |
| sphinx__hist__0093 | 2022_2023 | directives | py39_2018_2021_editable | 6.898 | sphinx_certification_expansion |
| sphinx__hist__0098 | 2022_2023 | builders | py39_2018_2021_editable | 24.333 | sphinx_certification_wave |
| sphinx__hist__0102 | 2022_2023 | builders | py39_2018_2021_editable | 7.964 | sphinx_certification_expansion |
| sphinx__hist__0105 | 2022_2023 | environment | py39_2018_2021_editable | 5.43 | sphinx_certification_expansion |
| sphinx__hist__0107 | 2022_2023 | directives | py39_2018_2021_editable | 4.83 | sphinx_certification_expansion |
| sphinx__hist__0109 | 2022_2023 | core_or_other | py39_2018_2021_editable | 4.15 | sphinx_certification_expansion |
| sphinx__hist__0111 | 2022_2023 | builders | py39_2018_2021_editable | 23.006 | sphinx_certification_expansion |
| sphinx__hist__0118 | 2022_2023 | builders | py39_2018_2021_editable | 86.196 | sphinx_certification_expansion |
| sphinx__hist__0120 | 2022_2023 | directives | py39_2018_2021_editable | 4.243 | sphinx_certification_expansion |
| sphinx__hist__0122 | 2022_2023 | builders | py39_2018_2021_editable | 12.296 | sphinx_certification_expansion |
| sphinx__hist__0125 | 2022_2023 | domains | py310_2022_2023_editable | 7.348 | sphinx_certification_expansion |
| sphinx__hist__0127 | 2022_2023 | core_or_other | py310_2022_2023_editable | 13.599 | sphinx_certification_expansion |
| sphinx__hist__0129 | 2022_2023 | builders | py310_2022_2023_editable | 51.319 | sphinx_certification_expansion |
| sphinx__hist__0131 | 2022_2023 | builders | py310_2022_2023_editable | 5.17 | sphinx_certification_expansion |
| sphinx__hist__0134 | 2022_2023 | extensions | py310_2022_2023_editable | 5.187 | sphinx_certification_wave |
| sphinx__hist__0136 | 2022_2023 | domains | py310_2022_2023_editable | 9.783 | sphinx_certification_expansion |
| sphinx__hist__0138 | 2022_2023 | extensions | py310_2022_2023_editable | 11.663 | sphinx_certification_expansion |
| sphinx__hist__0140 | 2022_2023 | builders | py310_2022_2023_editable | 4.424 | sphinx_certification_expansion |
| sphinx__hist__0149 | 2022_2023 | builders | py310_2022_2023_editable | 16.218 | sphinx_certification_expansion |
| sphinx__hist__0151 | 2022_2023 | config | py310_2022_2023_editable | 32.19 | sphinx_certification_expansion |
| sphinx__hist__0156 | 2022_2023 | domains | py310_2022_2023_editable | 4.59 | sphinx_certification_expansion |
| sphinx__hist__0158 | 2022_2023 | builders | py310_2022_2023_editable | 10.411 | sphinx_certification_expansion |
| sphinx__hist__0160 | 2022_2023 | config | py310_2022_2023_editable | 10.24 | sphinx_certification_wave |
| sphinx__hist__0163 | 2022_2023 | util | py310_2022_2023_editable | 2.936 | sphinx_certification_expansion |
| sphinx__hist__0165 | 2022_2023 | extensions | py310_2022_2023_editable | 5.282 | sphinx_certification_expansion |
| sphinx__hist__0167 | 2022_2023 | directives | py310_2022_2023_editable | 25.338 | sphinx_certification_expansion |
| sphinx__hist__0169 | 2022_2023 | extensions | py310_2022_2023_editable | 7.147 | sphinx_certification_expansion |
| sphinx__hist__0172 | 2022_2023 | environment | py310_2022_2023_editable | 4.245 | sphinx_certification_expansion |
| sphinx__hist__0176 | 2022_2023 | core_or_other | py310_2022_2023_editable | 10.532 | sphinx_certification_expansion |
| sphinx__hist__0178 | 2022_2023 | directives | py310_2022_2023_editable | 4.446 | sphinx_certification_wave |
| sphinx__hist__0181 | 2022_2023 | core_or_other | py310_2022_2023_editable | 4.807 | sphinx_certification_expansion |
| sphinx__hist__0183 | 2022_2023 | core_or_other | py310_2022_2023_editable | 8.108 | sphinx_certification_expansion |
| sphinx__hist__0187 | 2022_2023 | directives | py310_2022_2023_editable | 10.348 | sphinx_certification_expansion |
| sphinx__hist__0192 | 2022_2023 | domains | py310_2022_2023_editable | 7.516 | sphinx_certification_expansion |
| sphinx__hist__0195 | 2024_plus | config | py312_2024_editable | 20.469 | sphinx_certification_wave |
| sphinx__hist__0200 | 2024_plus | core_or_other | py312_2024_editable | 14.687 | sphinx_certification_expansion |
| sphinx__hist__0214 | 2024_plus | extensions | py310_2022_2023_editable | 9.637 | sphinx_certification_expansion |
| sphinx__hist__0218 | 2024_plus | extensions | py310_2022_2023_editable | 9.654 | sphinx_certification_expansion |
| sphinx__hist__0223 | 2024_plus | config | py312_2024_editable | 5.124 | sphinx_certification_expansion |
| sphinx__hist__0228 | 2024_plus | builders | py312_2024_editable | 12.814 | sphinx_certification_wave |
| sphinx__hist__0232 | 2024_plus | extensions | py312_2024_editable | 3.976 | sphinx_certification_expansion |
| sphinx__hist__0237 | 2024_plus | extensions | py312_2024_editable | 5.154 | sphinx_certification_expansion |
| sphinx__hist__0251 | 2024_plus | domains | py312_2024_editable | 6.98 | sphinx_certification_expansion |
| sphinx__hist__0256 | 2024_plus | util | py312_2024_editable | 2.716 | sphinx_certification_expansion |
| sphinx__hist__0265 | 2024_plus | extensions | py312_2024_editable | 6.93 | sphinx_certification_expansion |
| sphinx__hist__0303 | 2024_plus | builders | py312_2024_editable | 5.176 | sphinx_certification_expansion |
| sphinx__hist__0307 | 2024_plus | config | py312_2024_editable | 5.883 | sphinx_certification_expansion |
| sphinx__hist__0312 | 2024_plus | extensions | py312_2024_editable | 13.715 | sphinx_certification_wave |
| sphinx__hist__0326 | 2024_plus | builders | py312_2024_editable | 15.835 | sphinx_certification_expansion |
| sphinx__hist__0335 | 2024_plus | extensions | py312_2024_editable | 3.276 | sphinx_certification_expansion |
| sphinx__hist__0345 | 2024_plus | extensions | py312_2024_editable | 15.1 | sphinx_certification_expansion |
| sphinx__hist__0349 | 2024_plus | domains | py312_2024_editable | 15.045 | sphinx_certification_expansion |
| sphinx__hist__0354 | 2024_plus | builders | py312_2024_editable | 6.088 | sphinx_certification_expansion |
| sphinx__hist__0359 | 2024_plus | domains | py312_2024_editable | 5.898 | sphinx_certification_wave |
| sphinx__hist__0363 | 2024_plus | extensions | py312_2024_editable | 7.27 | sphinx_certification_expansion |
| sphinx__hist__0368 | 2024_plus | domains | py312_2024_editable | 8.364 | sphinx_certification_expansion |
| sphinx__hist__0382 | 2024_plus | directives | py314_current_editable | 5.34 | sphinx_certification_expansion |
| sphinx__hist__0387 | 2024_plus | builders | py314_current_editable | 6.443 | sphinx_certification_expansion |
| sphinx__hist__0391 | 2024_plus | builders | py314_current_editable | 6.75 | sphinx_certification_wave |
| sphinx__hist__0396 | 2024_plus | extensions | py314_current_editable | 6.833 | sphinx_certification_expansion |
| sphinx__hist__0401 | 2024_plus | extensions | py314_current_editable | 7.593 | sphinx_certification_expansion |
| sphinx__hist__0406 | 2024_plus | extensions | py314_current_editable | 9.297 | sphinx_certification_expansion |
| sphinx__hist__0410 | 2024_plus | domains | py314_current_editable | 5.915 | sphinx_certification_expansion |
| sphinx__hist__0415 | 2024_plus | builders | py314_current_editable | 14.973 | sphinx_certification_expansion |
| sphinx__hist__0420 | 2024_plus | extensions | py314_current_editable | 16.79 | sphinx_certification_expansion |
| sphinx__hist__0424 | 2024_plus | extensions | py314_current_editable | 18.26 | sphinx_certification_wave |
| sphinx__hist__0434 | 2024_plus | extensions | py314_current_editable | 11.433 | sphinx_certification_expansion |
| sphinx__hist__0438 | 2024_plus | extensions | py314_current_editable | 8.458 | sphinx_certification_expansion |
| sphinx__hist__0448 | 2024_plus | extensions | py314_current_editable | 5.199 | sphinx_certification_expansion |
| sphinx__hist__0452 | 2024_plus | extensions | py314_current_editable | 7.48 | sphinx_certification_expansion |
| sphinx__hist__0471 | 2024_plus | builders | py314_current_editable | 8.763 | sphinx_certification_wave |

## Artifact hygiene

manifest 只保留 sanitized task metadata、profile、duration、provenance 和 evidence digest；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
