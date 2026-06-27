# Large-repo target selection gate

Generated at: `2026-06-15T07:54:12+00:00`. Paid Agent cells: `0`. Paid LLM calls: `0`. Paid tuner calls: `0`.

## Executive Recommendation

Primary recommendation: `sphinx` (`balanced_target_prep_candidate`).
Backup recommendation: `mypy` (`capacity_promising_but_speed_unproven`).

This is a no-paid target-prep recommendation, not permission to start paid baseline discovery or tuning. The best balance in this run is `sphinx` because it combines projected task capacity, rolling-origin shape, and targeted verifier evidence better than the old attrs/click fallback and better than the large compiled stacks whose setup risk dominated their raw capacity.

## Candidate Table By Track

### Baseline And Prior Near-miss

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltons | 202 | 42 | 57 | 2 | passed | ideal_under_60s | low | fast_but_underpowered |
| click | 420 | 63 | 30 | 3 | passed | ideal_under_60s | low | fast_but_underpowered |
| attrs | 361 | 249 | 31 | 7 | failed | environment_failed_or_unusable | low | screened_out |
| packaging | 248 | 179 | 0 | 4 | failed | environment_failed_or_unusable | low | screened_out |
| pytest | 841 | 319 | 48 | 4 | not_run | risky | high_self_hosting_test_harness | screened_out |

### Large/Heavy Candidates

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| mypy | 571 | 570 | 86 | 5 | not_run | acceptable | medium_large_custom_test_harness | capacity_promising_but_speed_unproven |
| sqlalchemy | 1604 | 25 | 7 | 0 | passed | ideal_under_60s | medium_database_backend_matrix | fast_but_underpowered |
| django | 1888 | 1717 | 86 | 4 | failed | environment_failed_or_unusable | medium_database_and_settings_matrix | large_but_heavy |
| pandas | 1672 | 1671 | 84 | 1 | failed | environment_failed_or_unusable | high_compiled_extension_build | large_but_heavy |
| scikit-learn | 1520 | 1520 | 76 | 2 | failed | environment_failed_or_unusable | high_compiled_extension_build | large_but_heavy |
| matplotlib | 552 | 218 | 11 | 0 | not_run | risky | high_compiled_extension_and_image_test_stack | screened_out |
| sympy | 911 | 37 | 2 | 0 | failed | environment_failed_or_unusable | low_pure_python_but_large_suite | screened_out |

### Medium-large Fast-evaluation Candidates

| Repo | Impl+Test | Source refs | Projected | Windows | Smoke | Speed | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| sphinx | 804 | 514 | 157 | 2 | passed | ideal_under_60s | medium_doc_build_fixture_matrix | balanced_target_prep_candidate |
| black | 602 | 488 | 73 | 6 | partial_failed | partial_probe_failure | low | capacity_promising_but_speed_unproven |
| anyio | 394 | 220 | 11 | 4 | failed | environment_failed_or_unusable | low_to_medium_async_backend_matrix | screened_out |
| httpx | 474 | 398 | 20 | 3 | failed | environment_failed_or_unusable | low_to_medium_network_mocking | screened_out |
| pydantic | 0 | 0 | 0 | 0 |  |  | medium_rust_core_dependency_but_wheel_available | screened_out |
| starlette | 435 | 381 | 57 | 6 | partial_failed | partial_probe_failure | low_to_medium_async_http_stack | screened_out |
| tornado | 1022 | 36 | 5 | 1 | not_run | ideal | low_to_medium_async_network_tests | screened_out |
| trio | 457 | 121 | 18 | 2 | not_run | ideal | low_to_medium_async_backend_matrix | screened_out |

## Large/heavy Findings

The large/heavy track confirms that size alone is not enough. `pandas` and `scikit-learn` have strong raw capacity signals, but compiled-extension setup and generic-probe failures make them `large_but_heavy` rather than practical mainline targets. `django` has very high source-linked capacity, but the bounded pytest shards failed under the generic verifier command, so it is an environment/profile repair candidate. `sqlalchemy` timed well on current targeted shards, but this simple public-ref screen found too little source-linked changed-test oracle volume. `sympy` also screened low under the public-ref heuristic despite being large, so it needs a different source-context miner before it can be considered.

## Medium-large Fast-evaluation Findings

The medium-large fast track is the right comparison class against old attrs/click. `sphinx` is the strongest measured result in the final run: its current targeted shards passed quickly and projected source-linked changed-test capacity clears the conservative threshold. `black` and `starlette` have attractive raw history, but their configured current probes were only partial or failed after dependency profile tightening, so they are bounded repair opportunities rather than recommendations. `httpx` and `anyio` also need verifier-profile repair before they can compete on practical iteration speed.

## Top Deep-probe Summaries

| Repo | Track | Smoke | Median s | P95 s | Hist replay | Projected | Repair projection | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| boltons | baseline | passed | 0.174 | 0.174 | 0/1 | 57 | 57 | fast_but_underpowered |
| attrs | baseline | failed | 0.114 | 0.114 | 0/1 | 31 | 31 | screened_out |
| click | baseline | passed | 0.426 | 0.426 | 1/1 | 30 | 30 | fast_but_underpowered |
| packaging | baseline | failed | 0.275 | 0.275 | 0/1 | 0 | 0 | screened_out |
| django | large_heavy | failed | 0.014 | 0.015 | 0/1 | 86 | 258 | large_but_heavy |
| sqlalchemy | large_heavy | passed | 0.963 | 1.172 | 0/1 | 7 | 7 | fast_but_underpowered |
| sympy | large_heavy | failed | 5.341 | 9.951 | 0/1 | 2 | 2 | screened_out |
| pandas | large_heavy | failed | 0.085 | 0.092 | 0/1 | 84 | 251 | large_but_heavy |
| scikit-learn | large_heavy | failed | 0.084 | 0.084 | 0/1 | 76 | 228 | large_but_heavy |
| black | medium_large_fast | partial_failed | 9.722 | 16.063 | 0/1 | 73 | 73 | capacity_promising_but_speed_unproven |
| httpx | medium_large_fast | failed | 2.155 | 3.993 | 0/1 | 20 | 20 | screened_out |
| starlette | medium_large_fast | partial_failed | 1.012 | 1.693 | 0/1 | 57 | 57 | screened_out |
| anyio | medium_large_fast | failed | 0.129 | 0.136 | 0/1 | 11 | 11 | screened_out |
| sphinx | medium_large_fast | passed | 0.508 | 0.663 | 0/1 | 157 | 231 | balanced_target_prep_candidate |

## Capacity vs Evaluation-speed Tradeoff

The preferred target is not the largest repository. A repository needs enough source-linked implementation-plus-test changes to survive release certification, but the verifier must also be targetable to sub-suite tests. The avoid-by-default group is high-capacity but environment-heavy; the underpowered group is fast but does not yet clear the `60` conservative task threshold. The recommended path is to prep the candidate with the strongest middle: high enough projected task count and targeted verifier timing that leaves room for iteration.

## Recommended Target And Backup

Recommended target: `sphinx`. It should receive a target profile, package map, verifier pinning, and a 20-30 task no-paid certification wave before any paid work. Its current targeted verifier timing is strong, but the one-sample historical changed-test replay did not pass under the generic dependency profile, so version-aware verifier pinning is a required next gate.

Backup: `mypy`. Use it only as a follow-up no-paid prep candidate if `sphinx` fails; it still needs its own targeted smoke and certification wave before any paid baseline discovery.

## Repositories Rejected Despite High Capacity

| Repo | Why rejected | Repair opportunity |
| --- | --- | --- |
| django | reject for mainline today unless environment repair can make targeted verification fast and stable | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |
| pandas | reject for mainline today unless environment repair can make targeted verification fast and stable | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |
| scikit-learn | reject for mainline today unless environment repair can make targeted verification fast and stable | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |

## Repositories Rejected Despite Fast Evaluation

| Repo | Why rejected | Repair opportunity |
| --- | --- | --- |
| boltons | keep only as backup or small pilot; capacity below rolling-origin threshold | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |
| click | keep only as backup or small pilot; capacity below rolling-origin threshold | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |
| sqlalchemy | keep only as backup or small pilot; capacity below rolling-origin threshold | bounded verifier/environment repair, then repeat no-paid certification; otherwise reject for practical iteration |

## Next No-paid Prep Plan

1. Create a target profile and package map for `sphinx`.
2. Pin a task-level verifier command that prefers changed tests or narrow module shards, not full-suite execution.
3. Run a 20-30 task no-paid release-certification wave across at least two time buckets.
4. Freeze a rolling-origin split only if the certified count supports at least two evidence-backed windows.
5. Recompute paid baseline discovery cells and stop again before any paid Agent or tuner call.

## Paid Baseline Discovery Estimate

For `sphinx`, the rough baseline-discovery estimate is `360` cells, with a coarse historical cost range of `$72.0` to `$162.0`. This estimate is not an authorization.

## Unsupported Claims

- No paid Agent cell, paid LLM call, or paid tuner call was run.
- No Agent tuning improvement is supported.
- No predictive-validity or cross-repo generalization claim is supported.
- sphinx is a no-paid target-prep recommendation, not an immediate paid-run authorization.
- Projected certified counts are capacity estimates until a bounded release-certification wave proves conversion.
