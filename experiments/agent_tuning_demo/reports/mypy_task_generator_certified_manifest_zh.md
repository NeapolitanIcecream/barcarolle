# mypy Task Generator certified manifest

生成时间：`2026-06-17T14:49:14+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

exact certified tasks: `100`；threshold state: `preferred_met`。

- selected benchmark size: `20`
- future holdout size: `20`
- time buckets: `{'2024_plus': 100}`
- module families: `{'type_checker': 71, 'semantic_analysis': 14, 'core_or_other': 11, 'mypyc': 4}`
- reservoirs: `{'mypy_typecheck_data_with_impl': 81, 'mypy_python_test_with_impl': 19}`
- verifier duration: `{'count': 100, 'median_seconds': 6.562, 'p95_seconds': 15.27, 'max_seconds': 42.274}`

## Certified rows

| Task | Time | Family | Reservoir | Profile | Seconds |
| --- | --- | --- | --- | --- | --- |
| mypy__taskgen__2304 | 2026-02-11 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 10.933 |
| mypy__taskgen__2305 | 2026-02-12 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 5.501 |
| mypy__taskgen__2306 | 2026-02-12 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 11.207 |
| mypy__taskgen__2307 | 2026-02-12 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 10.444 |
| mypy__taskgen__2308 | 2026-02-13 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 5.62 |
| mypy__taskgen__2309 | 2026-02-13 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.287 |
| mypy__taskgen__2310 | 2026-02-16 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.913 |
| mypy__taskgen__2311 | 2026-02-16 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 9.956 |
| mypy__taskgen__2312 | 2026-02-17 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 10.731 |
| mypy__taskgen__2313 | 2026-02-17 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 10.256 |
| mypy__taskgen__2314 | 2026-02-19 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.181 |
| mypy__taskgen__2316 | 2026-02-22 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.111 |
| mypy__taskgen__2315 | 2026-02-22 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.774 |
| mypy__taskgen__2318 | 2026-02-23 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 8.696 |
| mypy__taskgen__2317 | 2026-02-23 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.946 |
| mypy__taskgen__2320 | 2026-02-23 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.798 |
| mypy__taskgen__2322 | 2026-02-24 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.008 |
| mypy__taskgen__2321 | 2026-02-24 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 10.178 |
| mypy__taskgen__2323 | 2026-02-24 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.864 |
| mypy__taskgen__2325 | 2026-02-25 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.838 |
| mypy__taskgen__2327 | 2026-02-25 | semantic_analysis | mypy_python_test_with_impl | py312_data_or_pytest | 42.274 |
| mypy__taskgen__2330 | 2026-02-26 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 12.436 |
| mypy__taskgen__2331 | 2026-02-26 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 9.197 |
| mypy__taskgen__2332 | 2026-02-26 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.144 |
| mypy__taskgen__2333 | 2026-02-26 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.338 |
| mypy__taskgen__2335 | 2026-02-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.82 |
| mypy__taskgen__2336 | 2026-02-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.827 |
| mypy__taskgen__2337 | 2026-02-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.118 |
| mypy__taskgen__2334 | 2026-02-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 8.61 |
| mypy__taskgen__2338 | 2026-02-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.889 |
| mypy__taskgen__2340 | 2026-03-02 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.456 |
| mypy__taskgen__2341 | 2026-03-03 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.269 |
| mypy__taskgen__2342 | 2026-03-03 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.242 |
| mypy__taskgen__2343 | 2026-03-04 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.109 |
| mypy__taskgen__2344 | 2026-03-04 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 8.551 |
| mypy__taskgen__2346 | 2026-03-04 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.16 |
| mypy__taskgen__2345 | 2026-03-04 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.621 |
| mypy__taskgen__2347 | 2026-03-04 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.688 |
| mypy__taskgen__2349 | 2026-03-10 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 8.668 |
| mypy__taskgen__2348 | 2026-03-10 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.566 |
| mypy__taskgen__2352 | 2026-03-16 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 8.266 |
| mypy__taskgen__2353 | 2026-03-17 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 36.691 |
| mypy__taskgen__2354 | 2026-03-23 | mypyc | mypy_python_test_with_impl | py312_data_or_pytest | 6.383 |
| mypy__taskgen__2355 | 2026-03-25 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 10.154 |
| mypy__taskgen__2357 | 2026-03-30 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.626 |
| mypy__taskgen__2358 | 2026-03-30 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.754 |
| mypy__taskgen__2360 | 2026-04-02 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.538 |
| mypy__taskgen__2361 | 2026-04-03 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.648 |
| mypy__taskgen__2362 | 2026-04-03 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.09 |
| mypy__taskgen__2363 | 2026-04-03 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.821 |
| mypy__taskgen__2365 | 2026-04-09 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.932 |
| mypy__taskgen__2366 | 2026-04-09 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.47 |
| mypy__taskgen__2367 | 2026-04-09 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.519 |
| mypy__taskgen__2371 | 2026-04-13 | type_checker | mypy_python_test_with_impl | py312_data_or_pytest | 6.074 |
| mypy__taskgen__2368 | 2026-04-13 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.932 |
| mypy__taskgen__2369 | 2026-04-13 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.305 |
| mypy__taskgen__2370 | 2026-04-13 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.268 |
| mypy__taskgen__2373 | 2026-04-14 | mypyc | mypy_python_test_with_impl | py312_data_or_pytest | 4.669 |
| mypy__taskgen__2374 | 2026-04-14 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.351 |
| mypy__taskgen__2376 | 2026-04-15 | mypyc | mypy_python_test_with_impl | py312_data_or_pytest | 15.27 |
| mypy__taskgen__2377 | 2026-04-16 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.148 |
| mypy__taskgen__2378 | 2026-04-16 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.86 |
| mypy__taskgen__2380 | 2026-04-17 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 8.691 |
| mypy__taskgen__2381 | 2026-04-17 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.652 |
| mypy__taskgen__2388 | 2026-04-21 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 8.621 |
| mypy__taskgen__2389 | 2026-04-22 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.585 |
| mypy__taskgen__2391 | 2026-04-23 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.099 |
| mypy__taskgen__2392 | 2026-04-23 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 8.871 |
| mypy__taskgen__2394 | 2026-04-24 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.956 |
| mypy__taskgen__2396 | 2026-04-25 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.286 |
| mypy__taskgen__2398 | 2026-04-26 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.157 |
| mypy__taskgen__2401 | 2026-04-29 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.243 |
| mypy__taskgen__2404 | 2026-05-01 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.2 |
| mypy__taskgen__2405 | 2026-05-04 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.233 |
| mypy__taskgen__2406 | 2026-05-04 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.148 |
| mypy__taskgen__2407 | 2026-05-07 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.297 |
| mypy__taskgen__2409 | 2026-05-07 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.644 |
| mypy__taskgen__2410 | 2026-05-07 | core_or_other | mypy_python_test_with_impl | py312_data_or_pytest | 9.617 |
| mypy__taskgen__2411 | 2026-05-08 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.828 |
| mypy__taskgen__2413 | 2026-05-08 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 17.859 |
| mypy__taskgen__2415 | 2026-05-10 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.704 |
| mypy__taskgen__2416 | 2026-05-10 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.422 |
| mypy__taskgen__2417 | 2026-05-10 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 8.189 |
| mypy__taskgen__2418 | 2026-05-12 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.518 |
| mypy__taskgen__2419 | 2026-05-13 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.299 |
| mypy__taskgen__2420 | 2026-05-19 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.092 |
| mypy__taskgen__2421 | 2026-05-19 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 7.166 |
| mypy__taskgen__2422 | 2026-05-19 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.453 |
| mypy__taskgen__2423 | 2026-05-20 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.737 |
| mypy__taskgen__2424 | 2026-05-20 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.599 |
| mypy__taskgen__2426 | 2026-05-21 | type_checker | mypy_python_test_with_impl | py312_data_or_pytest | 6.79 |
| mypy__taskgen__2428 | 2026-05-21 | mypyc | mypy_python_test_with_impl | py312_data_or_pytest | 4.642 |
| mypy__taskgen__2429 | 2026-05-22 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.156 |
| mypy__taskgen__2432 | 2026-05-27 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 18.697 |
| mypy__taskgen__2437 | 2026-05-29 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 5.904 |
| mypy__taskgen__2439 | 2026-06-02 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 8.021 |
| mypy__taskgen__2440 | 2026-06-03 | semantic_analysis | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.051 |
| mypy__taskgen__2442 | 2026-06-04 | semantic_analysis | mypy_python_test_with_impl | py312_data_or_pytest | 5.595 |
| mypy__taskgen__2443 | 2026-06-05 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 17.195 |
| mypy__taskgen__2445 | 2026-06-10 | type_checker | mypy_typecheck_data_with_impl | py312_data_or_pytest | 6.737 |

## Artifact hygiene

manifest 只保留 sanitized task metadata、subgate summaries、command digest 和 evidence digest；未提交 raw stdout/stderr、solver workspace、verifier workspace、prompt、completion 或 transcript。
