# Capped Shrinkage Weights

Status: `pass`.

| Candidate | Status | Weight statuses | Min ESS ratio |
| --- | --- | --- | --- |
| block_plus_shrinkage_weighted | uniform_fallback | {'optimized': 2, 'uniform_fallback': 2} | 0.72 |
| old_weighted_target_profile | reference_only | {'existing_reference_weight': 4} | 0.884689 |

Capped shrinkage mostly falls back to uniform weights under sparse support; old weighted pilot weights remain reference-only.
