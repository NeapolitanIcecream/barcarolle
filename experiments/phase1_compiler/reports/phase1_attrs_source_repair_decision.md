# Phase 1 Attrs Source Repair Decision

Decision: attrs_reached_30_third_repo_still_needed.

What happened: attrs source context was repaired through public upstream context for the three remaining technical-certified attrs tasks.

attrs release eligible before: 28.
attrs release eligible after: 31.
Newly promoted tasks: ['attrs__v2__218', 'attrs__v2__231', 'attrs__v2__237'].
Paid ready: False.

Research questions:
- RQ1: 3 attrs source-review tasks were repaired through public context.
- RQ2: 0 attrs tasks were repaired through reviewed diff-assisted statements.
- RQ3: attrs reached 30 release-eligible tasks: True.
- RQ4: Repaired statements failing leakage or ambiguity review: [].
- RQ5: No paid LLM calls were made.
- RQ6: At least three repos now at 30 release-eligible tasks: False. Repos at threshold: ['attrs', 'boltons'].
- RQ7: The next blocker is third repo supply; attrs and boltons are now at or above 30 release-eligible tasks, but paid readiness requires three repos.

Why it matters: attrs now reaches 30 release-eligible tasks, but paid validation is still blocked by third-repo supply.

Paid calls: No paid ACUT solver cells, paid task-solving calls, paid replication, benchmark scoring, or paid LLM statement-generation/review calls were made.
Artifact hygiene: Committed artifacts contain sanitized metadata, summaries, hashes, provenance classes, review verdicts, and task ids only.

Completed steps:
- Step 0 preflight and dirty-tree audit completed.
- Step 1 sanitized candidate packets completed.
- Step 2 public context search and review completed.
- Step 3 diff-assisted statement repair skipped because public context repaired at least two tasks.
- Step 4 leakage and ambiguity review completed for promoted public-context statement packets.
- Step 5 release eligibility overlay and paid readiness gate recomputed.
- Step 6 decision and closeout written without drafting a follow-up runbook.

Tests run:
- uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_attrs_source_repair.py -q (5 passed)
- uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q (219 passed)
- git diff --check (passed)
- git status --short --untracked-files=all (run; unrelated experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526 remains untracked)

Known blockers:
- third_repo_still_needed
