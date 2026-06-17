# Task Generator baseline failure reproduction

生成时间：`2026-06-17T14:19:35+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Baseline reproduction shows generic changed-Python-test mining is insufficient: Sphinx had an early bad chronological block, and mypy underused data-driven test-data oracles.

| Repo | Source | Passes | Attempts | Failures |
| --- | --- | --- | --- | --- |
| sphinx | experiments/agent_tuning_demo/results/sphinx_failure_diagnosis.json | 0 | 30 | {'base_worktree_failed': 1, 'target_changed_tests_fail_on_target_commit': 28, 'target_commit_worktree_unavailable_or_invalid': 1} |
| mypy | experiments/agent_tuning_demo/results/mypy_certification_sample.json | 7 | 24 | {'base_passed_changed_tests_not_meaningful': 2, 'reference_collection_failed': 2, 'reference_dependency_mismatch_or_install_failed': 7, 'reference_target_test_failure': 5, 'reference_unknown_failed': 1} |
