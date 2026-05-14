# Rich Golden-Oracle Queue

Status: `completed`
Split: `R`
Generated at: `2026-05-14T16:37:17.547992Z`

## Denominator Boundary

- Accepted direct tasks: `8`
- Oracle work items: `29`
- Additional acceptances needed for 20 primary: `12`
- Maximum admitted design count if all queued oracles pass: `37`
- Can reach 20 primary if all queued oracles pass: `True`
- Can reach 20 primary + 5 reserve under current design supply: `True`
- 40-candidate pool gap: `3`

## Queue Composition

- Work item kinds: `{"direct_smoke_replacement_oracle": 4, "source_only_golden_oracle": 25}`
- Priorities: `{"high": 2, "low": 4, "medium": 23}`
- Triage codes: `{"behavior_edge_case_probe": 1, "deprioritized_low_behavior_signal": 4, "manual_probe_required": 20, "non_discriminating_existing_test": 1, "rejected_direct_candidate_review": 3}`

## Boundary

This queue does not admit tasks or authorize primary runs. It only identifies the next hidden-verifier construction work needed after the direct-smoke batch.
