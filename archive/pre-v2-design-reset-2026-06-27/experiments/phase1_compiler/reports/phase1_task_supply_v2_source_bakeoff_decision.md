# Source Bakeoff Decision

Primary decision: continue_internal_repo_history_v2

Broad local mining found more candidate anchors, but certified supply is still not paid-ready. The next useful move is to certify the v2 pool and repair weak source-context/oracle paths.

Recommended next action: continue_internal_generator_v2_on_selected_repos

| Research Question | Answer |
| --- | --- |
| RQ1 | Yes. Current v1 artifacts reproduce the bottleneck: attrs/toolz/humanize remain below 30, boltons reaches 31 only after adding confirmed historical-environment recoveries. |
| RQ2 | Yes for raw candidate yield and source-reservoir visibility; not yet proven for certified yield because broad v2 candidates still need bounded certification execution. |
| RQ3 | Dominant modes are source context quality, missing oracle for issue-only candidates, and environment/reference subgates. |
| RQ4 | Repos projected at >=30: ['boltons']. The three-repo paid gate is not met. |
| RQ5 | SWE-smith, SWE-bench-Live, and R2E-style systems are feasible design references or future adapters; none is adopted or counted as default certified supply. |
| RQ6 | Paid validation, paid statement generation, benchmark release freeze, generated-oracle promotion, broad multi-language implementation, and ACUT harness work were not implemented and are tracked in the future-direction ledger. |
| RQ7 | Continue internal repo-history v2 on selected repos, then run a bounded certification pass; use external-source adapters only as later spikes. |

Source mixing policy:

{
  "external_tasks_must_be_recertified_locally": true,
  "max_commit_message_only_share_unless_manually_reviewed": 0.2,
  "max_single_source_reservoir_share_unless_waived": 0.7,
  "max_synthetic_or_generated_oracle_share_until_predictive_evidence": 0.25,
  "minimum_source_reservoirs_per_repo_when_feasible": 2,
  "per_repo_certified_candidates_min_before_paid_validation": 30,
  "policy_status": "draft_for_future_release_candidates_not_release_freeze"
}

Verification:

- `uv run --project experiments/phase1_compiler python experiments/phase1_compiler/tools/phase1_task_supply_v2_generator_bakeoff.py --run all` completed with `primary_decision_label=continue_internal_repo_history_v2`.
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_task_supply_v2_generator_bakeoff.py -q` passed: 17 tests.
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q` passed: 201 tests in 34.75s.
- `git diff --check` passed.
