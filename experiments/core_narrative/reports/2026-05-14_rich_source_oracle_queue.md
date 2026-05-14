# Rich W* Golden-Oracle Queue

Status: `completed`
Generated at: `2026-05-14T15:07:30.080675Z`

## Denominator Boundary

- Accepted direct W* tasks: `5`
- Oracle work items: `18`
- Additional acceptances needed for 20 primary: `15`
- Maximum admitted design count if all queued oracles pass: `23`
- Can reach 20 primary if all queued oracles pass: `True`
- Can reach 20 primary + 5 reserve under current design supply: `False`
- 40-candidate pool gap: `17`

## Queue Composition

- Work item kinds: `{"direct_smoke_replacement_oracle": 3, "direct_tests_without_extractable_nodes": 1, "source_only_golden_oracle": 14}`
- Priorities: `{"high": 5, "low": 8, "medium": 5}`
- Triage codes: `{"behavior_edge_case_probe": 3, "deprioritized_low_behavior_signal": 8, "existing_tests_without_extractable_nodes": 1, "manual_probe_required": 1, "non_discriminating_existing_test": 2, "performance_or_import_behavior_probe": 2, "timeout_verifier_prune_or_rewrite": 1}`

## Boundary

This queue does not admit tasks or authorize primary runs. It only identifies the next hidden-verifier construction work needed after the direct-smoke batch.
