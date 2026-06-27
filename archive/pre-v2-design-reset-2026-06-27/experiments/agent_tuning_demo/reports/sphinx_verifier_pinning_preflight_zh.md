# Sphinx version-aware verifier preflight

生成时间：`2026-06-17T10:40:57+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

小样本 replay preflight 为 `4/5` 通过。该结果只回答 version-aware verifier 是否能工作，不是完整 certification wave。

## Verifier pinning policy

Choose a small date-bucket profile from task_time. Prefer editable installs for 2024+ and 2022-2023 tasks; use older Python and capped pytest/docutils/setuptools constraints for pre-2022 tasks. Try at most three profiles per task, stop on first reference pass, and label dependency mismatch rather than solving arbitrary environments.

Profile 尝试边界：date-compatible historical profiles only; include the current profile only for near-current tasks; stop on first reference pass。

## Preflight 结果

| Task | Date | Family | Status | Label | Profile | Seconds |
| --- | --- | --- | --- | --- | --- | --- |
| sphinx__hist__0001 | 2020-04-14 | extensions | failed | reference_target_test_failure |  | 0.315 |
| sphinx__hist__0064 | 2022-01-14 | domains | passed |  | py39_2018_2021_editable | 4.813 |
| sphinx__hist__0195 | 2024-01-04 | config | passed |  | py312_2024_editable | 20.214 |
| sphinx__hist__0471 | 2025-12-31 | builders | passed |  | py314_current_editable | 5.257 |
| sphinx__hist__0046 | 2021-11-09 | extensions | passed |  | py39_2018_2021_editable | 9.337 |

Dominant failure labels: `{'reference_target_test_failure': 1}`。

## 边界

本步骤只提交 sanitized command metadata、duration、subgate label 和输出尾部 hash；未提交 raw stdout/stderr、worktree、prompt、completion 或 transcript。
