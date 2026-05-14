# Rich Golden-Oracle Queue

Status: `completed`
Split: `C`
Generated at: `2026-05-14T17:36:21.740707Z`

## Denominator Boundary

- Accepted direct tasks: `3`
- Oracle work items: `17`
- Additional acceptances needed for 20 primary: `17`
- Maximum admitted design count if all queued oracles pass: `20`
- Can reach 20 primary if all queued oracles pass: `True`
- Can reach 20 primary + 5 reserve under current design supply: `False`
- 40-candidate pool gap: `20`

## Queue Composition

- Work item kinds: `{"direct_smoke_replacement_oracle": 3, "direct_tests_without_extractable_nodes": 1, "source_only_golden_oracle": 13}`
- Priorities: `{"high": 5, "medium": 12}`
- Triage codes: `{"behavior_edge_case_probe": 2, "existing_tests_without_extractable_nodes": 1, "manual_probe_required": 11, "non_discriminating_existing_test": 3}`

## Boundary

This queue does not admit tasks or authorize primary runs. It only identifies the next hidden-verifier construction work needed after the direct-smoke batch.
