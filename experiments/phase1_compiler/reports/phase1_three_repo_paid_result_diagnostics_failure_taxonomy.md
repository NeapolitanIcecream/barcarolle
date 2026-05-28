# Three-Repo Paid Result Diagnostics Failure Taxonomy

Status: `complete`.

What happened: failures and adapter disagreements were labeled from score rows, committed metadata, and bounded raw verifier-output scans.
Why it matters: the labels separate likely solver failure, thin source context, adapter-specific behavior, and verifier/environment suspicion without leaking raw artifacts.
Action suggested next: harden source context and keep verifier/environment as a low-priority watch item, not the main explanation.

- Reviewed tasks: `49`.
- Both-fail tasks included: `22`.
- Adapter-disagreement tasks included: `22`.
- Both-pass contrast tasks included: `5`.
- Raw verifier artifacts found for reviewed tasks: `44`.
- Raw content committed: `false`.

## Explanation Status

- `task_statement_quality`: `inconclusive`.
- `source_context_thinness`: `partially_supported`.
- `verifier_or_environment_issue`: `not_supported`.
- `outlier_task_or_task_family`: `partially_supported`.

## Label Counts

- `adapter_specific_behavior`: `22`.
- `classification_inconclusive`: `5`.
- `likely_agent_solution_failure`: `22`.
- `source_context_too_thin`: `16`.
- `task_intrinsically_hard`: `22`.
