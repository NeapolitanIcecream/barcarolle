# Boltons small expansion inventory

生成时间：`2026-06-15T10:20:07+00:00`。

## Preflight

- Endpoint/model gate: `ready`；present models: `claude-sonnet-4-6, gpt-5.4, gpt-5.4-mini`；endpoint host hash: `9952174049b2`。
- Secret isolation gate: `ready`；agent child sees real endpoint env: `False`。
- Target repo: `mahmoud/boltons`。

## Inventory classes

| Class | Count |
| --- | --- |
| already_displayed_holdout | 10 |
| already_displayed_selection | 20 |
| newly_promotable_after_no_paid_certification | 22 |
| previously_certified_but_unused | 4 |
| unused_smoke_but_release_ready | 1 |

Doubled-timeout repeated top-2 tasks are the existing original Holdout tasks only; count: `10`。

## Rejected or deferred capacity rows

- `attempted_not_certified_collect_failed`: `5`
- `attempted_not_certified_install_failed`: `5`
- `attempted_not_certified_noop_assert_failed`: `10`
- `attempted_not_certified_reference_assert_failed`: `9`
- `blocked_missing_oracle_or_changed_tests`: `32`
- `blocked_source_context_leakage_risk`: `8`
- `raw_cap_deferred_commit_message_only`: `100`
- `technical_certified_needs_source_context_repair`: `7`

## Frozen candidate order preview

| Role | Task | Time | Source |
| --- | --- | --- | --- |
| selection | boltons__supply_expansion_20260526__001 | 2015-04-19T00:13:33-07:00 | supply_expansion_20260526 |
| selection | boltons__supply_expansion_20260526__002 | 2015-04-19T00:30:30-07:00 | supply_expansion_20260526 |
| selection | boltons__supply_expansion_20260526__003 | 2015-04-20T13:52:04-07:00 | supply_expansion_20260526 |
| selection | boltons__supply_expansion_20260526__004 | 2015-04-20T13:52:53-07:00 | supply_expansion_20260526 |
| selection | boltons__supply_expansion_20260526__006 | 2015-05-01T09:16:13+08:00 | supply_expansion_20260526 |
| selection | boltons__supply_expansion_20260526__019 | 2015-07-30T11:07:00+02:00 | supply_expansion_20260526 |
| selection | boltons__v2__068 | 2016-05-16T23:12:59-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__supply_expansion_20260526__048 | 2016-05-23T13:39:22+08:00 | supply_expansion_20260526 |
| selection | boltons__v2__086 | 2016-07-31T19:01:42-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__087 | 2016-08-03T02:11:02-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__091 | 2016-10-24T07:19:32-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__092 | 2016-10-24T08:50:45-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__093 | 2016-10-24T09:13:19-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__095 | 2016-10-25T12:30:18-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__supply_expansion_20260526__066 | 2017-01-16T11:01:53-06:00 | supply_expansion_20260526 |
| selection | boltons__v2__103 | 2017-01-22T18:45:47-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__122 | 2017-04-13T23:58:21-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__128 | 2017-11-08T15:37:41-06:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__132 | 2018-06-19T12:28:43-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__133 | 2018-06-27T16:51:35-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__supply_expansion_20260526__093 | 2018-10-11T12:54:38+05:30 | supply_expansion_20260526 |
| selection | boltons__v2__141 | 2018-10-14T19:44:49+05:30 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__supply_expansion_20260526__095 | 2018-10-17T00:38:58Z | supply_expansion_20260526 |
| selection | boltons__v2__142 | 2018-12-23T23:04:54-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__144 | 2018-12-24T11:37:08-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__147 | 2019-01-15T07:00:03-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__148 | 2019-01-15T07:15:46-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__supply_expansion_20260526__107 | 2019-02-09T00:09:14-08:00 | supply_expansion_20260526 |
| selection | boltons__v2__155 | 2019-02-09T17:33:51-08:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| selection | boltons__v2__163 | 2019-02-12T15:15:17-05:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| later_check | boltons__v2__164 | 2019-02-13T12:18:00+01:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| later_check | boltons__v2__169 | 2019-05-07T14:01:45-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| later_check | boltons__v2__170 | 2019-05-07T14:34:01-07:00 | phase1_three_repo_paid_validation_incremental_boltons_v2 |
| later_check | boltons__clean_ext__001 | 2020-01-06T22:29:17-08:00 | clean_outcome_unseen |
| later_check | boltons__hist__006 | 2020-03-25T10:22:48-04:00 | canonical_history |
| later_check | boltons__hist__007 | 2020-03-28T09:38:32+01:00 | canonical_history |
| later_check | boltons__clean_ext__008 | 2020-03-29T19:27:42-07:00 | clean_outcome_unseen |
| later_check | boltons__clean_ext__010 | 2020-04-21T02:03:26-07:00 | clean_outcome_unseen |
| later_check | boltons__hist__011 | 2020-06-22T01:19:35-04:00 | canonical_history |
| later_check | boltons__hist__013 | 2021-02-21T22:35:25-08:00 | canonical_history |
| later_check | boltons__hist__014 | 2021-05-15T00:08:53-07:00 | canonical_history |
| later_check | boltons__hist__017 | 2022-01-16T07:08:40+08:00 | canonical_history |
| later_check | boltons__clean_ext__017 | 2022-12-07T18:22:36-08:00 | clean_outcome_unseen |
| later_check | boltons__hist__019 | 2022-12-08T03:45:47-06:00 | canonical_history |
| later_check | boltons__hist__020 | 2022-12-08T15:51:37+06:00 | canonical_history |
| later_check | boltons__hist__022 | 2023-02-20T07:22:09+01:00 | canonical_history |
| later_check | boltons__hist__023 | 2023-04-02T15:11:27-04:00 | canonical_history |
| later_check | boltons__hist__024 | 2023-04-20T18:29:33-07:00 | canonical_history |
| later_check | boltons__hist__025 | 2023-04-21T13:05:37+05:30 | canonical_history |
| later_check | boltons__hist__026 | 2023-05-07T01:25:38+08:00 | canonical_history |
| smoke_or_unused | boltons__hist__027 | 2023-10-29T21:31:16-07:00 | canonical_history |
| unused | boltons__hist__028 | 2023-10-31T11:31:12-07:00 | canonical_history |
| unused | boltons__hist__031 | 2024-06-30T00:24:35-07:00 | canonical_history |
| unused | boltons__supply_expansion_20260526__159 | 2025-07-22T13:47:31+02:00 | supply_expansion_20260526 |
| unused | boltons__supply_expansion_20260526__157 | 2025-10-04T13:09:43-04:00 | supply_expansion_20260526 |

本报告只读取 committed sanitized metadata、score tables 和 capacity summaries；没有读取 raw prompts、raw completions、transcripts、solver workspaces 或 verifier workspaces。
