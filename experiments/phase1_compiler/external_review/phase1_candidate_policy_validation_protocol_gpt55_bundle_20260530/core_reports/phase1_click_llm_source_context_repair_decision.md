# Click LLM-Assisted Source-Context Repair Decision

Decision label: click_source_repair_clean_enough_for_three_repo_claim

What happened: The frozen 30-task click supply was repaired through sanitized public issue and pull-request context; no LLM calls were needed.
Why it matters: Click no longer has to be described as title-only/minor-risk for the source-quality dimension, but the result remains an exploratory supply-quality improvement rather than predictive-validity evidence.
Action suggested next: Use the repaired click overlay for cleaner narrative support and keep paid ACUT reruns blocked by default.

- Click tasks in scope: 30
- Public-context repaired: 30
- LLM-assisted repaired: 0
- Still title-only/minor-risk: 0
- Rejected or blocked: 0
- Paid LLM calls: 0
- Paid ACUT solver cells: 0
- Token-estimated LLM cost: $0.00
- Predictive validity established: false
- Click claim boundary: click_clean_enough_for_three_repo_claim
- PROCESS.md updated: true

## Boundary

Completed paid outcomes, score tables, selected task ids, split labels, historical source-eligibility artifacts, raw target patches, raw test patches, raw public API payloads, raw prompts, raw completions, and ACUT transcripts were not changed or committed.

## Verification
- uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_click_llm_source_context_repair.py -q: passed (5 tests)
- uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q: passed (287 tests)
- git diff --check: passed

Recommended next action categories:
- use click with the repaired source-quality overlay for cleaner narrative support
- keep paid ACUT reruns blocked unless a future runbook identifies a concrete benchmark-side bug
- preserve the historical exploratory supplement as exploratory evidence
