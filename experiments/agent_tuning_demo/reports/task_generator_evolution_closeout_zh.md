# Task Generator evolution closeout

生成时间：`2026-06-17T14:51:59+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Terminal state: `task_generator_evolved_two_repo_ready`。Preferred acceptance met: `True`。

| Repo | Exact certified | Windows | Manifest state | Window state |
| --- | --- | --- | --- | --- |
| sphinx | 100 | 3 | preferred_met | preferred_policy_supported |
| mypy | 100 | 3 | preferred_met | preferred_policy_supported |

## Kept mechanisms

- exact-certified manifest before windows
- continue past bad chronological blocks instead of early stopping on one failed hypothesis
- repo-specific oracle adapters
- mypy TypeCheckSuite test-data nodeids
- target-commit support/test-data oracle injection
- version-aware uv verifier profiles
- corrected rolling-origin future-holdout leakage boundary

## Rejected or deferred

- generic Python-test-only mypy miner rejected because it undercounted data-driven oracles
- chronological bad-block early stop rejected because it discarded later Sphinx capacity
- synthetic SWE-smith-style reservoirs deferred because real-history certification reached target
- paid LLM statement generation deferred; source-confidence labels are used instead

## Next paid preregistration step

Freeze selectors, agents, score-join rules, invalid-cell policy, seeds, and cost caps before any paid baseline discovery or before/after tuning run.

## Remaining risks

- Solver-visible statements are provenance-labeled but not human or paid-LLM reviewed.
- Pass-to-pass guards are recorded as not run where no stable adjacent shard was bounded.
- Sphinx final rows reuse the Sphinx replay primitive and sanitized expansion manifest rather than storing raw per-row stdout/stderr.
