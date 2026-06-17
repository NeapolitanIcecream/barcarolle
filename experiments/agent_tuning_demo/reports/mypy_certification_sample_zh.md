# Mypy certification sample

生成时间：`2026-06-17T13:11:42+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certification sample: `7/24`；conversion `0.2917`；decision `reject_mypy_conversion_below_0_30`。

- candidate inventory count: `559`
- normal-risk eligible count: `440`
- failure labels: `{'reference_dependency_mismatch_or_install_failed': 7, 'reference_target_test_failure': 5, 'base_passed_changed_tests_not_meaningful': 2, 'reference_collection_failed': 2, 'reference_unknown_failed': 1}`
- verifier duration: `{'count': 7, 'median_seconds': 5.835, 'p95_seconds': 14.153, 'max_seconds': 14.153}`

## Rows

| Task | Time | Family | Status | Failure | Profile | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| mypy__hist__0558 | 2019-11-12 | mypyc | failed | reference_dependency_mismatch_or_install_failed |  | 0.335 |
| mypy__hist__0530 | 2020-03-07 | core_or_other | failed | reference_dependency_mismatch_or_install_failed |  | 0.928 |
| mypy__hist__0507 | 2020-07-17 | mypyc | failed | reference_dependency_mismatch_or_install_failed |  | 0.306 |
| mypy__hist__0484 | 2020-09-03 | core_or_other | failed | reference_dependency_mismatch_or_install_failed |  | 0.923 |
| mypy__hist__0462 | 2020-10-28 | core_or_other | failed | reference_dependency_mismatch_or_install_failed |  | 0.321 |
| mypy__hist__0435 | 2021-02-26 | core_or_other | failed | reference_dependency_mismatch_or_install_failed |  | 0.595 |
| mypy__hist__0406 | 2021-08-01 | core_or_other | failed | reference_dependency_mismatch_or_install_failed |  | 0.74 |
| mypy__hist__0386 | 2021-12-01 | core_or_other | failed | reference_target_test_failure |  | 3.963 |
| mypy__hist__0364 | 2022-04-07 | core_or_other | failed | base_passed_changed_tests_not_meaningful | py310_legacy_editable | 5.202 |
| mypy__hist__0339 | 2022-07-17 | mypyc | failed | reference_target_test_failure |  | 16.151 |
| mypy__hist__0311 | 2022-08-12 | core_or_other | passed |  | py310_legacy_editable | 4.205 |
| mypy__hist__0282 | 2022-11-10 | daemon_finegrained | failed | base_passed_changed_tests_not_meaningful | py310_legacy_editable | 40.001 |
| mypy__hist__0257 | 2023-03-24 | core_or_other | failed | reference_target_test_failure |  | 4.401 |
| mypy__hist__0230 | 2023-06-23 | mypyc | failed | reference_unknown_failed |  | 7.561 |
| mypy__hist__0207 | 2023-09-15 | core_or_other | failed | reference_target_test_failure |  | 12.374 |
| mypy__hist__0187 | 2023-12-25 | type_checker | passed |  | py312_editable | 14.153 |
| mypy__hist__0162 | 2024-08-11 | core_or_other | passed |  | py312_editable | 7.753 |
| mypy__hist__0142 | 2024-12-17 | core_or_other | passed |  | py312_editable | 5.291 |
| mypy__hist__0116 | 2025-03-07 | core_or_other | failed | reference_target_test_failure |  | 26.886 |
| mypy__hist__0096 | 2025-08-15 | core_or_other | passed |  | py312_editable | 5.14 |
| mypy__hist__0074 | 2025-11-25 | mypyc | failed | reference_collection_failed |  | 14.472 |
| mypy__hist__0046 | 2026-02-03 | mypyc | failed | reference_collection_failed |  | 16.097 |
| mypy__hist__0021 | 2026-04-13 | core_or_other | passed |  | py312_editable | 5.835 |
| mypy__hist__0002 | 2026-06-04 | core_or_other | passed |  | py312_editable | 6.605 |

## Artifact hygiene

本 artifact 只保存 sanitized command metadata 和 tail hashes；未提交 raw stdout/stderr、workspaces、prompts、completions、transcripts 或 secrets。
