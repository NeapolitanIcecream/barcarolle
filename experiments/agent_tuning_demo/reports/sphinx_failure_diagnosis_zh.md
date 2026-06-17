# Sphinx failure diagnosis

生成时间：`2026-06-17T12:54:38+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Sphinx decision: `reject_sphinx_move_to_candidate_loop`。Repair attempted: `False`。Next action: `continue_to_candidate_loop`。

诊断重放了 expansion 的前 `30` 个未尝试候选，conversion `0/30` (`0.0`)。

主要 failure labels: `{'reference_target_test_failure': 28, 'base_worktree_failed': 1, 'target_worktree_failed': 1}`。

具体 failure labels: `{'base_worktree_failed': 1, 'target_changed_tests_fail_on_target_commit': 28, 'target_commit_worktree_unavailable_or_invalid': 1}`。

repair classes: `{'inventory_or_checkout_repair_candidate': 1, 'not_locally_repairable': 1, 'not_locally_repairable_changed_tests_do_not_self_verify': 28}`。

命令 subgates: `{'target_test_failure': 28}`。

## 判断依据

The sampled expansion rows reproduced 0/30 conversion; the dominant concrete label is target changed-test failure on the target commit, which is not a narrow verifier-profile or support-file repair.

`reference_target_test_failure` 样本不少于 10 行；`target_worktree_failed` 行数较小，因此全部列入 JSON 和下表。命令记录只保留 profile、return code、duration、subgate 和尾部 hash，不提交 raw stdout/stderr。

## Reference target test failure sample

| Task | Time | Family | Failure | Repair class | Subgates |
| --- | --- | --- | --- | --- | --- |
| sphinx__hist__0003 | 2021-05-01 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0004 | 2021-05-02 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0005 | 2021-05-02 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0006 | 2021-05-03 | util | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0007 | 2021-05-08 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0008 | 2021-05-10 | util | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0010 | 2021-05-15 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0011 | 2021-05-15 | util | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0012 | 2021-05-16 | extensions | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |
| sphinx__hist__0013 | 2021-05-17 | builders | target_changed_tests_fail_on_target_commit | not_locally_repairable_changed_tests_do_not_self_verify | target_test_failure |

## Target worktree failures

| Task | Time | Family | Failure | Repair class |
| --- | --- | --- | --- | --- |
| sphinx__hist__0024 | 2021-07-07 | util | target_commit_worktree_unavailable_or_invalid | inventory_or_checkout_repair_candidate |

## Passing contrast

| Task | Time | Family | Subgates |
| --- | --- | --- | --- |
| sphinx__hist__0044 | 2021-10-31 | extensions | passed,target_test_failure |
| sphinx__hist__0052 | 2021-12-03 | extensions | passed,target_test_failure |
| sphinx__hist__0061 | 2021-12-27 | extensions | passed,target_test_failure |
| sphinx__hist__0064 | 2022-01-14 | domains | dependency_mismatch_or_install_failed,passed,target_test_failure |
| sphinx__hist__0080 | 2022-05-07 | extensions | dependency_mismatch_or_install_failed,passed,target_test_failure |

## Artifact hygiene

本 artifact 不包含 raw logs、workspaces、prompts、completions、transcripts 或 secrets；只记录 sanitized metadata 和 command gate summaries。
