# Three-Repo Paid Readiness Packaging Decision

Decision: `pilot_package_ready_but_precision_target_not_claimable`.
Entry gate status: `ready_for_paid_validation_runbook`.
Paid ready: `True`.

What happened: attrs, boltons, and click were packaged into a frozen local-only paid-validation entry package.

Why it matters: paid validation can now be considered by a later runbook, but predictive validity is still not established.

Release-eligible counts: `{'attrs': 31, 'boltons': 35, 'click': 30}`.
Source-quality audit passed: `True`.
Primary design: `repo_stratified`.
Recommended paid batch: `primary_pilot` with cost range `{'conservative': 60.0, 'lower': 37.21}`.

Research questions:
- RQ1: attrs, boltons, and click are frozen into the paid entry package.
- RQ2: Source-quality audit passed: True.
- RQ3: Primary design is repo_stratified.
- RQ4: Repo-unweighted, repo-stratified, temporal-recent, old weighted diagnostic, and block-randomized stratified candidate are frozen.
- RQ5: Thresholds preregister zero policy violations, endpoint compliance, no raw oracle exposure, scoreability >= 0.95, and primary gap <= 0.15.
- RQ6: Recommended paid batch is primary_pilot with cost range {'conservative': 60.0, 'lower': 37.21}.
- RQ7: Package ready for paid validation runbook: True.
- RQ8: No paid ACUT or paid LLM calls were made by this packaging runbook.

Commits made during the run:
- e36e982d Add three-repo paid readiness packaging scaffold
- 1837d7c7 Record three-repo packaging preflight
- b910487e Freeze three-repo packaging supply snapshot
- 21f27543 Record three-repo packaging source audit
- 95c47168 Preregister three-repo packaging split plan
- 1ce78485 Preregister three-repo packaging baselines
- 2968d96e Preregister three-repo packaging thresholds
- 34da2a5a Plan three-repo packaging paid batches
- f3febf8a Record three-repo packaging entry gate
- final closeout commit: records Step 8 decision artifacts

Tests run:
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_readiness_packaging.py -q` -> returncode `0`
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q` -> returncode `0`
- `git diff --check` -> returncode `0`

Known blockers:
- None for local entry packaging.

Recommended next action categories:
- coordinating session may choose whether to run a later paid validation runbook
- if run, keep repo_stratified as primary and old weighted as diagnostic only
- treat the recommended batch as pilot-grade unless a later preregistration expands precision

Paid-call statement: no paid ACUT solver cells, paid task-solving calls, paid replication, paid LLM generation, or paid LLM review were run by this packaging runbook.

Predictive validity statement: not established. This is a pilot-ready entry package, not a completed paid validation.
