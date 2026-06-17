# Target repair selection method-limitation diagnosis

生成时间：`2026-06-17T13:14:53+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Terminal state: `task_generation_method_needs_revision`。

没有仓库达到 corrected rolling-origin paid preregistration 的 exact manifest 门槛。当前证据指向 Task Generator / certification method 修订，而不是继续用同一方法重试另一个仓库。

## Did repositories fail because they are too small?

- attrs, click, starlette, black, boltons-style backups, and many additional screen rows fall below the corrected 80 exact-task minimum or below preferred 100 exact tasks after projected conversion.
- Small fast repositories remain useful pilots, but they cannot support the corrected selected-from-history plus future-holdout protocol without stronger mining/certification yield.
## Did historical environments fail?

- mypy exact sample converted 7/24 with dependency, collection, target-test, and non-meaningful-oracle failures.
- django, pandas, and scikit-learn have raw capacity but existing bounded probes classify them as environment-heavy or compiled-extension-heavy.
## Are changed tests self-contained hidden oracles?

- Sphinx repair diagnosis classified {'base_worktree_failed': 1, 'target_changed_tests_fail_on_target_commit': 28, 'target_commit_worktree_unavailable_or_invalid': 1} after a 0/30 expansion replay.
- Several mypy rows either passed on base after target-test injection or failed on target, so changed Python test files alone are not a reliable hidden oracle.
## Did the miner undercount or use the wrong source pattern?

- The current miner is mostly implementation-plus-Python-test anchored and underuses repository-specific oracle shapes such as mypy test-data files, Sphinx fixture roots, generated fixtures, and support files.
- It also did not preserve enough per-row failure detail in the first Sphinx expansion until this run added a diagnosis artifact.
## Would richer mining/environment synthesis likely change this?

- SWE-bench-style PR/issue mining could expose issue-specific or PR-specific oracle context instead of relying only on changed test files.
- Version-aware environment synthesis and repository-specific oracle extraction would likely improve mypy/Sphinx conversion more than retrying another repository with the same generic miner.

## Smallest next improvement

Add a repository-specific Task Generator repair pass that mines changed test-data/support-file roots, captures target/base replay subgate details for every attempted row, and creates version-aware verifier profiles before expanding to another target.
