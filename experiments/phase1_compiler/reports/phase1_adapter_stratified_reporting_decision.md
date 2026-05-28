# Adapter-Stratified Reporting Decision

Status: `complete`.

What happened: adapter-stratified reporting is now policy-backed, tested, and populated for the completed three-repo paid pilot.
Why it matters: the reporting blocker is cleared without spending new paid cells, while the completed paid pilot remains pilot evidence only.
Action suggested next: harden source context and task statements, then redesign the split before any precision-target paid replication.

## Decision

- Primary decision label: `adapter_reporting_policy_ready_but_source_context_next`.
- Adapter reporting policy ready: `true`.
- Paid calls made by this run: `0`.
- Completed paid pilot decision changed: `false`.
- Predictive validity established: `false`.
- Provider-billed exact cost available: `false`.

## Research Questions

| Question | Answer |
| --- | --- |
| RQ1: Did this run make any new paid calls? | No. |
| RQ2: Does the adapter-stratified summary reproduce the diagnostics numbers? | Yes: Codex `22/60`, Kilo `32/60`, both fail `22`, both pass `16`, Codex-only pass `6`, Kilo-only pass `16`. |
| RQ3: Are adapter-level score, cost, and latency now reportable from committed artifacts? | Yes. The summaries use committed result cube, cost summaries, and usage ledger artifacts. |
| RQ4: Does the reporting policy prevent a pooled-only cross-harness headline? | Yes. Adapter-level results are required first; pooled-only cross-harness headlines are disallowed. |
| RQ5: What still blocks a precision-target paid replication? | Source-context/task-statement hardening, split redesign, and the fact that predictive validity is not established. |
| RQ6: What is the recommended next action category? | `source_context_hardening_then_split_redesign_before_precision_paid_replication`. |

## Summary

| Adapter | Passes | Cells | Pass rate | Token-estimated USD | Cost/cell | Median latency |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| `codex_workspace` | 22 | 60 | 0.3667 | 32.22309 | 0.53705 | 115.059s |
| `kilo_workspace` | 32 | 60 | 0.5333 | 19.044243 | 0.31740 | 52.5495s |

Paired disagreement is `22/60 = 0.3667`. Provider-billed exact cost is unavailable because `actual_provider_billed_cost_usd` is null.

## Verification

- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_adapter_stratified_reporting.py -q`: 9 passed.
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests/test_phase1_three_repo_paid_result_diagnostics.py -q`: 5 passed.
- `uv run --project experiments/phase1_compiler pytest experiments/phase1_compiler/tests -q`: 249 passed.
- `git diff --check`: passed.

## Hygiene

- Raw prompts, raw completions, raw ACUT transcripts, solver workspaces, verifier workspaces, raw diffs, raw logs, target repository clones, caches, and secrets were not committed.
- The unrelated untracked external-review package under `experiments/phase1_compiler/external_review/phase1_task_generator_design_review_20260526/` was left unmodified and uncommitted.
- No future runbook was drafted or created.
