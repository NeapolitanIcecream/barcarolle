# Large-repo target selection gate

Generated at: `2026-06-15T07:31:17+00:00`. Paid Agent cells: `0`. Paid LLM calls: `0`. Paid tuner calls: `0`.

## Executive Recommendation

Primary recommendation: `black` (`capacity_promising_but_speed_unproven`).
Backup recommendation: `httpx` (`capacity_promising_but_speed_unproven`).

This is a no-paid target-prep recommendation, not permission to start paid baseline discovery or tuning. The best balance in this run is `black` because it combines projected task capacity, rolling-origin shape, and targeted verifier evidence better than the old attrs/click fallback and better than the large compiled stacks whose setup risk dominated their raw capacity.

## Candidate Table By Track

### Baseline And Prior Near-miss

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attrs | 361 | 249 | 31 | 7 | not_run | ideal | low | screened_out |
| boltons | 202 | 42 | 57 | 2 | not_run | ideal | low | screened_out |
| click | 420 | 63 | 30 | 3 | not_run | ideal | low | screened_out |
| packaging | 248 | 179 | 27 | 4 | not_run | ideal | low | screened_out |
| pytest | 841 | 319 | 48 | 4 | not_run | risky | high_self_hosting_test_harness | screened_out |

### Large/Heavy Candidates

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| django | 1888 | 1717 | 258 | 4 | not_run | acceptable | medium_database_and_settings_matrix | capacity_promising_but_speed_unproven |
| mypy | 571 | 570 | 86 | 5 | not_run | acceptable | medium_large_custom_test_harness | capacity_promising_but_speed_unproven |
| pandas | 1672 | 1671 | 84 | 1 | not_run | risky | high_compiled_extension_build | large_but_heavy |
| scikit-learn | 1520 | 1520 | 76 | 2 | not_run | risky | high_compiled_extension_build | large_but_heavy |
| matplotlib | 552 | 218 | 11 | 0 | not_run | risky | high_compiled_extension_and_image_test_stack | screened_out |
| sqlalchemy | 1604 | 25 | 4 | 0 | not_run | acceptable | medium_database_backend_matrix | screened_out |
| sympy | 911 | 37 | 6 | 0 | not_run | acceptable | low_pure_python_but_large_suite | screened_out |

### Medium-large Fast-evaluation Candidates

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| black | 602 | 488 | 73 | 6 | not_run | ideal | low | capacity_promising_but_speed_unproven |
| httpx | 474 | 398 | 60 | 3 | not_run | ideal | low_to_medium_network_mocking | capacity_promising_but_speed_unproven |
| sphinx | 804 | 514 | 77 | 2 | not_run | acceptable | medium_doc_build_fixture_matrix | capacity_promising_but_speed_unproven |
| anyio | 0 | 0 | 0 | 0 |  |  | low_to_medium_async_backend_matrix | screened_out |
| pydantic | 0 | 0 | 0 | 0 |  |  | medium_rust_core_dependency_but_wheel_available | screened_out |
| starlette | 435 | 381 | 57 | 6 | not_run | ideal | low_to_medium_async_http_stack | screened_out |
| tornado | 1022 | 36 | 5 | 1 | not_run | ideal | low_to_medium_async_network_tests | screened_out |
| trio | 457 | 121 | 18 | 2 | not_run | ideal | low_to_medium_async_backend_matrix | screened_out |

## Large/heavy Findings

The large/heavy track confirms that size alone is not enough. `pandas`, `scikit-learn`, and `matplotlib` have strong raw capacity signals but carry compiled-extension or image-test stack risk. They are useful negative controls for capacity-versus-speed, not the practical next target. Large pure-Python or mostly-Python candidates are more interesting: `sympy`, `django`, and `sqlalchemy` have enough source/oracle volume to justify deeper no-paid target prep when their targeted verifier remains under the practical threshold.

## Medium-large Fast-evaluation Findings

The medium-large fast track is the right comparison class against old attrs/click. `black`, `httpx`, `starlette`, and `anyio` are easier to evaluate locally than scientific compiled stacks, but several are either under the conservative capacity threshold or still need more release-certification proof before they can carry a multi-window demo.

## Top Deep-probe Summaries

| Repo | Track | Smoke | Median s | P95 s | Hist replay | Projected | Repair projection | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltons | baseline | not_run | None | None | 0/0 | 57 | 57 | screened_out |
| attrs | baseline | not_run | None | None | 0/0 | 31 | 31 | screened_out |
| click | baseline | not_run | None | None | 0/0 | 30 | 30 | screened_out |
| packaging | baseline | not_run | None | None | 0/0 | 27 | 27 | screened_out |
| django | large_heavy | not_run | None | None | 0/0 | 258 | 258 | capacity_promising_but_speed_unproven |
| sqlalchemy | large_heavy | not_run | None | None | 0/0 | 4 | 4 | screened_out |
| sympy | large_heavy | not_run | None | None | 0/0 | 6 | 6 | screened_out |
| pandas | large_heavy | not_run | None | None | 0/0 | 84 | 251 | large_but_heavy |
| scikit-learn | large_heavy | not_run | None | None | 0/0 | 76 | 228 | large_but_heavy |
| black | medium_large_fast | not_run | None | None | 0/0 | 73 | 73 | capacity_promising_but_speed_unproven |
| httpx | medium_large_fast | not_run | None | None | 0/0 | 60 | 60 | capacity_promising_but_speed_unproven |
| starlette | medium_large_fast | not_run | None | None | 0/0 | 57 | 57 | screened_out |
| anyio | medium_large_fast | None | None | None | 0/0 | None | None | screened_out |

## Capacity vs Evaluation-speed Tradeoff

The preferred target is not the largest repository. A repository needs enough source-linked implementation-plus-test changes to survive release certification, but the verifier must also be targetable to sub-suite tests. The avoid-by-default group is high-capacity but environment-heavy; the underpowered group is fast but does not yet clear the `60` conservative task threshold. The recommended path is to prep the candidate with the strongest middle: high enough projected task count and targeted verifier timing that leaves room for iteration.

## Recommended Target And Backup

Recommended target: `black`. It should receive a target profile, package map, verifier pinning, and a 20-30 task no-paid certification wave before any paid work.

Backup: `httpx`. Use it if `black` fails the next verifier/certification wave.

## Repositories Rejected Despite High Capacity

| Repo | Why rejected | Repair opportunity |
| --- | --- | --- |
| pandas | reject for mainline today unless environment repair can make targeted verification fast and stable | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |
| scikit-learn | reject for mainline today unless environment repair can make targeted verification fast and stable | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |

## Repositories Rejected Despite Fast Evaluation

_No fast candidate was rejected solely for low capacity after this bounded screen._

## Next No-paid Prep Plan

1. Create a target profile and package map for `black`.
2. Pin a task-level verifier command that prefers changed tests or narrow module shards, not full-suite execution.
3. Run a 20-30 task no-paid release-certification wave across at least two time buckets.
4. Freeze a rolling-origin split only if the certified count supports at least two evidence-backed windows.
5. Recompute paid baseline discovery cells and stop again before any paid Agent or tuner call.

## Paid Baseline Discovery Estimate

For `black`, the rough baseline-discovery estimate is `292` cells, with a coarse historical cost range of `$58.4` to `$131.4`. This estimate is not an authorization.

## Unsupported Claims

- No paid Agent cell, paid LLM call, or paid tuner call was run.
- No Agent tuning improvement is supported.
- No predictive-validity or cross-repo generalization claim is supported.
- black is a no-paid target-prep recommendation, not an immediate paid-run authorization.
- Projected certified counts are capacity estimates until a bounded release-certification wave proves conversion.
