# Baseline Registry

Future validation must compare the candidate against the best eligible simple baseline, not only a weak random sample.

| Baseline | Purpose | Budget matching | Status |
| --- | --- | --- | --- |
| temporal_recent_baseline | Strong recency comparator for future target-repo work. | same per-repo task budget as the candidate | mandatory |
| repo_unweighted_same_budget | Tests whether fixed per-repo budget alone explains performance. | exact same per-repo count as the candidate | mandatory |
| repo_stratified_by_target_profile | Conservative simple stratified comparator and fallback reference. | same repo budget and same eligibility filters | mandatory |
| many_seed_random_same_budget | Distributional same-budget random check; avoids overreading a small seed sample. | same per-repo budget for each random seed | mandatory |
| coverage_only_same_budget | Optional feasible no-paid comparator isolating coarse coverage without target-profile weighting. | same per-repo budget and eligibility filters | add_when_selector_can_be_frozen_outcome_blind |
| stricter_temporal_recent_same_eligibility | Optional stricter temporal variant with exactly matched eligibility and frozen tie-breaks. | same per-repo budget, same eligibility, same source-quality overlays | recommended_for_future_protocol_if_supply_supports_it |

Deferred comparator:
- `external_or_general_benchmark_comparator`: External/general candidates are untrusted until local certification, license status, source provenance, oracle source, and release schema fields are clean.

Boundary:
- Random baseline must be many-seed with frozen seeds.
- External/general candidates are untrusted until certified locally.
- Paid-validation authorization remains `false`.
