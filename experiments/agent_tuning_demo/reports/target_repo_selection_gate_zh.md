# 目标仓库选择门禁报告

生成时间：`2026-06-15T06:53:52+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 执行建议

主推荐：`attrs`。备选：`click`。

本轮结论是选择 `attrs` 作为下一轮 no-paid target-prep 的主仓库，而不是今天启动付费调优。本轮没有新仓库在 certification/replay 环节实质优于 attrs/click/boltons。`attrs` 因此是保守 fallback：它已有 31 个 release-eligible 任务、当前 smoke 通过、source/context 时间分布较好，但仍不是 strong multi-window paid-ready 仓库。`click` 是备选；`boltons` 只保留为弱一窗口历史路径，不建议继续作为 stronger demo 主线。

## 候选对比

| Repo | Baseline | Impl+Test | Public refs | Release/projected | Raw windows | Evidence windows | Smoke | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| attrs | True | 361 | 249 | 31 | 8 | 0 | passed | low_current_visible_smoke_passed | prep_candidate_certification_needed |
| boltons | True | 202 | 42 | 57 | 7 | 1 | passed | low_current_visible_smoke_passed | small_pilot_or_backup |
| click | True | 392 | 59 | 30 | 10 | 0 | passed | low_current_visible_smoke_passed | small_pilot_or_backup |
| humanize | True | 90 | 10 | 12 | 5 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| toolz | True | 196 | 12 | 5 | 4 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| cachetools | False | 89 | 53 | 22 | 7 | 0 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |
| dateutil | False | 161 | 6 | 1 | 2 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| jinja2 | False | 251 | 32 | 5 | 9 | 0 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |
| jsonschema | False | 254 | 10 | 2 | 9 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| marshmallow | False | 463 | 106 | 0 | 9 | 0 | passed | high_prior_replay_probe_failed | screened_out_or_supply_below_gate |
| packaging | False | 248 | 179 | 0 | 10 | 0 | passed | high_prior_replay_probe_failed | screened_out_or_supply_below_gate |
| pluggy | False | 103 | 11 | 2 | 8 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| pytest | False | 520 | 234 | 82 | 2 | 0 | not_run | high_complex_or_infrastructure_heavy_tests | small_pilot_or_backup |
| requests | False | 176 | 48 | 12 | 10 | 0 | not_run | medium_external_or_integration_tests_need_isolation | screened_out_or_supply_below_gate |
| rich | False | 0 | 0 | 0 | 0 | 0 |  |  | screened_out |
| sortedcontainers | False | 69 | 6 | 1 | 3 | 0 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| urllib3 | False | 537 | 177 | 0 | 10 | 0 | failed | high_visible_smoke_failed | screened_out_or_supply_below_gate |
| werkzeug | False | 454 | 42 | 6 | 9 | 0 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |

## 旧基线结果

`boltons` 仍只支持弱化的一窗口故事：保守投影 `57` 个 release tasks，低于 `60` 门槛，且当前 Kilo low-cost headroom 只支持一个 evidence-backed window。`attrs` 是先前 fallback，但只有 `31` release-eligible，并且 packaging/verifier pinning 未完成。`click` 有 `30` release-eligible 和较好的技术认证记录，是最稳的 baseline 备选，但 supply 仍更像小 pilot 而不是强多窗口调优 demo。

## 新候选结果

本轮筛查新仓库数：`13`；deep probe 新仓库数：`6`。

| Repo | Impl+Test | Public refs | Release/projected | Raw windows | Smoke | Risk | Label |
| --- | --- | --- | --- | --- | --- | --- | --- |
| packaging | 248 | 179 | 0 | 10 | passed | high_prior_replay_probe_failed | screened_out_or_supply_below_gate |
| jinja2 | 251 | 32 | 5 | 9 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |
| werkzeug | 454 | 42 | 6 | 9 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |
| cachetools | 89 | 53 | 22 | 7 | passed | low_current_visible_smoke_passed | screened_out_or_supply_below_gate |
| pluggy | 103 | 11 | 2 | 8 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| sortedcontainers | 69 | 6 | 1 | 3 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| pytest | 520 | 234 | 82 | 2 | not_run | high_complex_or_infrastructure_heavy_tests | small_pilot_or_backup |
| requests | 176 | 48 | 12 | 10 | not_run | medium_external_or_integration_tests_need_isolation | screened_out_or_supply_below_gate |
| marshmallow | 463 | 106 | 0 | 9 | passed | high_prior_replay_probe_failed | screened_out_or_supply_below_gate |
| jsonschema | 254 | 10 | 2 | 9 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| urllib3 | 537 | 177 | 0 | 10 | failed | high_visible_smoke_failed | screened_out_or_supply_below_gate |
| dateutil | 161 | 6 | 1 | 2 | not_run | medium_needs_current_smoke_or_replay_probe | screened_out_or_supply_below_gate |
| rich | 0 | 0 | 0 | 0 |  |  | screened_out |

## 筛出新候选

| Repo | Reason | Repair |
| --- | --- | --- |
| packaging | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| jinja2 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| werkzeug | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| cachetools | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| pluggy | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| sortedcontainers | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| pytest | evidence_backed_multi_window_not_proven; high_complex_or_infrastructure_heavy_tests; bounded_no_paid_certification_needed | use only as small second-repo pilot or backup unless further certification expands supply |
| requests | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| marshmallow | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| jsonschema | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| urllib3 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_visible_smoke_failed; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| dateutil | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed | do not advance unless new mining or environment repair changes the supply conclusion |
| rich | checkout_dirty_or_partial | repair or reclone the ignored external checkout, then rerun the gate |

## Top 候选 no-paid probe

| Repo | Smoke | Prior cert | Release ready | Projected | Windows | Blockers |
| --- | --- | --- | --- | --- | --- | --- |
| boltons | passed | 30.34/80 observed_prior_no_paid_release_conversion | 42 | 57 | 7 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| attrs | passed | 1/4 observed_prior_no_paid_replay_sample | 249 | 31 | 8 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| click | passed | 30.0/102 observed_prior_no_paid_release_conversion | 59 | 30 | 10 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| packaging | passed | 0/12 observed_prior_no_paid_probe | 179 | 0 | 10 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| jinja2 | passed | no replay sample | 32 | 5 | 9 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| werkzeug | passed | no replay sample | 42 | 6 | 9 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| cachetools | passed | 5/12 observed_prior_no_paid_probe | 53 | 22 | 7 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| marshmallow | passed | 0/3 observed_prior_no_paid_probe | 106 | 0 | 9 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| urllib3 | failed | 0/2 observed_prior_no_paid_probe | 177 | 0 | 10 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_visible_smoke_failed; bounded_no_paid_certification_needed |

## 为什么选择这个仓库

本轮没有新仓库在 certification/replay 环节实质优于 attrs/click/boltons。`attrs` 因此是保守 fallback：它已有 31 个 release-eligible 任务、当前 smoke 通过、source/context 时间分布较好，但仍不是 strong multi-window paid-ready 仓库。`click` 是备选；`boltons` 只保留为弱一窗口历史路径，不建议继续作为 stronger demo 主线。

## 不推荐仓库

| Repo | Why not |
| --- | --- |
| boltons | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| toolz | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| humanize | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| packaging | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| jinja2 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| werkzeug | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| cachetools | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| pluggy | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| sortedcontainers | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| pytest | evidence_backed_multi_window_not_proven; high_complex_or_infrastructure_heavy_tests; bounded_no_paid_certification_needed |
| requests | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| marshmallow | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| jsonschema | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| urllib3 | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_visible_smoke_failed; bounded_no_paid_certification_needed |
| dateutil | projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; bounded_no_paid_certification_needed |
| rich | checkout_dirty_or_partial |

## 下一步 no-paid 准备计划

1. 为 `attrs` 写 target profile/package map/verifier command。
2. 从 release-ready rows 中抽样运行 20-30 个 bounded no-paid certification/replay probes。
3. 只在 conversion、source context、verifier pinning 通过后，冻结两个 rolling-origin windows。
4. 用同一脚本重算 release manifest、split plan、cost plan、artifact-hygiene scan。

## 粗略付费 baseline discovery 计划

若只复用当前 `attrs` 的 `31` task 级别，小型 baseline discovery 约 `124` cells；若 no-paid certification 证明至少 `60` 个 release-eligible tasks，强 demo 下限约 `240` cells（4 个候选 Agent）。按历史单 cell 粗估，小型方案约 `$24.8` 到 `$55.8`；强 demo 需另行重算预算。这不是授权，只是后续 runbook 的预算输入。

## 明确不支持的 claim

- No paid Agent tuning improvement is supported by this gate.
- No predictive-validity or cross-repo generalization claim is supported.
- No repository is immediate-paid-ready until target profile, verifier pinning, split freeze, and baseline discovery gates pass.
- attrs is recommended for next no-paid target preparation, not for starting a tuning experiment today.
