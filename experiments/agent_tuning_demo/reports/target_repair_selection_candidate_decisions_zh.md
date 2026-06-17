# Target repair selection candidate decisions

生成时间：`2026-06-17T13:12:22+00:00`。付费 Agent cells：`0`。付费 LLM calls：`0`。付费 tuner calls：`0`。

## 结论

Candidate-loop terminal state: `candidate_loop_no_ready_target`。Selected target: `None`。

## Decisions

| Repo | Exact certified | Windows | Smoke | Decision | Reason |
| --- | --- | --- | --- | --- | --- |
| sphinx | 16 | 0 | passed_prior | rejected | reject_sphinx_move_to_candidate_loop |
| mypy | 7 | 0 | passed | rejected | exact certification sample conversion 0.2917; corrected threshold requires 80 exact tasks |
| black | 0 | 0 | partial_probe_failure | rejected | projected/existing supply 73 below corrected exact minimum 80 |
| starlette | 0 | 0 | partial_probe_failure | rejected | projected/existing supply 57 below corrected exact minimum 80 |
| attrs | 0 | 0 | passed | rejected | projected/existing supply 31 below corrected exact minimum 80; blockers: projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| click | 0 | 0 | passed | rejected | projected/existing supply 30 below corrected exact minimum 80; blockers: projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven |
| django | 0 | 0 | environment_failed_or_unusable | rejected | classified large_but_heavy; setup/replay blocker not bounded enough for this loop |
| pandas | 0 | 0 | environment_failed_or_unusable | rejected | classified large_but_heavy; setup/replay blocker not bounded enough for this loop |
| scikit-learn | 0 | 0 | environment_failed_or_unusable | rejected | classified large_but_heavy; setup/replay blocker not bounded enough for this loop |
| packaging | 0 | 0 | passed | rejected | projected/existing supply 0 below corrected exact minimum 80; blockers: projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| marshmallow | 0 | 0 | passed | rejected | projected/existing supply 0 below corrected exact minimum 80; blockers: projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_prior_replay_probe_failed; bounded_no_paid_certification_needed |
| urllib3 | 0 | 0 | failed | rejected | projected/existing supply 0 below corrected exact minimum 80; blockers: projected_release_eligible_count_below_60; evidence_backed_multi_window_not_proven; high_visible_smoke_failed; bounded_no_paid_certification_needed |
| pytest | 0 | 0 | not_run | rejected | classified small_pilot_or_backup; exact certification not available from current method; blockers: evidence_backed_multi_window_not_proven; high_complex_or_infrastructure_heavy_tests; bounded_no_paid_certification_needed |
