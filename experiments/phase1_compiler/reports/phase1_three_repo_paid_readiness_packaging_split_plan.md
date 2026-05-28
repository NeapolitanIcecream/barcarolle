# Three-Repo Split Plan

What happened: `96` audited tasks were assigned deterministically to `B_eval` and `H_future`.

Why it matters: later paid validation must not choose splits after seeing outcomes.

Primary design: `repo_stratified`.
Primary score: `unweighted_pass_rate_by_repo_split_then_pooled_summary`.
Split seed: `phase1_three_repo_paid_readiness_packaging_20260528_seed_v1`.
Split counts by repo: `{'attrs': {'B_eval': 16, 'H_future': 15}, 'boltons': {'B_eval': 18, 'H_future': 17}, 'click': {'B_eval': 15, 'H_future': 15}}`.

H_future outcomes used for selection or weighting: `False`.
Old weighted design primary: `False`.

Paid validation readiness: split plan is frozen for a later paid runbook.
