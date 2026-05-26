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
| 3 | Estimate Target Profiles | completed | Estimate pre-paid replication target profiles | 662dbd681e0ca4fd20969b6ce71470ec99472f92 |
| 4 | Diagnose And Repair Split Matching | completed | Design pre-paid replication split matching | 5d6e8b8a05e32737c4b3aa1c3e655f0f0f5ac97a |
| 5 | Audit Statement And Source Quality Gates | completed | Audit pre-paid replication statement quality gates | e5b8b240b187acb85dccf348975043954557e877 |
| 6 | Freeze Release Candidates And Baselines | completed | Freeze pre-paid replication release candidates | 48afa84f269af09544187886add14faa7f40345b |
| 7 | Write The Baseline Comparison Plan | completed | Plan pre-paid replication baseline comparisons | 6f5144d2460aae8d86035387c6653e6fddca8493 |
| 8 | Update Power, Sample-Size, And Cost Planning | completed | Plan pre-paid replication power and cost | 8a5a9268c11abf75a055caf7188b0965574413a5 |
| 9 | Build The Paid Replication Entry Package | completed | Build pre-paid replication entry package | pending_current_or_future_commit |
| 10 | Final Decision And Closeout | pending | Record pre-paid replication readiness decision | pending_current_or_future_commit |

## Notes

- The current runbook and overnight-analysis runbook are recorded as inputs if present; their Git tracking state is captured in preflight.
- Historical paid outcomes are stored only as nested reference metadata and are excluded from target-profile estimation and new release selection.
- The paid replication entry package stops at a pilot-grade ready gate; precision-target predictive validity remains underpowered.
