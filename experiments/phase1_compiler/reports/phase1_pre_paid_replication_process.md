# Phase 1 Pre-Paid Replication Process

Run id: `phase1_pre_paid_replication_20260526`.

Boundary: no paid ACUT replication and no paid LLM statement-prep calls were run by this readiness process.

Verification command family: `uv run --project experiments/phase1_compiler python -m pytest experiments/phase1_compiler/tests -q` plus `git diff --check` after each artifact step.

## Work Queue

| Step | Name | Status | Commit target | Commit hash |
| --- | --- | --- | --- | --- |
| 0 | Preflight And Boundary Check | completed | Record pre-paid replication readiness preflight | 2d68c6f35204259cacece9dbaae57dcda31e2232 |
| 1 | Freeze Predictive-Validity Thresholds | completed | Preregister pre-paid replication predictive thresholds | 0a3f30d63fb858471f19769290bc7aefbd79f93e |
| 2 | Build The Enriched Candidate Inventory | completed | Build pre-paid replication candidate inventory | 82bab0859d500aff602fe1e141a4737615a44fa0 |
| 3 | Estimate Target Profiles | completed | Estimate pre-paid replication target profiles | pending_current_or_future_commit |
| 4 | Diagnose And Repair Split Matching | pending | Design pre-paid replication split matching | pending_current_or_future_commit |
| 5 | Audit Statement And Source Quality Gates | pending | Audit pre-paid replication statement quality gates | pending_current_or_future_commit |
| 6 | Freeze Release Candidates And Baselines | pending | Freeze pre-paid replication release candidates | pending_current_or_future_commit |
| 7 | Write The Baseline Comparison Plan | pending | Plan pre-paid replication baseline comparisons | pending_current_or_future_commit |
| 8 | Update Power, Sample-Size, And Cost Planning | pending | Plan pre-paid replication power and cost | pending_current_or_future_commit |
| 9 | Build The Paid Replication Entry Package | pending | Build pre-paid replication entry package | pending_current_or_future_commit |
| 10 | Final Decision And Closeout | pending | Record pre-paid replication readiness decision | pending_current_or_future_commit |

## Notes

- The current runbook and overnight-analysis runbook are recorded as inputs if present; their Git tracking state is captured in preflight.
- Historical paid outcomes are stored only as nested reference metadata and are excluded from target-profile estimation and new release selection.
- The paid replication entry package stops at a pilot-grade ready gate; precision-target predictive validity remains underpowered.
